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
'''
__filename__ = "pgdriveneestimator.py"
__date__ = "20160510"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import glob
import sys
import os
from multiprocessing import Pool

#arguments passed either at command line
#or from python using def mymain, having
#imported this module

LS_ARGS=[ "glob pattern to match genepop files, enclosed in quotes. (Example: \"mydir/*txt\")", 
		"\"percent\" or \"remove\", indicating whether to sample by percentages or removing N individuals randomly",
		"list of integers, percentages or N's (for removing N individuals),  (Examples: 10,70,90 or 1,3,5)", 
		"minimum pop size (single integer)",
		"float, minimum allele frequency for NeEstimator's Crit value",
		"integer, total replicates to run (Note: when removing one individual in a pop of N, all N combinations will be run)" ]

LS_OPTIONAL_ARGS=[ "total processes to use (single integer) Default is 1 process.  " \
		+ "This arg is required if the final debug optional arg is added",
		"\"debug1\" to add to the output a table listing, for each indiv. in each file, " \
				+ "which replicate Ne estimates include the indiv, or,\n \"debug2\" " \
				+ "to run without parallelized processes," \
				+ "to produce the table, and to save all subsample " \
				+ "genepop files and NeEstimator output files." ]


#these args are used by callers who import this mod
#and call mymain directly -- users of the console
#don't use these, and resultsa are to stdout for the main outpu,
#and stderr for the secondary output.  THis is just a 
#bit of stand-in code in case usage ever implements hidden
HIDDEN_ARGS=[ "file_object_main", "file_object_secondary" ]

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
MAX_GENEPOP_FILE_NAME_LENGTH=31

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

#user enters the string as command
#line arg, codes tests with the constants
SAMPLE_BY_PERCENTAGES="percent"
SAMPLE_BY_REMOVAL="remove"

OUTPUT_DELIMITER="\t"
ENDLINE_SEQ="\n"
OUTPUT_ENDLINE="\n"
REPLICATE_DELIMITER=","

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


def set_indices_ne_estimator_output_fields_to_skip():

	IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP=[]

	for s_field_name in NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP:
		i_idx=pgout.PGOutputNeEstimator.OUTPUT_FIELDS.index( s_field_name )
		IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP.append( i_idx )
	#end for each ne est output field name

	return IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP
#end set_indices_ne_estimator_output_fields_to_skip


class DebugMode( object ):
	
	MODES=[ "no_debug", "debug1", "debug2", "debug3", "testserial", "testmulti" ]

	NO_DEBUG="no_debug"
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
	KEEP_NEXTP_FILES=64
		
	def __init__( self, s_mode="no_debug" ):
		self.__mode=s_mode
		self.__modeval=0
		self.__set_debug_mode()
	#end init

	def __set_debug_mode( self  ):
		if self.__mode==DebugMode.NO_DEBUG:
			self.__modeval=DebugMode.ALLOW_MULTI_PROCESSES
		elif self.__mode==DebugMode.MAKE_TABLE:
			self.__modeval=DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.ALLOW_MULTI_PROCESSES
		elif self.__mode==DebugMode.MAKE_TABLE_AND_KEEP_FILES:
			self.__modeval=DebugMode.KEEP_REPLICATE_GENEPOP_FILES \
					+ DebugMode.KEEP_ESTIMATOR_FILES \
					+ DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.ALLOW_MULTI_PROCESSES \
					+ DebugMode.KEEP_NODAT_FILES \
					+ DebugMode.KEEP_NEXTP_FILES 
		elif self.__mode==DebugMode.ALL_DEBUG_OPTIONS:
			self.__modeval=DebugMode.KEEP_REPLICATE_GENEPOP_FILES \
					+ DebugMode.KEEP_ESTIMATOR_FILES \
					+ DebugMode.MAKE_INDIV_TABLE  \
					+ DebugMode.KEEP_NODAT_FILES \
					+ DebugMode.KEEP_NEXTP_FILES \
					+ DebugMode.PRINT_REPLICATE_SELECTIONS
		elif self.__mode==DebugMode.TEST_SERIAL:
			self.__modeval=DebugMode.KEEP_REPLICATE_GENEPOP_FILES \
					+ DebugMode.KEEP_ESTIMATOR_FILES \
					+ DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.PRINT_REPLICATE_SELECTIONS \
					+ DebugMode.KEEP_NODAT_FILES \
					+ DebugMode.KEEP_NEXTP_FILES 
		elif self.__mode==DebugMode.TEST_MULTI:
			self.__modeval=DebugMode.MAKE_INDIV_TABLE \
					+ DebugMode.ALLOW_MULTI_PROCESSES \
					+ DebugMode.PRINT_REPLICATE_SELECTIONS 
		else:
			s_msg="in " + __filename__ + "DebugMode object, set_debug_mode: " \
			+ "unknown value for mode: " + str ( i_mode ) 
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
		s_msg="optional 6th argument must be one of, " \
				+ ",".join( DebugMode.MODES )
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
	#end try eval, except name error

	return ls_files
#end get_genepop_file_list

def parse_args( *args ):

	IDX_GENEPOP_FILES=0
	IDX_SAMPLE_SCHEME=1
	IDX_SAMPLE_VALUE_LIST=2
	IDX_MIN_POP_SIZE=3
	IDX_MIN_ALLELE_FREQ=4
	IDX_REPLICATES=5
	IDX_PROCESSES=6
	IDX_DEBUG_MODE=7
	IDX_MAIN_OUTFILE=8
	IDX_SECONDARY_OUTFILE=9

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
	if s_sample_scheme == SAMPLE_BY_PERCENTAGES:
		lv_sample_values=[ int( s_val )/100.0  for s_val in args[ IDX_SAMPLE_VALUE_LIST ].split( "," ) ]
	elif s_sample_scheme == SAMPLE_BY_REMOVAL:
		lv_sample_values=[ int( s_val ) for s_val in args[ IDX_SAMPLE_VALUE_LIST ].split( "," ) ]
	else:
		s_msg = "In pgdriveneestimator.py, def parse_args, unknown sample scheme: " \
						+ s_sample_scheme + "."
		raise Exception( s_msg  )
	#end if sample percent, else removal, else error

	#sort the sample param values, in case we need to make an individual/replicate table:
	lv_sample_values.sort()

	i_min_pop_size=int( args[ IDX_MIN_POP_SIZE ] )
	f_min_allele_freq = float( args[ IDX_MIN_ALLELE_FREQ ] )
	i_total_replicates=int( args[ IDX_REPLICATES ] )
	i_total_processes=int( args[ IDX_PROCESSES ] )
	o_debug_mode=set_debug_mode ( args[ IDX_DEBUG_MODE ] )
	o_main_outfile=args[ IDX_MAIN_OUTFILE ]
	o_secondary_outfile=args[ IDX_SECONDARY_OUTFILE ]

	return( ls_files, s_sample_scheme, lv_sample_values, 
								i_min_pop_size, f_min_allele_freq, 
								i_total_replicates, i_total_processes, o_debug_mode, 
								o_main_outfile, o_secondary_outfile )
#end parse_args

def get_sample_val_and_rep_number_from_sample_name( s_sample_name, s_sample_scheme ):

	i_sample_value=0
	i_replicate_number=0

	if s_sample_scheme==SAMPLE_BY_PERCENTAGES:
		s_sampler_type=gps.SCHEME_PROPORTION
	elif s_sample_scheme==SAMPLE_BY_REMOVAL:
		s_sampler_type=gps.SCHEME_REMOVAL
	else:
		s_msg = "In pgdriveneestimator.py, def get_sample_value_and_replicate_number_from_sample_tag, " \
				+ "unknown sampling scheme: " + s_sample_scheme + "."
		raise Exception( s_msg )
	#end if scheme percent, else removal, else error

	i_sample_value, i_replicate_number= \
			gps.get_sample_value_and_replicate_number_from_sample_tag ( s_sample_name, s_sampler_type )	

	return ( i_sample_value, i_replicate_number )
#end get

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
					+ s_filename
		else:
			s_msg+="Current implementation of drive accepts genepop " \
				+ "files with only a single pop."
		#end if lt 1 else more
		raise Exception( s_msg )
	#end if non-single pop file

	return
#end raise_exception_non_single_pop_file

def get_pops_in_file_too_small_to_run( o_genepopfile, f_proportion, i_min_pop_size ):
	'''
	checks size of every pop in the file
	in case we need to skip some pops and 
	accept others.
	'''

	li_popsizes=o_genepopfile.getIndividualCounts()

	li_pops_too_small = []
	for idx_pop in range( len ( li_popsizes ) ):
		i_size_of_pop=int( round( li_popsizes[ idx_pop ] * f_proportion ) )
		if i_size_of_pop < i_min_pop_size:
			li_pops_too_small.append( idx_pop )
		#end if subsample size too small
	#end for each pop number
	return li_pops_too_small
#end get_pops_in_file_too_small_to_run

def do_estimate( ( o_genepopfile, o_ne_estimator, 
				f_proportion, f_min_allele_freq, 
				s_subsample_tag, s_pop_subsample_tag,
				i_replicate_number, 
				o_debug_mode,
				IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP) ):

	s_genepop_file_subsample=o_ne_estimator.input.genepop_file

	o_genepopfile.writeGenePopFile( s_genepop_file_subsample, 
					s_indiv_subsample_tag=s_subsample_tag,
					s_pop_subsample_tag=s_pop_subsample_tag ) 

	o_ne_estimator.doOp()

	llv_output=o_ne_estimator.deliverResults()

	li_sample_indiv_count=o_genepopfile.getIndividualCounts( s_indiv_subsample_tag = s_subsample_tag, 
			s_pop_subsample_tag = s_pop_subsample_tag )

	s_sample_indiv_count = str( li_sample_indiv_count[ 0 ] )

	ls_runinfo=[ o_genepopfile.original_file_name, 
			s_pop_subsample_tag, 
			s_sample_indiv_count, 
			str( f_proportion ), 
			str( i_replicate_number), 
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

	#as of Fri May 13 20:06:14 MDT 2016 currently not able
	#to parse nodat file,  so leave this rem'd out:
#	if s_nodat_file is not None:
#		s_nodat_info=o_ne_estimator.output.parsed_nodat_info
#		if s_nodat_info is not None:
#			s_stderr="\t".join( ls_runinfo + s_nodat_info ) 
#		#end if nodat info is not none
#		os.remove( s_nodat_file )
	#end if nodat file is not none

	if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
		ls_indiv_list = o_genepopfile.getListIndividuals( 
				i_pop_number=int( s_pop_subsample_tag ), 
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

	if not( o_debug_mode.isSet( DebugMode.KEEP_NEXTP_FILES) ):
		ls_nextp_files=glob.glob( "*nexTp.txt" )
		for o_nextpfile in ls_nextp_files:
			os.remove( o_nextpfile )
		#end for each nextpfile
	#end if debug mode says remove nodats

	return { "for_stdout" : s_stdout, "for_stderr" : s_stderr, 
			"for_indiv_table": None if ls_indiv_list is None \
					else { "file" : o_genepopfile.original_file_name, 
						"proportion": f_proportion,
						"rep" : i_replicate_number,
						"list" : ls_indiv_list,
						"pop" : s_pop_subsample_tag } }

#end do_estimate

def write_results( ds_results, o_main_outfile, o_secondary_outfile ):
	o_main_outfile.write( ds_results[ "for_stdout" ] + "\n" )
	if ds_results[ "for_stderr" ] is not None:
		o_secondary_outfile.write( ds_results [ "for_stderr" ] )
	#end if we have stderr results
#end write_results

def update_indiv_list( dddli_indiv_list, dv_indiv_info_for_replicate, lf_proportions ):

	s_orig_file=dv_indiv_info_for_replicate[ "file" ]
	s_population_number=dv_indiv_info_for_replicate[ "pop" ]
	f_this_proportion= dv_indiv_info_for_replicate[ "proportion" ]  
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

		#we create an empty lists for all proportions at once.
		#So, if a give proportionn is missing from the current dddli_indiv_list
		#for this file/indiv combo, we know that all are missing, so we need to add 
		#all proportions:
		if f_this_proportion not in dddli_indiv_list[ s_orig_file ][ s_population_number][ s_indiv ]:
			for f_proportion in lf_proportions:
				dddli_indiv_list[ s_orig_file ][ s_population_number ][ s_indiv ][ f_proportion ] = []
			#end for each proportion
		#end if new proportion

		dddli_indiv_list[ s_orig_file ][s_population_number][ s_indiv ][ f_this_proportion ].append( i_replicate )
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
													o_secondary_outfile,
													s_population_subsample_tag ):

	i_sample_value, i_replicate_number = \
			get_sample_val_and_rep_number_from_sample_name( s_indiv_subsample_tag, 
			s_sample_scheme )

	li_selected_indices=o_genepopfile.getListIndividualNumbers( \
						i_pop_number = int( s_population_subsample_tag ), 
						s_indiv_subsample_tag=s_indiv_subsample_tag )

	s_indiv_indices= ",".join( [ str(i) for i in li_selected_indices ] ) 

	ls_values_to_print=	[ o_genepopfile.original_file_name, 
								s_population_subsample_tag,
								str( i_sample_value ), 
								str( i_replicate_number ), 
								s_indiv_indices ] 

	s_values_to_print="\t".join( ls_values_to_print )
	o_secondary_outfile.write( s_values_to_print + "\n" )
	#end for each pop number, print the selected indices
	return
#end get_test_list_replicate_selection_indices


def do_sample( o_genepopfile, s_sample_scheme, lv_sample_values, i_replicates ):
	'''
	do_sample adds subsample info to the o_genepopfile GenepopFileManager object,
	and so changes it in place, returns no value.  The o_genepopfile can then
	be accessed to write a new genepop file that contains the subsampled data.
	'''
	i_total_pops_in_file=o_genepopfile.pop_total

	#sampler requires a population list (in case we want to sample fewer than
	#all the pops in the file). We default to lising all:
	#GenepopFileManager instance o_genepopfile lists populations as 1,2,3...
	li_population_list=list( range( 1, i_total_pops_in_file + 1 ) )

	o_sampler=None	

	s_population_subsample_tag=s_sample_scheme

	if s_sample_scheme==SAMPLE_BY_PERCENTAGES:

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
	else:
		s_msg="in pgdriveneestimator, def do_sample, unknown value " \
				+ "for sample scheme: " + s_sample_scheme
		raise Exception( s_msg )
	#end if percent, else removal, else error

	o_sampler.doSample()

	return
#end do_sample

def add_to_set_of_calls_to_do_estimate( o_genepopfile, 
						f_min_allele_freq, 
						i_min_pop_size,
						o_debug_mode,
						llv_args_each_process,
						IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP,
						o_secondary_outfile ):
	'''		
	creates ne-estimator caller object and adds it to list of args for a single call
	to do estimate.  This call is then appended to llv_args_each_process
	'''

	#all these GenepopFileManager objects should now have
	#a single population sample name (and which also names the 
	#sampling scheme type):
	s_population_sample_name=o_genepopfile.population_subsample_tags[ 0 ]
	s_sample_scheme=s_population_sample_name

	ls_indiv_sample_names=o_genepopfile.indiv_subsample_tags

	li_population_numbers=o_genepopfile.getListPopulationNumbers( s_population_sample_name )
	#for each sample (i.e. for each replicate of a sampling with a given set of params:
	for s_indiv_sample in ls_indiv_sample_names:

		#we also check that at least one pop has at least one individual
		#listed for this subsample
		li_indiv_counts_for_this_sample=o_genepopfile.getIndividualCounts( s_indiv_subsample_tag=s_indiv_sample )
	
		if sum( li_indiv_counts_for_this_sample ) == 0:
			v_sample_value, i_replicate_count=get_sample_val_and_rep_number_from_sample_name( \
											s_indiv_sample, s_sample_scheme )
			#we only want to report the first replicate
			#(by inference of course all replicates will be skipped:
			if i_replicate_count == 0:
				s_msg="Skipping samples from: " \
						+ o_genepopfile.original_file_name \
						+ ".  In pgdriveneestimator.py, all populations " \
						+ "have zero individuals when sampled using " \
						+ "scheme: " + s_sample_scheme \
						+ ", and with sample parameter, " + str( v_sample_value ) + "."
				o_secondary_outfile.write( s_msg + "\n" )
			#end if first replicate, report
			continue
		#end skip this subsample if no pops have any individuals

		#we skip populations if their (original, un-subsampled size is under 
		#min_pop_size -- so moved this call above the subsampling
		#loop, and revised to check the population size(s) in the
		#original file #make sure the population(s) meet the min size criteria:
		li_too_small_pops=get_pops_in_file_too_small_to_run( o_genepopfile, 1.0, i_min_pop_size )

		#to most-efficiently use multi-processes, that is, to assign to a process a single
		#file with many populations, we sample each pop in the file separately, and divvy
		#the pops up among processes:
		for i_population_number in li_population_numbers:

			if i_population_number in li_too_small_pops:
				s_msg=( "In pgdriveneestimator.py, def drive_estimator, " \
								+ " in file, "  + s_filename \
								+ ", skipping pop number, "  + str( i_pop_number ) \
								+ ".  It has fewer than " + str( i_min_pop_size ) \
								+ " individuals." )
				o_secondary_outfile.write( s_msg + "\n" )
				continue
			#end if i_population_number is

			#we make population subsample list consisting of only this populations number:
			s_this_pop_sample_name=str( i_population_number ) 

			o_genepopfile.subsamplePopulationsByList( [ i_population_number ], s_this_pop_sample_name )

			if o_debug_mode.isSet( DebugMode.PRINT_REPLICATE_SELECTIONS ):
				print_test_list_replicate_selection_indices( o_genepopfile, 
										s_sample_scheme,	
										s_indiv_sample, 
										o_secondary_outfile, 
										s_population_subsample_tag=s_this_pop_sample_name )
			#end if we're testing, print 
				
			s_genepop_file_subsample=o_genepopfile.original_file_name + "_" +  s_indiv_sample \
											+ "_g_" + s_this_pop_sample_name

			i_sample_value, i_replicate_number= \
						get_sample_val_and_rep_number_from_sample_name( s_indiv_sample, s_sample_scheme )

			#Note: if a period is left in the original file name,
			#NeEstimator, when naming "*NoDat.txt" file, will replace the right-most
			#period all text that follows it,  with "NoDat.txt" 
			#-- this then removes any percent and replicate number text 
			#I'm using to make files unique, and so creates a 
			#non-uniq *NoDat.txt file name, which, when one process removes it, 
			#and another goes looking for it , throws an exception -- (an 
			#exception from the multiprocessing.Pools async mapping -- file-not-found,
			#but no trace since it occurs in a different process from the main).
			#This peculiar mangling of a users input file -- was preventing me in previous versions, 
			#from deleting NoDat files, and also I think meant that only the 
			#last process in a given group of replicates (share same genepop file
			#and proportion sampled) to use the NoDAt file got to write it's NoDat info. 
			#Removing all periods from the input file to the NeEstimator program, I belive,
			#completely solves the problems.
			s_genepop_file_subsample=s_genepop_file_subsample.replace( ".", "_" )

			s_run_output_file=s_genepop_file_subsample + "_ne_run.txt"

			o_neinput=pgin.PGInputNeEstimator( s_genepop_file_subsample )

			o_neinput.run_params={ "crits":[ f_min_allele_freq ]  }

			o_neoutput=pgout.PGOutputNeEstimator( s_genepop_file_subsample, s_run_output_file )	

			o_ne_estimator=pgne.PGOpNeEstimator( o_neinput, o_neoutput ) 

			#we send to def do_estimate the genepop file object, o_genepopfile, and the subsample tag
			#that identifies the correct subsample calculated and stored in the object, so we can write
			#each subsample genepop file in the same process that will use it as input to the the estimator, 
			#This should limit the number of input files existing concurrenty in the directory to the 
			#number of processes in use.  We also send allele freq, and the original genepop file name 
			#inside the genepop file manager object):

			v_sample_value, i_replicate_number = \
					get_sample_val_and_rep_number_from_sample_name( s_indiv_sample, s_sample_scheme )

			lv_these_args = [ o_genepopfile,  
								o_ne_estimator, 
								v_sample_value, 
								f_min_allele_freq, 
								s_indiv_sample, 
								s_this_pop_sample_name, 
								i_replicate_number, 
								o_debug_mode,
								IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP ]

			llv_args_each_process.append( lv_these_args )
		#end for each population
	#end for each sample name
	return
#end add_to_set_of_calls_to_do_estimate

def write_result_sets( lds_results, lv_sample_values, o_debug_mode, o_main_outfile, o_secondary_outfile ):

	dddli_indiv_list=None

	if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
		dddli_indiv_list={}
	#end if debug mode, init indiv list

	for ds_result in lds_results:
			write_results( ds_result, o_main_outfile, o_secondary_outfile )
			if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
				update_indiv_list( dddli_indiv_list, 
						ds_result[ "for_indiv_table" ], 
						lv_sample_values )
			#end if make indiv table, update list
	#end for each result set

	if o_debug_mode.isSet( DebugMode.MAKE_INDIV_TABLE ):
		s_indiv_table_file=make_indiv_table_name ()
		write_indiv_table( dddli_indiv_list, s_indiv_table_file, lv_sample_values )
	#end if we made indiv table, write it

	return
# write_result_sets		

def execute_ne_for_each_sample( llv_args_each_process, o_process_pool, o_debug_mode ):

	lds_results=None

	#if this run is not in serial mode
	#then we're using the mulitprocessor pool,
	#(even if user only requested a single processor):
	if  o_debug_mode.isSet( DebugMode.ALLOW_MULTI_PROCESSES ): 
		lds_results=o_process_pool.map( do_estimate, llv_args_each_process )
		o_process_pool.close()
		o_process_pool.join()
		#end for each result
	else:
		lds_results=[]
		for lv_these_args in llv_args_each_process:
			ds_result=do_estimate( lv_these_args )
			lds_results.append( ds_result )	
		#end for each set of args
	#end if multiprocess allowed, execute async, else serially
	return lds_results
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

	ls_run_fields=[ "original_file", "pop", "indiv_count", "sample_value", "replicate_number", 
						"min_allele_freq" ] 

	o_main_outfile.write( OUTPUT_DELIMITER.join( ls_run_fields + ls_reported_fields  ) + OUTPUT_ENDLINE )
#end write_header_main_table

def drive_estimator( *args ):

	( ls_files, s_sample_scheme, lv_sample_values, 
				i_min_pop_size, f_min_allele_freq, i_total_replicates, 
				i_total_processes, o_debug_mode, o_main_outfile, o_secondary_outfile ) = parse_args( *args )

	o_process_pool=None

	IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP = \
			set_indices_ne_estimator_output_fields_to_skip()

	if o_debug_mode.isSet( DebugMode.ALLOW_MULTI_PROCESSES ):
		o_process_pool=Pool( i_total_processes )
	#end if multi processing

	llv_args_each_process=[]

	s_indiv_table_file=None
	#these used soley
	#to add header to output before 
	#computing the first rep
	#of the first proportion
	#for the first file:
	i_filecount=0
	i_proportion_count=0
	i_replicate_count=0

	#the counters will total
	#this on the first call to estimator:
	FIRST_RUN=3

	write_header_main_table( IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP, o_main_outfile )

	for s_filename in ls_files:

		o_genepopfile=gpf.GenepopFileManager( s_filename )

		i_total_populations=o_genepopfile.pop_total
		do_sample( o_genepopfile, s_sample_scheme, lv_sample_values, i_total_replicates )
			
		add_to_set_of_calls_to_do_estimate( o_genepopfile, 
												f_min_allele_freq, 
												i_min_pop_size,
												o_debug_mode,
												llv_args_each_process,
												IDX_NE_ESTIMATOR_OUTPUT_FIELDS_TO_SKIP,
												o_secondary_outfile )
		
	#end for each genepop file, sample, add an ne-estimator object, and setup call to estimator 

	lds_results=execute_ne_for_each_sample( llv_args_each_process, o_process_pool, o_debug_mode )

	write_result_sets( lds_results, lv_sample_values, o_debug_mode, o_main_outfile, o_secondary_outfile )

	return
#end drive_estimator

def did_find_ne_estimator_executable():
	b_found=False
 
	#make sure the neestimator is in the user's PATH:
	NEEST_EXEC_LINUX="Ne2L"
	NEEST_EXEC_WIN="Ne2.ext"
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
		s_neestimator_exec="Ne2.exe"
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

	b_exec_found=did_find_ne_estimator_executable()

	if not did_find_ne_estimator_executable():
		raise Exception( "in pgdriveneestimator.py, def mymain(), did not find NeEstimator executable." )
	#end if can't find executable

	drive_estimator(  *( q_args ) )

	return
#end mymain

if __name__ == "__main__":
	s_usage = pgut.do_usage_check( sys.argv, LS_ARGS, 
			ls_optional_arg_descriptions=LS_OPTIONAL_ARGS,
			b_multi_line_msg=True )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	#add the hidden file object args, 
	#that are explicitely passed by
	#users who import this module and call mymain()

	ls_args_passed=sys.argv[ 1: ] 

	i_total_args_passed=len( ls_args_passed )
	i_total_nonopt=len( LS_ARGS )

	i_total_with_process_opt=i_total_nonopt + 1
	i_total_with_debug=i_total_nonopt + 2

	#if args given at command line don't include
	#the optionals, add the defaults
	if i_total_args_passed == i_total_nonopt:
		ls_args_passed += [ DEFAULT_NUM_PROCESSES , DEFAULT_DEBUG_MODE ]
	elif i_total_args_passed==i_total_with_process_opt:
		ls_args_passed += [ DEFAULT_DEBUG_MODE ]
	#end if optional args supplied else use default

	#now we add the default file objects, args hidden from console user:
	ls_args_passed+=[ sys.stdout, sys.stderr ]

	mymain( *( ls_args_passed ) )

#end if main

