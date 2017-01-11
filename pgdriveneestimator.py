#!/usr/bin/env python

'''
Description

given 
	-->a list of genepop files, 
	-->a list of percentages of the total indiv
	   to subsample
	--> a number giving a minimum pop size 
	   after subsampling
	-->a minimum allele frequency (single float)
	--> a number giving the total replicate NeEstimator runs 
	    to be executed on each file at each subsample percentage 

	subsamples and then runs the Ne estimator for each combination of 
	genepop_file,percentage,replicate_number. 
	
	As of Fri May 13 19:01:06 MDT 2016, still not sure
	how best to get the results to file or stream.

Mon Aug 15 20:04:00 MDT 2016
	revised so that now args list includes
	-->a list of genepop files, 
	-->one of [percent|remove] (names a subsampling scheme, to be enlarged)
	-->a list of percentages, for percent samplin, or N-values for removing N
		from the individuals	
	--> a number giving a minimum pop size 
	   after subsampling (fewer than the min count of indiv, and the pop is skipped)
	-->a minimum allele frequency (single float)
	--> a number giving the total replicate NeEstimator runs 
	    to be executed on each file at each subsample percentage 
	-->optional the number of processes to create in performing the
		estimates in parallele, on process for each population (as divided up inside a file,
		or as given by a signle genepop file with only one population listed)
	
	Also revised to allow the improtation of this mod, so that the same operations
	can be intitiated by a call to "mymain".  The importation method allows for 
	passing in two file objects, open for writing.  The console method, that satisfies
	"if __name__== "__main__", does not allow the file object args and prints to stdout and stderr.

Wed Sep  7 18:12:26 MDT 2016
	revised so that now args list includes
	-->a list of genepop files, 
	-->one of [percent|remove|criteria] (names a subsampling scheme, to be enlarged)
	-->a list of comma-delimited percentages, for percent samplin, or N-values for removing N
		from the individuals, or, for criteria, a comma-delimited list consisting of:
				1. list of semicolong-delimited genepop indiv id fields (example "numberage;sex;parent")
				2. list of python types corresponding to each field (example "int;int;string")
				3. one or more test expressions using field names 
					surrounded by percentage signs.  For example, to include 
					2 criteria: "%age%>3 and %age%<6 and %sex% == 3","%parent% <= "3992"
	--> a number giving a minimum pop size 
	   after subsampling (fewer than the min count of indiv, and the pop is skipped)
	-->a hypnated pair of numbers giving the minimum and maximum i where
		i gives the ith population listed in any one of the genepop files. For
		example to run the estimator only on the 2nd through the 10th population,
		the arg would be: "2-10" (all subject to minimum pop size).  
		Using "all" for this arg will result in all pops being included.
	-->a minimum allele frequency (single float)
	--> a number giving the total replicate NeEstimator runs 
	    to be executed on each file at each subsample percentage 
	-->optional the number of processes to create in performing the
		estimates in parallele, on process for each population (as divided up inside a file,
		or as given by a signle genepop file with only one population listed)

2016_09_24
	Revisions to add new sampling schemes (No-subsampling, and AgeStructureNe schemes to get
	cohorts and siblings (Relateds).  In addition to the percent, remove, and
	criteria schemes, we add "none", "cohorts", and "relateds" as options for arg 2.
	For arg 3 we now add, if cohorts is the second arg value, comma-delimited
	fields (see mod genepopfilesampler.py, class 
	GenepopFileSamplerParamsAgeStructureCohorts):
			--> int, max individual age
	And, if "relateds" is the 2nd arg value (see mod genepopfilesampler.py, class
	GenepopFileSamplerIndividualsAgeStructureRelateds):
			1. float, percent of relateds each gen
	Also added max pop size as new arg, now arg #
2016_10_20
	Adding to Loci scheme "percent," to subsample a percentage
	of the loci (as circumscribed by existing params min loci 
	position and max loci position.
'''
__filename__ = "pgdriveneestimator.py"
__date__ = "20160510"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import glob
import sys
import os
from multiprocessing import Pool
import time
import genepopindividualid as gpi

'''
In case of interrupted 
multiprocessing runs.
We copy the output files
as *.interrupted. (See
except clause in def 
drive_estimator)
'''
import shutil

#read genepop file, and 
#sample its pop, and store
#results:
import genepopfilemanager as gpf
import genepopfilesampler as gps

#related to calling Tiago's
#pygenomics class that itself
#calls NeEstimator
import pgopneestimator as pgne
import pginputneestimator as pgin
import pgoutputneestimator as pgout
import pgutilities as pgut

VERBOSE=False
VERY_VERBOSE=False

#arguments passed either at command line
#or from python using def mymain, having
#imported this module
spacer="   "
spacer2="   "
spacer3="  "

LS_FLAGS_SHORT_REQUIRED=[ "-f",  "-s", "-p", "-m", "-a", "-r", "-e", "-c", "-l", "-i",  "-n", "-x", "-g","-q" ]
LS_FLAGS_LONG_REQUIRED=[ "--gpfiles", "--scheme", "--params", "--minpopsize", "--maxpopsize", "--poprange", "--minallelefreq", "--replicates", "--locischeme", "--locischemeparams",  "--mintotalloci", "--maxtotalloci", "--locirange", "--locireplicates" ]
LS_ARGS_HELP_REQUIRED=[ "Glob pattern to match genepop files, enclosed in quotes. " \
						+ "(Example: \"mydir/*txt\")",
				"\"none\", \"percent\", \"remove\", \"criteria\", \"cohorts\", \"cohortsperc\", or \"relateds\", " \
						+ "indicating an individual-sampling scheme,  whether to sample none " \
						+ "(only apply min/max pop size criteria), " \
						+ "by percentages, removing N individuals randomly, testing individual id fields, " \
						+ "selecting evenly within age groups, or selecing siblings.",
				"The comma-delimited list of parameters used for the sampling scheme. " \
						 + spacer + "For \"none\", any value (it will be ignored)." \
						 + spacer + "For \"percent\", a list of integers, percentages." \
						 + spacer + "For \"remove\", a list of integers, total indiv. to remove." \
						 + spacer + "For \"criteria\", \"cohorts\", and \"relateds\", 3 parts (the whole surrounded by quotes):" \
						 + spacer2 + "(1) Semicolon-delimited field names (ex, for the AgeStructureNe genpop output: \"id;sex;father;mother;age\")."\
						 + spacer2 + "(2) Semicolon-delimited field (python) types (ex, for the AgeStructureNe genepop: \"floatint;float;float;float\")." \
						 + spacer2 + "(3) A set of parameters for the given sampling scheme:" \
						 + spacer3 + "i. \"critera\": semicolon-delimited test expressions " \
								   + "(ex: \"age<5;sex==1\")." \
						 + spacer3 + "ii. \"cohorts\": single integer giving max age of cohorts. " \
						 + spacer3 + "iii. \"cohortsperc\": two semicolon-delimited values, a single " \
						 + "integer giving max age of cohorts, and a hyphenated list of numbers " \
						 		   + "(ints or floats) giving percenantages at which to randomly " \
								   + "sample from the cohorts. " \
						 + spacer3 + "iv. \"relateds\": single float giving percent of relateds to select " \
							+ "(remainder filled in by the un-chosen to meet the min pop size value).", 
		"Minimum pop size (single integer).",
		"Maximum pop size (single integer).",
		"Genepop file pop range (hyphenated pair of integers, i-j indicating estimator should evaluate " \
				+ "the ith through the jth pops in each genepop file).",
		"Float, minimum allele frequency, one of NeEstimator's \"crit\" values.",
		"Integer, total sampling replicates (for the individual sampling scheme) " \
				+ "to run (Note: under the \"remove\" scheme," \
				+ "when sampling by removing one individual from a pop of size p, " \
				+ "all p combinations will be run, ignoring this arg).", 
		"String, loci sampling scheme.  Values for the scheme are \"none\", "  \
				+ "\"percent\", \"total\".  \"none\" and \"percent\"  use " \
				+ "all of the loci range values (see below), while the \"total\". " \
				+ "scheme ignores the min and max loci limits." \
				+ "Under the loci scheme \"none\", the value for max total loci "\
				+ "(see below ) will result in a random sample of the max " \
				+ "value when the range exceeds it.",  
		"Sampling scheme paramaters, for \"none\", any string (required as place-holder); for \"percent\","  \
				+ "a comma-delimited list of numeric values (int or float) p, with 0<=p<=100; " \
				+ "for \"total\", a comma-delimited list of integers, each giving a number of " \
				+ "loci to randomly sample from each pop.", 
		"Integer, minimum number of loci required for sample.",
		"Integer, maximum number of loci, randomly selected among i-j, if max is less than (j-i)+1." ,
		"Loci range (hyphenated pair of integers), include loci numbers i-j as ordrered in the file.",
		"Integer, Number of loci sampling replicates (value of 1 means one loci subsample per loci sampling param, per individual replicate)." ]

LS_FLAGS_SHORT_OPTIONAL=[  "-o", "-d" ]
LS_FLAGS_LONG_OPTIONAL=[ "--processes", "--mode" ]
LS_ARGS_HELP_OPTIONAL=[  "total processes to use (single integer) Default is 1 process.",
				"\"no_debug\", \"debug1\", \"debug2\", \"debug3\", \"testserial\", \"testmulti\"" \
				+ ".  Indicates a run mode. The default is \"no_debug\", which runs multiplexed with standard output.  " \
				+ "Other modes except \"testmulti\", run non-parallelized, with increasing output.  " \
				+ "Debug 3, for example, adds to the output a table listing, for each indiv. " \
				+ "in each file, which replicate Ne estimates include the individual.  It also preserves " \
				+ "the intermediate genepop and NeEstimator output files" ]


#Indices into the args as passed as list/sequence to def parse_args:
IDX_GENEPOP_FILES=0
IDX_SAMPLE_SCHEME=1
IDX_SAMPLE_VALUE_LIST=2
IDX_MIN_POP_SIZE=3
IDX_MAX_POP_SIZE=4
IDX_POP_RANGE=5
IDX_MIN_ALLELE_FREQ=6
IDX_REPLICATES=7
IDX_LOCI_SAMPLING_SCHEME=8
IDX_LOCI_SCHEME_PARAM=9
IDX_LOCI_MIN_TOTAL=10
IDX_LOCI_MAX_TOTAL=11
IDX_LOCI_RANGE=12
IDX_LOCI_SAMPLE_REPLICATES=13
IDX_PROCESSES=14
IDX_DEBUG_MODE=15
IDX_MAIN_OUTFILE=16
IDX_SECONDARY_OUTFILE=17
IDX_MULTIPROCESSING_EVENT=18

#these args are used by callers who import this mod
#and call mymain directly -- users of the console
#don't use these, and resultsa are to stdout for the main outpu,
#and stderr for the secondary output.  This is just a 
#bit of stand-in code in case usage ever implements hidden
HIDDEN_ARGS=[ "file_object_main", "file_object_secondary", "multiprocessing_event" ]

#if caller from console or to mymain
#does not include opetionals,
#these are the defaults (see mymain,
#which is either invoked by python importing
#this mod, or is invoked by this mods
#code when python calls it as __main__:
DEFAULT_NUM_PROCESSES="1"
DEFAULT_DEBUG_MODE="no_debug"

#in order to properly name the subsampled
#files with replicate number, sample parameter
#value, and population number, and not to subsequently
#violate the NeEstimators limit of writing file names
#to 31 characters, we impose this limit on the input
#genepop files:
MAX_GENEPOP_FILE_NAME_LENGTH=310

#when running the estimate calls
#asynchronously, we test for event
#set (i.e. user wants to cancel)
#then wait a bit (see def 
#execute_ne_for_each_sample)
SECONDS_TO_SLEEP=1.00

#user enters the string as command
#line arg, codes tests with the constants
SAMPLE_BY_NONE="none"
SAMPLE_BY_PERCENTAGES="percent"
SAMPLE_BY_REMOVAL="remove"
SAMPLE_BY_CRITERIA="criteria"
SAMPLE_BY_COHORT="cohorts"
SAMPLE_BY_COHORT_PERCENTAGE="cohortsperc"
SAMPLE_BY_RELATEDS="relateds"

SAMPLE_SCHEMES_NON_CRITERIA=[ SAMPLE_BY_PERCENTAGES, 
									SAMPLE_BY_REMOVAL ]

SAMPLE_LOCI_SCHEME_NONE="none"
SAMPLE_LOCI_SCHEME_PERCENT="percent"
SAMPLE_LOCI_CONSTANT_TOTAL="total"

OUTPUT_DELIMITER="\t"
ENDLINE_SEQ="\n"
OUTPUT_ENDLINE="\n"
REPLICATE_DELIMITER=","
SAMPLE_SCHEME_PARAM_DELIMITER=","

#case number will be the populatiuon number
#based on the subsampled file sent to the
#Ne Estimator, but we will be using pop numbers
#always based on the original geepop file --
#and the current case ( Mon Jul 25 19:49:56 MDT 2016)
#is that before doing Ne Estimation, we split 
#up the original so that each population in it
#is run via a (temporary) separate genepop file,
#hence this field is always 0:
NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP=[ "case_number" ]

#For pgguineestimator.py to import and use to delete
#any files left after user has cancelled a run:
NE_ESTIMATOR_OUTPUT_FILE_TAGS=[ "NoDat.txt", "xTp.txt", "ne_run.txt" ]

NE_ESTIMATOR_OUTPUT_FILES_GENERAL_TAG="_g_[0-9]" 

#for users, namely instances of PGGuiNeEstimator,
#to be able to use their genpop file basename,
#and then locate intermediate genepopfiles
#created by this mod:
GLOB_INTERMEDIATE_GENEPOP_FILE_TAGS="*_r_*_g_*"


#because Ne2L (Ne2.exe, Ne2M), truncates output files
#using dot char, to unabiguiously name the subsampled
#input genepops and the Ne2L output files, we have
#to replace the dots.  This is the replacement char
INPUT_FILE_DOT_CHAR_REPLACEMENT="_"


'''
Main table formatting info:
'''
MAIN_TABLE_RUN_INFO_COLS=[ "original_file", "pop", "census",   "indiv_count", 
							"sample_value", "replicate_number", "loci_sample_value", 
							"loci_replicate_number","min_allele_freq" ] 

def set_indices_ne_estimator_output_fields_to_skip():

	IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP=[]

	for s_field_name in NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP:
		i_idx=pgout.PGOutputNeEstimator.OUTPUT_FIELDS.index( s_field_name )
		IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP.append( i_idx )
	#end for each ne est output field name

	return IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP
#end set_indices_ne_estimator_output_fields_to_skip

class ArgSet( object ):
	'''
	Wraps list of the arguments and their param names
	needed by this driver to do Ne estimations.

	Note: this class (a more elaborate version) should have 
	been created and used to more extensibly manag
	the evaluation and accessability of the argset passed. 
	Instead it is only a late addition,
	used to print out the arguments to a file (see def 
	write_parms_to_file).
	'''

	def __init__( self, ls_args ):

		self.param_names_in_order= \
				[ "genepop_files", "pop_sampling_scheme",
						"pop_sampling_values",
						"min_pop_size", "max_pop_size",
						"pop_num_range", "min_allele_frequency",
						"pop_sampling_replicates", "loci_sampling_scheme",
						"loci_sampling_values", "loci_min_total",
						"loci_max_total", "loci_num_range", 
						"loci_sampling_replicates", "total_cpu_processes",
						"debug_mode", "output_file",
						"secondary_output_file" ]
		
		#we make a copy of the arg values:
		self.arg_values=[ v_arg for v_arg in ls_args ]
		return
	#end init

	def __write_param_table_as_string( self ):
		'''
		We don't write the last arg, which is a ref
		to a multiprocessing event, only used by a
		call from the GUI (and otherwise None). So
		we just make sure that our arg values number
		at least as many as in our param name list.
		'''
		if len( self.arg_values ) < len( self.param_names_in_order ):
			s_msg="In pgdriveneestimator.py, class instance ArgSet, " \
						+ "def __write_param_table_as_string" \
						+ "the arg set fewer members (" \
						+ str( len( self.arg_values ) ) \
						+ ") than our total number of param names: " \
						+ str( len ( self.param_names_in_order ) ) + "."
			raise Exception( s_msg )
		#end if too many args than known number
		s_return_val = None

		#A header for the table:
		ls_return_val_lines=[ "Parameter\tValue" ]

		#so we can use pop:
		lv_reversed_copy_of_args=[ v_arg for v_arg in self.arg_values ]
		lv_reversed_copy_of_args.reverse()

		for s_param in self.param_names_in_order:
			s_value=str( lv_reversed_copy_of_args.pop() )
			ls_return_val_lines.append( s_param + "\t" + s_value )
		#end for each param name

		s_return_val="\n".join( ls_return_val_lines )

		return s_return_val

	#end __write_param_table_as_string

	@property 
	def paramtable( self ):
		s_table = self.__write_param_table_as_string()
		return s_table
	#end paramtable

#end class ArgSet

class DebugMode( object ):
	
	MODES=[ "no_debug", "no_debug_serial", "debug1", "debug2", "debug3", "testserial", "testmulti" ]

	NO_DEBUG="no_debug"
	NO_DEBUG_SERIAL="no_debug_serial"
	MAKE_TABLE="debug1"
	MAKE_TABLE_AND_KEEP_FILES="debug2"
	ALL_DEBUG_OPTIONS="debug3"
	TEST_SERIAL="testserial"
	TEST_MULTI="testmulti"

	KEEP_REPLICATE_GENEPOP_FILES=1
	KEEP_ESTIMATOR_FILES=2
	MAKE_INDIV_TABLE=4
	ALLOW_MULTI_PROCESSES=8
	PRINT_REPLICATE_SELECTIONS=16
	KEEP_NODAT_FILES=32
	'''
	These are files sometimes
	generated by NeEstimator, 
	none relevant to the LDNE
	results and described in
	the NeEstimator realease document
	"common.txt", which are non-informative,
	conaining only runtime, gpfilename,
	and number of loci.  See the file
	"common.txt" that is released with
	the NeEstimator program.
	'''
	KEEP_NE_EXTRA_FILES=64
		
	def __init__( self, s_mode="no_debug" ):
		self.__mode=s_mode
		self.__modeval=0
		self.__set_debug_mode()
	#end init

	def __set_debug_mode( self  ):
		if self.__mode==DebugMode.NO_DEBUG:
			self.__modeval=DebugMode.ALLOW_MULTI_PROCESSES
		elif self.__mode==DebugMode.NO_DEBUG_SERIAL:
			'''
			Mode no_debug_serial saves/writes no 
			extra files, nor does it allow mult 
			processes, so we set no flags. 
			(This mode is meant to duplicate the 
			output of "no_debug" but to operate 
			without the process pool).
			'''
			pass
		elif self.__mode==DebugMode.MAKE_TABLE:
			self.__modeval=DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.ALLOW_MULTI_PROCESSES
		elif self.__mode==DebugMode.MAKE_TABLE_AND_KEEP_FILES:
			self.__modeval=DebugMode.KEEP_REPLICATE_GENEPOP_FILES \
					+ DebugMode.KEEP_ESTIMATOR_FILES \
					+ DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.ALLOW_MULTI_PROCESSES \
					+ DebugMode.KEEP_NODAT_FILES \
					+ DebugMode.KEEP_NE_EXTRA_FILES 
		elif self.__mode==DebugMode.ALL_DEBUG_OPTIONS:
			self.__modeval=DebugMode.KEEP_REPLICATE_GENEPOP_FILES \
					+ DebugMode.KEEP_ESTIMATOR_FILES \
					+ DebugMode.MAKE_INDIV_TABLE  \
					+ DebugMode.KEEP_NODAT_FILES \
					+ DebugMode.KEEP_NE_EXTRA_FILES \
					+ DebugMode.PRINT_REPLICATE_SELECTIONS
		elif self.__mode==DebugMode.TEST_SERIAL:
			self.__modeval=DebugMode.KEEP_REPLICATE_GENEPOP_FILES \
					+ DebugMode.KEEP_ESTIMATOR_FILES \
					+ DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.PRINT_REPLICATE_SELECTIONS \
					+ DebugMode.KEEP_NODAT_FILES \
					+ DebugMode.KEEP_NE_EXTRA_FILES 
		elif self.__mode==DebugMode.TEST_MULTI:
			self.__modeval=DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.ALLOW_MULTI_PROCESSES \
					+ DebugMode.PRINT_REPLICATE_SELECTIONS 
		else:
			s_msg="in " + __filename__ + "DebugMode object, set_debug_mode: " \
			+ "unknown value for mode: " + str ( self.__mode ) 
			raise Exception( s_msg )
		#end if mode 0, 1, 2, ...  or undefined

		return		
    #end setDebugMode

	def isSet( self, i_flag ):
		return ( self.__modeval & i_flag ) > 0
	#end isSet

	@property
	def mode( self ):
		return self.__mode
	#end getDebugMode

	@mode.setter
	def mode( self, s_mode ):
		self.__mode=s_mode
		self.__set_debug_mode()
		return
	#end setter, mode
#end class DebugMode

def get_datetime_as_string():
	from datetime import datetime
	o_now=datetime.now()
	return  o_now.strftime( "%Y.%m.%d.%H.%M.%f" )
#end get_datetime_as_string

def set_debug_mode( s_arg ):

	o_debug_mode=None

	if s_arg in DebugMode.MODES:
		o_debug_mode=DebugMode( s_arg )
	else:
		s_msg="mode argument must be one of, " \
				+ ",".join( DebugMode.MODES ) \
				+ ".  value received: " + s_arg \
				+ "."
		raise Exception(  s_msg )
	#end if s_arg in MODES
	
	return o_debug_mode

#end set_debug_mode

def get_invalid_file_names( ls_file_names ):
	'''
	Currently only check is for file name
	length (see comments above declaration of const 
	MAX_GENEPOP_FILE_NAME_LENGTH.
	'''
	MSG_FILE_TOO_LONG="File name longer than " \
			+ str( MAX_GENEPOP_FILE_NAME_LENGTH ) \
			+ " characters."

	ls_invalid_file_names_and_messages=[]

	for s_file_name in ls_file_names:
		s_file_name_no_path=os.path.basename( s_file_name )
		i_len_file_name=len( s_file_name_no_path )

		if i_len_file_name > MAX_GENEPOP_FILE_NAME_LENGTH:
			ls_invalid_file_names_and_messages.append( \
					", ".join( [ s_file_name, MSG_FILE_TOO_LONG ] ) )
		#and if file name too long
	#end for each file name

	return ls_invalid_file_names_and_messages
#end get_invalid_file_names

def file_name_list_is_all_strings( ls_files ):

	b_all_strings=True

	lo_types=[ type( s_file ) for s_file in  ls_files ]
	set_types=set( lo_types )
	i_num_types=len( set_types )

	if set_types.pop() != str or i_num_types != 1:
		b_all_strings=False
	#end if type not str or >1 type

	return b_all_strings

#end file_name_list_is_all_strings
	
def get_genepop_file_list( s_genepop_files_arg ):
	'''
	if invoked from the console the arg is a glob expression
	if invoked from the gui interface in pgguineestimator.py,
	the arg is a list, such that eval will genreate a python
	list of strings.

	This def assumes that no user will invoke this mod from 
	the command line with a glob expression, includeing a file name,
	that can be evaluated as a python list (i.e. "[ \"item\", \"item\" ... ]
	
	'''

	ls_files=None

	try:

		ls_files=eval( s_genepop_files_arg )

		if type( ls_files ) != list:
			#still could be a glob expression, for example,
			#of a file name that python can eval as an int or float,
			#so we'll just glob the orig:

			ls_files=glob.glob( s_genepop_files_arg )
		else:
			#make sure it's a list of strings
			if not( file_name_list_is_all_strings( ls_files ) ):
				s_msg="In pgdriveneestimator.py, def get_genepop_file_list, " \
						+ "genepop file arg evaluated as a list, but, not composed " \
						+ "of strings: " + str( list ) + "."
				raise Exception( s_msg )
			#end if not all strings in list
	except ( NameError, SyntaxError ) as evalfail:

		'''
		this is caught if the eval fails due to 
		the arg being a string.  Further, a syntax
		error results if the arg begins/ends in a wildcard
		"*" char -- as will happen often with a glob.

		So for these eval failures we assume the arg 
		is a glob expression
		'''

		ls_files=glob.glob( s_genepop_files_arg )

	except Exception as unknown_fail:
		s_errortype=type( unknown_fail ).__name__
		s_msg="In pgdriveneestimator.py, def get_genepop_file_list, " \
						+ "gene pop file arg, " \
						+ str( s_genepop_files_arg ) \
						+ ", eval operation produced " \
						+ "error of type " + s_errortype \
						+ ", with message, " + str( unknown_fail ) + "." 
		raise Exception( s_msg )
	#end try eval, except name error, except other

	return ls_files
#end get_genepop_file_list

def parse_args( *args ):

	
	ls_files=get_genepop_file_list( args[ IDX_GENEPOP_FILES ] )

	ls_invalid_file_names_and_messages=get_invalid_file_names( ls_files )

	if len( ls_invalid_file_names_and_messages ) > 0:

		s_details="\n".join( ls_invalid_file_names_and_messages )
		s_msg="In pgdriveneestimator.py, def parse_args, " \
				+ "the following files can't be processed for " \
				+ "the reasons noted:\n" 
		s_msg += s_details

		raise Exception( s_msg )

	#end if invalid file names, exception

	s_sample_scheme=args[ IDX_SAMPLE_SCHEME ]

	#if percentages,  convert to proportions
	#for the sampler
	if s_sample_scheme == SAMPLE_BY_NONE:
		lv_sample_values=None
	elif s_sample_scheme == SAMPLE_BY_PERCENTAGES:
		lv_sample_values=[ float( s_val )/100.0  for s_val in args[ IDX_SAMPLE_VALUE_LIST ].split( \
																	SAMPLE_SCHEME_PARAM_DELIMITER ) ]
	elif s_sample_scheme == SAMPLE_BY_REMOVAL:
		lv_sample_values=[ int( s_val ) for s_val in args[ IDX_SAMPLE_VALUE_LIST ].split( \
																SAMPLE_SCHEME_PARAM_DELIMITER ) ]
	elif s_sample_scheme == SAMPLE_BY_CRITERIA \
			or s_sample_scheme == SAMPLE_BY_COHORT \
			or s_sample_scheme == SAMPLE_BY_RELATEDS \
			or s_sample_scheme == SAMPLE_BY_COHORT_PERCENTAGE:
		lv_sample_values=[ s_val for s_val in args[ IDX_SAMPLE_VALUE_LIST ].split( \
																SAMPLE_SCHEME_PARAM_DELIMITER ) ]
	else:
		s_msg = "In pgdriveneestimator.py, def parse_args, unknown sample scheme: " \
						+ s_sample_scheme + "."
		raise Exception( s_msg  )
	#end if sample percent, else removal, else criteria, else error

	#sort the sample param values, in case we need to make an individual/replicate table:
	if s_sample_scheme in SAMPLE_SCHEMES_NON_CRITERIA:
		lv_sample_values.sort()
	#end if sampole scheme has values we want to sort

	i_min_pop_size=int( args[ IDX_MIN_POP_SIZE ] )
	i_max_pop_size=int( args[ IDX_MAX_POP_SIZE ] )

	#we assign None and only
	#assign ints when arg val is not "all":
	i_min_pop_range=None
	i_max_pop_range=None

	if args[ IDX_POP_RANGE ] != "all":
		li_pop_number_range=[ int( s_val ) for s_val in args[ IDX_POP_RANGE ].split( "-" ) ]

		if len( li_pop_number_range ) != 2  \
				or li_pop_number_range[ 0 ] > li_pop_number_range[ 1 ]:

			s_msg="In pgdriveneestimator.py, def parse_args, " \
					+ "invalid range of population numbers in args. " \
					+ "It either does not parse correctly or the min " \
					+ "is greather than the max.  Args after parsing: " \
					+ str( li_pop_number_range ) + "."
			raise Exception( s_msg )
		#end if pop range list wrong len or invalid range

		i_min_pop_range=li_pop_number_range[ 0 ]
		i_max_pop_range=li_pop_number_range[ 1 ]

	#end if we have a range (rather than "all")

	f_min_allele_freq = float( args[ IDX_MIN_ALLELE_FREQ ] )
	i_total_replicates=int( args[ IDX_REPLICATES ] )
	i_total_processes=int( args[ IDX_PROCESSES ] )
	o_debug_mode=set_debug_mode ( args[ IDX_DEBUG_MODE ] )
	o_main_outfile=args[ IDX_MAIN_OUTFILE ]
	o_secondary_outfile=args[ IDX_SECONDARY_OUTFILE ]
	o_multiprocessing_event=args[ IDX_MULTIPROCESSING_EVENT ]

	s_loci_sampling_scheme=args[ IDX_LOCI_SAMPLING_SCHEME ]

	v_loci_sampling_scheme_param=None

	if s_loci_sampling_scheme == SAMPLE_LOCI_SCHEME_NONE:
		pass
	elif s_loci_sampling_scheme == SAMPLE_LOCI_SCHEME_PERCENT:
		ls_list_of_percentages=args[ IDX_LOCI_SCHEME_PARAM ].split( "," )
		v_loci_sampling_scheme_param=[ float( s_val )/100.0 \
				for s_val in ls_list_of_percentages ]
	elif s_loci_sampling_scheme == SAMPLE_LOCI_CONSTANT_TOTAL:
		ls_list_of_totals= \
				args[ IDX_LOCI_SCHEME_PARAM ].split ( "," )
		v_loci_sampling_scheme_param= \
				[ int( s_val ) for s_val in ls_list_of_totals ]
	else:
		s_msg="In pgdriveneestimator.py, def parse_args, " \
					+ "unrecognized loci sampling scheme: " \
					+ s_loci_sampling_scheme \
					+ "."
		raise Exception( s_msg )
	#end if loci sampling scheme "none" else unrecognized

	i_min_loci_position = None
	i_max_loci_position = None

	try:	
		[ i_min_loci_position, i_max_loci_position ] = [ \
				int( s_arg ) for s_arg in args[ IDX_LOCI_RANGE ].split( "-" ) ]
	except:
		s_msg="In pgdriveneestimator.py, def parse_args, " \
				+ "failed to get loci range from arg passed: " \
				+ args[ IDX_LOCI_RANGE ] + ".  " \
				+ "Should be hyphenated integers i-j, giving " \
				+ "a range of loci indices (ith through jth loci " \
				+ "as ordered in the genepop file)."
		raise Exception( s_msg )
	#end try, except

	i_min_total_loci=int( args[ IDX_LOCI_MIN_TOTAL ] )
	i_max_total_loci=int( args[ IDX_LOCI_MAX_TOTAL ] )
	i_loci_repliates=int( args[ IDX_LOCI_SAMPLE_REPLICATES ] )

	return( ls_files, s_sample_scheme, lv_sample_values, 
								i_min_pop_size, 
								i_max_pop_size,
								i_min_pop_range,
								i_max_pop_range,
								f_min_allele_freq, 
								i_total_replicates, 
								s_loci_sampling_scheme,
								v_loci_sampling_scheme_param,
								i_min_loci_position,
								i_max_loci_position,
								i_min_total_loci,
								i_max_total_loci,
								i_loci_repliates,
								i_total_processes, 
								o_debug_mode, 
								o_main_outfile, 
								o_secondary_outfile,
								o_multiprocessing_event )
	
#end parse_args

def write_parms_to_file( lv_params ):
	return
#end write_parms_to_file

def get_sample_val_and_rep_number_from_sample_name( s_sample_name, s_sample_scheme ):

	s_sample_value="0"
	s_replicate_number="0"

	if s_sample_scheme==SAMPLE_BY_NONE:
		s_sampler_type=gps.SCHEME_NONE
	elif s_sample_scheme==SAMPLE_BY_PERCENTAGES:
		s_sampler_type=gps.SCHEME_PROPORTION
	elif s_sample_scheme==SAMPLE_BY_REMOVAL:
		s_sampler_type=gps.SCHEME_REMOVAL
	elif s_sample_scheme==SAMPLE_BY_CRITERIA:
		s_sampler_type=gps.SCHEME_CRITERIA
	elif s_sample_scheme==SAMPLE_BY_COHORT:
		s_sampler_type=gps.SCHEME_COHORTS
	elif s_sample_scheme==SAMPLE_BY_COHORT_PERCENTAGE:
		s_sampler_type=gps.SCHEME_COHORTS_PERC
	elif s_sample_scheme==SAMPLE_BY_RELATEDS:
		s_sampler_type=gps.SCHEME_RELATEDS
	else:
		s_msg = "In pgdriveneestimator.py, def get_sample_value_and_replicate_number_from_sample_tag, " \
				+ "unknown sampling scheme: " + s_sample_scheme + "."
		raise Exception( s_msg )
	#end if scheme percent, else removal, else error

	s_sample_value, s_replicate_number= \
			gps.get_sample_value_and_replicate_number_from_sample_tag ( s_sample_name, s_sampler_type )	

	return ( s_sample_value, s_replicate_number )
#end get_sample_val_and_rep_number_from_sample_name

def raise_exception_if_non_single_pop_file( o_genepopfile ):
	'''
	Not currently in use ( 2016_08_10 ) -- was used when
	genepop files with >1 population were not accepted.
	'''
	i_total_pops=o_genepopfile.pop_total

	if ( i_total_pops != 1 ):
		s_msg="In pgdriveneestimator.py:" + OUTPUT_ENDLINE
		if i_total_pops < 1:
			s_msg+="No \"pop\" entry found in file, " \
					+ o_genepopfile.original_file_name
		else:
			s_msg+="Current implementation of drive accepts genepop " \
				+ "files with only a single pop."
		#end if lt 1 else more
		raise Exception( s_msg )
	#end if non-single pop file

	return
#end raise_exception_non_single_pop_file

def get_pops_in_file_outside_valid_size_range( o_genepopfile, 
												i_min_pop_size,
												i_max_pop_size ):
	'''
	checks size of every pop in the file
	in case we need to skip some pops and 
	accept others.
	'''

	li_popsizes=o_genepopfile.getIndividualCounts()

	li_pops_too_small = []
	for idx_pop in range( len ( li_popsizes ) ):
		i_size_of_pop=li_popsizes[ idx_pop ] 
		if i_size_of_pop < i_min_pop_size \
				or i_size_of_pop > i_max_pop_size:
			li_pops_too_small.append( idx_pop )
		#end if subsample size too small
	#end for each pop number
	return li_pops_too_small
#end get_pops_in_file_too_small_to_run

def do_estimate( ( o_genepopfile, o_ne_estimator, 
					s_sample_param_val, s_loci_sample_value,
					f_min_allele_freq, s_subsample_tag, 
					s_loci_sample_tag, s_population_number, 
					s_census, i_replicate_number, 
					s_loci_replicate_number, o_debug_mode, 
						IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP) ):

	try:
		s_genepop_file_subsample=o_ne_estimator.input.genepop_file

		o_genepopfile.writeGenePopFile( s_genepop_file_subsample, 
								s_indiv_subsample_tag=s_subsample_tag,
								s_pop_subsample_tag=s_population_number,
								s_loci_subsample_tag=s_loci_sample_tag ) 

		o_ne_estimator.doOp()

		llv_output=o_ne_estimator.deliverResults()

		li_sample_indiv_count=o_genepopfile.getIndividualCounts( s_indiv_subsample_tag = s_subsample_tag, 
				s_pop_subsample_tag = s_population_number )

		s_sample_indiv_count = str( li_sample_indiv_count[ 0 ] )

		ls_runinfo=[ o_genepopfile.original_file_name, 
									s_population_number, 
									s_census,
									s_sample_indiv_count, 
									s_sample_param_val, 
									str( i_replicate_number), 
									s_loci_sample_value,
									s_loci_replicate_number,
									str( f_min_allele_freq ) ]
		
		ls_stdout=[]

		for lv_output in llv_output:
			ls_fields_to_report=[]	
			ls_output_vals_as_strings=[ str( v_val ) for v_val in lv_output ]

			for idx in range( len( ls_output_vals_as_strings ) ):
				if idx not in IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP:
					ls_fields_to_report.append( ls_output_vals_as_strings[ idx ] )
				#end if idx is not for a field we're skipping
			#end for each field's index

			ls_stdout.append( OUTPUT_DELIMITER.join(  ls_runinfo + ls_fields_to_report )  )

		#end for each line of parsed NeEstimator Output
		
		#Make one long string, endline-delimited, for the stdout.
		#Note:  if the inpout genepop file had only one
		#population, this should be a single line of text.

		s_stdout=ENDLINE_SEQ.join( ls_stdout )

		s_stderr=None

		ls_indiv_list=None

		s_nodat_file=o_ne_estimator.output.getNoDatFileName()

		if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
			ls_indiv_list = o_genepopfile.getListIndividuals( 
					i_pop_number=int( s_population_number ), 
					s_indiv_subsample_tag = s_subsample_tag )	
		#end if return list indiv
		
		if not( o_debug_mode.isSet( DebugMode.KEEP_ESTIMATOR_FILES) ):
			if os.path.exists( o_ne_estimator.output.run_output_file ):
				os.remove( o_ne_estimator.output.run_output_file )
			#end if NeEstimator's orig output file exists, delete it
		#end if flag to keep output file is false

		if not( o_debug_mode.isSet( DebugMode.KEEP_REPLICATE_GENEPOP_FILES ) ):
			if os.path.exists( o_ne_estimator.output.run_input_file ):
				os.remove( o_ne_estimator.output.run_input_file )
			#end if subsample genepop file exists, delete it
		#end if flag to keep input file is false

		if not( o_debug_mode.isSet( DebugMode.KEEP_NODAT_FILES ) ):
			s_nodat_file=o_ne_estimator.output.getNoDatFileName()
			if s_nodat_file is not None:
				os.remove( s_nodat_file )
			#end for each nodatfile
		#end if debug mode says remove nodats

		if not( o_debug_mode.isSet( DebugMode.KEEP_NE_EXTRA_FILES) ):

			ls_extra_files=glob.glob( \
					o_ne_estimator.output.run_output_file \
					+ "*x??.txt" )

			for o_extra_file in ls_extra_files:
				os.remove( o_extra_file )
			#end for each nextpfile
		#end if debug mode says remove nodats
	except Exception as oex:
		print ( "Exception in do_estimate: " + str( oex ) )
		raise oex
	return { "for_stdout" : s_stdout, "for_stderr" : s_stderr, 
			"for_indiv_table": None if ls_indiv_list is None \
					else { "file" : o_genepopfile.original_file_name, 
						"sample_val": s_sample_param_val,
						"loci_val":s_loci_sample_value,
						"rep" : i_replicate_number,
						"loci_rep":s_loci_replicate_number,
						"list" : ls_indiv_list,
						"pop" : s_population_number } }

#end do_estimate

def write_results( ds_results, o_main_outfile, o_secondary_outfile ):
	o_main_outfile.write( ds_results[ "for_stdout" ] + "\n" )
	if ds_results[ "for_stderr" ] is not None:
		o_secondary_outfile.write( ds_results [ "for_stderr" ] )
	#end if we have stderr results
#end write_results

def update_indiv_list( dddli_indiv_list, dv_indiv_info_for_replicate, lv_sample_vals ):

	s_orig_file=dv_indiv_info_for_replicate[ "file" ]
	s_population_number=dv_indiv_info_for_replicate[ "pop" ]
	v_this_sample_val= dv_indiv_info_for_replicate[ "sample_val" ]  
	i_replicate= dv_indiv_info_for_replicate[ "rep" ] 
	ls_individuals=dv_indiv_info_for_replicate[ "list" ]

	if s_orig_file not in dddli_indiv_list:
		dddli_indiv_list[ s_orig_file ] = {}
	#end if file new to list

	if s_population_number not in dddli_indiv_list[ s_orig_file ]:
		dddli_indiv_list[ s_orig_file ] [ s_population_number ]={}
	#end if pop name new 

	for s_indiv in ls_individuals:
		if s_indiv not in dddli_indiv_list[ s_orig_file ][ s_population_number ]:
			dddli_indiv_list[ s_orig_file ][ s_population_number ] [ s_indiv ] = {} 
		#end if new indiv

		'''
		we create an empty lists for all sample_values at once.  So, if a given
		proportionn is missing from the current dddli_indiv_list for this
		file/indiv combo, we know that all are missing, so we need to add all
		proportions.  However, in the case of sampling by criteria, cohorts, or
		relatedes, our sample values are simply stubbed in abbreviations (as of
		2016_09_05, as given by the result set).  Any session that uses one of
		these sampling can have only one set of criteria.  This means
		that the ls_sample_values passed to this def, in the case of criteria
		sampling, lists only values for which ne estimate results were
		obtainedare done.  Hence populations that were too small or had no
		members meeting the criteria, will not be represented in the table:
		'''

		if v_this_sample_val not in dddli_indiv_list[ s_orig_file ][ s_population_number][ s_indiv ]:
			for v_sample_val in lv_sample_vals:
				dddli_indiv_list[ s_orig_file ][ s_population_number ][ s_indiv ][ str( v_sample_val ) ] = []
			#end for each proportion
		#end if new proportion

		dddli_indiv_list[ s_orig_file ][s_population_number][ s_indiv ][ v_this_sample_val ].append( i_replicate )
	#end for each individual

	return
#end update_indiv_list

def make_indiv_table_name():
	INDIV_TABLE_EXT="indiv.table"
	s_name = get_datetime_as_string() + "." + INDIV_TABLE_EXT
	return  s_name
#end make_indiv_table_name

def get_indiv_table_header(  lf_proportions ):
	s_header="original_file\tpop_number\tindividual"
	s_header=OUTPUT_DELIMITER.join( [ s_header ] + \
			[ str( f_proportion )  for f_proportion in lf_proportions ]   )
	return s_header
#end write_indiv_table_header

def write_indiv_table( dddli_indiv_list, s_file_name, lf_proportions ):

	o_indiv_table=None
	
	if os.path.exists( s_file_name ):
		s_msg="In " + __filename__ + " write_indiv_table(), " \
				+ "can't write table file.  File, " \
				+ s_file_name + " exists."
		raise Exception( s_msg )
	else:
		o_indiv_table=open( s_file_name, 'w' )
	#end if file exists, exception, else open

	s_header=get_indiv_table_header(  lf_proportions )

	o_indiv_table.write( s_header + "\n" )

	for s_file in dddli_indiv_list:
		for s_pop_number in dddli_indiv_list[ s_file ]:
			for s_indiv in dddli_indiv_list[ s_file ][s_pop_number]:
				s_reps_by_proportion=""
				#sort proportions to sync up with header:
				lf_proportion_keys_sorted=(dddli_indiv_list[ s_file ][s_pop_number][ s_indiv ]).keys()
				lf_proportion_keys_sorted.sort()
				for f_proportion in lf_proportion_keys_sorted:
					ls_replist=dddli_indiv_list[ s_file ][s_pop_number] [ s_indiv ][ f_proportion ]
					s_reps=REPLICATE_DELIMITER.join( [ str( i_rep ) for i_rep in ls_replist ] )
					#may be an empty list of replicates, if this indiv
					#did not get sampled at this proportion:
					s_reps="NA" if s_reps == "" else s_reps
					s_reps_by_proportion+=OUTPUT_DELIMITER + s_reps 
				#end for each proportion

				s_entry = OUTPUT_DELIMITER.join( [ s_file, s_pop_number, s_indiv ] )
				s_entry += s_reps_by_proportion
				o_indiv_table.write( s_entry + "\n" )

		#end for each indiv
	#end for each file
	o_indiv_table.close()
	return
#end write_indiv_table

def print_test_list_replicate_selection_indices( o_genepopfile,  
													s_sample_scheme, 
													s_indiv_subsample_tag,
													s_loci_sample_value,
													s_loci_replicate_number,
													o_secondary_outfile,
													s_population_subsample_tag ):
	s_sample_value, s_replicate_number = \
			get_sample_val_and_rep_number_from_sample_name( s_indiv_subsample_tag, 
																	s_sample_scheme )

	li_selected_indices=o_genepopfile.getListIndividualNumbers( \
						i_pop_number = int( s_population_subsample_tag ), 
						s_indiv_subsample_tag=s_indiv_subsample_tag )

	s_indiv_indices= ",".join( [ str(i) for i in li_selected_indices ] ) 

	ls_values_to_print=	[ o_genepopfile.original_file_name, 
								s_population_subsample_tag,
								s_sample_value, 
								s_replicate_number, 
								s_loci_sample_value,
								s_loci_replicate_number,
								s_indiv_indices ] 

	s_values_to_print="\t".join( ls_values_to_print )
	o_secondary_outfile.write( s_values_to_print + "\n" )
	#end for each pop number, print the selected indices
	return
#end get_test_list_replicate_selection_indices

def parse_sampling_list_that_uses_indiv_id_fields( ls_sampling_list_items ):

	'''
	We require that we have at least 3 items
	to set up  sampling using individual id field
	criteria:
	--list of field names (space delimited)
		ex: "age parent1 parent2"
	--list of field types (python types, space delimited)
		ex: "int str str"
	--at least one parameter (not validated here
		-> example in criteria expression  "age > 3"
		->example, in cohort we expect several params like max. age 	
	2016_11_10
		->example, in cohorts by percentages, we'll have the max age
		  followed by a hyphented list of percentage numerics.  This
		  will not be parsed here, but will be passsed as part of the
		  list returned as  ls_params

	'''

	MIN_NUM_SAMPLING_ITEMS=3
	IDX_FIELD_NAMES=0
	IDX_FIELD_TYPES=1
	IDX_FIRST_PARAM=2
	FIELD_DELIMITER=";"

	i_tot_sampling_items=len( ls_sampling_list_items )

	if i_tot_sampling_items < MIN_NUM_SAMPLING_ITEMS:
		s_msg = "In pgdriveneestimatory.py, def parse_sampling_list_that_uses_indiv_id_fields, " \
					+ "for the sampling criteria list, expecting at 3 items " \
					+ "(field names, field types, and one or more " \
					+ "parameters.  Found list: " \
					+ str( ls_sampling_list_items ) + "."
		raise Exception( s_msg )

	#end if too few criteria items
	ls_field_names=ls_sampling_list_items[ IDX_FIELD_NAMES ].split( FIELD_DELIMITER )
	ls_types=ls_sampling_list_items[ IDX_FIELD_TYPES ].split( FIELD_DELIMITER )
	try:

		lo_field_types=[ eval( s_type ) for s_type in ls_types ]
	
	except Exception as oex:
		s_msg="In pgdriveneestimator.py, def parse_sampling_list_that_uses_indiv_id_fields, " \
					+ "Exception trying to evaluate the field type list. "\
					+ "Type list: " + str( ls_types ) + ".  Exception raised: " \
					+ str( oex ) + "."
		raise Exception ( s_msg )
	#end try ... except

	ls_params=[]

	for idx in range( IDX_FIRST_PARAM, i_tot_sampling_items ):
		ls_params.append( ls_sampling_list_items[ idx ] )
	#end for each item with idx>1

	return ls_field_names, lo_field_types, ls_params

#end parse_sampling_list_that_uses_indiv_id_fields

def get_field_names_from_criteria_test( ls_field_names, s_test ):

		ls_fields_in_test_expression=[]

		for s_field_name in ls_field_names:
			s_var_delimit=gpi.GenepopIndivCriterion.FIELD_DELIMITER_FOR_TEST_EXPRESSION
			v_field_as_var_name=s_var_delimit + s_field_name + s_var_delimit
			if v_field_as_var_name in s_test:
				ls_fields_in_test_expression.append( s_field_name )
			#end if field name is a test var append
		#end for each field name

		if len( ls_fields_in_test_expression ) == 0:
			s_msg="In pgdriveneestimator, def get_field_names_from_criteria_test, " \
					+ "No field name variable found in test expression: " \
					+ s_test + "."
			raise Exception( s_msg )
		#end if no match

		return ls_fields_in_test_expression
#end get_field_name_from_criteria_test

def get_criteria_sampling_params( lv_sample_values ):

	ls_field_names, lo_field_types, ls_criteria_tests = \
					parse_sampling_list_that_uses_indiv_id_fields( lv_sample_values )

	o_genepop_indiv_fields=gpi.GenepopIndivIdFields( ls_field_names, lo_field_types )

	lo_criteria=[]
	i_criteria_count=0
	for s_test in ls_criteria_tests:
		i_criteria_count+=1
		s_crit_name="c" + str( i_criteria_count )
		ls_crit_fields=get_field_names_from_criteria_test( o_genepop_indiv_fields.names, s_test )
		o_criterion=gpi.GenepopIndivCriterion( s_crit_name, 
												ls_crit_fields,
												 s_test )
		lo_criteria.append( o_criterion )
	#end for each test, make a criterion object

	o_criteria=gpi.GenepopIndivCriteria( lo_criteria )
							
	return o_genepop_indiv_fields, o_criteria

#end get_criteria_sampling_params

def get_cohorts_sampling_params( lv_sample_values ):

	ls_field_names, lo_field_types, ls_params = \
					parse_sampling_list_that_uses_indiv_id_fields( lv_sample_values )

	o_genepop_indiv_fields=gpi.GenepopIndivIdFields( ls_field_names, lo_field_types )

	IDX_MAX_AGE=0
	
	f_max_age=float( ls_params[ IDX_MAX_AGE ] )

	return ( o_genepop_indiv_fields,
				f_max_age )

#end get_cohorts_sampling_params

def get_relateds_sampling_params( lv_sample_values ):

	ls_field_names, lo_field_types, ls_params = \
					parse_sampling_list_that_uses_indiv_id_fields( lv_sample_values )

	o_genepop_indiv_fields=gpi.GenepopIndivIdFields( ls_field_names, lo_field_types )

	IDX_PERCENT_RELATEDS=0
	
	f_percent_relateds=float( ls_params[ IDX_PERCENT_RELATEDS ] )

	return ( o_genepop_indiv_fields,
				f_percent_relateds )

#end get_relateds_sampling_params

def do_sample( o_genepopfile, 
				i_min_pop_range,
				i_max_pop_range,
				i_min_pop_size,
				i_max_pop_size,
				s_sample_scheme, 
				lv_sample_values, 
				i_replicates,
				s_loci_sampling_scheme,
				v_loci_sampling_scheme_param,
				i_min_loci_position,
				i_max_loci_position,
				i_min_total_loci,
				i_max_total_loci,
				i_loci_replicates ):

	li_population_list=do_sample_individuals( o_genepopfile, 
					i_min_pop_range,
					i_max_pop_range,
					i_min_pop_size,
					i_max_pop_size,
					s_sample_scheme, 
					lv_sample_values, 
					i_replicates )

	#we also want to sample loci one loci sampling
	#replicate for each each individual replicate,
	#the latter now included in the genepopfile object:
	do_sample_loci( o_genepopfile,
					s_loci_sampling_scheme,
					v_loci_sampling_scheme_param,
					i_min_loci_position,
					i_max_loci_position,
					i_min_total_loci,
					i_max_total_loci,
					li_population_list,
					i_loci_replicates )

	return
#end do_sample

def do_sample_individuals( o_genepopfile, 
				i_min_pop_range,
				i_max_pop_range,
				i_min_pop_size,
				i_max_pop_size,
				s_sample_scheme, 
				lv_sample_values, 
				i_replicates ):

	'''
	do_sample adds subsample info to the o_genepopfile GenepopFileManager object,
	and so changes it in place, returns no value.  The o_genepopfile can then
	be accessed to write a new genepop file that contains the subsampled data.
	sampler requires a population list (in case we want to sample fewer than
	all the pops in the file). If the client passed in "all" parse_args
	will have assigned None to both min and max.
	'''

	i_total_pops_in_file=o_genepopfile.pop_total
	li_population_list=None

	if i_min_pop_range is None:
		#make sure both are None, else
		#arg-parsing error:
		if i_max_pop_range is None:
			li_population_list=list( range( 1, i_total_pops_in_file + 1 ) )
		else:
			s_msg="In pgdriveneestimator.py, def do_sample, " \
						+ " found arg min pop range is None, " \
						+ " but max pop range is not None, " \
						+ str( i_max_pop_range ) \
						+ ".  Invalid argument pair."
			raise Exception( s_msg )
		#end if max is None else error
	else:
		if i_min_pop_range < 1 or i_min_pop_range > i_max_pop_range:
			s_msg="In pgdriveneestimator.py, def do_sample, " \
						+ "min pop number range, " \
						+ str( i_min_pop_range ) \
						+ ", is less than one or " \
						+ "greaterh than max pop number, " \
						+ str( i_max_pop_range ) + "." 
			raise Exception( s_msg )
		#end if min or max out of range

		i_max_pop_range=min( i_max_pop_range, i_total_pops_in_file )

		li_population_list=range( i_min_pop_range, i_max_pop_range + 1 )
	#end if min pop range is None, else have a value

	o_sampler=None	

	s_population_subsample_tag=s_sample_scheme

	if s_sample_scheme==SAMPLE_BY_NONE:
		o_sample_params=gps.GenepopFileSampleParamsNone( li_population_numbers=li_population_list,
															i_min_pop_size=i_min_pop_size,
															i_max_pop_size=i_max_pop_size,
															i_replicates=i_replicates,
															s_population_subsample_name=s_population_subsample_tag )	

		o_sampler=gps.GenepopFileSamplerNone( o_genepopfile, o_sample_params )

	elif s_sample_scheme==SAMPLE_BY_PERCENTAGES:

		#our "proportion" sampler object needs proportions instead of percentages:

		o_sample_params=gps.GenepopFileSampleParamsProportion( li_population_numbers=li_population_list,
												lf_proportions=lv_sample_values,
												i_replicates=i_replicates,
												s_population_subsample_name=s_population_subsample_tag )

		o_sampler=gps.GenepopFileSamplerIndividualsByProportion( o_genepopfile, o_sample_params )

	elif s_sample_scheme==SAMPLE_BY_REMOVAL:

		o_sample_params=gps.GenepopFileSampleParamsRemoval( li_population_numbers=li_population_list,
												li_n_to_remove=lv_sample_values,
												i_replicates=i_replicates,
												s_population_subsample_name=s_population_subsample_tag )

		o_sampler=gps.GenepopFileSamplerIndividualsByRemoval( o_genepopfile, o_sample_params )

	elif s_sample_scheme==SAMPLE_BY_CRITERIA:

		o_indiv_fields, o_criteria = get_criteria_sampling_params( lv_sample_values )

		o_sample_params=gps.GenepopFileSampleParamsCriteria( o_genepop_indiv_id_fields=o_indiv_fields,
																	o_genepop_indiv_id_critera=o_criteria,
																	li_population_numbers=li_population_list,
																	i_min_sampled_pop_size=i_min_pop_size,
																	i_max_sampled_pop_size=i_max_pop_size,
																	s_population_subsample_name = s_population_subsample_tag,
																	i_replicates=i_replicates )

		o_sampler=gps.GenepopFileSamplerIndividualsByCriteria( o_genepopfile, o_sample_params )

	elif s_sample_scheme==SAMPLE_BY_COHORT:

		( o_indiv_fields,
			i_max_age ) = get_cohorts_sampling_params( lv_sample_values )

		o_sample_params=gps.GenepopFileSampleParamsAgeStructureCohorts( \
										o_genepop_indiv_id_fields = o_indiv_fields,
										li_population_numbers = li_population_list,
										i_max_age=i_max_age,
										i_min_individuals_per_gen=i_min_pop_size,
										i_max_individuals_per_gen=i_max_pop_size,
										i_replicates=i_replicates )

		o_sampler=gps.GenepopFileSamplerIndividualsAgeStructureCohorts( o_genepopfile,
																	o_sample_params )
	elif s_sample_scheme==SAMPLE_BY_COHORT_PERCENTAGE:

		#this scheme has params identical to the regular "cohorts" scheme,
		#with a hyphenated list percentage values appended to the max-age param, 
		#so we extract the last two values of the last param list:	
		
		COHORT_PARAM_LIST_DELIMITER=";"
		COHORT_PERC_DELIM="-"
		IDX_MAX_AGE=0
		IDX_PERC=1

		s_last_param=lv_sample_values[ -1 ]

		ls_age_and_percentage=s_last_param.split( \
						COHORT_PARAM_LIST_DELIMITER )

		s_max_age=ls_age_and_percentage[ IDX_MAX_AGE ]
		s_percentages=ls_age_and_percentage[ IDX_PERC ]
		
		#we reassemble the list to match the expected
		#cohort sampling params (without the percentage):
		lv_cohort_param_fields=lv_sample_values[ 0:len( lv_sample_values ) - 1 ] \
															+ [ s_max_age ]		
		#Convert the percentages to a list of floats giving proportion:
		lf_proportions=[ float( s_percentage )/100.0 for s_percentage  \
							in s_percentages.split( COHORT_PERC_DELIM ) ]

		( o_indiv_fields,
				i_max_age ) = get_cohorts_sampling_params( lv_cohort_param_fields )

		o_sample_params=gps.GenepopFileSampleParamsAgeStructureCohorts( \
											o_genepop_indiv_id_fields = o_indiv_fields,
											li_population_numbers = li_population_list,
											i_max_age=i_max_age,
											lf_proportions=lf_proportions,
											i_min_individuals_per_gen=i_min_pop_size,
											i_max_individuals_per_gen=i_max_pop_size,
											i_replicates=i_replicates )

		o_sampler=gps.GenepopFileSamplerIndividualsAgeStructureCohortsPercentage( o_genepopfile,
																					o_sample_params )
								
	elif s_sample_scheme==SAMPLE_BY_RELATEDS:

			( o_indiv_fields,
				f_percent_relateds) = get_relateds_sampling_params( lv_sample_values )

			o_sample_params=gps.GenepopFileSampleParamsAgeStructureRelateds( \
										o_genepop_indiv_id_fields = o_indiv_fields,
										li_population_numbers = li_population_list,
										f_percent_relateds_per_gen=f_percent_relateds,
										i_min_individuals_per_gen=i_min_pop_size,
										i_max_individuals_per_gen=i_max_pop_size,
										i_replicates=i_replicates )

			o_sampler=gps.GenepopFileSamplerIndividualsAgeStructureRelateds( o_genepopfile,
																	o_sample_params )
	else:

		s_msg="In pgdriveneestimator.py, def do_sample, " \
				+ "unknown sampling scheme: " \
				+ s_sample_scheme + "."
		raise Exception( s_msg )
	#end if percent, else removal, else criteria, else cohort, else relateds, else error

	o_sampler.doSample()

	return li_population_list
#end do_sample_individuals

def do_sample_loci( o_genepopfile,
						s_loci_sampling_scheme,
						v_loci_sampling_scheme_param,
						i_min_loci_position,
						i_max_loci_position,
						i_min_total_loci,
						i_max_total_loci,
						li_population_list,
						i_loci_replicates=1 ):
		
	'''
	As of 2016_10_06, we have no loci sampling scheme
	but we still subsample by loci order, start index, stop index
	and a max total -- randomly drawn if the start/stop range
	results in total loci over the max. 

	Further, we currently only permit one loci subsample for
	each individual subsampling session -- i.e. for all 
	of a given sample replicate.

	As of 2016_10_20, we've added new scheme "percent", but
	still doing one sample in the genepop file per call
	to this def, which now still means one loci sample will
	be applied to all replicate indiv samples.

	2016_11_06, revising to do multiple loci sampling.  The
	scheme is, for each existing individual subsample,
	we subsample the loci for each loci-subsampling parameter
	value, and for each of these, for the number of loci
	replicates given by def param i_loci_replicates.
	'''

	for s_indiv_subsample_tag in o_genepopfile.indiv_subsample_tags:
		if s_loci_sampling_scheme == SAMPLE_LOCI_SCHEME_NONE:

			for idx in range( i_loci_replicates ):
				'''
				Loci subsample tags consist of an individual subsample tag
				followed by "_l_t_v_r" where t gives the scheme type, v gives
				the salient param value for the scheme, and r gives the replicate.
				'''
				s_loci_subsample_tag_base=s_indiv_subsample_tag

				o_sample_params=gps.GenepopFileSampleParamsLoci( \
											li_population_numbers=li_population_list,
											i_min_loci_position=i_min_loci_position,
											i_max_loci_position=i_max_loci_position,
											i_min_total_loci=i_min_total_loci,
											i_max_total_loci=i_max_total_loci,
											i_replicates=1,
											s_sample_tag_base=s_loci_subsample_tag_base )

				o_sampler=gps.GenepopFileSamplerLociByRangeAndTotal( o_genepopfile,
																		o_sample_params )
				o_sampler.doSample()
			#end for each replicate

		elif s_loci_sampling_scheme == SAMPLE_LOCI_SCHEME_PERCENT:

			s_loci_subsample_tag_base=s_indiv_subsample_tag

			o_sample_params=gps.GenepopFileSampleParamsLoci( \
													li_population_numbers=li_population_list,
													i_min_loci_position=i_min_loci_position,
													i_max_loci_position=i_max_loci_position,
													i_min_total_loci=i_min_total_loci,
													i_max_total_loci=i_max_total_loci,
													lf_proportions=v_loci_sampling_scheme_param,
													i_replicates=i_loci_replicates,
													s_sample_tag_base=s_loci_subsample_tag_base )

			o_sampler=gps.GenepopFileSamplerLociByRangeAndPercentage( o_genepopfile,
																	o_sample_params )
			o_sampler.doSample()

		elif s_loci_sampling_scheme == SAMPLE_LOCI_CONSTANT_TOTAL:

			s_loci_subsample_tag_base=s_indiv_subsample_tag
		
			'''
			For the constant sampling totals, the sampler ignores 
			the passed values #for min and max loci total, and 
			substitutes the current total for both min and max. Thus,
			for each N in the list of Ns, (and also for each replicate),  
			a random N will be drawn from the loci (positions). 
			'''

			o_sample_params=gps.GenepopFileSampleParamsLoci( \
										li_population_numbers=li_population_list,
										i_min_loci_position=i_min_loci_position,
										i_max_loci_position=i_max_loci_position,
										i_min_total_loci=i_min_total_loci,
										i_max_total_loci=i_max_total_loci,
										li_sample_totals=v_loci_sampling_scheme_param,
										i_replicates=i_loci_replicates,
										s_sample_tag_base=s_loci_subsample_tag_base )

			o_sampler=gps.GenepopFileSamplerLociByRangeAndSampleTotalList( o_genepopfile,
																			o_sample_params )
			o_sampler.doSample()
		else:
			s_msg="In pgdriveneestimator.py, def do_sample_loci, " \
						+ "unknown loci sampling scheme: " \
						+ s_loci_sampling_scheme + "."
			raise Exception( s_msg )
		#end if sampling scheme none else unknown
	#end for each individual subsample tag

	return
#end do_sample_loci

def get_subsample_genepop_file_name( s_original_genepop_file_name, 
													s_loci_subsample_tag,
													s_this_pop_sample_name ):
	'''
	Was originally simply a matter of replacing, in the original genepop file,
	dots with underscores, but Windows revealed a case that needed attention 
	(see "replace" below).
	'''

	s_genepop_file_subsample=s_original_genepop_file_name \
								+ INPUT_FILE_DOT_CHAR_REPLACEMENT \
								+  s_loci_subsample_tag \
								+ INPUT_FILE_DOT_CHAR_REPLACEMENT \
								+ "g" + INPUT_FILE_DOT_CHAR_REPLACEMENT \
								+ s_this_pop_sample_name
	
	'''
	Note: In the original file name, if a period is left to the left of that
	used do delimit the file extension, then NeEstimator, when naming
	"*NoDat.txt" file, will replace the left-most period and all text that
	follows it,  with "NoDat.txt" -- this then removes any percent and replicate
	number text I'm using to make files unique, and so creates a non-uniq
	*NoDat.txt file name, which, when one process removes it, and another goes
	looking for it , throws an exception -- (an exception from the
	multiprocessing.Pools async mapping -- file-not-found, but no trace since it
	occurs in a different process from the main).  This peculiar mangling of a
	users input file -- was preventing me in previous versions, from deleting
	NoDat files, and also I think meant that only the last process in a given
	group of replicates (share same genepop file and proportion sampled) to use
	the NoDAt file got to write it's NoDat info.  Removing all periods from the
	input file to the NeEstimator program, I belive, completely solves the
	problems.
	'''

	s_basename=os.path.basename( s_genepop_file_subsample )
	s_dirs=os.path.dirname( s_genepop_file_subsample )
	s_subsample_file_basename=s_basename.replace( ".", INPUT_FILE_DOT_CHAR_REPLACEMENT )
	s_genepop_file_subsample=os.path.join( s_dirs, s_subsample_file_basename )
	
	#remmed out -- problems when the orig file has path that includes 
	#directories with dots in their names, so the wholesale replace
	#then includes directories that are renamed and (no doubt) non-existent

	#s_genepop_file_subsample=s_genepop_file_subsample.replace( ".", INPUT_FILE_DOT_CHAR_REPLACEMENT )
	
	'''
	problem seen in Windows, in which when this mod is invoked as __main__ from a shell
	then ".\\" is appended to (at least) one genepop file name.  This then is mangled by
	the above replace, so we restore the leading dot char:
	'''

	if s_genepop_file_subsample.startswith(  "_" ):
		s_genepop_file_subsample="." + s_genepop_file_subsample[1:] 
	#end if path was mangled by replace

	return s_genepop_file_subsample
#end get_subsample_genepop_file_name

def add_to_set_of_calls_to_do_estimate( o_genepopfile, 
											s_sample_scheme,
											f_min_allele_freq, 
											i_min_pop_size,
											i_max_pop_size,
											o_debug_mode,
											llv_args_each_process,
											IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP,
											o_secondary_outfile ):
	'''		
	This def creates ne-estimator caller object and adds it to list of args for a single call
	to def do_estimate.  The call is then appended to llv_args_each_process
	'''

	#all these GenepopFileManager objects should now have
	#a single population sample name:
	s_population_sample_name=o_genepopfile.population_subsample_tags[ 0 ]

	ls_indiv_sample_names=o_genepopfile.indiv_subsample_tags

	li_population_numbers=o_genepopfile.getListPopulationNumbers( s_population_sample_name )
	#for each sample (i.e. for each replicate of a sampling with a given set of params:
	for s_indiv_sample in ls_indiv_sample_names:

		#we also check that at least one pop has at least one individual
		#listed for this subsample
		li_indiv_counts_for_this_sample=o_genepopfile.getIndividualCounts( s_indiv_subsample_tag=s_indiv_sample )

		if sum( li_indiv_counts_for_this_sample ) == 0:
			s_sample_value, i_replicate_count=get_sample_val_and_rep_number_from_sample_name( \
											s_indiv_sample, s_sample_scheme )
			#we only want to report the first replicate
			#(by inference of course all replicates will be skipped:
			if i_replicate_count == 0:
				s_msg="Skipping samples from: " \
						+ o_genepopfile.original_file_name \
						+ ".  In pgdriveneestimator.py, all populations " \
						+ "have zero individuals when sampled using " \
						+ "scheme: " + s_sample_scheme \
						+ ", and with sample parameter, " + s_sample_value + "."
				o_secondary_outfile.write( s_msg + "\n" )
			#end if first replicate, report
			continue
		#end skip this subsample if no pops have any individuals

		'''
		For percent and remove-N schemes, the min/max pop size params are not 
		enforced in the sampler, and, as of 2016_09_27, are to be applied
		before sampling.  Thus, for these scheme we skip populations if their 
		original, un-subsampled size is outside the pop size range.  Other schemes
		should have applied the criteria when subsampling.  For the latter, this
		would not be an appropriate test::
		'''

		li_pops_with_invalid_size=[]
		
		if s_sample_scheme in SAMPLE_SCHEMES_NON_CRITERIA:
			li_pops_with_invalid_size=get_pops_in_file_outside_valid_size_range( o_genepopfile, 
																				i_min_pop_size,
																				i_max_pop_size )
		#end if we need to check original (non-sampled) pop sizes


		ls_loci_subsample_tags_associated_with_this_indiv_sample= \
				get_loci_subsample_tags_for_this_indiv_subsample( o_genepopfile,
																	s_indiv_sample )

		for s_loci_subsample_tag in ls_loci_subsample_tags_associated_with_this_indiv_sample:

			'''
			To most-efficiently use multi-processes, that is, to assign many
			processes a single file with many populations, we do an
			estimate on each pop in the file separately, and divvy
			the pops up among processes:
			'''
			for i_population_number in li_population_numbers:

				if i_population_number in li_pops_with_invalid_size:
					s_msg= "In pgdriveneestimator.py, def add_to_set_of_calls_to_do_estimate, " \
									+ " in file, " + o_genepopfile.original_file_name \
									+ ", skipping pop number, "  + str( i_population_number ) \
									+ ".  It has an indiv count outside of valid " \
									+ "range, " + str( i_min_pop_size ) \
									+ " - " + str( i_max_pop_size ) + "."
					o_secondary_outfile.write( s_msg + "\n" )
					continue
				#end if i_population_number is

				'''
				We send to def do_estimate the genepop file object, o_genepopfile, and the subsample tag
				that identifies the correct subsample calculated and stored in the object, so we can write
				each subsample genepop file in the same process that will use it as input to the the estimator.
				This should limit the number of input files existing concurrenty in the directory to the 
				number of processes in use.  We also send allele freq, and the original genepop file name 
				inside the genepop file manager object):
				'''
				s_sample_value, s_replicate_number = \
						get_sample_val_and_rep_number_from_sample_name( s_indiv_sample, s_sample_scheme )

				s_loci_sample_value, s_loci_replicate_number = \
						get_loci_sample_val_and_rep_number_from_loci_sample_tag( s_loci_subsample_tag )

				i_tot_indivs_this_subsample=o_genepopfile.getIndividualCount( i_population_number, s_indiv_sample )

				if i_tot_indivs_this_subsample == 0:
					s_msg= "In pgdriveneestimator.py, def add_to_set_of_calls_to_do_estimate, " \
									+ " in file, " + o_genepopfile.original_file_name \
									+ ", with sample value: " + s_sample_value \
									+ ", and loci sample value: " + s_loci_sample_value \
									+ ", skipping pop number, "  + str( i_population_number ) \
									+ ".  It has a zero indiv count."
					o_secondary_outfile.write( s_msg + "\n" )
					continue
				# end if this sample for this pop has zero individuals

				#for downstream analysis, we get the census of total indiv
				#non-sampled, for this pop section:
				s_census=str( o_genepopfile.getIndividualCount( i_population_number ) )

				#we make population subsample list consisting of only this populations number:
				s_this_pop_number=str( i_population_number ) 

				o_genepopfile.subsamplePopulationsByList( [ i_population_number ], s_this_pop_number )

				if o_debug_mode.isSet( DebugMode.PRINT_REPLICATE_SELECTIONS ):
					print_test_list_replicate_selection_indices( o_genepopfile, 
											s_sample_scheme,	
											s_indiv_sample, 
											s_loci_sample_value,
											s_loci_replicate_number,
											o_secondary_outfile, 
											s_population_subsample_tag=s_this_pop_number )
				#end if we're testing, print 
				

				#in naming a the genepop file for the subsampled pop,
				#some processing is needed to avoid NeEstimator file naming errors, and
				#path mangling, so we made a separate def:
				s_genepop_file_subsample=get_subsample_genepop_file_name( o_genepopfile.original_file_name, 
														s_loci_subsample_tag, 
														s_this_pop_number )

				s_run_output_file=s_genepop_file_subsample + "_ne_run.txt"

				o_neinput=pgin.PGInputNeEstimator( s_genepop_file_subsample )

				o_neinput.run_params={ "crits":[ f_min_allele_freq ]  }

				o_neoutput=pgout.PGOutputNeEstimator( s_genepop_file_subsample, s_run_output_file )	

				o_ne_estimator=pgne.PGOpNeEstimator( o_neinput, o_neoutput ) 
				
				lv_these_args = [ o_genepopfile,  
									o_ne_estimator, 
									s_sample_value, 
									s_loci_sample_value,
									f_min_allele_freq, 
									s_indiv_sample, 
									s_loci_subsample_tag,
									s_this_pop_number, 
									s_census,
									s_replicate_number, 
									s_loci_replicate_number,
									o_debug_mode,
									IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP ]

				llv_args_each_process.append( lv_these_args )
			#end for each population
		#end for each loci sample name assoc with this indiv sample name
	#end for each indiv sample name
	return
#end add_to_set_of_calls_to_do_estimate

def get_loci_sample_val_and_rep_number_from_loci_sample_tag( s_loci_subsample_tag ):
	'''
	The loci info in the tag follows an indiv tag prefix,
	and has form "_l_t_v_r", with t giving the scheme,
	v giving the scheme salient param value (ex percent val),
	and r giving the replicate number.
	'''
	#Sample param val is 2nd to last item
	#in the tag fields, while the replicate
	#number is the last:
	IDX_LOCI_SAMPLE_VAL=-2
	IDX_LOCI_REP=-1

	s_sample_val=None
	s_replicate_number=None

	s_tag_delim=gps.TAG_DELIMITER
	
	ls_tag_fields=s_loci_subsample_tag.split( s_tag_delim )

	s_sample_val=ls_tag_fields[ IDX_LOCI_SAMPLE_VAL ]
	s_replicate_number=ls_tag_fields[ IDX_LOCI_REP ]

	return s_sample_val, s_replicate_number
#end get_loci_sample_val_and_rep_number_from_loci_sample_tag

def get_loci_subsample_tags_for_this_indiv_subsample( o_genepopfile,  s_indiv_sample_tag ):

	ls_loci_tags=o_genepopfile.loci_subsample_tags

	ls_loci_tags_assoc_with_indiv_subsample=[]

	for s_loci_tag in ls_loci_tags:
		if s_loci_tag.startswith( s_indiv_sample_tag  + "_" ):
			ls_loci_tags_assoc_with_indiv_subsample.append( s_loci_tag )
		#end if loci tag has prefix mathich indiv tag
	#end for each loci tag

	return ls_loci_tags_assoc_with_indiv_subsample
#end get_loci_subsample_tags_for_this_indiv_subsample

def write_result_sets( lds_results, lv_sample_values, o_debug_mode, o_main_outfile, o_secondary_outfile ):

	#Disabled call to update_indiv_list below,
	#now makes this assignment unneeded.  May
	#want to re-implement the idiv list table later.
#	dddli_indiv_list=None

	if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
		'''
		2016_11_22, the *indiv.table file is not currently
		correcly updated to reflect loci sampling multi-
		plicity, so I'm pringint a warning and have
		passed on the call to the def updaete_indiv_list.
		'''
		s_msg="Warning:  the *.indiv.table file is not implemented for the current version."
		o_secondary_outfile.write( s_msg + "\n" )	
		#dddli_indiv_list={}
	#end if debug mode, init indiv list

	for ds_result in lds_results:
			write_results( ds_result, o_main_outfile, o_secondary_outfile )
			if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
				'''
				2016_11_22, the *indiv.table file is not 
				correctly updated to the current output,
				and so for now I'm no longer calling.
				'''
				pass
#				update_indiv_list( dddli_indiv_list, 
#						ds_result[ "for_indiv_table" ], 
#						lv_sample_values )
			#end if make indiv table, update list
	#end for each result set

	if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
		'''
		See notes above about skipping the *indiv.table file
		'''
		pass
#		s_indiv_table_file=make_indiv_table_name ()
#		write_indiv_table( dddli_indiv_list, s_indiv_table_file, lv_sample_values )
	#end if we made indiv table, write it

	return
# write_result_sets		

def execute_ne_for_each_sample( llv_args_each_process, o_process_pool, o_debug_mode,
												o_multiprocessing_event ):
	if VERY_VERBOSE:
		print ( "In pgdriveneestimator.py, def execute_ne." )
	#end if very verbose

	'''
	This return value was added 2016_11_27, to
	aid in the handling of multiprocessing.Pool
	hangs.  See the elapsted-time code below,
	used when MULTI_PROCESSED are running.
	'''
	b_run_was_interrupted=False

	lds_results=None

	#if this run is not in serial mode
	#then we're using the mulitprocessor pool,
	#(even if user only requested a single processor):
	if  o_debug_mode.isSet( DebugMode.ALLOW_MULTI_PROCESSES ): 
		'''
		2016_11_26, while trying to debug hangs 
		in the pool of processes, Ive added
		a timeout procedure.  If the pool shows
		no change (presumably, a reduction),
		in remaining chunks of work over a TIMEOUT period, 
		we save the results that have come in so far,
		set a flag that indicates an interrupted run,
		and return these to drive_estimator, which in turn
		handles writinng an interrupted set of outfiles,
		and raises an error. )

		Heuristically, with high observed variance in the per-chunk runtime,
		We give at least 3 minutes per chunk in the fastest case, and compute
		a per chunk timout based on the slowest per-call rate that I observed 
		in a few tests (two Linux computers, one Windows), with total 160000 calls
		and from 2 to 12 processes used.  Note that the typical longest chunk 
		processing time (to get results into the mapresult objec) was the first
		chunk, but I did observe nearly as lengthly times in subsequenct chunks
		in Windows.
		'''
	
		#for now giving each chunk at least 3 hours, as
		#the upper limit on the variability of per-chunk processing time is
		#hard to find:
		MIN_ALLOWED_TIMEOUT=60*180
		SLOWEST_PER_CALL_RATE=0.4
		ELBOW_ROOM_FACTOR=3

		#computes the chunk size (number of calls to do_estimate per chunk):
		seqdiv=divmod( len( llv_args_each_process ), o_process_pool._processes * 4 )
		i_chunk_size= seqdiv[ 0 ] + ( seqdiv[ 1 ] > 0 )

		i_timeout_as_fx_chunksize=round( i_chunk_size * SLOWEST_PER_CALL_RATE * ELBOW_ROOM_FACTOR ) 

		i_pool_timeout=max( MIN_ALLOWED_TIMEOUT, i_timeout_as_fx_chunksize )

		if VERY_VERBOSE:
			print( "In pgdriveneestimator, def execute_ne_for_each_sample, timeout set: " + str( i_pool_timeout ) )
		i_last_work_chunk_total=0

		f_chunk_progress_start_time=time.time()
		
		#We set chunksize to 1 so we can use a timeout that estimates suffiient
		#time to run 1 call to do_estimate:
		o_mapresult=o_process_pool.map_async( do_estimate, llv_args_each_process )
		
		while not ( o_mapresult.ready() ):

			if VERY_VERBOSE:
				print ("In pgdriveneestimator, def execute_ne_for_each_sample, looping while results not ready" )
				print( "In pgdriveneestimator, def execute_ne_for_each_sample, with chunksize: " \
																		+ str( o_mapresult._chunksize ) )
				print ( "In pgdriveneestimator, def execute_ne_for_each_sample, remaining work chunks: " \
																			+ str( o_mapresult._number_left ) )
				print ( "In pgdriveneestimator, def execute_ne_for_each_sample, total completed calls: "  \
									+ str( sum( [ ( o_res is not None ) for o_res in o_mapresult._value  ] ) ) )
			#end if very verbose

			i_updated_work_chunk_total=o_mapresult._number_left

			if i_last_work_chunk_total != i_updated_work_chunk_total:

				if VERY_VERBOSE:
					f_elapsed=time.time()-f_chunk_progress_start_time
				
					print( "In pgdriveneestimator, def execute_ne_for_each_sample, chunk " \
							+ str( i_last_work_chunk_total ) + " processed in " \
							+ str( f_elapsed ) + " seconds." )

				#end if very verbose

				i_last_work_chunk_total=i_updated_work_chunk_total
				f_chunk_progress_start_time=time.time()

			else:

				f_time_elapsed_last_chunk_total=time.time()-f_chunk_progress_start_time
			
				if VERY_VERBOSE:
					print ( "In pgdriveneestimator, def execute_ne_for_each_sample, " \
								+ "chunk: " + str( i_last_work_chunk_total ) \
								+ ", elapsed_time: " + str( f_time_elapsed_last_chunk_total ) \
								+ "." )
				#end if very verbose

				if f_time_elapsed_last_chunk_total >= i_pool_timeout:
					'''
					We make a result set list minus any with "None",
					assuming that the maprsult object either has 
					the complete results from the call to do_estimate,
					or a None value for that call. Return this likely
					truncated result set to caller, with flag set to
					indicate interrupted run.
					'''
					if VERY_VERBOSE:
						print ( "In pgdriveneestimator, def execute_ne_for_each_sample, " 
									+ "time out with chunk total: " + str( i_last_work_chunk_total ) )
					#end if VERY_VERBOSE

					b_run_was_interrupted=True
					ldv_interruped_results=o_mapresult._value
					ldv_completed_results=[]


					for  dv_result in ldv_interruped_results:
						if dv_result is not None:
							ldv_completed_results.append( dv_result )
						#end if lv_result is not None
					#end for each item in incomplete result set

					return b_run_was_interrupted, ldv_completed_results
				#end if  progress timed out
			#end if new chunk total else check elapsed time

			if o_multiprocessing_event is not None:

				if VERY_VERBOSE:
					print( "In pgdriveneestimator, def execute_ne_for_each_sample, with chunksize: " + str( o_mapresult._chunksize ) )
					print ( "In pgdriveneestimator, def execute_ne_for_each_sample, remaining work chunks: " + str( o_mapresult._number_left ) )
					print ( "In pgdriveneestimator, def execute_ne_for_each_sample, total completed calls: "  \
								+ str( sum( [ ( o_res is not None ) for o_res in o_mapresult._value  ] ) ) )
				#end if very verbose

				if o_multiprocessing_event.is_set():

					if VERY_VERBOSE:
						print( "In pgdriveneestimator.py def execute_ne_for_each_sample: terminating pool" )
					#end if very verbose

					o_process_pool.terminate()

					if VERY_VERBOSE:
						print( "In pgdriveneestimator.py def execute_ne_for_each_sample: op process clearing event" )
					#end if very verbose

					o_multiprocessing_event.clear()
				#end if event is set
			#end if event is not none

			time.sleep( SECONDS_TO_SLEEP )
		#end while results not ready

		o_process_pool.close()
		o_process_pool.join()
		#end for each result

		lds_results=o_mapresult.get()
	else:
		lds_results=[]
		for lv_these_args in llv_args_each_process:
			ds_result=do_estimate( lv_these_args )
			lds_results.append( ds_result )	
		#end for each set of args
	#end if multiprocess allowed, execute async, else serially

	return b_run_was_interrupted, lds_results
#end execute_ne_for_each_sample

def write_header_main_table( IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP, o_main_outfile ):

	#write header -- field names for the main output table

	ls_estimator_fields=pgout.PGOutputNeEstimator.OUTPUT_FIELDS

	ls_reported_fields=[]

	for s_field in ls_estimator_fields:
		if s_field not in NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP:
			ls_reported_fields.append( s_field )
		#end if field in estimatorfields
	#end for each estimator fields

	o_main_outfile.write( OUTPUT_DELIMITER.join( MAIN_TABLE_RUN_INFO_COLS + ls_reported_fields  ) + OUTPUT_ENDLINE )

	return
#end write_header_main_table

def get_sample_abbrevs_for_criteria( lds_results ):
	ds_abbrevs={}
	for ds_results in lds_results:
		if ds_results[ "for_indiv_table" ] is not None:
			s_value=str( ds_results[ "for_indiv_table" ][ "sample_val" ] )
			ds_abbrevs[ s_value ] = 1
		#end if indiv table fields exist
	#end for each result
	#for python3, we cast the keys as a list
	#(else they are type dict_keys
	return list( ds_abbrevs.keys() )
#end get_sample_abbrevs_for_criteria

def drive_estimator( *args ):

	if VERY_VERBOSE:
		print ( "in pgdriveneestimator, def drive_estimator, calling parse args" )
	#end  if VERY_VERBOSE

	( ls_files, s_sample_scheme, 
				lv_sample_values, 
				i_min_pop_size, 
				i_max_pop_size,
				i_min_pop_range, 
				i_max_pop_range,
				f_min_allele_freq, 
				i_total_replicates, 
				s_loci_sampling_scheme,
				v_loci_sampling_scheme_param,
				i_min_loci_position,
				i_max_loci_position,
				i_min_total_loci,
				i_max_total_loci,
				i_loci_replicates,
				i_total_processes, 
				o_debug_mode, 
				o_main_outfile, 
				o_secondary_outfile, 
				o_multiprocessing_event ) = parse_args( *args )

	o_process_pool=None

	IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP = \
			set_indices_ne_estimator_output_fields_to_skip()

	if o_debug_mode.isSet( DebugMode.ALLOW_MULTI_PROCESSES ):
		o_process_pool=Pool( i_total_processes )
	#end if multi processing

	llv_args_each_process=[]

	#Was used in call to make indiv table file
	#currently disabled:
	#s_indiv_table_file=None
	
	write_header_main_table( IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP, o_main_outfile )

	for s_filename in ls_files:

		if VERY_VERBOSE:
			print( "in pgdriveneestimator, def drive_estimator, processing file, " \
								+ s_filename + "." )
		#end if VERY_VERBOSE

		o_genepopfile=gpf.GenepopFileManager( s_filename )

		if VERY_VERBOSE:
			print ( "in pgdriveneestimator, def drive_estimator, calling do_sample " \
								+ "for file, " + s_filename + "." )	
		#end if VERY_VERBOSE

		do_sample( o_genepopfile, 
					i_min_pop_range,
					i_max_pop_range,
					i_min_pop_size,
					i_max_pop_size,
					s_sample_scheme, 
					lv_sample_values, 
					i_total_replicates,
					s_loci_sampling_scheme,
					v_loci_sampling_scheme_param,
					i_min_loci_position,
					i_max_loci_position,
					i_min_total_loci,
					i_max_total_loci,
					i_loci_replicates )

		if VERY_VERBOSE:
			print ( "in pgdriveneestimator, def drive_estimator, calling " \
					 			+ "add_to_set_of_calls_to_do_estimate " \
								+ "for file, " + s_filename + "." )	
		#end if VERY_VERBOSE

		add_to_set_of_calls_to_do_estimate( o_genepopfile, 
												s_sample_scheme,
												f_min_allele_freq, 
												i_min_pop_size,
												i_max_pop_size,
												o_debug_mode,
												llv_args_each_process,
												IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP,
												o_secondary_outfile )
		
	#end for each genepop file, sample, add an ne-estimator object, and setup call to estimator 

	if len( llv_args_each_process ) == 0:
		s_msg="Warning:  no calls were made to NeEstimator, indicating " \
					+ "that sampling parameters resulted in no samples."

		sys.stderr.write( s_msg + "\n" )

	#end if no calls were made, print warning to stderr

	if VERY_VERBOSE:
		print ( "in pgdriveneestimator, def drive_estimator, calling " \
							+ "execute_ne_for_each_sample." )	

	#end if VERY_VERBOSE

	b_run_was_interrupted, lds_results=execute_ne_for_each_sample( llv_args_each_process, 
												o_process_pool, 
												o_debug_mode,
												o_multiprocessing_event )
	'''
	For proportional (random) and remove-n (random)
	sampling, the list of sample values (proprotions
	or n's) is the correct list to use. For criteria
	sampling (ex: age==1), we can't use the sample
	values list, because the list does not contain
	the (short) abbreviation needed for 
	NeEstimator file names.  Hence criteria sampling
	sample param names are simply c<sum-of-critera>.
	Which we calculate from the result sets.
	'''	
	lv_sample_value_groupings=lv_sample_values \
			if s_sample_scheme in SAMPLE_SCHEMES_NON_CRITERIA \
			else get_sample_abbrevs_for_criteria( lds_results )

 	if VERY_VERBOSE:
		print ( "in pgdriveneestimator, def drive_estimator, calling " \
							+ "write_result_sets" )	

	#end if VERY_VERBOSE


	write_result_sets( lds_results, 
						lv_sample_value_groupings, 
						o_debug_mode, 
						o_main_outfile, 
						o_secondary_outfile )

	'''
	Last, for the secondary outfile, we write a
	table of parameters and their corresponding
	arg values
	'''
	o_argset=ArgSet( args )
	o_secondary_outfile.write( "Table of parameters and values:\n" \
							+ o_argset.paramtable + "\n" )
	if b_run_was_interrupted:

		'''
		When we throw erroro below, the calling def in pgutilities 
		(run_driveneestimator_in_new_process) will set the multiprocessing 
		event, which will then result in the outfiles being delted by
		the GUI cleanup op. Thus we save a "interrupted" version
		of the output, not recognized by the GUI as needing to be 
		deleted.
		'''
		for o_outfile in [ o_main_outfile, o_secondary_outfile ]:
			o_outfile.close()
			s_name_this_file=o_outfile.name
			shutil.copy( s_name_this_file, s_name_this_file + ".interrupted" )
		#end for each outfile, copy it as interrupted version

		if o_multiprocessing_event is not None:
			o_multiprocessing_event.set()
		#end if we have multi processing event

		s_msg="In pgdriveneestimator.py, def execute_ne_for_each_sample, " \
					+ "multiprocessing pool timed out.\nResult output files " \
					+ "have been saved with tag, \"interrupted,\"" \
					+ "\nand may be empty or truncated."
		raise Exception( s_msg )
	#end if the estimations were interrupted (see def execute_ne_for_each_sample 

	return
#end drive_estimator

def did_find_ne_estimator_executable():
	b_found=False
 
	#make sure the neestimator is in the user's PATH:
	NEEST_EXEC_LINUX="Ne2L"
	NEEST_EXEC_WIN="Ne2.exe"
	NEEST_EXEC_MAC="Ne2M"

	s_neestimator_exec=None

	if os.name == "posix":
		if sys.platform.lower().startswith( "linux" ):
			s_neestimator_exec=NEEST_EXEC_LINUX
		elif sys.platform.lower() == "darwin" :
			s_neestimator_exec=NEEST_EXEC_MAC
		else:
			s_msg="in pgdriveneestimator.py, " \
					+ "looking for appropriate NeEstimator executable, " \
					+ "found os name \"posix\" " \
					+ "but unknown platform: " \
					+ sys.platform + "."
			raise Exception( s_msg )
		#end if linux else mac else error
	elif os.name == "nt":
		s_neestimator_exec=NEEST_EXEC_WIN
	else:
		s_msg="For this OS: %s, don't know the name of the appropriate NeEstimator executable." \
		% os.name 
		raise Exception(  s_msg )
	#end if os posix else nt else error

	b_neestimator_found=pgut.confirm_executable_is_in_path( s_neestimator_exec )

	if b_neestimator_found:
		b_found=True
	#end if we found the executable

	return b_found
#end did_find_ne_estimator_executable

def mymain( *q_args ):

	'''
	This code was at mod level under if __name__=="__main__",
	but moved inside this def so this mod can be imported
	and run inside python with a set of args identical to
	those required on the command line.

	This was an adaptation to enable PGGuiNeEstimator objects
	to import this mod, then call this def after they load 
	params (args for this driver) from their interface
	'''
	
	if VERY_VERBOSE:
		print( "In pgdriveneestimator, def mymain" )
	#end if VERY_VERBOSE

	'''
	To allow the pygenomics genomics.ne2.controller modules
	Ne2 estimator class object to loop over the paths in the
	PATH environmental variable, and be ensured that each
	exists.
	'''
	pgut.remove_non_existent_paths_from_path_variable()

	'''
	Make sure we have the Ne2 executable.
	'''
	if not did_find_ne_estimator_executable():
		raise Exception( "in pgdriveneestimator.py, def mymain(), " \
							+ "did not find NeEstimator executable." )
	#end if can't find executable
	
	'''

	We adapted this def to open and close the main and secondary 
	output files. Originally, it simply passed open file objects to def,
	parse args.  Now we we check for string vs file for these
	args, as the console version will still pass stdout and sterr
	file objects, but the GUI will call with string filenames.  
	We strip off the last 3 items, which now need to be checked 
	for type string file names and assume, if not string, then 
	the objects passed are assumed to be (open-for-writing) 
	file objects.  We also pass along the last arg, the multiprocessing
	event.  
	'''
	seq_unaltered_args=q_args[0:IDX_DEBUG_MODE + 1 ]

	v_main_outfile_arg= q_args[ IDX_MAIN_OUTFILE ]
	v_secondary_outfile_arg=q_args[ IDX_SECONDARY_OUTFILE ]

	'''
	Note that we check for string type, and otherwise
	assume open file objects. (In Linux sys.std{out,err} return
	"file" as type, but in Windows they return iostream or
	something similar, but not file object.
	'''
	if type( v_main_outfile_arg  ) == str:
		o_main_outfile=open( v_main_outfile_arg, 'w' )
		o_secondary_outfile=open( v_secondary_outfile_arg, 'w' )
	else:
		o_main_outfile=v_main_outfile_arg
		o_secondary_outfile=v_secondary_outfile_arg
	#end if passed non-file object, open file, else pass along file object

	o_event=None

	seq_args_to_parse=seq_unaltered_args + ( o_main_outfile, o_secondary_outfile, o_event )

	drive_estimator( *seq_args_to_parse )

	if o_main_outfile != sys.stdout:
		o_main_outfile.close()
	#end if not stdout, close

	if o_secondary_outfile != sys.stderr:
		o_secondary_outfile.close()
	#end if not stderr, close file

	return
#end mymain

if __name__ == "__main__":

	import argparse as ap

	o_parser=ap.ArgumentParser()

	o_arglist=o_parser.add_argument_group( "args" )

	i_total_nonopt=len( LS_FLAGS_SHORT_REQUIRED )

	for idx in range( i_total_nonopt ):
		o_arglist.add_argument( \
				LS_FLAGS_SHORT_REQUIRED[ idx ],
				LS_FLAGS_LONG_REQUIRED[ idx ],
				help=LS_ARGS_HELP_REQUIRED[ idx ],
				required=True )
	#end for each required argument

	i_total_opt=len( LS_FLAGS_SHORT_OPTIONAL )

	for idx in range( i_total_opt ):
		o_parser.add_argument( \
				LS_FLAGS_SHORT_OPTIONAL[ idx ],
				LS_FLAGS_LONG_OPTIONAL[ idx ],
				help=LS_ARGS_HELP_OPTIONAL[ idx ],
				required=False )

	#add the hidden file object args, 
	#that are explicitely passed by
	#users who import this module and call mymain()

	o_args=o_parser.parse_args()

	ls_args_passed=[]

	for s_flag in LS_FLAGS_LONG_REQUIRED:
		s_argname=s_flag.replace( "--", "" )
		s_val=getattr( o_args, s_argname )
		ls_args_passed.append( s_val )
	#end for each arg flag

	#check for optionals, use default if not passed:
	if o_args.processes is None:
		ls_args_passed.append( DEFAULT_NUM_PROCESSES )
	else:
		ls_args_passed.append( o_args.processes )
	#end if no processes arg

	if o_args.mode is None:
		ls_args_passed.append( DEFAULT_DEBUG_MODE )
	else:
		ls_args_passed.append( o_args.mode )
	#end if no mode passed

	#now we add the default output file objects and 
	#mp event args hidden from console user, set by
	#users who import this mod and call mymain:
	ls_args_passed+=[ sys.stdout, sys.stderr, None ]

	mymain( *( ls_args_passed ) )

#end if main

