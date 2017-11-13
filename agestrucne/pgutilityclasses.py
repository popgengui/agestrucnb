'''
Description
Instead of putting utility classes in pgutilities,
this module will house all classes not directly related
to front or back end of the pg operations.
'''
from __future__ import division
from __future__ import print_function

from builtins import range
from past.utils import old_div
from builtins import object
__filename__ = "pgutilityclasses.py"
__date__ = "20160702"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import numpy
import re

from agestrucne.pgvalidationdefs import *

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

	'''
	These are the names used in the gui combobox,
	and so are the values returned when corresponding
	scheme is selected.
	'''

	SCHEME_ALL="All"
	SCHEME_NONE="None"
	SCHEME_PERCENT="Percent"
	SCHEME_REMOVE="Remove-N"
	SCHEME_CRIT="Indiv Criteria"
	SCHEME_COHORTS_PERC="Cohorts Percent"
	SCHEME_COHORTS_COUNT="Cohorts Count"
	SCHEME_RELATEDS="Relateds"

	SCHEMES_REQUIRING_ID_FIELDS=[ SCHEME_CRIT, 
									SCHEME_COHORTS_PERC, 
									 SCHEME_COHORTS_COUNT,
										SCHEME_RELATEDS ]

	PARAMS_IN_ID_FIELD_SCHEMES_WITH_NUMERIC_LISTS= [ "scheme_cohortperc_percentages", "scheme_cohortcount_counts" ]

	ATTR_NAME_SCHEME="sampscheme"
	ATTR_NAME_MIN_POP_NUMBER="min_pop_number"
	ATTR_NAME_MAX_POP_NUMBER="max_pop_number"
	ATTR_NAME_MIN_POP_SIZE="min_pop_size"
	ATTR_NAME_MAX_POP_SIZE="max_pop_size"
	
	DICT_DRIVER_SCHEME_NAME_BY_INTERFACE_NAME = { \
				SCHEME_NONE : "none",
				SCHEME_PERCENT : "percent",
				SCHEME_REMOVE : "remove",
				SCHEME_CRIT : "criteria",
				SCHEME_COHORTS_PERC : "cohortsperc",
				SCHEME_COHORTS_COUNT : "cohortscount",
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
				SCHEME_COHORTS_PERC : { "max_age" : "scheme_cohortperc_max_age",
								"min_pop_size" : "scheme_cohortperc_min_indiv_per_gen",
								"max_pop_size" : "scheme_cohortperc_max_indiv_per_gen",
								"percentages" : "scheme_cohortperc_percentages" },
				SCHEME_COHORTS_COUNT :{ "max_age" : "scheme_cohortcount_max_age",
								"min_pop_size" : "scheme_cohortcount_min_indiv_per_gen",
								"max_pop_size" : "scheme_cohortcount_max_indiv_per_gen",
								"counts" : "scheme_cohortcount_counts" },
				SCHEME_RELATEDS : { "percent_relateds" : "scheme_relateds_percent_relateds",
							"min_pop_size" : "scheme_relateds_min_indiv_per_gen",
							"max_pop_size" : "scheme_relateds_max_indiv_per_gen" } }

	DICT_ATTR_ORDER_BY_SCHEME= { \
				SCHEME_ALL : [ "min_pop_number", "max_pop_number" ],
				SCHEME_NONE : [ "none_dummy_param", "min_pop_size", "max_pop_size" ],
				SCHEME_PERCENT : [ "percentages", "min_pop_size", "max_pop_size"  ],
				SCHEME_REMOVE : [ "n", "min_pop_size", "max_pop_size"  ],
				SCHEME_CRIT : [ "min_age" , "max_age", "min_pop_size", "max_pop_size" ],
				SCHEME_COHORTS_PERC : [ "max_age" , "percentages", "min_pop_size", "max_pop_size" ],
				SCHEME_COHORTS_COUNT : [ "max_age" , "counts", "min_pop_size", "max_pop_size" ],
				SCHEME_RELATEDS : [ "percent_relateds", "min_pop_size",  "max_pop_size" ] }
		
	CRIT_EXPRESSIONS_IN_ATTR_ORDER=[ "%age% >= ", "%age% <=" ]


	'''
	2017_06_02.  See def validateArgs, which creates a dict of arg values keyed to
	param names.
	'''
	DICT_VALIDATIONS_BY_SCHEME={ \
					SCHEME_ALL : lambda dsv : dsv[ "min_pop_number" ] > 0  \
										and dsv[ "min_pop_number" ] <= dsv[ "max_pop_number" ],
					SCHEME_NONE : lambda dsv : dsv[ "min_pop_size" ] > 0 \
										and dsv ["min_pop_size" ] <= dsv [ "max_pop_size" ],
					SCHEME_PERCENT : lambda dsv : dsv [ "min_pop_size" ] > 0 \
										and dsv [ "min_pop_size" ] <= dsv [ "max_pop_size" ],					
					SCHEME_REMOVE : lambda dsv : dsv [ "min_pop_size" ] > 0 \
										and dsv [ "min_pop_size" ] <= dsv [ "max_pop_size" ], \
					SCHEME_CRIT :  lambda dsv : dsv [ "min_age" ] >= 0  \
										and dsv[ "min_age" ] <= dsv[ "max_age" ]
										and dsv[ "min_pop_size" ] > 0 \
										and dsv[ "min_pop_size" ] <= dsv [ "max_pop_size" ],					
					SCHEME_COHORTS_PERC : lambda dsv : dsv[ "max_age" ] >= 0  \
										and dsv[ "min_pop_size" ] >= 0 \
										and dsv[ "min_pop_size" ] <= dsv [ "max_pop_size" ] ,
					SCHEME_COHORTS_COUNT : lambda dsv : dsv[ "max_age" ] >= 0  \
										and dsv[ "min_pop_size" ] >= 0 \
										and dsv[ "min_pop_size" ] <= dsv [ "max_pop_size" ] ,
					SCHEME_RELATEDS : lambda dsv : dsv[  "percent_relateds" ] >= 0 \
										and dsv[ "percent_relateds" ] <= 100 \
										and dsv[ "min_pop_size" ] >= 0 \
										and dsv[ "min_pop_size" ] <= dsv[ "max_pop_size" ] }

	POP_NUM_RANGE_MESSAGE="min pop number > 0, " \
							"min pop number <= max pop number"
	POP_SIZE_RANGE_MESSAGE="min pop size > 0, " \
							"min pop size <= max pop size"
	POP_AGE_RANGE_MESSAGE="min age > 0 and min age <= max age"
	PERCENT_RELATEDS_RANGE_MESSAGE="percent relateds >= 0 and percent relateds <= 100"

	DICT_VALIDATION_MESSAGES_BY_SCHEME={ \
					SCHEME_ALL :  POP_NUM_RANGE_MESSAGE,
					SCHEME_NONE : POP_NUM_RANGE_MESSAGE + ", " + POP_SIZE_RANGE_MESSAGE,				
					SCHEME_PERCENT : POP_SIZE_RANGE_MESSAGE,
					SCHEME_REMOVE : POP_SIZE_RANGE_MESSAGE,
					SCHEME_CRIT : POP_AGE_RANGE_MESSAGE + ", " + POP_SIZE_RANGE_MESSAGE,
					SCHEME_COHORTS_PERC : "max age >= 0, " + POP_SIZE_RANGE_MESSAGE,
					SCHEME_COHORTS_COUNT : "max age >= 0, " + POP_SIZE_RANGE_MESSAGE,
					SCHEME_RELATEDS : PERCENT_RELATEDS_RANGE_MESSAGE + POP_SIZE_RANGE_MESSAGE }

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

	def validateArgs( self ):

		'''
		2017_06_02.  We add a validation def for the parameters that involve
		minima and maxima.
		'''

		MYCLASS=NeEstimatorSamplingSchemeParameterManager
		
		s_validation_message=None

		s_scheme=self.__get_scheme_name()
		
		dsv_value_by_param={}

		for s_arg in NeEstimatorSamplingSchemeParameterManager\
							.DICT_ATTR_ORDER_BY_SCHEME[ s_scheme ]:

			s_attr_name=self.__attr_prefix \
					+ NeEstimatorSamplingSchemeParameterManager\
											.DICT_ATTR_BY_SCHEME[ s_scheme ][ s_arg ]

			v_value=getattr( self.__interface, 
									s_attr_name )

			dsv_value_by_param[ s_arg ] = v_value
		#end for each arg get its value

		b_are_valid_args=MYCLASS.DICT_VALIDATIONS_BY_SCHEME[ s_scheme ]( dsv_value_by_param )

		if not b_are_valid_args:
			s_validation_message=MYCLASS.DICT_VALIDATION_MESSAGES_BY_SCHEME[ s_scheme ]
		#end if not valid args
		
		return s_validation_message
	#end validateArgs

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

	#end getSampleSchemeArgsForDriver

	'''
	This getter added 2017_08_27 to facilitate the PGGuiNeEstimator
	interface plotting progress from min to max cycle.
	'''

	def getSampleSchemePopRange( self ):

		CLSVALS=NeEstimatorSamplingSchemeParameterManager
		s_scheme_all=CLSVALS.SCHEME_ALL

		s_attr_min_pop_number=self.__attr_prefix \
				+ CLSVALS.DICT_ATTR_BY_SCHEME[ s_scheme_all ] [ "min_pop_number" ]

		s_attr_max_pop_number= self.__attr_prefix \
				+ CLSVALS.DICT_ATTR_BY_SCHEME[ s_scheme_all ][ "max_pop_number" ]
	
		i_min_pop_number=getattr( self.__interface, s_attr_min_pop_number )
		i_max_pop_number=getattr( self.__interface, s_attr_max_pop_number )
		return( i_min_pop_number, i_max_pop_number )		
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
	'''
	2017_06_02.  See def validateArgs, which creates a dict of arg values keyed to
	param names.
	'''
	DICT_VALIDATIONS_BY_SCHEME={ \
					SCHEME_ALL : lambda dsv : dsv[ "min_loci_number" ] > 0  \
										and dsv[ "min_loci_number" ] <= dsv[ "max_loci_number" ],
					SCHEME_NONE : lambda dsv : dsv[ "min_loci_count" ] > 0 \
										and dsv ["min_loci_count" ] <= dsv [ "max_loci_count" ],
					SCHEME_PERCENT : lambda dsv : dsv [ "min_loci_count" ] > 0 \
										and dsv [ "min_loci_count" ] <= dsv [ "max_loci_count" ],
					SCHEME_TOTAL : lambda dsv : dsv [ "min_loci_count" ] > 0 \
										and dsv [ "min_loci_count" ] <= dsv [ "max_loci_count" ] }
					

	LOCI_NUM_RANGE_MESSAGE="min loci number > 0, " \
							"min loci number <= max loci number"
	LOCI_COUNT_RANGE_MESSAGE="min loci count > 0, " \
							"min loci count <= max loci count"

	DICT_VALIDATION_MESSAGES_BY_SCHEME={ \
					SCHEME_ALL :  LOCI_NUM_RANGE_MESSAGE,
					SCHEME_NONE : LOCI_NUM_RANGE_MESSAGE + ", " + LOCI_COUNT_RANGE_MESSAGE,				
					SCHEME_PERCENT : LOCI_COUNT_RANGE_MESSAGE }

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

	def validateArgs( self ):

		'''
		2017_06_02.  We add a validation def for the parameters that involve
		minima and maxima.
		'''

		MYCLASS=NeEstimatorLociSamplingSchemeParameterManager
		
		s_validation_message=None

		s_scheme=self.__get_scheme_name()
		
		dsv_value_by_param={}

		for s_arg in MYCLASS.DICT_ATTR_ORDER_BY_SCHEME[ s_scheme ]:

			s_attr_name=self.__attr_prefix \
					+ MYCLASS.DICT_ATTR_BY_SCHEME[ s_scheme ][ s_arg ]

			v_value=getattr( self.__interface, 
									s_attr_name )

			dsv_value_by_param[ s_arg ] = v_value
		#end for each arg get its value

		b_are_valid_args=MYCLASS.DICT_VALIDATIONS_BY_SCHEME[ s_scheme ]( dsv_value_by_param )

		if not b_are_valid_args:
			s_validation_message=MYCLASS.DICT_VALIDATION_MESSAGES_BY_SCHEME[ s_scheme ]
		#end if not valid args
		
		return s_validation_message
	#end validateArgs

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
		elif self.__callable_after_eval( v_bool_expression_or_function_ref ):		
			self.__validator=eval( v_bool_expression_or_function_ref )
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
	def __callable_after_eval( self, v_bool_expression_or_function_ref ):
		b_return_value=True

		try:
			o_evaluated_item=eval( v_bool_expression_or_function_ref )
			b_return_value=callable( o_evaluated_item )
		except NameError as one:
			b_return_value=False
		#end try except

		return b_return_value
	#end __callable_after_eval

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

			self.__adjusted_nb = old_div(f_numerator, f_denominator)
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

'''
This s a convenience class supporting and used by
the NbAdjustmentRangeAndRate class below.  
It can be typed by an except clause,
because it will be the type of exception raised
when a an NbAdjustmentRangeAndRate object
is initialized with an invalid range or rate.
defs below.  This allows the validation def, 
validateNbAdjustment, in the PGGuiSimuPop 
object, to simply try to create
an NbAdjustmentRangeAndRate with the proposed
new user-entred expression, and to return false
if this kind of excetpion is thrown. 
'''

class RangeAndRateViolationException( Exception ):
	pass
#end class RangeAndRateViolationException

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
			raise RangeAndRateViolationException( s_msg )
		#end if invalid range and rate list len

		ls_range=ls_range_and_rate[ INDEX_RANGE ].split( DELIMIT_RANGE )
		i_total_range_items=len( ls_range )

		if i_total_range_items < 1 \
					or i_total_range_items > 2:

			s_msg="In pgutilityclasses, class NbAdjustmentRangeAndRate, " \
								+ "instance, the range/rate string, " \
								+ s_string + ", cannot be parsed to yield a " \
								+ "cycle range."
			raise RangeAndRateViolationException( s_msg )
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

			if self.isValidRange( i_start, i_end ):
				self.__start_cycle=i_start
				self.__end_cycle=i_end
			else:
				s_msg="In pgutilityclasses, class NbAdjustmentRangeAndRate, " \
								+ "instance, the range values, start-end: " \
								+ str( i_start ) + "-" + str( i_end ) \
								+ " is not valid. Please check that your min " \
								+ "cycle number is at least " + str( self.__min_valid_cycle )\
								+ ", your max cycle is no more " \
								+ "than the total reproductive cycles, " \
								+ "and that your min is less than or equal to your max."
				raise RangeAndRateViolationException( s_msg )
			#end if range is valid
		except ValueError as ve:
			s_msg="In pgutilityclasses, class NbAdjustmentRangeAndRate, " \
								+ "instance, the range/rate string, " \
								+ s_string + ", cannot be parsed to yield a " \
								+ "cycle rate and range."
			
			raise RangeAndRateViolationException( s_msg )
		except Exception as oex:
			raise oex 
		#end try...except 

		return
	#end __set_range_and_rate_from_string

	def isValidRange( self, i_start, i_end ):
		b_increasing=i_start<=i_end
		b_in_range=self.isValidCycleNumber( i_start ) \
						and self.isValidCycleNumber( i_end )

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

class NbNeReader( object ):

	'''
	2017_04_17.  This class is used to check the header line of a
	Genepop file for a terminating string of the form, "nbne=r", where
	r is a float giving an Nb/Ne ratio.  Genepop file generated using our
	pgop, pginput and pgoutput simupop driving modules will store the 
	value suchwise.  If the value stored in the header is very close
	to zero (see def __read_nbne_ratio), then the __nbne_ratio will
	be set to NO_RATIO (curently = None).
	'''

	NO_RATIO=None

	def __init__( self, v_genepop_file ):
		'''
		Param v_genepopfile_manager_object should be either,
			--A string giving the name of a genepop file, or, 
			--A GenepopFileManager object.
		'''
		self.__nbne_ratio=NbNeReader.NO_RATIO
		self.__read_nbne_ratio( v_genepop_file )
		return
	#end init

	def __read_nbne_ratio( self, v_genepop_file ):
		'''
		Except for the file open call, this def was copied
		from module pgdriveneestimator.

		Note that this def will only assign the self.__nbne_ratio
		when it can find it in the file header.  Otherwise the
		def returns without touching the attribute's value.

		Note that if the value found in the header text is very
		close to zero, the def will not assign any value to the attribute
		self.__nbne_ratio.
		'''

		s_header_text=None

		if hasattr( v_genepop_file, 'header' ):
			s_header_text=v_genepop_file.header
		else:
			try:
				o_file=open( v_genepop_file, 'r' )
			except IOError as ioe:
				s_msg="In NbNeReader, def __read_nbne_ratio, " \
							+ "there was an error opening the file, " \
							+ v_genepop_file + ".  The error message is: " \
							+ str( ioe )
				raise Exception( IOError )
			#end try...except
			s_header_text=o_file.readline().strip()

		#end if we have a genepop file

		'''
		2017_02_13.  In searching for an Nb/Ne ratio value in the
		genepop file header text, we assume it is in the form, 
		"nbne=<float>", or possibly "nbne=<int>", where <float>
		or <int> are numbers.  We also assume it is the final
		text in the header line.
		'''

		v_value=None
		s_keyval_splitter="="
		s_nbne_regex="nbne=[0-9,\.]+"
		f_reltol=1e-90

		ls_matches=re.findall( s_nbne_regex, s_header_text )

		'''
		We do not expect groups of matches from 
		the header, and so reject any non-list
		(such as the resulting tuple for groups)
		returned from re.findall.
		'''
		if type( ls_matches ) != list:
			s_msg="In NbNeReader instance, def __read_nbne_ratio, " \
						+ "The program is expecting a list to be returned from call to " \
						+ "re.findall.  Returned:  " + str( ls_matches ) \
						+ "."
			raise Exception( s_msg )
		#end if return is not a list, exception

		i_total_matches=len( ls_matches )
		
		if i_total_matches > 0:
			if i_total_matches > 1:
				s_msg="In NbNeReader instance, def __read_nbne_ratio, " \
						+ "the program cannot correctly parse the " \
						+ "genepop file header to find the nb/ne ratio.  " \
						+ "It expects either no entry " \
						+ "or one key=value entry at the end of the header " \
						+ "text.  Header text: \"" + s_header_text + "\"."
				raise Exception( s_msg )
			else:
				ls_keyval=( ls_matches[ 0 ].split( s_keyval_splitter ) )
				try:
					s_value=ls_keyval[ 1 ]
					v_value=float( s_value )

					#We retain the intitialized None value,
					#unless ratio > 0.0
					if v_value > f_reltol:

						self.__nbne_ratio=v_value

					#end if value > zero
				except:
					s_msg="In NbNeReader instance, def __read_nbne_ratio, " \
								+ "The program cannot parse and type the Nb/Ne ratio value from " \
								+ "the genepop file entry, " + str( ls_matches[ 0 ] ) + "."
					raise Exception( s_msg )
				#end try ... except
			#end if more than one match, else one
		#end if total matches > 0
		return
	#end __read_nbne_ratio

	@property 
	def nbne_ratio( self ):
		return self.__nbne_ratio
	#end property

#end class NbNeReader

class GenepopPopWriter( object ):
	'''
	This class was created to simplify
	and speed up the output performance 
	of the simulation.  It is an alternative
	to the original 3-file output that I conserved
	from the original AgeStructure code.  

	This class is meant to be used by PGOpSimuPop instances,
	and the PGOutputSimuPop instances,
	to store output until a threshold is reached, when it
	will then write it to file.  

	Assumtions 
	  1. The client adds entries using numbering with ints the "pop" sections
		in the order they are intended to be written to file. 
	  2.  The client adds entries in the order they are to be written.
	  3.  The loci list is either \n endlined, or on a single line.

	As of 2017_04_22 it is not yet integrated into the
	simulation code.
	'''

	#How many entry lines are stored
	#before writing then to file.
	STANDARD_CAPACITY=1e5
	
	def __init__( self, s_genepop_file_name, s_header, 
							s_loci_lines,
							i_max_entry_capacity=STANDARD_CAPACITY ):
		
		self.__genepop_file=s_genepop_file_name
		self.__header=s_header
		self.__loci_lines=s_loci_lines
		self.__max_capacity=i_max_entry_capacity

		self.__pops={}
		self.__num_last_pop_written=None
		self.__numbers_of_written_pops=None
		self.__entry_count=0
		return
	#end __init

	def __write_current_pop_entries( self ):

		'''
		This def assumes that the keys
		to the self.__pops dictionary
		are integers, that the order
		they should be in in the file
		is given by the integers.		
		'''

		o_file=open( self.__genepop_file, 'a' )	

		li_pop_nums_sorted=list( self.__pops.keys() )
		li_pop_nums_sorted.sort()

		if self.__num_last_pop_written is None:
			o_file.write( self.__header + "\n" )
			o_file.write( self.__loci_lines + "\n" )
		#end if no pop yet written

		#If we are not in the middle of the last pop written,
		#end add a "pop" line
		if li_pop_nums_sorted[ 0 ] != self.__num_last_pop_written:
			o_file.write( "pop\n" )
		#end if a new pop entry

		self.__numbers_of_written_pops.append( li_pop_nums_sorted[ 0 ] )

		for s_entry in self.__pops[ li_pop_nums_sorted[ 0 ] ]:
				o_file.write( s_entry + "\n" )
				self.__entry_count -= 1
		#end for each entry in the pop with lowest number

		for i_pop in li_pop_nums_sorted[ 1: ]:
			o_file.write( "pop\n" )

			for s_entry in self.__pops[ i_pop ]:
				o_file.write( s_entry + "\n" )
				self.__entry_count -= 1
			#end for each entry in this pop, write
		#end for each pop after the one with lowest number
		
		o_file.close()
		self.__num_last_pop_written=max( li_pops_by_num_sorted )

		return
	#end __write_current_pop_entries	

	def addEntryAndWriteFirstIfFull( self, i_pop_number, s_indiv_and_loci_entry ):
		'''
		This def checks the current capacity, and if the number of entries 
		currently meets it, it will write the current pops to the file
		given by the self.__genepop_file string.

		Otherwise it will add the entry to the pop indicated by arg i_pop_number.
		'''

		if self.__entry_count > i_max_entry_capacity:
			s_msg="In GenepopPopWriter instance, the current total " \
						+ "for number of entries, " + str( self.__entry_count ) \
						+ "exceeds the value for maximum capacity, " \
						+ str( self.__max_capacity ) + "."
		elif self.__entry_count==i_max_entry_capacity:
			self.__write_current_pop_entries
		else:
			b_pop_already_written_and_surpassed = \
				i_pop_number in self.__numbers_of_written_pops \
					and i_pop_number != self.__num_last_pop_written
			b_pop_number_smaller_than_current = \
				i_pop_number < self.__num_last_pop_written
			if b_pop_already_written_and_surpassed \
					or b_pop_number_smaller_than_current:
				s_msg="In GenepopPopWriter instance, the current entry, " \
							+ "cannot be added.  It has a pop number, "  \
							+ str( i_pop_number ) \
							+ "lower than the last one written,  " \
							+ "with other pops written after it."
				raise Exception( s_msg )
			else:
				if i_pop not in self.__pops:
					self.__pops[ i ]=[ s_indiv_and_loci_entry ]
				else:
					self.__pops[ i ].append( s_indiv_and_loci_entry )
				#end
				'''
				This should be the only code that increments the
				entry count. Note that it is decremented only in
				__write_current_pop_entries.
				'''
				self.__entry_count += 1
					
			#end if pop has a number showing its either out of order
			#or already written

	def __get_total_unused_capacity( self ):
		return i_max_entry_capacity - self.__entry_count
	#end __get_total_unused_capacity

	@property 
	def entry_count( self ):
		return self.__entry_count	
	#end property entry_count

#end class GenepopPopWriter

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

