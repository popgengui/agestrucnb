'''
Description
For the Ne-estimation gui, the operation object
that takes simupop-operation results (from the pgopsimupop
object), and performes and ldne analysis using Tiago Antao's
ne.py code and his other utilitites.
'''
__filename__ = "pgopneestimator.py"
__date__ = "20160502"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

__REQUIRE_PYGENOMICS__=False

import sys


'''
2017_04_15. This test and the __REQUIRE_PYGENOMICS__ flag added above
allow the program to rely exclusively on the LDNe2 executable as shipped
with the program in the bin directory, which renders pygenomics unnecessary.
'''

if __REQUIRE_PYGENOMICS__ == True:
	from genomics.popgen.ne2.controller import NeEstimator2Controller
	from genomics.popgen import ne2

#end if we are using the pygenomics package

'''
2017_03_16.  New class to allow using LDNe2 instead 
of NeEstimator (see defs below that select estimator
program baseed on new class __init__ param 
"s_estimator_name."
'''
import agestrucne.pgldne2controller as pgldne

from agestrucne.apgoperation import APGOperation

from agestrucne.pginputneestimator import PGInputNeEstimator
from agestrucne.pgoutputneestimator import PGOutputNeEstimator

import agestrucne.pgutilities as pgut

import sys
import os
#so we can the NeEstimator session in its own
#temporary directory:
import tempfile

#so we can copy renamed input files
import glob

'''
2017_03_15. Adding constants to distinguish 
the use of NeEstimator vs LDNe in order to 
get the ldne estimation.
'''

NEESTIMATOR="Ne2"
LDNE_ESTIMATION="LDNe2"

'''
This allows pgdriveneestimator to get the correct 
executable name, to test for its presence before
running.  
'''

LDNE_EXEC_BY_OS=pgldne.EXEC_NAMES_BY_OS.copy()
LDNE_DEFAULT_LOC_IN_DIST=pgldne.DEFAULT_LOC_INSIDE_DIST

'''
2017_03_19. Depending on the estimator, we call the 
applicable def:
'''
def_neestimator=None

if __REQUIRE_PYGENOMICS__ == True:
	def_neestimator=NeEstimator2Controller.run
#end no def for neestimator unless pygenomics is required

RUN_DEF_BY_ESTIMATOR={ NEESTIMATOR:def_neestimator,
						LDNE_ESTIMATION:pgldne.PGLDNe2Controller.runWithNeEstimatorParams }

class PGOpNeEstimator( APGOperation ):
	'''
	For the Ne-estimation gui, the operation object
	that takes simupop-operation results (from the pgopsimupop
	object), and performes and ldne analysis using Tiago Antao's
	ne.py code and his other utilitites.

	2017_03_15. We are revising this class to add the option to use
	the program LDNe (beta version) instead of NeEstimator.  New
	__init__ parameter tells the object which program is to be used.
	
	'''
	def __init__( self, o_input=None, 
							o_output=None, 
								s_estimator_name=NEESTIMATOR, 
									s_parent_dir_for_workspace=None ):

		'''
		2017_03_27. Adding parameter s_parent_dir_for_workspace to allow
		for the gui to use a temp directory.  This object will run still
		run the estimator in a separate temporary dir, but it will put
		that directory inside that given by s_parent_dir_for_workspace,
		if it is not None
		'''
		super( PGOpNeEstimator, self ).__init__( o_input, o_output )

		self.__indir=None
		self.__outdir=None
		self.__infile=None
		self.__outfile=None

		'''
		2017_03_29.  To allow passing the executable path
		into the controller objects.  Motivated by a problem
		finding the path to the LDNe2 executable during
		instantiation of the object.
		'''
		self.__ldne_path=None
		self.__neestimator_path=None

		'''
		2017_03_27.  This is set in doOp(), so that the
		curdir can be saved, and then returned-to after
		changing to a temp directory, which now may be
		different than a subdirectdory inside the curdir.
		'''
		self.__original_op_path=None
		self.__parent_dir_for_workspace=s_parent_dir_for_workspace

		if s_estimator_name not in [ NEESTIMATOR, LDNE_ESTIMATION ]:
			s_msg="In PGOpNeEstimator instance, def __init__, " \
						+ "caller passed unknown estimator name: " \
						+ s_estimator_name + "."
			raise Exception( s_msg )
		elif s_estimator_name == NEESTIMATOR and __REQUIRE_PYGENOMICS__ == False:
			s_msg="In PGOpNeEstimator instance, def __init__, " \
						+ "the caller has selected " + NEESTIMATOR \
						+ " as for LDNe estimations, " \
						+ " but this module has its __REQUIRE_PYGENOMICS__ " \
						+ " flag set to false."
			raise Exception( s_msg )
		else:
			self.__estimator_to_use=s_estimator_name
		#end if unknown name else known

		return
	#end __init__

	def prepareOp( self ):
		'''
		abstract base class requires this def
		'''
		raise Exception( "def not implemented" )
	#end prepareOp

	def __extract_file_in_out_info( self ):

		'''
		Because we are, per Tiago's advice, running
		the NeEstimator with currdir in a temp directory,
		we use absolute paths to input/output files to 
		simplify copying to/from temp dir:
		'''

		self.__indir, self.__infile= \
				self.__get_separate_dir_and_file_name( self.input.genepop_file )

		self.__outdir, self.__outfile= \
				self.__get_separate_dir_and_file_name (  self.output.run_output_file  )
		return
	#end __extract_file_in_out_info

	def __get_separate_dir_and_file_name(self,  s_filename ):

		s_abs_path_and_file=os.path.abspath( s_filename )
		s_dir=os.path.dirname( s_abs_path_and_file )
		s_file=os.path.basename( s_abs_path_and_file )

		return(  s_dir, s_file ) 
	#end get_separate_dir

	def __set_original_op_directory_path( self ):
		self.__original_op_path=os.path.abspath( os.path.curdir )
		return
	#end __set_current_directory_path

	def __change_current_directory_to_temporary_directory( self ):

		s_parent_dir=None
		s_temp_dir=None

		if self.__parent_dir_for_workspace is None:

			s_parent_dir = \
					os.path.abspath( os.path.curdir )

			#make the temp dir inside the current directory
		else:
			s_parent_dir = self.__parent_dir_for_workspace
		#end if client assigned no parent dir, use currdir, else use client's dir
	
		s_temp_dir=tempfile.mkdtemp( dir=s_parent_dir )
		os.chdir( s_temp_dir )

		return s_temp_dir
	#end __change_current_directory_to_temporary_directory

	def __return_to_original_non_temporary_directory( self ):

		'''
		Assumes that the temporary directory is
		the current directory when this def is called,
		and that the original directory to which to return
		is the parent of the current directory

		2017_03_27.  We now may be using a temporary directory
		whose path is not a subdirectory of the original
		directory used for the operation.  Hence we have
		now store the original operation directory, its
		absolute path, as a class attribute:
		'''

		try:
			os.chdir( self.__original_op_path )
		except Exception as oex:
			s_msg="An exception occurred in PGOpNeEstimator instance, " \
						+ "def __return_to_original_non_temporary_directory, " \
						+ "with message: " + str( oex )
			raise Exception( s_msg )
		#end try ... except

		return
	#end __return_to_original_non_temporary_directory

	def __remove_temporary_directory_and_all_of_its_contents( self, s_temp_dir ):

		'''
		Note: shutil.rmtree fails on encountering readonly files
		We add a few paranoia-induced checks, in case the arg s_temp_dir
		is not, as intended, solely the garbage dump for NeEstimator
		'''

		CORRECT_TMP_DIR_PREFIX="tmp"
		NUMBER_SUBDIRS_EXPECTED=0
		SUSPICOUSLY_HIGH_FILE_COUNT=4

		tup_path_head_tail =  os.path.split( s_temp_dir )
		
		s_dir_name=tup_path_head_tail[ 1 ]

		if not( s_dir_name.startswith( CORRECT_TMP_DIR_PREFIX ) ):
				s_msg = "in PGOpNeEstimator instance, " \
							+ "def __remove_temporary_directory_and_all_its_contents, " \
							+ "s_temp_dir directory name, " \
							+ s_temp_dir \
							+ " should begin with \"tmp\"."

				raise Exception(  s_msg )
		#end if non-tmp name

		i_num_subdirs=len( pgut.get_list_subdirectories( s_temp_dir ) )
		i_num_files=len( pgut.get_list_file_objects( s_temp_dir ) )
		
		if i_num_subdirs > NUMBER_SUBDIRS_EXPECTED \
				or i_num_files >= SUSPICOUSLY_HIGH_FILE_COUNT:
				s_msg="in PGOpNeEstimator instance, " \
							+ "def __remove_temporary_directory_and_all_its_contents, " \
							+ "temp dir: " + s_temp_dir \
							+ ", not able to remove temp directory " \
							+ "due to unexpectedly high " \
							+ "file count, " + str( i_num_files )  \
							+ ", and/or subdirectory count, " + str(i_num_subdirs ) + "."
				raise Exception( s_msg )
		else:
				pgut.do_shutil_rmtree( s_temp_dir )
		#end if high file or subdir count, error, else remove 

		return
	#end __remove_temporary_directory_and_all_its_contents

	def __copy_genepop_input_and_get_temp_file_names( self ):

		s_temp_input_filename="tempgp"
		s_temp_output_base="tempout"

		s_currdir=os.path.abspath( os.curdir )

		pgut.do_shutil_copy( self.__indir + os.path.sep + self.__infile, 
						s_currdir + os.path.sep + s_temp_input_filename )

		return s_temp_input_filename, s_temp_output_base
	#end __prepare_temp_files_and_get_temp_file_names

	def __correct_and_add_columnar_output_file_if_not_present( self, 
														ls_output_files,
														s_temp_out_base ):
		'''
		This def assumes that the current directory is the temp
		directory in which the estimator wrote its output files.
		'''

		LDNE_COLUMN_FILE_EXT="x.txt"

		ls_columnar_files=glob.glob( \
				"*" + LDNE_COLUMN_FILE_EXT )
		
		if len( ls_columnar_files ) != 1:
			s_msg="In PGOpNeEstimator instance, " \
						+ "def correct_and_add_columnar_output_file_if_not_present, " \
						+ "the number of LDNe2 result files with the columnar-file " \
						+ "extension should be one, but " + str( len( ls_columnar_files ) ) \
						+ " were found.  List of files:\n" + str( ls_columnar_files )
			raise Exception( s_msg )
		#end if  non uniq file found

		if ls_columnar_files[ 0 ] not in ls_output_files:
			#We correct the file name. 
			s_corrected_name= s_temp_out_base + LDNE_COLUMN_FILE_EXT
			pgut.do_shutil_move( ls_columnar_files[ 0 ], s_corrected_name )
			ls_output_files.append( s_corrected_name )
		#end if columnar file name not in output files list

		return
	#end __correct_and_add_columnar_output_file_if_not_present

	def __copy_results_to_orig_dir( self, s_temp_out_base ):
		'''
		This def assumes our current dir is still the 
		temp dir with result files inside.
		'''
		ls_output_files=glob.glob( s_temp_out_base + "*" )

		if self.__estimator_to_use == LDNE_ESTIMATION:
			'''
			2017_03_30.  Sometimes LDNe2 misnames (truncates) the 
			columnar output file name (*x.txt), when there are dot 
			characters in the outfile path/name supplied to LDNe2 as the
			output base name, so that the glob expression
			does not find it.
			'''
			self.__correct_and_add_columnar_output_file_if_not_present( \
												ls_output_files,
												s_temp_out_base )
		#end if we are using LDNe

		for s_file in ls_output_files:
			s_copy_for_orig_dir=self.__outdir + os.path.sep \
					+ s_file.replace( s_temp_out_base, self.__outfile )
			pgut.do_shutil_copy( s_file, s_copy_for_orig_dir  )
		#end for each file prefixed with our temp output file name

		return
	#end __copy_results_to_orig_dir

	def __get_op_neestimator( self ):
		o_op_object=None
		s_path=None

		if self.__ldne_path is not None:
			s_path=self.__ldne_path
		#end if we have an ldne path

		o_op_object=NeEstimator2Controller( 
					s_executable_and_path = s_path )

		return o_op_object
	#end def __get_op_neestimator

	def __get_op_ldne( self ):
		'''
		2017_03_15.  Not yet implemented.
		'''
		o_op_object=None
		o_op_object=pgldne.PGLDNe2Controller()
		return o_op_object
	#end __get_op_ldne

	def doOp( self ): 
		'''
		2017_03_15.  Adding an option to use the LDNe program
		instead of NeEstimator.
		'''
		if self.__estimator_to_use == NEESTIMATOR:
			o_op_object=self.__get_op_neestimator()
		elif self.__estimator_to_use == LDNE_ESTIMATION:
			o_op_object=self.__get_op_ldne()
		else:
			s_msg="In PGOpNeEstimator instance, def doOp, " \
						+ "Unknown estimator name: " \
						+ self.__estimator_to_use + "."
			raise Exception( s_msg )
		#end if NeEstimator, else LDNe, else unknown

		#This gives our instance attributes
		#values for dirnames and filenames
		#for the input genepop file and the
		#output base name:
		self.__extract_file_in_out_info()
	
		self.__set_original_op_directory_path()

		#run the estimator in a temporary directory, per Tiago's recommendation:
		s_temp_dir=self.__change_current_directory_to_temporary_directory()

		s_temp_in, s_temp_out=self.__copy_genepop_input_and_get_temp_file_names()	

		#run estimator -- give it full path to currdir:
		s_currdir=os.path.abspath( os.curdir )

		'''
		2017_03_20.  Signature of the NeEstimator2Controller.run and our
		PGLDNe2Controller.runWithNeEstimatorParams is the same.
		We call the def with our estimator controller instance as the first
		arg.  
		'''
		RUN_DEF_BY_ESTIMATOR[ self.__estimator_to_use ]( o_op_object,
														s_currdir, s_temp_in, 
														s_currdir, s_temp_out, 
													**( self.input.run_params  ) )

		self.__copy_results_to_orig_dir( s_temp_out )
			
		#make the current directory the original, before the change to a temporary dir:
		self.__return_to_original_non_temporary_directory()

		self.__remove_temporary_directory_and_all_of_its_contents( s_temp_dir )
		
		self.output.parseOutput()

		#in case the NeEstimator
		#generated a NoDat.txt file
		#we parse (output object
		#checks for NoDat.txt file,
		#does nothing if there is 
		#no file)
		self.output.parseNoDatFile()
		
		return
	#end doOP

	def deliverResults( self ):
		'''
		abstract base class requires this def
		'''
		return self.output.parsed_output
	#end deliver results 

	def getOutputColumnNumberForFieldName( self, s_field_name ):
		'''
		2017_02_11. In implementing a bias adjustment to NeEstimator
		ldne estimates, in pgdriveneestimator, we need a way to
		easily get the Nb (i.e. Nb when Ne calculated on a cohort),
		value from this object, since we want to keep the PGOutputNeEstimator
		objecte well hidden inside this "Op" object.
		'''
		return self.output.getColumnNumberForFieldName (s_field_name )
	#end def getColumnNumberForFieldName

	@property
	def ldne_path( self ):
		return self.__ldne_path
	#end property ldne_path

	@ldne_path.setter
	def ldne_path( self, s_value ):
		self.__ldne_path=s_value
		return
	#end ldne_path setter

	@property
	def neestimator_path( self ):
		return self.__neestimator_path
	#end property ldne_path

	@ldne_path.setter
	def neestimator_path( self, s_value ):
		self.__neestimator_path=s_value
		return
	#end ldne_path setter

#end class PGOpNeEstimator 

if __name__ == "__main__":

	s_datdir="/home/ted/documents/source_code/python/negui"
	sys.path.append( s_datdir )

	import agestrucne.genepopfilemanager as gpf
#	s_gpfile="AlpowaCreekBY2006_14.txt"
#	s_gpfile="AsotinCreekBY2006_104.txt"
	s_gpfile="BigCreekBY2006_29.txt"

	s_genepop_file="/".join( [ s_datdir,  "temp_data/genepop_from_brian_20160506", s_gpfile ] )
	
	f_prop=0.10

	o_gp=gpf.GenepopFileManager( s_genepop_file )
	o_gp.subsampleIndividualsRandomly( f_prop,  str( f_prop ) )

	s_subsample_genepop_file=o_gp.original_file_name + "." + str( f_prop )
	o_gp.writeGenePopFile( s_subsample_genepop_file, str( f_prop ) )

	#run orig or the subsample:
	s_file_to_run=s_genepop_file

	o_input=PGInputNeEstimator( s_file_to_run )
	o_output=PGOutputNeEstimator( s_file_to_run + ".ne.est" )
	f_thres= 0.011 
	o_input.run_params = { "crits":[ f_thres ]  } 
	o_estimator=PGOpNeEstimator( o_input, o_output )
	o_estimator.doOp()
			
	pass
#end if main

