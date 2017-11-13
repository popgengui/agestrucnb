'''
Description
Wrapper to execute the program LDNe2.
'''
from builtins import object
__filename__ = "pgldnecontroller.py"
__date__ = "20170314"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os
import agestrucne.pgutilities as pgut
import tempfile


'''
Constants used by the class objects.
'''

COMMON_VALUE_KEYS_ORDERED= ["number_of_crits",
									"crits",
									"tab_output_files",
									"CI_or_not",
									"mating",
									"max_indiv_per_pop",
									"pop_range",
									"locus_range",
									"output_file_name",
									"input_file_name" ]

'''
2017_03_19.
These bool-returning lambdas are used in def 
__common_values_look_valid.  Note that we are 
still expecing a list of floats for "crits," but that,
for now, we allow only a single float in the crits list,
as well as allowing only "1" for number of critical values.
'''
COMMON_VALUE_VALIDATIONS={ \
				"number_of_crits":lambda x: type(x)==int and x==1,
				"crits":lambda x: type(x)==list and len(x)==1 and type( x[0] )==float,
				"tab_output_files":lambda x: type(x)==int and x in [ 0,1 ],
				"CI_or_not":lambda x: type( x )==int and x in [ 0,1 ],
				"mating":lambda x: type(x)==int and x in [ 0,1 ],
				"max_indiv_per_pop":lambda x: type(x)==int and x>=0,
				"pop_range":lambda x: (x==0) or ( type(x)==str and len( x.split() ) == 2 \
									and type( eval( x.split()[ 0 ] ) ) == int \
									and type( eval( x.split()[1 ] ) ) == int \
									and int( x.split()[ 0 ] ) <= int( x.split()[1] ) ),
				"locus_range":lambda x: ( x==0 ) or ( type(x) == str and len( x.split() ) == 2 \
									and type( eval( x.split()[ 0 ] ) )== int \
									and type( eval( x.split()[ 1 ] ) ) == int \
									and int( x.split()[ 0 ] ) <= int( x.split()[1] ) ),
				"output_file_name":lambda x: type(x)==str and x != "" and not( os.path.exists( x ) ),
				"input_file_name":lambda x: type(x)==str and x != "" and os.path.exists( x ) }

EXTRA_VALIDITY_INFO= { "number_of_crits":None,
									"crits":None,
									"tab_output_files":None,
									"CI_or_not":None,
									"mating":None,
									"max_indiv_per_pop":None,
									"pop_range":None,
									"locus_range":None,
									"output_file_name":"value must name a file that does not exist",
									"input_file_name":"value must name a file that does not exist" }

DEFAULT_LOC_INSIDE_DIST="bin"

EXEC_NAMES_BY_OS= { pgut.SYS_LINUX:"LDNe2OptDbL",
					pgut.SYS_WINDOWS:"LDNe2OptDb.exe",
					pgut.SYS_MAC:"LDNe2OptDbOSX" }

class PGLDNe2Controller( object ):
	'''
	2017_03_15
	Wrapper to execute the program LDNE2.  This is to be used
	by pgopneestimator.py in the same way it uses the pygenomics 
	class genomics.popgen.ne2.controller.py class called 
	NeEstimator2Controller.  This class has has a def called
	runWithNeEstimatorParams which takes the same set of 
	paramaters as does the pygenomcis controller,
	but of course only uses those it shares with the latter class,
	in order to call the LDNe2 executable with a suitable config 
	file.  See class in module pgopneestimator.py for how objects
	of this class are used instead of the NeEstimator2Controller
	class objects.
	'''

	def __init__( self, s_executable_and_path=None, dv_params=None ):

		if s_executable_and_path is None:
			self.__set_exec_to_default()
		else:
			self.__exec=s_executable_and_path
		#end if execuable is none else caller-provided

		
		'''
		2017_03_15.  Currently we call the executable with only
		the "common settings," so called in the source.
		This list of parameters are presumably the common settings, used
		by this object when it makes a configuration file that
		the executable reads in when it gets an arg of the form,
		"c:<configfile>" in the command command.  These comments 
		head the source function RunMultiCommon, called when main()
		parses the args noted above:
			// 1. Number of (positive) critical values
			// 2. Critical values if applicable (i.e., number on line 2 is positive)
			// 3. Plan/Generations for Temporal if applicable.
			// 4. Tabular-format output file(s)
			// 5. CI or not (parameter and non-parameter)
			// 6. Random/Monogamy for LD if applicable
			// 7. Max individuals per pop.
			// 8. Population range
			// 9. Locus ranges to run
			// 10. Common output file name
			// Then the rest, at each line, are input file names including paths
			// if necessary.

		Trials show that line 3 turns tab files on/off, and
		line 4 turns CI's on/off, line 5 is Random/Monog, etc,
		so that the "Plan/Generations," at lease in our case,
		when lines 1 and 2 are standard number of crits and
		matching number of entries for crits, is skipped.
		We adjust our dict accordingly. 

		For most values we initialize to 0 for the default, 
		but we default to 1 critical value, 0.0, and
		1 to elicit CI's, and 1 to get a tabular output file.
		'''

		self.__common_values={ "number_of_crits":1,
									"crits":[0.0],
									"tab_output_files":1,
									"CI_or_not":1,
									"mating":0,
									"max_indiv_per_pop":0,
									"pop_range":0,
									"locus_range":0,
									"output_file_name":"",
									"input_file_name":"" }

		'''
		If the client supplied some values, we
		reset our dict to reflect the client's 
		request:
		'''
		if dv_params is not None:
			self.setCommonValues()
		#end if client wants to specify a set 
		#of param values

		return
	#end __init__

	def __set_exec_to_default( self ):

		'''
		This def assumes that the location of the current module
		is the same as the directory under which the LDNe2 executable
		is located, inside any subdirs named by DEFAULT_LOC_INSIDE_DIST.
		'''

		s_curr_mod_path = os.path.dirname ( os.path.abspath(__file__) )

		s_platform=pgut.get_platform()
		self.__exec=s_curr_mod_path + os.path.sep \
					+ DEFAULT_LOC_INSIDE_DIST \
					+ os.path.sep \
					+ EXEC_NAMES_BY_OS[ s_platform ]
		return
	#end __set_exec_to_default

	def __make_temp_file_name_inside_current_directory( self ):

		s_filename=None
		s_current_dir= os.path.abspath(os.curdir)
		s_filename=tempfile.mktemp( dir=s_current_dir )
		
		return s_filename
	#end __make_temp_file_name_inside_current_directory

	def __get_temp_config_file( self ):

		b_values_ok, s_messages=self.__common_values_look_valid()

		if not( b_values_ok ):

			s_msg="In PGLDNe2Controller, def __get_temp_config_file, "\
						+ "the program found invalid parameter values " \
						+ "for LDNe2: " + s_messages
			
			raise Exception( s_msg )
		#end if invalid values

		'''
		This def assumes that the filename delivered
		via the call to __make_temp_file_name is either 
		unique, or over-writeable, as it does no checking
		for a pre-existing file, and will overwrite it if
		it exists.
		'''

		s_filename=self.__make_temp_file_name_inside_current_directory()

		o_file=open( s_filename, 'w' )

		for s_key in COMMON_VALUE_KEYS_ORDERED:
			'''
			The "crits" parameter requires special handling,
			because it is a list of floats. In the 
			common case, though, it will be a list with
			only one value.
			'''
			if s_key=="crits":
				s_critsline=" ".join( \
							[ str( f_val ) for f_val \
							in self.__common_values[ s_key ] ] )

				'''
				Appending an asterisek to the last crit value 
				will prevent LDNe2 from adding output evaluating 
				at crit value 0.0, otherwise included by default:
				'''
				s_critsline+="*"
				o_file.write( s_critsline + "\n" )
			else:		 
				o_file.write( str( self.__common_values[ s_key ] ) + "\n" )
			#end if crits else not

		#end for each common value 

		o_file.close()

		return s_filename
	#end __get_temp_config_file

	def __common_values_look_valid( self ):
		
		ls_msgs=[]	
		b_return_value=True

		for s_key in self.__common_values:
			v_val=self.__common_values[ s_key ]	
			b_is_valid=COMMON_VALUE_VALIDATIONS[ s_key ]( v_val )

			if not b_is_valid:
				b_return_value=False
				s_this_msg="Invalid " + s_key + " value, " + str( v_val ) + "."
				if EXTRA_VALIDITY_INFO[ s_key ] is not None:
					s_this_msg += " " + EXTRA_VALIDITY_INFO[ s_key ] + "."
				#end if extra message
					
				ls_msgs.append( s_this_msg )
			#end if not valid
		#end for each parameter, test
				
		return b_return_value, "\n".join( ls_msgs )	

	#end __common_values_look_valid									

	def __get_file_name_from_dir_and_path( self, s_in_dir, s_file ):

		s_path_and_name=None
		
		s_path_and_name=s_in_dir + os.path.sep + s_file 

		return s_path_and_name
	#end __get_input_file_name

	def __update_ldne2_values_with_applicable_neestimator_values( self, s_in_dir, s_gen_file, 
																	s_out_dir, s_out_file,
																	crits, LD, hets, coanc, 
																	temp, monogamy, options ):
		'''
		2017_03_15. Input for this def are arguments meant for the pygenomics object
		NeEstimator2Controller, in its "run" def.  We use them to extract those applicable
		to the parameters used by LDNe2, and update our objects parameter values set,
		__common_values. 
		'''
		s_input_file_name = self.__get_file_name_from_dir_and_path( s_in_dir, s_gen_file ) 

		s_output_file_name = self.__get_file_name_from_dir_and_path( s_out_dir, s_out_file )

		self.setCommonValue( "input_file_name", s_input_file_name )
		self.setCommonValue( "output_file_name", s_output_file_name )
		self.setCommonValue( "crits", crits )
		self.setCommonValue( "mating", int( monogamy ) )
		
		return
	#end __update_ldne2_values_with_applicable_neestimator_values

	def runWithCommonValues( self ):

		s_config_file=self.__get_temp_config_file()

		'''
        Windows paths with directory names that
        include spaces will be misinterpreted by
        the system call unless we enclose the
        path and executable name in quotes.
		'''
		quoted_exe_path = "\"" + self.__exec + "\""

		os.system( quoted_exe_path + \
					  ' c:' + s_config_file + \
					  ' >' + os.devnull + ' 2>&1')

		os.remove( s_config_file )
		
		return
	#end def runWithCommonValues

	def runWithNeEstimatorParams ( self, s_in_dir, s_gen_file, s_out_dir, s_out_file,
					crits=None, LD=True, hets=False, coanc=False, temp=None,
					monogamy=False, options=None ):

		'''
		2017_03_15.  We are adding this class as a means to do LDNe2 as an alternatve to 
		running NeEstimator using Tiago's NeEstimator2Controller in his module 
		genomics/popgen/ne2/controller.py, and want to change the client class (PGOpNeEstimator)
		interface in PGOpNeEstimator instances as little as possible, and retain its ability
		to do the original operations.  So, we are keeping the signature  def identical to that in 
		Tiago's class def "run".

		I am also (currently) allowing the same set of options that clients of NeEstimator2Controller
		send into this def, to be sent here.  I will convert those applicable to LDNe (there will
		be some (most of them) not applicable, but unique to NeEstimator), in a special def call, 
		that will also update, where applicable, this objects set of parameter values.
		
		From Tiago's def "run":
        Args:
            in_dir: The input directory
            gen_file The genepop file
            out_dir: The output directory
            out_file Where the output will be stored
            LD: Do LD method
            hets: Do excessive heterozygosity
            coanc: Do Molecular coancestry
            temp: List of generations for the temporal method (None = Not do)

        '''

		self.__update_ldne2_values_with_applicable_neestimator_values(  s_in_dir, s_gen_file, 
																		s_out_dir, s_out_file, 
																		crits, LD, hets, coanc, 
																		temp, monogamy, options )
		self.runWithCommonValues()			

		return
	#end def runWithNeEstimatorParams
#
#	def runWithNeEstimatorParams ( self, s_in_dir, s_gen_file, s_out_dir, s_out_file,
#					crits=None, LD=True, hets=False, coanc=False, temp=None,
#					monogamy=False, options=None ):
#
#		'''
#		2017_03_15.  Because we are adding this class to the NeEstimator controller
#		class (Tiago's NeEstimator2Controller in his module genomics/popgen/ne2/controller.py)
#		and want to change the interface in PGOpNeEstimator instances as little as possible,
#		I am keeping the signature and name of this def identical to that in Tiago's module.
#		I am also (currently) allowing the same set of options that clients of NeEstimator2Controller
#		send into this def, to be sent here.  I will convert those applicable to LDNe (there will
#		be some not applicable, but unique to NeEstimator), in a special def call, that will also
#		update, where applicable, this objects set of parameter values.
#		
#		From Tiago's def "run":
#        Args:
#            in_dir: The input directory
#            gen_file The genepop file
#            out_dir: The output directory
#            out_file Where the output will be stored
#            LD: Do LD method
#            hets: Do excessive heterozygosity
#            coanc: Do Molecular coancestry
#            temp: List of generations for the temporal method (None = Not do)
#        '''
#
#		self.__update_ldne2_values_with_applicable_neestimator_values(  s_in_dir, s_gen_file, 
#																		s_out_dir, s_out_file, 
#																		crits, LD, hets, coanc, 
#																		temp, monogamy, options )
#		s_config_file=self.__get_temp_config_file()
#
#
#        #Windows paths with directory names that
#        #include spaces will be misinterpreted by
#        #the system call unless we enclose the
#        #path and executable name in quotes.
#		quoted_exe_path = "\"" + self.__exec + "\""
#
#		os.system( quoted_exe_path +
#                  ' c:' + s_config_file + ' >' + os.devnull + ' 2>&1')
#
#		os.remove( s_config_file )
#		
#		return
#	#end def runWithNeEstimatorParams

	def	setCommonValue( self, s_common_value_name, v_value ):
		if s_common_value_name not in self.__common_values:
			s_msg="In PGLDNe2Controller instance, def setCommonValue, "  \
								+ "common value name, " + str( s_common_value_name )  \
								+ "is not among valid common file name keys in " \
								+ "attribute __dv_common_values: "  \
								+ str( list( self.__common_values.keys() ) )  + "."

			raise Exception( s_msg )
		#end if unknown name

		self.__common_values[ s_common_value_name ] = v_value
		return
	#end setCommonValue

	def setCommonValues( self, dv_values_by_param_name ):
		for s_param_name in dv_values_by_param_name:
			self.setCommonValue( s_param_name, 
						dv_values_by_param_name[ s_param_name ] )
		#end for each param name
		return
	#end setParameters

	def setCommonValuesFromNeEstimatorParams( self, dv_neestimator_params ):
		self.__update_ldne2_values_with_applicable_neestimator_values( dv_neestimator_params )
		return
	#end setCommonValuesFromNeEstimatorParams
		
#end PGLDNe2Controller

if __name__ == "__main__":
	import agestrucne.pgldne2outputparser as ldneparser

	s_genepop="mygp2.txt"

	o_controller=PGLDNe2Controller()

	o_controller.setCommonValue( "input_file_name", s_genepop )
	o_controller.setCommonValue( "output_file_name", "googoo2" )
	o_controller.setCommonValue( "crits", [ 0.01 ] )
	o_controller.setCommonValue( "locus_range", "1 1" )
	o_controller.setCommonValue( "pop_range" , "10 20" )
	o_controller.runWithCommonValues()
	o_parser=ldneparser.PGLDNe2OutputParser( "googoo2x.txt" )
	
#end if main

