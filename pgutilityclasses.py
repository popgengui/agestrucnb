'''
Description
Instead of putting utility classes in pgutilities,
this module will house all classes not directly related
to front or back end of the pg operations.
'''

__filename__ = "pgutilityclasses.py"
__date__ = "20160702"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import numpy

class IndependantProcessGroup( object ):
	'''
	Simple convenience wrapper around a set of processes,
	allowing calls into the instance to add a process,
	or terminate all processes. This class is motivated
	by implementing parallell replicate AgeStructureNe-inititated
	simuPop simulations in a PGGuiSimuPop instance via
	python's multiprocessing class, which apparently interacts
	with simuPOP such that the multiprocessing.Pool and 
	multiprocessing.Queue process managers do not create
	simuPOP objects independant of each other.  This
	necessitated using separately instantiated and started
	multiprocessing.Process objects.  Because the typical
	case will be to run y replicates using x processes, with
	y>>x, then we need to manage the set of x processes, replacing
	those finished with fresh processes.
	
	All member processes are assumed to be completely 
	independant of all others, so that any I/O messes 
	caused by calling terminate() will not lock up 
	the parent process
	'''

	def __init__( self, lo_processes=[] ):
		self.__processes=lo_processes
		self.__pids=[ o_process.pid for o_process in lo_processes ]
		return
	#end __init__

	def addProcess( self, o_process ):
		self.__processes.append( o_process )
		self.__pids.append( o_process.pid )
		return
	#end addProcess

	def getTotalAlive( self ):
		i_count_living=0
		for o_process in self.__processes:
			if o_process.is_alive():
				i_count_living+=1
			#end if process is alive
		#end for each process
		return i_count_living
	#end getTotalAlive

	def terminateAllProcesses( self ):
		for o_process in self.__processes:
			o_process.terminate()
		#end for each process
		return
	#end terminatAllProcesses

#end class IndependantProcessGroup

class IndependantSubprocessGroup( object ):
	'''
	Minimal Revision of class independantProcessGroup	
	to operate on python subprocess.Popen proccesses.

	The main changes include use of kill() instead of 
	terminate in def terminateAllSubprocesses() and
	use poll() (is None) instead of is_alive() to get
	a count of living processes
	'''

	def __init__( self, lo_subprocesses=[] ):
		self.__subprocesses=lo_subprocesses
		self.__pids=[ o_subprocess.pid for o_subprocess in lo_subprocesses ]
		return
	#end __init__

	def addSubprocess( self, o_subprocess ):
		self.__subprocesses.append( o_subprocess )
		self.__pids.append( o_subprocess.pid )
		return
	#end addSubprocess

	def getTotalAlive( self ):
		i_count_living=0
		for o_subprocess in self.__subprocesses:
			if o_subprocess.poll() is None:
				i_count_living+=1
			#end if subprocess is alive
		#end for each subprocess
		return i_count_living
	#end getTotalAlive

	def terminateAllSubprocesses( self ):
		for o_subprocess in self.__subprocesses:
			try:
				o_subprocess.kill()
			except OSError as ose:
				s_msg="In IndependantSubprocessGroup instance, def " \
							+ " terminateAllSubprocesses, " \
							+ " on call to kill(), an OSError was generated: " \
							+ str( ose )  + "."
				sys.stderr.write( "Warning: " + s_msg + "\n" )
			#end 
		#end for each subprocess
		return
	#end terminateAllSubprocesses

#end class independantSubprocessGroup

class FloatIntStringParamValidity( object ):

	'''
	For validation checks on a parameter value
	before it is used to run an analysis.
	'''

	def __init__( self, s_name, o_type, o_value, i_min_value=None, i_max_value=None ):
		self.__name=s_name
		self.__param_type=o_type
		self.__value=o_value
		self.__min_value=i_min_value
		self.__max_value=i_max_value

		self.__type_message=None
		self.__value_message=None

		self.__is_valid=False
		self.__value_valid=False
		self.__type_valid=False
	
		self.__set_validity()
	#end __init__

	def __set_validity( self ):

		b_set_type_valid=self.__param_type in ( float, int, str )
		b_type_matches=type( self.__value) == self.__param_type
		b_value_in_range=self.__value_is_in_range()

		if b_set_type_valid:
			self.__type_message="Type, " + str( self.__param_type ) + "is valid."
			self.__type_valid=True
		else:
			self.__type_message="Type, " + str( self.__param_type ) \
					+ "is not among the valid types, float, int, str."
			self.__type_valid=False
		#end if not valid type	
		
		if b_type_matches:
			self.__type_message="Type, " + str( self.__param_type ) + " is valid."
			self.__type_valid=True
		else:
			self.__type_message="Param type is, " + str( self.__param_type ) \
					+ " but value, " + str( self.__value ) + " is of type, " \
					+ str( type( self.__value ) ) + "."
			self.__type_valid=False

		#end if not type match

		if b_value_in_range:
			self.__value_message= "Value, " + str( self.__value ) + " is valid."
			self.__value_valid=True
		else:
			if type( self.__value ) == str:
				self.__value_message="Length of string value " + str( self.__value ) \
					 		+ " is out of range.  Range is from " \
							+ str( self.__min_value ) + " to " +  str( self.__max_value ) \
							+ "."
			else:
				self.__value_message="Value, " + str( self.__value ) \
					 		+ ", is out of range.  Range is from " \
							+ str( self.__min_value ) + " to " \
							+  str( self.__max_value ) \
							+ "."
			#end if string else otehr

			self.__value_valid=False
		#end if not b_value_in_range
	
		if  b_set_type_valid + b_type_matches + b_value_in_range  == 3:
			self.__is_valid=True
		else:
			self.__is_valid=False
		#end if all checks good, else invalid param	

		return
	#end __set_validity

	def __value_is_in_range( self ):
		
		o_type_val=type( self.__value )
		i_range_val=None

		b_meets_min=False
		b_meets_max=False

		if o_type_val  in ( int, float ):
			i_range_val=self.__value
		elif o_type_val == str:
			i_range_val=len( self.__value )	
		else:
			''' 
				value has invalid type,
				so we default to designating
				it out-of-range
			'''
			return False
		#end if numeric, else string

		if self.__min_value is None:
			#infer no min:
			b_meets_min=True
		else:

			if i_range_val >= self.__min_value:
				b_meets_min=True
			#end if meets min
		#end if min is None, else test

		if self.__max_value is None:
				#infer no man:
				b_meets_max=True
		else:

			if i_range_val <= self.__max_value:
				b_meets_max=True
			#end if meets max			
		#end if max is none, else test

		return b_meets_min and b_meets_max
	#end __value_is_in_range

	def isValid( self ):
		self.__set_validity()
		return self.__is_valid
	#end is

	def reportValidity( self ):
		s_report="\n".join( \
				[ self.__type_message,
				self.__value_message] )
		return s_report
	#end __report_validity

	def reportInvalidityOnly( self ):

		ls_reports=[]
		s_report=""

		if not self.__type_valid:
			ls_reports.append( self.__type_message )
		#end if invalid type
		
		if not self.__value_valid:
			ls_reports.append( self.__value_message )
		#end if invalid value

		s_report="\n".join( ls_reports )

		return s_report 
	#end reportInvalidityOnly

	@property
	def value( self ):
		return self.__value
	#end def value

	@value.setter
	def value( self, v_value ):
		self.__value=v_value
		self.__set_validity()
	#end setter
#end class FloatIntStringParamWrapped

class NeEstimatorSamplingSchemeParameterManager( object ):
	'''
	Needed a way to manage the several sampling scheme
	parameters aquired in the PGGuiNeEstimator objects
	sampleparams interface, which then need to be used 
	in a call to pgdriveneestimator.

	A dictionary to get sampling scheme param names.  The names
	(the values in the inner dictionaries) were extracted from file 
	resources/neestimator_param_names on 2016_09_24

	Attribute names used by all sample schemes
	(though in the interface their attr names
	will be preceeded by the scheme name:
	'''

	DELIMITER_FOR_LIST_ARG=","
	DELIMITER_FOR_ID_FIELD_SCHEMES_NUMERIC_LISTS="-"
	DELIMITER_FOR_COMMAND_ARGS=","

	SCHEME_ALL="All"
	SCHEME_NONE="None"
	SCHEME_PERCENT="Percent"
	SCHEME_REMOVE="Remove-N"
	SCHEME_CRIT="Indiv Criteria"
	SCHEME_COHORTS="Cohorts"
	SCHEME_RELATEDS="Relateds"


	SCHEMES_REQUIRING_ID_FIELDS=[ SCHEME_CRIT, 
									SCHEME_COHORTS, 
										SCHEME_RELATEDS ]

	PARAMS_IN_ID_FIELD_SCHEMES_WITH_NUMERIC_LISTS= [ "scheme_cohort_percentages" ]

	ATTR_NAME_SCHEME="sampscheme"
	ATTR_NAME_MIN_POP_NUMBER="min_pop_number"
	ATTR_NAME_MAX_POP_NUMBER="max_pop_number"
	ATTR_NAME_MIN_POP_SIZE="min_pop_size"
	ATTR_NAME_MAX_POP_SIZE="max_pop_size"
	
	'''
	Note that in the GUI interface, all cohort
	scheme settings include one or more percentages,
	so we use the "cohortsperc" scheme arg for the 
	driver, while the interface uses simply "Cohorts".
	'''
	DICT_DRIVER_SCHEME_NAME_BY_INTERFACE_NAME = { \
				SCHEME_NONE : "none",
				SCHEME_PERCENT : "percent",
				SCHEME_REMOVE : "remove",
				SCHEME_CRIT : "criteria",
				SCHEME_COHORTS : "cohortsperc",
				SCHEME_RELATEDS : "relateds" }
		
	DICT_ATTR_BY_SCHEME= { \
				SCHEME_ALL : { "min_pop_number" : "scheme_all_min_pop_number",
							"max_pop_number" : "scheme_all_max_pop_number" },
				SCHEME_NONE : { "min_pop_size" : "scheme_none_min_pop_size",
								"max_pop_size" : "scheme_none_max_pop_size",
								"none_dummy_param" : "scheme_none_dummy_param"},
				SCHEME_PERCENT : { "min_pop_size" : "scheme_percent_min_pop_size",
									"max_pop_size" : "scheme_percent_max_pop_size",
									"percentages" : "scheme_percent_percentages" },
				SCHEME_REMOVE : { "min_pop_size" : "scheme_removen_min_pop_size",
									"max_pop_size" : "scheme_removen_max_pop_size",
									 "n": "scheme_removen_n" },
				SCHEME_CRIT : { "min_age" : "scheme_crit_min_age", 
							"max_age" : "scheme_crit_max_age",
							"min_pop_size" : "scheme_crit_min_pop_size",
							"max_pop_size" : "scheme_crit_max_pop_size" },
				SCHEME_COHORTS : { "max_age" : "scheme_cohort_max_age",
								"min_pop_size" : "scheme_cohort_min_indiv_per_gen",
								"max_pop_size" : "scheme_cohort_max_indiv_per_gen",
								"percentages" : "scheme_cohort_percentages" },
				SCHEME_RELATEDS : { "percent_relateds" : "scheme_relateds_percent_relateds",
							"min_pop_size" : "scheme_relateds_min_indiv_per_gen",
							"max_pop_size" : "scheme_relateds_max_indiv_per_gen" } }

	DICT_ATTR_ORDER_BY_SCHEME= { \
				SCHEME_ALL : [ "min_pop_number", "max_pop_number" ],
				SCHEME_NONE : [ "none_dummy_param", "min_pop_size", "max_pop_size" ],
				SCHEME_PERCENT : [ "percentages", "min_pop_size", "max_pop_size"  ],
				SCHEME_REMOVE : [ "n", "min_pop_size", "max_pop_size"  ],
				SCHEME_CRIT : [ "min_age" , "max_age", "min_pop_size", "max_pop_size" ],
				SCHEME_COHORTS : [ "max_age" , "percentages", "min_pop_size", "max_pop_size" ],
				SCHEME_RELATEDS : [ "percent_relateds", "min_pop_size",  "max_pop_size" ] }
		
	CRIT_EXPRESSIONS_IN_ATTR_ORDER=[ "%age% >= ", "%age% <=" ]

	def __init__( self, o_pgguineestimator, s_attr_prefix ):
		self.__interface=o_pgguineestimator
		self.__attr_prefix=s_attr_prefix
		return
	#end __init__

	def __get_scheme_name( self ):
		
		s_sampling_scheme_name = None

		try: 
			s_attr_name=self.__attr_prefix \
						+ NeEstimatorSamplingSchemeParameterManager\
									.ATTR_NAME_SCHEME 
		
			s_sampling_scheme_name=getattr( self.__interface,
													s_attr_name )

		except Exception as oex:
			s_msg="In NeEstimatorSamplingSchemeParameterManager instance, " \
						+ "def __get_scheme_name, " \
						+ "could not get the sample scheme attribute " \
						+ "value from the interface.  Exception raised: " \
						+ str( oex ) + "."
		#end try . . . except

		if s_sampling_scheme_name not in \
				NeEstimatorSamplingSchemeParameterManager.DICT_ATTR_BY_SCHEME:
			s_msg="In NeEstimatorSamplingSchemeParameterManager instance, " \
						+ "def __get_scheme_name, " \
						+ "the interface has a sampling scheme attribute value, " \
						+  s_sampling_scheme_name + ", " \
						+ "not found among the types listed in the dictionary " \
						+ "used by this class instance." 
			raise Exception ( s_msg )
		#end if unknown sampling scheme

		return s_sampling_scheme_name

	# end __get_scheme_name

	def __get_sampling_args_for_schemes_not_requiring_id_fields( self ):
		s_scheme=self.__get_scheme_name()

		ls_sample_scheme_args_as_strings=[]

		ls_sample_scheme_args_as_strings.append( \
				NeEstimatorSamplingSchemeParameterManager\
							.DICT_DRIVER_SCHEME_NAME_BY_INTERFACE_NAME[ s_scheme ] )

		for s_arg in NeEstimatorSamplingSchemeParameterManager\
							.DICT_ATTR_ORDER_BY_SCHEME[ s_scheme ]:

			s_attr_name=self.__attr_prefix \
					+ NeEstimatorSamplingSchemeParameterManager\
											.DICT_ATTR_BY_SCHEME[ s_scheme ][ s_arg ]

			v_value=getattr( self.__interface, 
									s_attr_name )
		
			s_value=None

			'''
			If a list, we assume it is the sample params
			list (a multi-valued arg)
			'''
			if type( v_value ) == list:
				s_value= \
					NeEstimatorSamplingSchemeParameterManager\
								.DELIMITER_FOR_LIST_ARG\
								.join( [ str( v_item ) for v_item in v_value ] )
			else:
				s_value=str( v_value )
			#end if type is a list else not

			ls_sample_scheme_args_as_strings.append( s_value )
		#end for each arg in DICT_ATTR_ORDER_BY_SCHEME

		return ls_sample_scheme_args_as_strings
	#end def __get_sampling_args_for_schemes_not_requiring_id_fields

	def __get_attr_val_as_string( self, s_scheme, s_arg ):
		MYCLS=self.__class__
		s_value=None
		s_attr_name=self.__attr_prefix + s_arg
		v_value=getattr( self.__interface, s_attr_name )

		if s_arg in MYCLS.PARAMS_IN_ID_FIELD_SCHEMES_WITH_NUMERIC_LISTS:
			s_value=MYCLS.DELIMITER_FOR_ID_FIELD_SCHEMES_NUMERIC_LISTS.join( \
					[ str( v_numeric) for v_numeric in v_value  ] )
		else:
			s_value=str( v_value )
		#end if numeric list in id-field scheme, join with correct delimiter

		return s_value
	#end __get_attr_val_as_string
		
	def __get_sampling_args_for_schemes_requiring_id_fields( self ):
		'''	
		As of 2016_09_30, pgdriveneestimator.py takes these
		scheme args like this:
		<scheme_name> <id;sex;father;mother;age,float;int;float;float;float;,param,param,...>
		where param differs.  In case of Indiv Criteia, param is a list of test expressions, currently
		onlt two such, "age>=min_age and age>=max_age".
		In case of cohorts, it consists of 1 int, max age.  In case of Relateds it consists
		of one float, percent relateds.
		'''
		
		CLSVALS=NeEstimatorSamplingSchemeParameterManager 
		DELIMIT_FIELD_LISTS=";"
		DELIMIT_FIELD_RELATED_PARAMS=","
		FLOAT_NAME=float.__name__
		INT_NAME=int.__name__
		FIELD_NAMES=DELIMIT_FIELD_LISTS.join( \
				[ "id", "sex", "father", "mother", "age" ] )
		FIELD_TYPES=DELIMIT_FIELD_LISTS.join( \
				[ FLOAT_NAME, INT_NAME, FLOAT_NAME, FLOAT_NAME, FLOAT_NAME ] )

		IDX_PARAM_VALS_AFTER_FIELD_LISTS=2

		ls_params=[ FIELD_NAMES, FIELD_TYPES ] 

		s_scheme=self.__get_scheme_name()

		ls_sample_scheme_args_as_strings=[]

		ls_sample_scheme_args_as_strings.append( \
				CLSVALS.DICT_DRIVER_SCHEME_NAME_BY_INTERFACE_NAME[ s_scheme ] )

		ls_final_sample_scheme_args=[]


	
		i_total_id_field_crit_expressions=len( CLSVALS.CRIT_EXPRESSIONS_IN_ATTR_ORDER )

		for idx in range( len( CLSVALS.DICT_ATTR_ORDER_BY_SCHEME[ s_scheme ] ) ):

			s_param_key=CLSVALS.DICT_ATTR_ORDER_BY_SCHEME[ s_scheme ][ idx ]
			s_param_name=CLSVALS.DICT_ATTR_BY_SCHEME[ s_scheme ][ s_param_key ]
			s_value = self.__get_attr_val_as_string( s_scheme, s_param_name )	

			'''	
			For the Indiv Criteria sampling scheme, the first N (currently, N=2)
			paramaters supplied by the interface are used in expressions (currently
			age>=x and age<=y), which are the 3rd and 4th comma-delimited parts of 
			the sampling scheme detail argument when calling pgdriveneestimator.py.
			'''
			if s_scheme==CLSVALS.SCHEME_CRIT and \
							idx < i_total_id_field_crit_expressions:
					s_expression=CLSVALS.CRIT_EXPRESSIONS_IN_ATTR_ORDER[ idx ]
					s_param=s_expression+s_value
					ls_params.append( s_param )
			elif idx == 0:
				'''
				For id-field schemes other than Indiv Criteia,
				we have (as of 2016_09_30) only a single id-field 
				parameter, always listed first in the attribute order, 
				to append to the id-field-params arg:				'''
				ls_params.append( s_value )
			elif s_param_name in CLSVALS.PARAMS_IN_ID_FIELD_SCHEMES_WITH_NUMERIC_LISTS:
				'''
				In some id-field schemess, such as cohorts, 
				we also have a list of percentages (hyphen
				delimited (see __get_attr_val_as_string),appended
				to the param arg, for the join using the same 
				delimiter (semicolon) as used between field lists:
				'''
				ls_params[ IDX_PARAM_VALS_AFTER_FIELD_LISTS ] = \
						ls_params[ IDX_PARAM_VALS_AFTER_FIELD_LISTS ] \
						+  DELIMIT_FIELD_LISTS + s_value

			else:
				ls_final_sample_scheme_args.append( s_value )
			#end if this arg is a field param, else not
		#end for each arg value

		s_field_related_params=\
				DELIMIT_FIELD_RELATED_PARAMS.join(  ls_params )

		ls_sample_scheme_args_as_strings.append( s_field_related_params )
		ls_sample_scheme_args_as_strings += ls_final_sample_scheme_args
		
		return ls_sample_scheme_args_as_strings
	#end def __get_sampling_args_for_schemes_requiring_id_fields

	def getSampleSchemeArgsForDriver( self ):

		'''
		We contruct the param-scheme-related
		arguments to a call to the main def
		in pgdriveneestimator.py.  As of
		2016_09_26 the args are in this order:
		<sample scheme> <parameter list (comma-delimited)>
		<min pop size> <max pop size>
		'''

		CLSVALS=NeEstimatorSamplingSchemeParameterManager

		s_scheme=self.__get_scheme_name()

		ls_sample_scheme_args_as_strings=None
	
		#Sampling scheme Indiv Criteia needs a special algorithm 
		#to assemble param args
		if s_scheme in \
				CLSVALS.SCHEMES_REQUIRING_ID_FIELDS:
			ls_sample_scheme_args_as_strings=\
					self.__get_sampling_args_for_schemes_requiring_id_fields()
		else:
			ls_sample_scheme_args_as_strings=\
					self.__get_sampling_args_for_schemes_not_requiring_id_fields()
		#end if not indiv criteria scheme, call def for such,
		#else call def to get indiv criteria scheme args

		'''
		All sampling schemes have a range of pop numbers,
		passed to pgdriveneestimator.py as a hyphenated
		pair min-max:
		'''
		s_scheme_all=CLSVALS.SCHEME_ALL
		s_attr_min_pop_number=self.__attr_prefix \
				+ CLSVALS.DICT_ATTR_BY_SCHEME[ s_scheme_all ] [ "min_pop_number" ]

		s_attr_max_pop_number= self.__attr_prefix \
				+ CLSVALS.DICT_ATTR_BY_SCHEME[ s_scheme_all ][ "max_pop_number" ]
	
		i_min_pop_number=getattr( self.__interface, s_attr_min_pop_number )
		i_max_pop_number=getattr( self.__interface, s_attr_max_pop_number )
						
		s_pop_range_arg=str( i_min_pop_number ) + "-" + str( i_max_pop_number )

		ls_sample_scheme_args_as_strings.append( s_pop_range_arg )

		#We return as tuple, to use as operand in creating
		#a complete arg set.
		return tuple( ls_sample_scheme_args_as_strings )

	#end getSampleSchemeArgToDriver

#end class NeEstimatorSamplingSchemeParameterManager


class NeEstimatorLociSamplingSchemeParameterManager( object ):
	'''
	Version of class pgguiutilities.NeEstimatorSamplingSchemeParameterManager
	(see) significanly shortened, simplified  for loci sampling rather than pop (individual)
	sampling.
	'''
	DELIMITER_FOR_LIST_ARG=","

	SCHEME_ALL="All"
	SCHEME_NONE="None"
	SCHEME_PERCENT="Percent"
	SCHEME_TOTAL="Total"

	ATTR_NAME_SCHEME="locisampscheme"
	ATTR_NAME_MIN_LOCI_NUMBER="min_loci_number"
	ATTR_NAME_MAX_LOCI_NUMBER="max_loci_number"
	ATTR_NAME_MAX_LOCI_COUNT="max_loci_count"

	DICT_DRIVER_SCHEME_NAME_BY_INTERFACE_NAME = { \
				SCHEME_NONE : "none",
				SCHEME_PERCENT : "percent",
				SCHEME_TOTAL : "total" }
		
	DICT_ATTR_BY_SCHEME= { \
				SCHEME_ALL : { "min_loci_number" : "locischeme_all_min_loci_number",
								"max_loci_number" : "locischeme_all_max_loci_number" },
				SCHEME_NONE : { "none_dummy_param" : "locischeme_none_dummy_param",
									"min_loci_count" : "locischeme_none_min_loci_count",
									"max_loci_count" : "locischeme_none_max_loci_count" }, 
				SCHEME_PERCENT : { "percentages" : "locischeme_percent_percentages",
									"min_loci_count" : "locischeme_percent_min_loci_count",
									"max_loci_count" : "locischeme_percent_max_loci_count" },
				SCHEME_TOTAL : { "totals" : "locischeme_total_totals", 
										"min_loci_count":"locischeme_total_min_loci_count",
										"max_loci_count":"locischeme_total_min_loci_count" } }

	#Note that the "total" scheme, while it does not use the min and max loci count params,
	#Nonetheless needs the default values to make a valid call to the driver.
	DICT_ATTR_ORDER_BY_SCHEME = { SCHEME_ALL : [ "min_loci_number", "max_loci_number" ], 
									SCHEME_NONE : [ "none_dummy_param", "min_loci_count", "max_loci_count" ],
									SCHEME_PERCENT : [ "percentages", "min_loci_count", "max_loci_count" ],
									SCHEME_TOTAL : [ "totals", "min_loci_count", "max_loci_count" ] }

	def __init__( self, o_pgguineestimator, s_attr_prefix ):
		self.__interface=o_pgguineestimator
		self.__attr_prefix=s_attr_prefix
		return
	#end __init__

	def __get_scheme_name( self ):
		
		s_sampling_scheme_name = None

		try: 
			s_attr_name=self.__attr_prefix \
						+ NeEstimatorLociSamplingSchemeParameterManager\
									.ATTR_NAME_SCHEME 
		
			s_sampling_scheme_name=getattr( self.__interface,
													s_attr_name )

		except Exception as oex:
			s_msg="In NeEstimatorLociSamplingSchemeParameterManager instance, " \
						+ "def __get_scheme_name, " \
						+ "could not get the sample scheme attribute " \
						+ "value from the interface.  Exception raised: " \
						+ str( oex ) + "."
		#end try . . . except

		if s_sampling_scheme_name not in \
					NeEstimatorLociSamplingSchemeParameterManager.DICT_ATTR_BY_SCHEME:
			s_msg="In NeEstimatorLociSamplingSchemeParameterManager instance, " \
						+ "def __get_scheme_name, " \
						+ "the interface has a sampling scheme attribute value, " \
						+  s_sampling_scheme_name + ", " \
						+ "not found among the types listed in the dictionary " \
						+ "used by this class instance." 
			raise Exception ( s_msg )
		#end if unknown sampling scheme

		return s_sampling_scheme_name

	# end __get_scheme_name

	def __get_sampling_args_for_scheme( self ):

		s_scheme=self.__get_scheme_name()

		ls_sample_scheme_args_as_strings=[]

		ls_sample_scheme_args_as_strings.append( \
				NeEstimatorLociSamplingSchemeParameterManager\
							.DICT_DRIVER_SCHEME_NAME_BY_INTERFACE_NAME[ s_scheme ] )

		for s_arg in NeEstimatorLociSamplingSchemeParameterManager\
							.DICT_ATTR_ORDER_BY_SCHEME[ s_scheme ]:

			s_attr_name=self.__attr_prefix \
					+ NeEstimatorLociSamplingSchemeParameterManager\
											.DICT_ATTR_BY_SCHEME[ s_scheme ][ s_arg ]

			v_value=getattr( self.__interface, 
									s_attr_name )
		
			s_value=None

			'''
			If a list, we assume it is the sample params
			list (a multi-valued arg)
			'''
			if type( v_value ) == list:
				s_value= \
					NeEstimatorLociSamplingSchemeParameterManager\
								.DELIMITER_FOR_LIST_ARG\
								.join( [ str( v_item ) for v_item in v_value ] )
			else:
				s_value=str( v_value )
			#end if type is a list else not

			ls_sample_scheme_args_as_strings.append( s_value )
		#end for each arg in DICT_ATTR_ORDER_BY_SCHEME


		return ls_sample_scheme_args_as_strings
	#end def __get_sampling_args_for_scheme

	def getSampleSchemeArgsForDriver( self ):

		'''
		We contruct the param-scheme-related
		arguments to a call to the main def
		in pgdriveneestimator.py.  
		'''

		CLSVALS=NeEstimatorLociSamplingSchemeParameterManager

		s_scheme=self.__get_scheme_name()

	
		ls_sample_scheme_args_as_strings=\
					self.__get_sampling_args_for_scheme()

		'''
		All sampling schemes have a range of loci numbers,
		passed to pgdriveneestimator.py as a hyphenated
		pair min-max:
		'''
		s_scheme_all=CLSVALS.SCHEME_ALL
		s_attr_min_loci_number=self.__attr_prefix \
				+ CLSVALS.DICT_ATTR_BY_SCHEME[ s_scheme_all ] [ "min_loci_number" ]

		s_attr_max_loci_number= self.__attr_prefix \
				+ CLSVALS.DICT_ATTR_BY_SCHEME[ s_scheme_all ][ "max_loci_number" ]
	
		i_min_loci_number=getattr( self.__interface, s_attr_min_loci_number )
		i_max_loci_number=getattr( self.__interface, s_attr_max_loci_number )
						
		s_loci_range_arg=str( i_min_loci_number ) + "-" + str( i_max_loci_number )

		ls_sample_scheme_args_as_strings.append( s_loci_range_arg )

		#We return as tuple, to use as operand in creating
		#a complete arg set.
		return tuple( ls_sample_scheme_args_as_strings )

	#end getSampleSchemeArgToDriver
	
#end class NeEstimatorLociSamplingSchemeParameterManager 


class ValueValidator( object ):

	'''
	Class to evaluate a value by applying
	a client-supplied def.  The def can be
	supplied either:
	---1. as reference to a function.
	---2. as a string expression
	that will be made into a lambda operation
	by concatenating "lambda x: "
	with the string. 
	
	Class created to use a PGParamSet instance "validation"
	value, from its tag item that
	supplies either a function name for a def that 
	takes a single arg and retirns (evals to) True or False, 
	or a string expression in "x" that does the same
	for example, "type(x)==float and x <= 1.0"

	Note that this class' def names and signatures are made
	to match relevant ones in class FloatIntStringParamValidity,
	since, as of 2016_10_03, we are calling them in the KeyValFrame
	class (see def __reset_value) as defined in mod pgguiutilities.py
	'''

	def __init__( self, v_bool_expression_or_function_ref, v_value=None ):

		if callable( v_bool_expression_or_function_ref ):
			self.__validator=v_bool_expression_or_function_ref
		elif type( v_bool_expression_or_function_ref ) == str:
			s_lambda="lambda x: "  \
						+ v_bool_expression_or_function_ref

			try:
				self.__validator=eval( s_lambda  )
			except Exception as oex:
				s_msg="In ValueValidator instance, def __init__, " \
							+ "failed to eval expression: " \
							+ s_lambda + ".  Exception raised: " \
							+ str( oex ) + "."
				raise Exception( s_msg )
			#end try to eval, except . . .
		else:	
			s_msg="In ValueValidator instance, def __init__, " \
							+ "the class expects " \
							+ "a validator argument to be either " \
							+ "a function or a string boolean expression in x."	\
							+ "Argument, " + str( v_bool_expression_or_function_ref ) \
							+ "is of type: " + str( type( v_bool_expression_or_function_ref ) ) \
							+ "."
			raise Exception( s_msg )

		#end if function else bool expression else eror

		self.__expression=str( v_bool_expression_or_function_ref )
		self.__value=v_value
		return
	#end __init__

	def isValid( self ):
		
		try:
			b_result=self.__validator( self.__value )
		except:
			s_msg="In ValueValidator instance, " \
						+ "def isValid, " \
						+ "call to __validator, " \
						+ str( self.__expression ) + " failed."
			raise Exception( s_msg )
		#end try . . . except . . .
		if b_result not in [ True, False ]:	
			s_msg="In ValueValidator instance, " \
						+ "def isValid, " \
						+ "call to __validator, \"" \
						+ self.__expression + "\" failed."
			raise Exception( s_msg )
		#if validator expression returned non-boolean value
		return b_result
	#end def validate

	def reportInvalidityOnly( self ):
		s_msg=None
		if not self.isValid():
			s_msg="Value, " + str( self.__value ) \
						+ ", failed validity test, " \
						+ self.__expression + "."
		#end if invalid

		return s_msg
	#end reportInvalidityOnly

	@property
	def value( self ):
		return self.__value
	#end def value

	@value.setter
	def value( self, v_value ):
		self.__value = v_value
		return
	#end  value setter
	
#end class ValueValidator

class NeEstimationTableFileManager:
	'''
	Class to read and write the table 
	files with Ne estimations generatted 
	by pgdriveneestimator.py.

	Motivation: Needed in order to filter the
	table for plotting using Brian T's
	line regresss program, when the table
	has more than one subsample value for 
	the "pop" sections and/or "loci" list. For example,
	if the user has subsampled a genepop file
	to get 95 and 85 percent fot individuals
	per pop, and and also subsampled the loci
	to get 95 and 85 percent of loci (however
	many replicates in each), then the reaults
	will need to be filtered to include only
	rows whose pop subsdample value i and loci 
	subsample value j are fixed, so that i,j
	is 85,85 or 85,95 or 95,85 or 95,95.

	The file is loaded into a numpy array,
	and all fields are typed as bytes.
	(There's a type problem if we type the array 
	"str", so that  we get different types depending 
	on py2 vs py3:

	"if you create a NumPy array containing strings, 
	the array will use the numpy.string_ type (or 
	the numpy.unicode_ type in Python 3)." More precisely, 
	the array will use a sub-datatype of np.string_

	This class returns its items as strings, after
	decoding the bytes using sys.stdout.encoding.
	I think this gives items compatible with 
	the string methods in both py2 and py3.
	
	'''

	DELIM_TABLE="\t"
	COL_NAME_FILE_NAME=b'original_file'
	COL_NAME_POP_SAMPLE_VAL=b'sample_value'
	COL_NAME_LOCI_SAMPLE_VAL=b'loci_sample_value'

	ENCODING=sys.stdout.encoding

	def __init__( self, s_file_name, 
					i_header_is_first_n_lines=1,
					i_col_names_line_num=1,
					s_tsv_file_delimiter="\t" ):
		'''
		param s_file_name gives the name
		of a file output by pgdriveneestimator.py,
		and is the main (*tsv) output file giving
		Ne estimations and related quants.

		param i_header_is_first_n_lines gives the number 
		of lines at the beginning of the file that are
		non-data.

		param i_col_names_line_num gives the file's line number
		that holds the delimited column names
		
		param s_tsv_file_delimiter gives the character that
		delimits the columns in the tsv file. The default
		is <tab>.
		'''

		self.__filename=s_file_name
		self.__header_line_tot=i_header_is_first_n_lines
		self.__line_number_col_names=i_col_names_line_num
		self.__tsv_file_delimiter=s_tsv_file_delimiter

		self.__myclassname=NeEstimationTableFileManager
		self.__table_array=None
		self.__load_file_into_array()
				
		'''
		Dictionary of functions keyed to column numbers. Valid
		values are None or a ref to a def that takes a single 
		string value and returns a boolean.  This dictionary 
		is used to write a filtered version of the input file 
		that includes only lines that pass all filters (all 
		return True). Users add these via def setFilter
		below.
		'''
		self.__filters={}

		return
	#end __init__

	def __load_file_into_array( self ):

		self.__table_array=numpy.loadtxt( fname=self.__filename, 
														dtype=bytes, 
														delimiter=self.__tsv_file_delimiter )

		return
	#end __load_file_into_array

	def __get_col_nums_for_col_name( self, b_col_name, b_enforce_uniq=True ):
		'''
		param b_col_name is a bytes object, to be compared
		to those read in to the first line of the table array.
		
		2017_02_16.  param b_enforce_uniq, when True employes an assert statment
		that the tup[0] returned by numpy.where (i.e. the tuple with
		indices for true values for the conditional) has exactly one
		item, indicating a single column number that matches the b_col_name arg.
		'''
		ar_col_names=self.__table_array[ self.__line_number_col_names - 1, : ]

		#Returns a tuple of arrays, the first array being the
		#index or indices in the bool array wherein ar_col_names has the match.
		tup_ar_col_nums=numpy.where( ar_col_names==b_col_name )
		ar_col_nums=tup_ar_col_nums[ 0 ]

		if b_enforce_uniq:
				s_msg="In NeEstimationTableFileManager instance, " \
							+ "def __get_col_nums_for_col_name, " \
							+ "non-unique column number for match for " \
							+ "column name, " + str( b_col_name ) + "."
				
				assert len( ar_col_nums ) == 1, s_msg
		#end if we are to enforce a unique column number

		return ar_col_nums
	#end __get_col_nums_for_col_name

	def __get_set_values_for_column( self, i_col_number ):
		'''
		This def returns a list givein the set (unique)
		string-typed values for the column given by i_col_number.
		'''
		ar_table=self.__table_array
		i_min_row=self.__header_line_tot

		return set( ar_table[ i_min_row : , i_col_number ] )
	#end __get_set_values_for_column

	def __get_set_bytes_values_for_column_name( self, b_col_name ):

		ar_col_nums=self.__get_col_nums_for_col_name( b_col_name  )

		if len( ar_col_nums ) != 1:
			s_msg="In NeEstimationTableFileManager instance, " \
							+ "def __get_set_bytes_values_for_col_name, " \
							+ "in fetching column number for name, " + str( b_col_name ) \
							+ " from the file header, a non unique column " \
							+ "number was returned, using sample value column " \
							+ "list of column numbers found for this column name: " \
							+ str( ar_col_nums ) + "."
			raise Exception( s_msg )
		#end if non uniq col number

		set_values=self.__get_set_values_for_column( ar_col_nums [ 0 ] )
		
		return list( set_values )

	#end def __get_set_bytes_values_for_col_name

	def __get_string_from_bytes_value( self, b_bytes ):
		s_bytes=str( b_bytes.decode( self.__myclassname.ENCODING ) )
		return s_bytes
	#end __get_string_from_bytes_value

	def __get_bytes_from_string_value( self, s_strval ):
		b_strval=bytes( s_strval.encode( self.__myclassname.ENCODING ) )
		return b_strval
	#end __get_bytes_from_string_value

	def __get_list_of_strings_from_list_of_bytes( self, lb_list ):
		ls_as_strings=[ str(  \
				b_val.decode( self.__myclassname.ENCODING )  )
											for b_val in lb_list ]
		return ls_as_strings
	#end __get_list_of_strings_from_list_of_bytes

	def __get_list_bytes_pop_sample_values( self ):
		b_col_name=self.__myclassname.COL_NAME_POP_SAMPLE_VAL
		set_pop_sample_values=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_pop_sample_values )
	#end __get_list_pop_sample_values

	def __get_list_bytes_loci_sample_values( self ):
		b_col_name=self.__myclassname.COL_NAME_LOCI_SAMPLE_VAL
		set_loci_sample_values=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_loci_sample_values )
	#end __get_list_bytes_loci_sample_values

	def __get_list_bytes_file_names( self ):
		b_col_name=self.__myclassname.COL_NAME_FILE_NAME
		set_file_names=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_file_names )
	#end __get_list_bytes_file_names

	def __get_list_of_column_numbers_for_list_of_column_names( self, ls_col_names ):

		li_column_numbers=[]
		for s_column_name in ls_col_names:
			b_column_name=self.__get_bytes_from_string_value( s_column_name )
			#Default 2nd arg for this call ensures we get back only one
			#column number in the returned array:
			ar_col_nums=self.__get_col_nums_for_col_name( b_column_name )
			i_col_num=ar_col_nums[ 0 ]
			li_column_numbers.append( i_col_num )
		#end for each column name
		return li_column_numbers
	#end __get_list_of_column_numbers_for_list_of_column_names

	def __get_filtered_table_as_list_of_strings( self, 
								ls_exclusive_cols=None ):

		ls_entries=[]

		i_line_count=0

		li_exclusive_col_nums=None

		if ls_exclusive_cols is not None:
			li_exclusive_col_nums= \
					self.__get_list_of_column_numbers_for_list_of_column_names( \
														ls_exclusive_cols )
		#end if we have exclusive col names

		for ar_line in self.__table_array:
			i_line_count+=1

			#We do an "and" op to this bool
			#with all non-None filters.
			b_line_should_be_included=True

			if i_line_count == 1:
				'''
				Header line, no tests needed, and our write flag,
				b_line_should_be_included is already set to True, 
				so pass
				'''
				pass
			else:
				for i_colnum in self.__filters:
					if self.__filters[ i_colnum ] is not None:
						b_table_value=ar_line[ i_colnum ]
						s_table_value=self.__get_string_from_bytes_value( b_table_value )
						b_line_should_be_included &= self.__filters[ i_colnum ] ( s_table_value ) 
					#end if non-None filter
				#end for each filter

			if b_line_should_be_included:
				ls_line_as_list_of_strings= \
						self.__get_list_of_strings_from_list_of_bytes( ar_line )

				#If we are to collect only a subset of the columns,
				#reduce the list:
				if li_exclusive_col_nums is not None:
					ls_line_as_list_of_strings=[ ls_line_as_list_of_strings[ i ] \
														for i in li_exclusive_col_nums ]
				#end if we have exlcusive col nums

				s_entry=self.__myclassname.DELIM_TABLE.join( \
													ls_line_as_list_of_strings )
				ls_entries.append( s_entry )
			#end if line should be included, append to list
		#end for each line in array
		return ls_entries
	#end def __get_filtered_table_as_list_of_strings

	def __write_filtered_table_to_open_file_object( self, o_open_file ):

		ls_entries=self.__get_filtered_table_as_list_of_strings()

		for s_entry in ls_entries:
			o_open_file.write( s_entry + "\n" )
		#end for each string entry

		return
	#end __write_filtered_table_to_open_file_object

	def setFilter( self, s_column_name, def_filter ):
		'''
		param s_column_name, an item in the delimited header list of column
			names.
		param def_filter, a def that takes a single string arg and returns
			a boolean.  The usual case, if filtering for one value, say, v1,
			would be a def like, lambda x: x==v1. If def_filter is set to None, 
			no filter will be applied to this column. Setting to None is the 
			way to effectively remove a previously set filter.
		'''
		b_column_name=self.__get_bytes_from_string_value( s_column_name )
		ar_col_numbers=self.__get_col_nums_for_col_name( b_column_name )
		if len( ar_col_numbers ) != 1:
			s_msg="In NeEstimationTableFileManager instance, " \
							+ "def setFilter, " \
							+ "in fetching column number for sample value " \
							+ "from the file header, a non unique column " \
							+ "number was returned, using column " \
							+ "name: " + str( b_column_name ) + ", and getting list of " \
							+ "column numbers: " + str( ar_col_numbers ) + "."
			raise Exception( s_msg )
		#end if non uniq col number

		self.__filters[ ar_col_numbers[ 0 ] ] = def_filter
	#end setFilter

	def unsetAllFilters( self ):
		self.__filters={}
		return
	#end clearFilters

	def writeFilteredTable( self, o_fileobject ):
		'''
		param o_fileobject is an open and writeable File object
		'''
		self.__write_filtered_table_to_open_file_object( o_fileobject )

		return
	#end writeFilteredTableToFile

	def getFilteredTableAsList( self, ls_exclusive_inclusion_cols=None ):
		'''
		This def returns a list of strings, each a tab-delmited set of values
		corresponding to the tsv file, with all currentfilters in self.__filters
		applied.  If ls_exclusive_inclusion_cols is not None than it will return
		only those columns named in the list (column names that match those in 
		the header (line 1) of the tsv file.
		'''
		ls_filtered_table=self.__get_filtered_table_as_list_of_strings( ls_exclusive_inclusion_cols )
		return ls_filtered_table
	#end getFilteredTableAsList

	def getUniqueStringValuesForColumn( self, s_colname ):
		b_column_name=self.__get_bytes_from_string_value( s_colname )
		ar_col_numbers=self.__get_col_nums_for_col_name( b_column_name )
		if len( ar_col_numbers ) != 1:
			s_msg="In NeEstimationTableFileManager instance, " \
							+ "def getValueSetForColumnName, " \
							+ "in fetching column number for sample value " \
							+ "from the file header, a non unique column " \
							+ "number was returned, using column " \
							+ "name: " + str( b_column_name ) + ", and getting list of " \
							+ "column numbers: " + str( ar_col_numbers ) + "."
			raise Exception( s_msg )
		#end if non uniq col number

		lb_column_values=list( self.__get_set_values_for_column( ar_col_numbers[ 0 ] ) )
		ls_column_values=self.__get_list_of_strings_from_list_of_bytes( lb_column_values )

		return ls_column_values

	#end getUniqueStringValuesForColumn

	'''
	These two columns' value sets are given as properties because
	these are the motivating-user-case fields needed to select one
	value for each and write a so-filtered version of the tsv file.
	'''

	@property 
	def pop_sample_values( self ):
		lb_pop_sample_values=self.__get_list_bytes_pop_sample_values()
		ls_pop_sample_values=self.__get_list_of_strings_from_list_of_bytes( lb_pop_sample_values )
		return ls_pop_sample_values
	#end property pop_sample_values
	
	@property
	def loci_sample_values( self ):
		lb_loci_sample_values=self.__get_list_bytes_loci_sample_values()
		ls_loci_sample_values=self.__get_list_of_strings_from_list_of_bytes( lb_loci_sample_values )
		return ls_loci_sample_values
	#end property loci_sample_values

	@property
	def header( self ):
		ls_header_as_strings=self.__get_list_of_strings_from_list_of_bytes(  \
															self.__table_array[ 0, : ] )
		s_header=self.__myclassname.DELIM_TABLE.join( ls_header_as_strings )
		return s_header
	#end property header

	@property 
	def file_names(self ):
		lb_file_names=self.__get_list_bytes_file_names()
		ls_file_names=self.__get_list_of_strings_from_list_of_bytes( lb_file_names )
		return ls_file_names
	#end property file_names

#end class NeEstimationTableFileManager

class LDNENbBiasAdjustor( object ):
	'''
	Wrapper around the bias adjustment as given in 
	Waples, etal., "Effects of Overlapping Generations on Linkage 
	Disequilibrium Estimates of Effective Population Size Genetics." 
	Available at: 
	http://www.genetics.org/content/early/2014/04/08/genetics.114.164822.
	'''
	def __init__( self, v_original_nb=None, f_nbne_ratio=None ):

		o_nbne_type=type( f_nbne_ratio ) 

		b_nb_is_numeric=self.__is_numeric_type( v_original_nb )
		b_nbne_ratio_is_numeric=self.__is_numeric_type( f_nbne_ratio )

		b_type_nb_correct = b_nb_is_numeric or v_original_nb is None 

		#We accept int for the ratio (will cast as float
		#when applying a bias adjustment.
		b_type_nbne_correct = b_nbne_ratio_is_numeric or f_nbne_ratio is  None 

		assert (  b_type_nb_correct and b_type_nbne_correct ), \
					"In LDNENbBiasAdjustor instance , " \
							+ "def __init__," \
							+ "type mismatch in nb or nb/ne values: " \
							+ "nb type: " + str( type( v_original_nb ) ) \
							+ "nb/ne type: " + str( type( f_nbne_ratio ) ) \
							+ "."

		self.__original_nb=v_original_nb
		self.__nbne_ratio=f_nbne_ratio
		self.__adjusted_nb=None
		self.__do_bias_adjustment()		

		return
	#end __init__

	def __is_numeric_type( self, v_value ):
		o_val_type=type( v_value )
		return ( o_val_type in [ int, float ] )
	#end __is_numeric_type

	def __do_bias_adjustment( self ):

		f_const_term1=1.26
		f_const_term2=0.323

		if self.__original_nb is None \
				or self.__nbne_ratio is None:
			self.__adjusted_nb = None 
		else:

			f_numerator = float( self.__original_nb )
			f_denominator = f_const_term1  - ( f_const_term2 * self.__nbne_ratio )
			f_float_tol=1e-90

			assert f_denominator  > f_float_tol, \
					"In LDNENbBiasAdjustor instance, " \
							+ "def __do_bias_adjustment, " \
							+ "the bias adjustment calculation " \
							+ "is undefined (denoninator term is zero)."

			self.__adjusted_nb = f_numerator / f_denominator
		#end if no original nb or no nb/ne ratio, else compute

		return

	#end __do_bias_adjustment

	@property 
	def adjusted_nb( self ):
		return self.__adjusted_nb
	#end adjusted_nb

	@property 
	def original_nb( self ):
		return self.__original_nb
	#end adjusted_nb

	@original_nb.setter
	def original_nb( self, v_nb ):
		assert self.__is_numeric_type( v_nb ) or v_nb is None, \
			"in LDNENbBiasAdjustor instance, " \
						+ "def original_nb setter " \
						+ "expecting nb value to be type " \
						+ "numeric or None, type passed: " + str( type( v_nb ) )

		self.__original_nb=v_nb
		self.__do_bias_adjustment()
		return
	#end original

	@property
	def nbne_ratio( self ):
		return self.__nbne_ratio
	#end nbne_ratio

	@nbne_ratio.setter
	def nbne_ratio( self, f_nbne_ratio ):
		b_is_numeric=type( f_nbne_ratio ) == int \
						or type( f_nbne_ratio == float )

		assert self.__is_numeric_type( f_nbne_ratio ) or f_nbne_ratio is None, \
			"in LDNENbBiasAdjustor instance, " \
						+ "def nbne_ratio setter " \
						+ "expecting nb value to be a numeric type " \
						+ "or None.  Type passed: " + str( type( f_nbne_ratio ) )

		self.__nbne_ratio=f_nbne_ratio
		self.__do_bias_adjustment()

		return
	#end setter nbne_ratio	

#end class LDNENbBiasAdjustor

class NbAdjustmentRangeAndRate( object ):

	'''
	2017_03_07.  Class to convert a string of the form m[-n]:r
	into two integers giving a start and end cycle number,
	and a float giving a rate for reducing/augmenting
	Nb (and Nc) by that rate over the given range of simulation 
	(breeding) cycles.  If string has form m:r, then the range 
	is restricted to the nth cycle.  Otherwise, given m-n:r, 
	the cycle range is set as cycles m to n.

	'''
	def __init__( self,
				i_min_valid_cycle, 
				i_max_valid_cycle, 
				s_range_as_string=None ):

		self.__min_valid_cycle=i_min_valid_cycle
		self.__max_valid_cycle=i_max_valid_cycle

		self.__start_cycle=None
		self.__end_cycle=None
		self.__rate=None
		
		if s_range_as_string is not None:
			self.__set_range_and_rate_from_string( s_range_as_string )
		#end if we have a string giving range and rate
		return
	#end __init__

	def __set_range_and_rate_from_string( self, s_string ):
		'''
		See comments at class declaration.
		'''
		INDEX_RANGE=0
		INDEX_RATE=1

		INDEX_START=0
		INDEX_END=1

		DELIMIT_RANGE_RATE=":"
		DELIMIT_RANGE="-"

		ls_range_and_rate=s_string.split( DELIMIT_RANGE_RATE )

		if len( ls_range_and_rate ) != 2:

			s_msg="In pgutilityclasses, class NbAdjustmentRangeAndRate, " \
								+ "instance, the range/rate string, " \
								+ s_string + ", cannot be parsed to yield a " \
								+ "a rate and a cycle range."
			raise Exception( s_msg )
		#end if invalid range and rate list len

		ls_range=ls_range_and_rate[ INDEX_RANGE ].split( DELIMIT_RANGE )
		i_total_range_items=len( ls_range )

		if i_total_range_items < 1 \
					or i_total_range_items > 2:

			s_msg="In pgutilityclasses, class NbAdjustmentRangeAndRate, " \
								+ "instance, the range/rate string, " \
								+ s_string + ", cannot be parsed to yield a " \
								+ "cycle range."
			raise Exception( s_msg )
		#end if invalid range list

		try:
			self.__rate=float( ls_range_and_rate[ INDEX_RATE ] )
			i_start=int( ls_range[ INDEX_START ] )

			#We keep this value only if there is no
			#second int in the range list:
			i_end=int( ls_range [ INDEX_START ] )
			if i_total_range_items == 2:
				i_end=int( ls_range[ INDEX_END ] )
			#end if there are 2 ints fo range

			##### temp
			print( "-------------")
			print( "in try having already typed the numbers" )
			#####

			if self.isValidRange( i_start, i_end ):
				self.__start_cycle=i_start
				self.__end_cycle=i_end
			else:
				s_msg="In pgutilityclasses, class NbAdjustmentRangeAndRate, " \
								+ "instance, the range values, start-end: " \
								+ str( i_start ) + "-" + str( i_end ) \
								+ "is not valid." 
				raise Exception( s_msg )
			#end if range is valid
		except ValueError as ve:
			s_msg="In pgutilityclasses, class NbAdjustmentRangeAndRate, " \
								+ "instance, the range/rate string, " \
								+ s_string + ", cannot be parsed to yield a " \
								+ "cycle rate and range."
			
			raise Exception( s_msg )
		except Exception as oex:
			#####  temp
			print("------------------" )
			print( "caught general exception" )
			print( "message: " + str(oex) )
			#####
			raise oex 
		#end try...except 

		##### temp
		print( "returning from __set_range_and_rate_from_string" )
		#####

		return
	#end __set_range_and_rate_from_string

	def isValidRange( self, i_start, i_end ):
		b_increasing=i_start<=i_end
		b_in_range=self.isValidCycleNumber( i_start ) \
						and self.isValidCycleNumber( i_end )
		##### temp
		print( "in isValidRange returning: " + str( b_increasing and b_in_range ) )
		#####

		return b_increasing and b_in_range
	#end isValidRange
	
	def isValidCycleNumber( self, i_number ):
		return ( i_number >= self.__min_valid_cycle \
					and i_number <= self.__max_valid_cycle )
	#end isValidCycleNumber

	def setRangeAndRate( self, s_string ):
		self.__set_range_and_rate_from_string( s_string )
		return
	#end setRangeAndRate

	@property
	def start_cycle( self ): 
		return self.__start_cycle
	#end property start_cycle

	@property
	def end_cycle( self ): 
		return self.__end_cycle
	#end property end_cycle

	@property
	def rate( self ):
		return self.__rate
	#end property rate


#end class NbAdjustmentRangeAndRate

if __name__ == "__main__":
#	
#	p1=1
#	p2=-3333.12
#	p3="test"
#
#	o1=FloatIntStringParamValidity( "p1", float, p1, 0, 10 )
#	o2=FloatIntStringParamValidity( "p2", int, p2, 0, 10 )
#	o3=FloatIntStringParamValidity( "p3", str, p3, 0, 10 )
#
#	for o in [ o1, o2, o3 ]:
#		print( o.isValid() )
#		print( o.reportValidity() )

	o_lc=LDNENbBiasCorrector( 200, 0.78 )
	print( o_lc.corrected_nb )

#end if main

