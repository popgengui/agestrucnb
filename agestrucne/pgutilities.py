'''
Description
Support defs for the pop gen interface programs.
'''
from __future__ import absolute_import, division, print_function

from builtins import range
__filename__ = "pgutilities.py"
__date__ = "20160601"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os
import sys

import subprocess
import glob
import inspect
import time
import multiprocessing

#For writing a filtered
#ne estimation table file.
import tempfile

'''
psutil is used as the preferred tool
for cancelling the subprocess
launched to do ne estimations. See def
run_driveneestimator_in_new_process.

2017_07_06. psutil is now also used 
to report availble virtual memory in
def get_memory_virtual_available
'''
import psutil

'''
Used to detect a Windows OS, and 
correct strings that give file paths:
'''
import platform

'''
2017_03_27.  See def remove_directory_and_all_contents
'''
import shutil

'''
2017_04_27
For traceback information for catchall
try statements made during processes
executing in parallell.
'''
import traceback

from agestrucne.pgutilityclasses import IndependantSubprocessGroup 
from agestrucne.pgneestimationtablefilemanager import NeEstimationTableFileManager 

#for getting roots of quadratic, for
#calls from pgopsimupop, to get initial
#allele frequencies, given a het value.
from numpy import sqrt as npsqrt

#For estimating microsat allele frequencies
#given an expected heterozygosity:
from numpy.random.mtrand import dirichlet 

'''
2017_04_27
For python 2 and 3 compatibility,
for users who have both versions
of python in their paths, we
need to use the current interpreters
executable for our spawned python processes.
'''
PYEXE_FOR_POPEN=sys.executable

VERBOSE=False

PROCESS_QUEUE_STOP_SIGN='STOP'
SIMULATION_OUTPUT_FILE_REPLICATE_TAG=".r"
DELIMITER_LIFE_TABLE_FILES=","

NE_ESTIMATION_MAIN_TABLE_FILE_EXT="ldne.tsv"
NE_ESTIMATION_SECONDARY_OUTPUT_FILE_EXT="ldne.msgs"

SYS_LINUX="linux"
SYS_WINDOWS="windows"
SYS_MAC="mac"


'''
Defs do_shutil_* below address the problem
with the limit on windows path length using
shutil.copy (and, presumably, move and rmtree too).
These are the paramaters needed to fix too-long paths.
'''
WINDOWS_PATH_LENGTH_LIMIT=254
WINDOWS_PREFIX_LONG_PATH="\\\\?\\"

def do_usage_check( ls_this_argv, 
            ls_required_arg_descriptions, 
            ls_optional_arg_descriptions = [],
            b_multi_line_msg=False,
            b_unlimited_final_args=False,
            s_note=None):
	'''
	arg 1 expects sys.argv, or a copy
	arg 2 expects a list strings, in order, required args
	arg 3 expects a list of strings, in order, any optional args
	'''
	i_num_args_required = len( ls_required_arg_descriptions )
	i_num_args_optional = len( ls_optional_arg_descriptions )
	i_max_poss_num_args = i_num_args_required + i_num_args_optional 
	i_num_args_passed = len( ls_this_argv ) - 1  
	s_usage_string = ""
	s_arg_delimit=""
	if b_multi_line_msg == True:
		s_arg_delimit="\n"
	#end if we put each arg descript on a 
	#separate line of output

	if i_num_args_passed <  i_num_args_required  \
			or (i_num_args_passed > i_max_poss_num_args and b_unlimited_final_args == False ): 
	
		s_scriptname = os.path.basename( ls_this_argv[ 0 ] )	
		s_usage_string = "usage: " + s_scriptname 

		if b_multi_line_msg:
			s_usage_string="usage: " + s_scriptname \
					+ "\nargs:\n"
		else:
			s_usage_string = "usage: " + s_scriptname 
		#end if multi line else not

		for s_arg in ls_required_arg_descriptions:

			s_usage_string += " <" \
				+ s_arg + ">" \
				+ s_arg_delimit
		#end for each requried arg

		for s_arg in ls_optional_arg_descriptions:

			s_usage_string += " <(optional) " \
				+ s_arg + ">" \
				+ s_arg_delimit
		#end for each required arg

	#end if number of args is out of range

	if s_usage_string != "" and s_note is not None:
		s_usage_string=s_usage_string + "\n" + s_note
	#end if note 

	return  s_usage_string 
#def do_usage_check

def get_temp_file_name( s_parent_dir=None ):
	s_tempfile=tempfile.mktemp( dir=s_parent_dir )	
	return s_tempfile
#end get_temp_file_name

def get_temporary_directory( s_parent_dir=None, s_prefix='tmp' ):
	
	s_tempdir_name=None

	try:
		s_tempdir_name=tempfile.mkdtemp( dir=s_parent_dir, prefix=s_prefix )
	except Exception as oex:
		s_msg="In module pgutilities.py, " \
					+ "def get_temporary_directory, " \
					+ "with arguments, dir, " \
					+ str( s_parent_dir ) + ", and prefix, " \
					+ s_prefix  + ", tempfile.mkdtemp threw  " \
					+ "an Exception with message: "  + str( oex )
		raise Exception( s_msg )
	#end try ... except

	return s_tempdir_name
#end get_temporary_directory

def do_shutil_copy( s_source, s_destination ):

	'''
	This wrapper around the shutil.copy guards
	against the Windows win32 api limit of 255
	characters in a path string (see http://
	stackoverflow.com/questions/14075465/
	copy-a-file-with-a-too-long-path-to-another-
	directory-in-python).  
	
	Despite the use 255 i nthe above info, and 260
    as the length limit given elsewhere on the web,
    My trial found that I needed to set my max path
    at 259, as measured by the python len() function.

    I also found that the long path prefix, 
    "\\\\?\\" -- though it worked fine (i.e. had no
    deleterious effect) on short paths (as long as
    they were absolute), it did nothing to prevent
    the copy failure problem on long paths (tests all
    done on windows 10).
	'''


	if is_windows_platform():

		if len( s_source ) > WINDOWS_PATH_LENGTH_LIMIT \
				or len( s_destination ) > WINDOWS_PATH_LENGTH_LIMIT:

			s_msg="In module pgutilities.py, def do_shutil_copy, " \
						+ "The program is unable to copy from, " \
						+ s_source + " to " + s_destination + ".\n" \
						+ "The path of the source and/or destination " \
						+ "exceed(s) the " \
						+ str( WINDOWS_PATH_LENGTH_LIMIT )  \
						+ " character  limit that causes " \
						+ "a copy failure in Windows."  
			raise Exception( s_msg )
		#end if path length exceeded
		
	#end if windows platform

	shutil.copy( s_source, s_destination )

	return
#end do_shutil_copy


def do_shutil_move( s_source, s_destination ):
	'''
	This wrapper around the shutil.move guards
	against the Windows win32 api limit of 255
	characters in a path string (see http://
	stackoverflow.com/questions/14075465/
	copy-a-file-with-a-too-long-path-to-another-
	directory-in-python).  

	See do_shutil_copy above for more details.
	'''


	if is_windows_platform():

		if len( s_source ) > WINDOWS_PATH_LENGTH_LIMIT \
				or len( s_destination ) > WINDOWS_PATH_LENGTH_LIMIT:

			s_msg="In module pgutilities.py, def do_shutil_copy, " \
						+ "The program is unable to move the frile from, " \
						+ s_source + " to " + s_destination + ".\n" \
						+ "The path of the source and/or destination " \
						+ "exceed(s) the " \
						+ str( WINDOWS_PATH_LENGTH_LIMIT )  \
						+ " character  limit that causes " \
						+ "a copy failure in Windows."  
			raise Exception( s_msg )
		#end if path length exceeded
		
	#end if windows platform

	shutil.move( s_source, s_destination )

	return
#end do_shutil_copy


def do_shutil_rmtree( s_path ):
	'''
	This wrapper around the shutil.rmtree guards
	against the Windows win32 api limit of 255
	characters in a path string (see http://
	stackoverflow.com/questions/14075465/
	copy-a-file-with-a-too-long-path-to-another-
	directory-in-python).  Not sure it applies
	to the rmtree, but we assume it does.
	'''

	if is_windows_platform():
		if len( s_path ) > WINDOWS_PATH_LENGTH_LIMIT:
			s_msg="In module pgutilities.py, def do_shutil_copy, " \
					+ "The program is unable to remove the directory tree from, " \
					+ s_source + " to " + s_destination + ".\n" \
					+ "The path of the source and/or destination " \
					+ "exceed(s) the " \
					+ str( WINDOWS_PATH_LENGTH_LIMIT )  \
					+ " character limit that causes " \
					+ "a failure in Windows."  
			raise Exception( s_msg )
		#end if path too long
	#end if windows platform

	shutil.rmtree( s_path )

	return
#end do_shutil_copy

def get_date_time_string_dotted():
	return time.strftime( '%Y.%m.%d.%H.%M.%S' )
#end get_date_time_string_dotted

def is_file_and_executable( s_path ):
	return ( os.path.isfile( s_path ) and os.access( s_path, os.X_OK ) )
#end is_file_and_executable

def confirm_executable_is_in_path( s_exectuable_file_name ):
    b_return_val=False

    #First, check without searching all paths in PATH
    if is_file_and_executable( s_exectuable_file_name ):
        b_return_val = True
    #failed as passed in, but maybe an executable name inside
    #a default PATH:
    else:

        IX_NAME="posix"
        WINDOWS_NAME="nt"

        LINUX_PATH_VAR="PATH"
        WINDOWS_PATH_VAR="PATH"

        s_paths=None

        if os.name==IX_NAME:
            s_paths=os.environ.get( LINUX_PATH_VAR )
        elif os.name==WINDOWS_NAME:
            s_paths=os.environ.get( WINDOWS_PATH_VAR )
        else:
            raise Exception( "In def confirm_executable_is_in_path, Unrecognized OS name: " + os.name )
        #end if posix else if nt, else unknown

        ls_paths=s_paths.split( os.pathsep )
        
        for s_path in ls_paths:
            s_file_loc=os.path.join( s_path, s_exectuable_file_name )
            if is_file_and_executable( s_file_loc ):
                b_return_val=True
                break
            #end if executable
        #end for each path in PATH

    return b_return_val
#end confirm_executable_is_in_path

def manage_process_queue( o_queue_with_target_calls, o_queue_to_hold_results=None ):
	for def_call, def_args in iter( o_queue_with_target_calls.get, 'STOP' ):
		v_result= def_call( *def_args )
		if o_queue_to_hold_results is not None:
			o_queue_to_hold_results.put( v_result )
		#end if results queue exists
	#end for each call

	return
#end manage_process_queue

def get_class_names_immediate_parent( o_object ):
	q_classes=inspect.getmro( o_object )
	o_class_immediate_parent = q_classes[1] 
	return str( o_class_immediate_parent )
#end get_class_name_immediate_parent

def get_current_working_directory():
	return os.getcwd()
#end get_current_working_directory

def get_listdir( s_parent_dir ):
	ls_dir_contents=os.listdir( s_parent_dir )
	return ls_dir_contents
#end get_listdir

def does_exist_and_is_file( s_file ):
	return os.path.isfile( s_file )
#end does_exist_and_is_file

def get_list_subdirectories( s_parent_dir ):
	ls_subdirs=[]
	ls_dir_contents=get_listdir( s_parent_dir )

	for s_item in ls_dir_contents:
		if os.path.isdir( s_item ):
			ls_subdirs.append( s_item )
		#end if is directory, add to list
	return ls_subdirs
#end get_list_subdirectories

def get_list_file_objects( s_parent_dir ):
	ls_files=[]
	ls_dir_contents=get_listdir( s_parent_dir )
	for s_item in ls_dir_contents:
		if os.path.isfile( s_item ):
			ls_files.append( s_item )
		#end if item is file, add to list
	#end for each item
	return ls_files
#end get_list_file_objects

def get_list_files_and_dirs_from_glob( s_glob ):
	ls_files=glob.glob( s_glob )
	return ls_files
#end get_list_files_and_dirs_from_glob

def get_basename_from_path( s_path ):
	return os.path.basename( s_path )
#end get_basename_from_path

def get_dirname_from_path( s_path ):
	return os.path.dirname( s_path )
#end get_basename_from_path


def remove_files( ls_files ):
	i_total_removed=0
	for s_file in ls_files:
		if os.path.isfile( s_file ):
			os.remove( s_file )
			i_total_removed += 1
		#end if is file, remove
	#end for each file
	return i_total_removed
#end remove files

def remove_directory_and_all_contents( s_directory ):
	try:
		if os.path.exists( s_directory ):
			shutil.rmtree( s_directory )
		else:
			raise Exception
		#end if path exists, remove, else exception

	except Exception as oex:
		s_msg="In module pgutilities.py, " \
				+ "def remove_directory_and_all_contents, " \
				+ "an exception was raised, with message: " \
				+ str( oex ) 
		raise Exception( oex )
	#end try...except
	return
#end def remove_directory_and_all_contents

def get_separator_character_for_current_os():
	return os.path.sep
#end get_separator_character_for_current_os

def get_platform():

	s_os_platform_name=platform.system()
	
	s_platform_informal=None

	if "linux" in s_os_platform_name.lower():
		s_platform_informal=SYS_LINUX
	elif "windows" in s_os_platform_name.lower():
		s_platform_informal=SYS_WINDOWS
	elif "darwin" in s_os_platform_name.lower():
		s_platform_informal=SYS_MAC
	else:
		s_msg="In pgutilitites, def get_platform, "  \
					+ "unrecognized platform name: " \
					+ s_os_platform_name + "."
		raise Exception( s_msg )
	#end if linux, else win, else mac, else error
	return s_platform_informal
#end get_platform

def is_windows_platform():
	s_os_plaform_name=get_platform()	
	return ( s_os_plaform_name == SYS_WINDOWS )
#end is_windows_platform

def fix_windows_path( s_path ):
	s_fixed_path=s_path.replace( "\\", "/" )
	return s_fixed_path
#end def fix_windows_path

#def do_simulation_reps_in_subprocesses( o_multiprocessing_event,
#										i_input_reps, 
#										i_total_processes_for_sims,
#										s_temp_config_file_for_running_replicates,
#										ls_life_table_files,
#										s_param_names_file,
#										s_output_basename,
#										b_use_gui_messaging=True,
#										i_output_mode=pgsim.PGOpSimuPop.OUTPUT_GENEPOP_ONLY ):
#
#	'''
#	Failed to get independant initialization of population per-replicate
#	when i used python's multiprocessing.process objects as hosts for 
#	running replicates in parallel.  Solution as of now, 
#	Sat Jul 30 22:38:42 MDT 2016, is to use OS processes via python's 
#	subprocess module, creating them in this def, which gets its
#	requisite info needed for the sim from the pgguisimupop instance
#	that calls this def (this def is called by the GUI interface instance
#	in a new python.multiprocessing.process instance, in order not to block the gui).
#
#	Note that this def was originally inside the pgguisimupop instance that calls it,
#	but on windows there was a pickling error not seen on linux or Mac.  Moving this
#	target def for the python.multiprocessing.process outside the pgguisimupop instance
#	seems to have solved the problem on windows (win 10).
#
#	This def manages the replices via creating subprocesses, and 
#	calling pgutilities.prep_and_call_do_pgopsimupop_replicate.
#
#	2017_05_30.  We added the def param b_use_gui_messaging=True, to allow
#	this def to be called from a command line implentation (new module 
#	pgdrivesimulation.py), and set the flag to false, without having to
#	revise the call from the GUI pgguisimupop.py.
#
#
#	'''	
#
#	'''	
#	Running this inside a try block allows us to notify GUI
#	users of exceptions propogated from anywere inside the 
#	simulation setup and execution code. When we catch exceptions 
#	below, we send an error message to a gui message box, then
#	re-raise the exception.	
#
#	 
#	2017_08_07.  I've added the params i_output_mode and s_pop_het_filter_string,
#	to allow callers to this def to set these new parameters in the PGOpSimuPop
#	object.
#
#	'''
#
#	try:
#		s_life_tables_stringified=",".join( ls_life_table_files )
#
#		#if we're on windows, out strings of file
#		#paths may be a mangled mix of unix and 
#		#windows separators -- with errors resulting
#		#downstream.  So we standardize:
#		if is_windows_platform():
#			s_life_tables_stringified= \
#				fix_windows_path( s_life_tables_stringified )
#			s_param_names_file= \
#				fix_windows_path( s_param_names_file )				
#			s_output_basename= \
#				fix_windows_path( s_output_basename )	
#		#end if windows, fix file path strings
#
#		i_total_replicates_requested=i_input_reps
#
#		i_max_processes_to_use=i_total_processes_for_sims
#
#
#		#we use a python command for a -c arg in the Popen command (see below)
#		#and these will be the same args for each replicate (we add the rep-number
#		#arg below).  We stringify so that they can be Popen command args.  Some
#		#are de-stringified by the pgutilities def before sending to pgop-creator
#		seq_first_four_args_to_sim_call=( s_temp_config_file_for_running_replicates,
#										s_life_tables_stringified,
#										s_param_names_file,
#										s_output_basename )
#		
#		i_total_replicates_started=0
#
#		o_subprocess_group=IndependantSubprocessGroup()
#
#		while i_total_replicates_started < i_total_replicates_requested:
#			#see if we need to cancel:	
#			if o_multiprocessing_event.is_set():
#
#				if VERBOSE:
#					print ( "received event in setup loop" )
#				#end if VERBOSE
#
#				o_subprocess_group.terminateAllSubprocesses()
#			
#				remove_simulation_replicate_output_files( s_output_basename )
#
#				break
#
#			else:
#
#				i_number_subprocesses_alive=o_subprocess_group.getTotalAlive()
#
#				i_number_subprocesses_available= \
#						i_max_processes_to_use-i_number_subprocesses_alive
#
#				i_number_replicates_to_go=i_total_replicates_requested - i_total_replicates_started
#
#				i_number_subprocesses_to_start=i_number_subprocesses_available
#
#				#reduce the number to start if we have fewer reps to go than avail procs:
#				if i_number_subprocesses_available > i_number_replicates_to_go:
#						i_number_subprocesses_to_start = i_number_replicates_to_go
#				#end if fewer needed than available
#
#				for idx in range( i_number_subprocesses_to_start ):
#
#					i_total_replicates_started += 1
#					
#					#In the Popen call, rather than rely on a driver python script 
#					#that would need to be in PATH, we'll simply
#					#invoke python with a "-c" argument that imports the 
#					#pgutilities module and executes the correct def:
#			
#					#complete the set of args used in the command by adding the
#					#replicate number (recall need comma in sequence with single item,
#					#to delineate sequence versus simple expression):
#					seq_complete_arg_set=seq_first_four_args_to_sim_call + ( str( i_total_replicates_started ), )
#
#					'''
#					2017_05_30.  We added this argument to def prep_and_call_do_pgopsimupop_replicate, to propgate
#					to its call to def do_pgopsimupop_replicate_from_files.
#					
#					'''
#					seq_complete_arg_set=seq_complete_arg_set + ( str( b_use_gui_messaging ), )
#
#					'''
#					2017_08_07.  We added args to allow caller to use diffeent output modes, 
#					and, if using the filter output mode, to pass a string with parameters,
#					for filtering pops by mean heterozygosity.  (See new additions to PGOpSimuPop code.)
#
#					2017_09_04. We remove the s_pop_het_filter_string argument.  It has been removed from
#					the arglist for initializing PGOpSimuPop instances, and instead those instances
#					will access it directly from the PGInputSimuPop object.
#					'''
#					seq_complete_arg_set=seq_complete_arg_set + ( str( i_output_mode ), )
#
#
#					'''
#					in case the negui mods are not in the default python 
#					install dirs, then we need to add them to the sys.paths in
#					any  spawned invocation of python exe -- seems that 
#					the PYTHONPATH env var known to this parent process 
#					is unknown to the "python" invocation via Popen.  
#					We can get for and then add to our new python invocation
#					the path to all negui modules by getting the
#					path to this module:
#					'''
#					s_curr_mod_path = os.path.abspath(__file__)
#
#					#path only (stripped off "/utilities.py" )
#					#-- gives path to all negui mods:
#					s_mod_dir=os.path.dirname( s_curr_mod_path )
#
#					#need to fix the path if we're on windows:
#					if is_windows_platform():
#						s_mod_dir=fix_windows_path( s_mod_dir )
#					#end if windows, fix path
#					
#					s_path_append_statements="import sys; sys.path.append( \"" \
#							+ s_mod_dir + "\" );"
#
#					s_python_command=s_path_append_statements + "import pgutilities;" \
#										"pgutilities.prep_and_call_do_pgopsimupop_replicate" \
#										+ "( \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\" )" %  seq_complete_arg_set
#
#					o_new_subprocess=subprocess.Popen( [ PYEXE_FOR_POPEN, "-c", s_python_command ] )
#					o_subprocess_group.addSubprocess( o_new_subprocess ) 
#				#end for each idx of new procs
#			#end if event is set else not
#		#end while preplicates need to be started
#
#		#we don't want to return until all processes are done.
#		#meantime test for cancel-request
#		i_total_still_alive_after_creating_all=o_subprocess_group.getTotalAlive()
#
#		while i_total_still_alive_after_creating_all > 0:
#			if o_multiprocessing_event.is_set():
#
#				if VERBOSE:
#					print( "received event in final loop" )
#				#end if verbose
#
#				o_subprocess_group.terminateAllSubprocesses()
#				remove_simulation_replicate_output_files( s_output_basename )
#			#end if we are to cancel
#			i_total_still_alive_after_creating_all=o_subprocess_group.getTotalAlive()
#		#end while
#
#	except Exception as oex:
#
#		o_traceback=sys.exc_info()[ 2 ]
#		s_err_info=get_traceback_info_about_offending_code( o_traceback )
#		s_prefix_msg_with_trace="Error caught by pgutilities, " \
#								+ "def __do_simulation_reps_in_subprocesses." \
#								+ "\\nError origin info:\\n" \
#								+ s_err_info 
#
#		if b_use_gui_messaging:
#			show_error_in_messagebox_in_new_process( oex, 
#				s_msg_prefix = s_prefix_msg_with_trace )
#		#end if use gui messaging
#
#		s_msg=s_prefix_msg_with_trace + str( oex )
#		raise Exception( oex )
#	#end try...except...
#	return
#end __do_simulation_reps_in_subprocesses

def get_cpu_count():
	return multiprocessing.cpu_count()
#end get_cpu_count

def dialog_returns_nothing( v_return_value ):

	'''
	To evaluate return values from askopenfilenames,
	askdirectory, askopenfilename, dialog windows.
	Note that unlike askopenfile (singular),
	an empty tuple is returned by askdirectory when
	the diag is cancelled on the first instance it
	is invoked, and an empty string thereafter.  
	askopenfilenames returns an empty tuple on all cancels.
	'''	

	b_is_nothing=False

	o_return_type=type( v_return_value )

	if o_return_type == tuple:
		b_is_nothing = ( len( v_return_value ) == 0 )
	elif o_return_type == str:
		b_is_nothing = ( v_return_value == "" )
	elif o_return_type == unicode:
		b_is_nothing = ( v_return_value == "" )
	else:
		s_msg = "In pgutilities, def dialog_returns_nothing(), " \
				+ "Unknown return value type: " \
				+ str( o_return_type ) + "."
		raise Exception( s_msg )
	#end if return is a tuple, else string, else error

	return b_is_nothing 
#end dialog_returns_nothing

def convert_genepop_files_string_to_list_format( s_genepop_files ):	
		'''
		pgguineestimator object stores genepop files as a single string.
		Each genepop file is delimited by a comma.  This def will
		format the string to s_formatted_list, so that pgdriveneestimator.py can 
		execute eval( s_formatted_list) and retrieve a python list of file names.
		'''
		ls_files=s_genepop_files.split( "," )

		ls_quoted_file_names=[ "'" + s_file + "'" for s_file in ls_files ]

		s_quoted_files=",".join( ls_quoted_file_names )

		s_genepop_files_formatted_as_python_list= "[" + s_quoted_files + "]"

		return s_genepop_files_formatted_as_python_list
#end convert_genepop_files_string_to_list_format

def run_driveneestimator_in_new_process( o_multiprocessing_event,
										s_genepop_files,
										qs_sample_scheme_args,
										f_min_allele_freq,
										b_monogamy,
										i_replicates,
										qs_loci_sampling_scheme_args,
										i_loci_replicates,
										i_num_processes,
										s_runmode,
										s_nbne_ratio,
										s_do_nb_bias_adjustment,
										s_outfile_basename,
										s_temporary_directory_for_estimator,
										s_file_delimiter="," ):
	'''
	Similar to def above, "do_simulation_reps_in_subprocesses," this def is called from a
	PGGuiNeEstimator instance, in def runEstimator(), which first spawns
	a python multiprocessing.Process, which targest this def, and provides
	it with the multiprocessing.Event that will signal it to abort and cleanup
	(see above).

	This def is simpler than the do_simulation_reps_in_subprocesses def, however, in that it
	spawns only a single OS process, that calls python to execute pgdriveneestimator.py,
	which itself multiplexes the NeAnlaysis of multiple genepop files and (likely) multiple
	pops per file using python.multiprocessing.Process objects.


	2018_03_15.  We add the flag b_monogamy to the arg set, to assign it to LDNe2's
	monomgamy boolean parameter (see pgdriveneestimator.py, def __add_to_set_of_calls, etc.
	'''

	try:

		s_os_plaform_name=platform.system()
		
		#if we're on windows, file
		#paths may be a mangled mix of unix and 
		#windows separators -- with errors resulting
		#downstream.  So we standardize:
		if s_os_plaform_name == "windows":

			ls_current_file_list=s_genepop_files.split( s_file_delimiter )
			ls_new_file_list=[]
			for s_file in ls_current_file_list:
				ls_new_file_list.append( fix_windows_path( s_file ) )
			#end for each file
			
			#replace orig arg with new "fixed" file paths
			s_genepop_files=",".join( ls_new_file_list )

			#also need to fix outile path:
			s_outfile_basename = fix_windows_path( s_outfile_basename )
		#end if windows, fix file path strings

		#get the correct format for pgdriveneestimator.py's file name parsing alg:
		s_genepop_files_formatted_as_python_list= \
				convert_genepop_files_string_to_list_format( s_genepop_files )

		#caller, assumed to be a pgguineestimator instance,
		#will have "default" for the runmode val, 
		#when no extra output is desired, and multiprocessing is also
		#desired.  We convert to the proper term used by pgdriveneestimator.py
		#to designate this type of run:
		#2016_11_26 -- while a bug in the parallel processing of ne estimates
		#is being solved, we're now offering in the gui the two modes "serial"
		#and "parallel", and recommending "serial"
		if s_runmode=="default":
			s_runmode="no_debug"
		elif s_runmode=="serial":
			s_runmode="no_debug_serial"
		elif s_runmode =="parallel":
			s_runmode="no_debug"
		#end if runmode needs translating for the drive

		#Make of a single sequence of strings.
		qs_files_args=( s_genepop_files_formatted_as_python_list, ) 

		#join tuples of arguments in the proper order
		#for the call to pgdriveneestimator.py:
		'''
		2018_03_15. The arg set now includes b_monogamy, 
		to send a value for the LDNe2 param Monogamy.
		'''
		seq_arg_set=qs_files_args \
						+ qs_sample_scheme_args \
						+ ( str( f_min_allele_freq ), str( b_monogamy), str( i_replicates ) ) \
						+ qs_loci_sampling_scheme_args \
						+ ( str( i_loci_replicates ), str( i_num_processes ), s_runmode, s_nbne_ratio, s_do_nb_bias_adjustment ) 

		s_main_output_filename=s_outfile_basename + "." \
				+ NE_ESTIMATION_MAIN_TABLE_FILE_EXT

		s_secondary_output_filename=s_outfile_basename + "." \
				+ NE_ESTIMATION_SECONDARY_OUTPUT_FILE_EXT

		if is_windows_platform():
			s_main_output_filename=fix_windows_path( s_main_output_filename )
			s_secondary_output_filename=fix_windows_path( s_secondary_output_filename )
			s_temporary_directory_for_estimator=fix_windows_path( s_temporary_directory_for_estimator )
		#end if windows, fix paths

		'''
		2017_03_27.  The call now has an appended argument that
		gives the name of a temporary directory inside of which
		the pgdriveneestimator def do_estimate will write intermediate
		genepop files.  This name will be knowsn to the caller to
		run_driveneestimator_in_new_process, and so can delete
		its contents after the estimation code is run.
		'''
		seq_arg_set += ( s_main_output_filename,
								s_secondary_output_filename, 
								s_temporary_directory_for_estimator )

		'''
		2017_05_31.  We now add an argument that activates gui messaging.
		'''
		seq_arg_set += ( "True", )


		'''
		2017_02_20.  We check the set of arguments for total command length.
		So that it will not be mis-processed by Windows,
		and generate a WindowsError "The parameter is incorrect,"  
		we call a def to correct the command, if it is too long.  In any case
		it sends us the name of the correct def to call in in pgdriveneestimator.py 
		(mymain or mymainlongfilelist), and a (possibly altered), final arg set
		tuple.  It also returns the name of the temp file (None if no file written),
		so that we can remove it after the subprocess has completed.
		'''
		seq_final_arg_set, s_pgdriveneestimator_main_def_to_call, s_temp_file_for_long_genepop_file_list =\
				replace_genepop_file_list_arg_with_file_name_if_list_too_long( seq_arg_set,
																				s_main_output_filename )

		o_subprocess=call_driveneestimator_using_subprocess( seq_final_arg_set, 
											s_main_def_to_call=s_pgdriveneestimator_main_def_to_call )

		'''
		This def loops while calling poll() and tests timeout value, currently
		(2016_12_02)large enough to be irrelevant.  It also checks for the 
		callers multiprocessing.event.set(), and kills the subprocess
		and its children in event.set(), then calls even.clear():
		self.__temporary_directory_for_estimator=None
		'''
		manage_driveneestimator_subprocess( o_subprocess, o_multiprocessing_event )

		if s_temp_file_for_long_genepop_file_list is not None:
			try:
				'''
				02/21/2017 I have not yet been able to figure out why 
				Windows claims the file is being used by another process.
				This stop-gap will at least inform the user of the file
				and that it is temporary, but failed to disappear. Note 
				that we avoid throwing an exception, so that the GUI can
				finish up as though an Nb estimation process completed
				normally.
				'''
				os.remove( s_temp_file_for_long_genepop_file_list )
			except Exception as oex:
				s_msg="Warning:  a temporary file, " + s_temp_file_for_long_genepop_file_list \
								+ ", was created to handle a large list of genepop files.  The program " \
								+ "was not able to remove the file, and raised an exception with a message: " \
								+ str( oex ) + ".  The file is not needed and can be deleted." 
				show_warning_in_messagebox_in_new_process( s_msg )	
			#end try...except
		#end if we've made a file to hold a very long list of genepop files

	except Exception as oex:

		'''
		The calling GUI tests for this event's set status.
		If it finds set, it will reset the GUI to show
		the estimation has halted.
		'''
		if o_multiprocessing_event is not None:
			o_multiprocessing_event.set()
		#end if we have a non-None event object
		

		show_error_in_messagebox_in_new_process( oex, 
				s_msg_prefix = "Error caught by pgutilities, "
								+ "def run_driveneestimator_in_new_process." )
		raise oex
	#end try...except...

	return
#end run_driveneestimator_in_new_process


def replace_genepop_file_list_arg_with_file_name_if_list_too_long( seq_arg_set,
																s_main_output_filename ):
	'''
	2017_02_20.  We found a limitiation in Windows ability to invoke a 
	pOpen command if the command exceeds some N number of characters,
	N seemingly on the order of 10^4.  Exceeded, the "long" command 
	fails and windows throws a WindowsError with the usual non-informative
	message, in this case "The parameter is incorrect."

	We test our command length.  We assume the first argumane, the list
	of genepop files, is the the longest by far, and so we write the
	list string to a temp file, and use the file name as the first argument,
	in place of the list string.  We signal the change by returning the name
	of the (new) def in module pgdriveneestimator.py that will expect the
	tempfile name, and process the first arg accordingly.

	arg s_main_output_filename is used to get the output file directory path,
	so that, if we need to write a temporary file, we can do so in the output
	directory, rather than the current.

	We assume:
		--the s_main_output_filename argument has an absolute path.	
		--even if we're in a windows environment, that the path in the 
		s_main_output_filename uses unix path separators (see the windows 
		path fix in def fix_windows_path(), which is called in def 
		run_driveneestimator_in_new_process.
	'''

	GENEPOP_FILE_LIST_ARG_INDEX=0
	
	'''
	This threshold may need to be adjusted upwards.
	Inexact tests in Windows 10 showed the command 
	fails if its length is over N characters, with 
	N somethere in the range 29,000 to 32,000.
	'''
	MAX_CHARS_IN_COMMAND_WITHOUT_REDUCING=3e4

	ALTERNATE_DEF_FOR_LONG_FILELIST="mymainlongfilelist"
	DEFAULT_DEF_TO_CALL="mymain"

	s_def_in_pgdriveneestimator_to_call=None

	'''
	We pass this back to caller,
	so that caller can delete the temp
	file after the call to 
	pgdriveneestimator:
	'''
	s_temp_file_name=None

	s_path_separator="/"

	i_tot_chars_in_current_command=sum( [ len( s_arg ) for s_arg in seq_arg_set ] )

	seq_new_arg_set=None

	if i_tot_chars_in_current_command > MAX_CHARS_IN_COMMAND_WITHOUT_REDUCING:

		s_output_directory=os.path.dirname( s_main_output_filename )

		#Returns a duple, int file descriptor, and str file name:
		tup_tempfile=tempfile.mkstemp( dir=s_output_directory )

		s_temp_file_name=tup_tempfile[ 1 ]

		if is_windows_platform():
			s_temp_file_name=fix_windows_path( s_temp_file_name )
		#end if windows, standardize the path


		o_temp_file=open( s_temp_file_name, 'w' )

		o_temp_file.write( seq_arg_set[ GENEPOP_FILE_LIST_ARG_INDEX ] + "\n" )

		o_temp_file.close()
		
		#Replace the current genepopfile list argument
		#with the temp file name.

		#We take this step in case the genepop file list
		#Is moved from its position as the first argument
		#to pgdriveneestimator.mymain().
		#As arg[0], this assigns an emtpy tuple:
		tup_args_before_genepop_file_list=seq_arg_set[ 0 : GENEPOP_FILE_LIST_ARG_INDEX ]
		tup_args_after_genepop_file_list=seq_arg_set[ GENEPOP_FILE_LIST_ARG_INDEX + 1 : ]
		seq_new_arg_set=tup_args_before_genepop_file_list \
									+ ( s_temp_file_name, ) \
									+ tup_args_after_genepop_file_list

		s_def_in_pgdriveneestimator_to_call=ALTERNATE_DEF_FOR_LONG_FILELIST
	else:
		seq_new_arg_set=seq_arg_set
		s_def_in_pgdriveneestimator_to_call=DEFAULT_DEF_TO_CALL 
	#end if the command arg is too long, else not
		
	return seq_new_arg_set, s_def_in_pgdriveneestimator_to_call, s_temp_file_name
#end def replace_genepop_file_list_arg_with_file_name_if_list_too_long

def get_add_path_statment_for_popen():
	'''
	This def creates a string that is a
	path path.append statement.  It uses the 
	absolute path of the current module.
	It is used to add all the project modules
	to the path, since we assume this module
	is in the same directory as all of the 
	project files.
	'''
	s_path_append_statement=None

	s_curr_mod_path = os.path.abspath(__file__)

	#path only (stripped off "/utilities.py" )
	#-- gives path to all negui mods:
	s_mod_dir=os.path.dirname( s_curr_mod_path )

	'''
	Found that windows python would claim no such
	module found in the import agestrucne.pgguiutilities 
	statment, unless I replaced the windows os.sep
	char with linux "/".
	'''
	if is_windows_platform():
		s_mod_dir=fix_windows_path( s_mod_dir )
	#end if windows platform


	s_path_append_statement="import sys; sys.path.append( \"" \
					+ s_mod_dir + "\" );"

	return s_path_append_statement
#end get_add_path_statment_for_popen

def call_driveneestimator_using_subprocess( seq_arg_set, s_main_def_to_call="mymain" ):

	'''
	2017_02_20.  We add param s_main_def_to_call to resolve
	a bug in windows, whereby if the genepop file list is too long,
	windows can't correctly invoke the command.  In such cases
	we write the file list to a temp file, and call mymainlongfilelist instead
	of mymain.  We retain the former in case a more graceful handling of
	the long command string becomes possible.
	'''

	QUOTE="\""
	s_path_statement=get_add_path_statment_for_popen()

	s_import_statement="import agestrucne.pgdriveneestimator as pgd;"

	s_arg_list=( QUOTE +"," + QUOTE ).join( seq_arg_set )
	s_arg_list=QUOTE + s_arg_list + QUOTE

	

	s_call_statement="pgd." + s_main_def_to_call \
								+ "(" + s_arg_list + ");" 

	s_command=s_path_statement + s_import_statement + s_call_statement

	'''
	We use psutil version of Popen.  Having struggled with NeEstimation hangs and orphan using
	multiprocessing.Process objects, the psutil version seems better able to perform for this 
	chore.  This from the docs for psutil module:
			"A more convenient interface to stdlib subprocess.Popen. It starts a sub process 
			and you deal with it exactly as when using subprocess.Popen but in addition it also 
			provides all the methods of psutil.Process class. For method names common to both 
			classes such as send_signal(), terminate() and kill() psutil.Process implementation 
			takes precedence. For a complete documentation refer to subprocess module documentation.
			Unlike subprocess.Popen this class preemptively checks whether PID has been reused on 
			send_signal(), terminate() and kill() so that you can't accidentally terminate another
			process, fixing http://bugs.python.org/issue6973."
	'''
	o_subprocess=psutil.Popen( [ PYEXE_FOR_POPEN, "-c", s_command ] )

	return o_subprocess
#end call_driveneestimator_using_subprocess

def manage_driveneestimator_subprocess( o_subprocess, o_multiprocessing_event ):
	'''
	This def uses an absolute time out, and a looping check of the 
	passed subprocess poll(). On each iteration it also checks
	for a set()==True of the multiprocessing event, indicating a
	request from the GUI to kill the process (and its children).
	'''
	if VERBOSE:
		print( "In pgutilities.py, def manage_driveneestimator_subprocess, " \
							+ "entered def with subprocess, " \
							+ str( o_subprocess ) + ", and event, "  \
							+ str( o_multiprocessing_event ) + "."  )
	#end if VERBOSE

	f_start_run=time.time()

	SLEEPTIMELOOP=3

	'''
	Originally, we used a MAX running time
	limit when we were using a multiprocess.Process
	to drive the pgdriveneestimator.py, but
	found that long runs vs hands were very difficult
	to distinguish between.  We've seen no hangs
	since switching to a subprocess.  This fact,
	plus the difficult in deciding when a run
	has hung vs a very large data set, suggests
	that we should, as of 2016_12_23, for now 
	apply what amounts to no time limit.

	'''

	MAX_HOURS_PER_RUN=100000
	TIMEOUT=60*60*MAX_HOURS_PER_RUN

	while ( o_subprocess.poll() is None ) \
						and ( time.time() - f_start_run ) < TIMEOUT:

		if o_multiprocessing_event is not None:
			if o_multiprocessing_event.is_set():

				i_pid_subproc=o_subprocess.pid

				#kill the child processes:
				for o_proc in psutil.process_iter():
					if o_proc.pid == i_pid_subproc:
						for o_child_proc in o_proc.children():
							o_child_proc.kill()
						#end for each child
				#end for each process

				#With children killed, now we kill the parent:
				o_subprocess.kill()

				if VERBOSE:
					print( "In pgutilities.py, def manage_driveneestimator_subprocess, " \
								+ "after main Ne estimator subprocess kill(), " \
								+ "result of calling process.is_running(): " \
								+ str( o_subprocess.is_running() )  + "." )
				#end if VERBOSE

				o_multiprocessing_event.clear()
				break;
			#end if event is set
		#end if we have multiproc evennt

		time.sleep ( SLEEPTIMELOOP )
		if VERBOSE:
			print( "In pgutilities.py, def manage_driveneestimator_subprocess, " \
						+ "Popen poll: " + str( o_subprocess.poll() ) ) 
			print( "In pgutilities.py, def manage_driveneestimator_subprocess, " \
						+ "in loop waiting for poll() is not None or timeout" )
		#end if verbose
	#end while running

	return
#end manage_driveneestimator_subprocess

def get_subsample_value_filtered_ne_estimates_table_file( s_estimates_table_file,
															s_pop_subsample_value,
															s_loci_subsample_value ):
	'''
	If the value of sither param s_pop_subsample_value or s_loci_subsample_value is not 
	None, these are used to filter the estimates table given by param s_estimates_table_file.

	This def returns the name of a file that gives the filtered table.

	Assumtions: Either s_pop_subsample_value or s_loci_subsample_value are non None,
				otherwise, this def simply rewrites the original table file to the new
				file name
	'''
	o_ne_estimates_file_manager=NeEstimationTableFileManager( s_estimates_table_file )

	if s_pop_subsample_value is not None:
		o_ne_estimates_file_manager.setFilter( 'sample_value', lambda x : x == s_pop_subsample_value ) 
	#end if there is a pop subsample value

	if s_loci_subsample_value is not None:
		o_ne_estimates_file_manager.setFilter( 'loci_sample_value' , lambda x : x == s_loci_subsample_value )
	#end if we have a loci subsample value

	s_current_dir=os.path.abspath( os.curdir )

	#Returns a duple, int file descriptor, and str file name:
	tup_tempfile=tempfile.mkstemp( dir=s_current_dir )

	s_temp_file_name=tup_tempfile[ 1 ]

	o_tempfile=open( s_temp_file_name, 'w' )

	o_ne_estimates_file_manager.writeFilteredTable( o_tempfile )

	o_tempfile.close()

	return s_temp_file_name
#end get_subsample_value_filtered_ne_estimates_table_file

def call_plotting_program_in_new_subprocess( s_type, s_estimates_table_file, 
														s_plotting_config_file, 
														s_pop_subsample_value,
														s_loci_subsample_value,
														o_multiprocessing_event ):
	try:

		s_temp_file_for_filtered_table=None

		#If we've been passed any non-None subsample values, we
		#need to use a filtered table file:
		if [ s_pop_subsample_value, s_loci_subsample_value ] != [ None, None ]:

			s_temp_file_for_filtered_table=get_subsample_value_filtered_ne_estimates_table_file( s_estimates_table_file,
																			s_pop_subsample_value,
																			s_loci_subsample_value )
			#and we use the temp file as our table for plotting.
			s_estimates_table_file=s_temp_file_for_filtered_table
		#end if one or more of the subsample values is not None

		s_curr_mod_path = os.path.abspath(__file__)

		#path only (stripped off "/utilities.py" )
		#-- gives path to all negui mods:
		s_mod_dir=os.path.dirname( s_curr_mod_path )

		'''
		I Found that windows python would claim no such
		module found in the import agestrucne.pgguiutilities 
		statement, unless I replaced the windows os.sep
		char with linux "/". Also, note the conversion
		of the ts and config file args, too.  In that
		case, the Windows sep char will act like an escape
		and was in some cases splitting the file path where
		it encounted a \t or an \n.
		'''
		if is_windows_platform():
			s_mod_dir=fix_windows_path( s_mod_dir )
			s_estimates_table_file=fix_windows_path( s_estimates_table_file )
			s_plotting_config_file=fix_windows_path( s_plotting_config_file )
		#end if windows platform

		s_path_append_statement="import sys; sys.path.append( \"" \
						+ s_mod_dir + "\" );"

		s_import_statement="import agestrucne.pgutilities as pgu;"

		s_quoted_plot_type="\"" + s_type + "\""

		s_quoted_ne_file="\"" + s_estimates_table_file + "\""

		s_quoted_config_file="\"" + s_plotting_config_file + "\""

		s_command_statement=\
				"pgu.run_plotting_program( " \
				+ s_quoted_plot_type + "," \
				+ s_quoted_ne_file + "," \
				+ s_quoted_config_file + ");" \

		s_python_command=s_path_append_statement + s_import_statement + s_command_statement

		o_subprocess=subprocess.Popen( [ PYEXE_FOR_POPEN, "-c" , s_python_command ] )

		manage_plotting_program_subprocess( o_subprocess, o_multiprocessing_event )

		#We remove the temp file if we used one for filtered results:
		if s_temp_file_for_filtered_table is not None:
			os.remove( s_temp_file_for_filtered_table )
		#end if we used a temp file

	except Exception as oex:
		show_error_in_messagebox_in_new_process( oex, s_msg_prefix="In pgutilities.py, " \
						+ "def call_plotting_program_in_new_subprocess" )
		raise( oex )
	#end try...except
	return	
#end call_plotting_program_in_new_subprocess

def manage_plotting_program_subprocess( o_subprocess, o_multiprocessing_event ):
	'''
	This def is called by def call_plotting_program_in_new_subprocess,
	and loops while waiting for either the death (presumably by completion
	of the plotting taskes) of the subprocess that is executing def 
	run_plotting_program, or finds a True value for the multiprocessing event 
	"is_set()", in which case the plotting subprocess is killed.

	The multiprocessing event is presumably set by the GUI, which itself
	has called def call_plotting_program_in_new_subprocess, and indicates
	a user or GUI-determined decision to cancel the plotting tasks.
	'''

	if VERBOSE:
		print( "In pgutilities.py, def manage_plotting_program_subprocess, " \
							+ "entered def with subprocess, " \
							+ str( o_subprocess ) + ", and event, "  \
							+ str( o_multiprocessing_event ) + "."  )
	#end if VERBOSE

	f_start_run=time.time()

	SLEEPTIMELOOP=1

	#For now we apply essentially
	#no time limit
	MAX_HOURS_PER_RUN=100000
	TIMEOUT=60*60*MAX_HOURS_PER_RUN

	while ( o_subprocess.poll() is None ) \
						and ( time.time() - f_start_run ) < TIMEOUT:

		if o_multiprocessing_event is not None:
			if o_multiprocessing_event.is_set():

				i_pid_subproc=o_subprocess.pid

				#kill the child processes:
				for o_proc in psutil.process_iter():
					if o_proc.pid == i_pid_subproc:
						for o_child_proc in o_proc.children():
							o_child_proc.kill()
						#end for each child
				#end for each process

				#With children killed, now we kill the parent:
				o_subprocess.kill()

				if VERBOSE:
					print( "In pgutilities.py, def manage_plotting_program_subprocess, " \
								+ "after  subprocess kill(), " \
								+ "result of calling process.is_running(): " \
								+ str( o_subprocess.is_running() )  + "." )
				#end if VERBOSE

				o_multiprocessing_event.clear()
				break;
			#end if event is set
		#end if we have multiproc evennt

		time.sleep ( SLEEPTIMELOOP )
		if VERBOSE:
			print( "In pgutilities.py, def manage_plotting_program_subprocess, " \
						+ "Popen poll: " + str( o_subprocess.poll() ) ) 
			print( "In pgutilities.py, def manage_plotting_program_subprocess, " \
						+ "in loop waiting for poll() is not None or timeout" )
		#end if verbose
	#end while running

	return
#end manage_driveneestimator_subprocess

def run_plotting_program( s_type, s_estimates_table_file, s_plotting_config_file ):

	try:

		if is_windows_platform():
			s_estimates_table_file=fix_windows_path( s_estimates_table_file )
			s_plotting_config_file=fix_windows_path( s_plotting_config_file )
		#end if windows platform, fix path

		if s_type == "Regression":

			import agestrucne.asnviz.LineRegress
			
			'''
			2017_01_23 We use the newer def "runNe", which Brian T created
			to replace the double call, to neGrapher and neStats, 
			formerly required to get plots and then a stats file.
			'''
			agestrucne.asnviz.LineRegress.neRun( s_estimates_table_file, s_plotting_config_file )
		elif s_type == "Subsample":

			import agestrucne.asnviz.SubSamplePlot

			agestrucne.asnviz.SubSamplePlot.subSamplePlotter( s_estimates_table_file, s_plotting_config_file  )

		else:
			s_msg = "In pgutilities.py, def run_plotting_program, " \
							+ "unknown plot type: " + s_type  + "."
			raise Exception( s_msg )
		#end if type is regression, else...
	except Exception as oex:
		o_traceback=sys.exc_info()[ 2 ]
		s_err_info=get_traceback_info_about_offending_code( o_traceback )
		s_prefix="In pgutilities.py " \
						+ "def, run_plotting_program, " \
						+ "An exception was caught, with origin:\\n" \
						+ s_err_info + "\\n"

		'''
		For sending the string into a new process,  we need to escape 
		any quotes in the error message:
		'''
		s_prefix=s_prefix.replace( "\"", "\\\""	)
		show_error_in_messagebox_in_new_process( oex, s_msg_prefix=s_prefix )
		raise ( oex )
	#end try...except
	return
#end run_plotting_program

def show_error_in_messagebox_in_new_process( o_exception, s_msg_prefix=None ):
	
	s_errortype= o_exception.__class__.__name__
	s_msg=str( o_exception ).replace( "\n", "  " )	

	s_msg=s_msg.replace( "\"", "" )

	s_errormsg=s_errortype + ", " + s_msg

	#prepend a prefix if caller supplied one.
	if s_msg_prefix is not None:
		s_errormsg=s_msg_prefix + "\\n" + s_errormsg
	#end if we have a prefix

	s_curr_mod_path = os.path.abspath(__file__)

	#path only (stripped off "/utilities.py" )
	#-- gives path to all negui mods:
	s_mod_dir=os.path.dirname( s_curr_mod_path )

	'''
	Found that windows python would claim no such
	module found in the import agestrucne.pgguiutilities 
	statment, unless I replaced the windows os.sep
	char with linux "/".
	'''
	if is_windows_platform():
		s_mod_dir=fix_windows_path( s_mod_dir )
	#end if windows platform


	s_path_append_statements="import sys; sys.path.append( \"" \
						+ s_mod_dir + "\" );"

	s_import_statement="from agestrucne.pgguiutilities import PGGUIErrorMessage;"

	s_gui_statement="PGGUIErrorMessage( s_message=\"" + s_errormsg  + "\" )"


	s_command=s_path_append_statements + s_import_statement + s_gui_statement

	subprocess.Popen( [ PYEXE_FOR_POPEN, "-c" , s_command ] )

#end show_error_in_messagebox_in_new_process

def show_warning_in_messagebox_in_new_process( s_warning_msg):
	
	s_curr_mod_path = os.path.abspath(__file__)

	#path only (stripped off "/utilities.py" )
	#-- gives path to all negui mods:
	s_mod_dir=os.path.dirname( s_curr_mod_path )

	'''
	Found that windows python would claim no such
	module found in the import agestrucne.pgguiutilities 
	statment, unless I replaced the windows os.sep
	char with linux "/".
	'''
	if is_windows_platform():
		s_mod_dir=fix_windows_path( s_mod_dir )
	#end if windows platform


	s_path_append_statements="import sys; sys.path.append( \"" \
						+ s_mod_dir + "\" );"

	s_import_statement="from agestrucne.pgguiutilities import PGGUIWarningMessage;"

	s_gui_statement="PGGUIWarningMessage( o_parent=None,  s_message=\"" + s_warning_msg  + "\" )"


	s_command=s_path_append_statements + s_import_statement + s_gui_statement

	subprocess.Popen( [ PYEXE_FOR_POPEN, "-c" , s_command ] )

#end show_warning_in_messagebox_in_new_process


def remove_non_existent_paths_from_path_variable():
	'''
	I needed to make PATH environmental variables
	that have no (old paths to discarded locations)
	non-existing paths.  The ne2.controller module's
	ne estimator controller class in the pygenomics
	package iterates over the PATH variable paths, 
	and uses each path qua existing path without
	checking whether it exists.
	'''
	ls_paths_that_exist=[]

	IX_NAME="posix"
	WINDOWS_NAME="nt"

	LINUX_PATH_VAR="PATH"
	WINDOWS_PATH_VAR="PATH"

	s_paths=None

	if os.name=="posix":
		s_var_name=LINUX_PATH_VAR
	elif os.name=="nt":
		s_var_name=WINDOWS_PATH_VAR
	else:
		raise Exception( "In def confirm_executable_is_in_path, Unrecognized OS name: " + os.name )
	#end if posix else if nt, else unknown

	s_paths=os.environ.get( s_var_name )

	ls_paths=s_paths.split( os.pathsep )
	
	for s_path in ls_paths:
		if os.path.exists( s_path ):
			ls_paths_that_exist.append( s_path )
		#end if executable
	#end for each path in PATH

	#Reset the path variable to only those paths in its
	#current set, that exist as real OS paths:
	os.environ[  s_var_name ]=os.pathsep.join( ls_paths_that_exist )

	return
#end remove_non_existent_paths_from_path_variable

def get_subsample_values_lists_from_tsv_file( s_tsv_file ):
	'''
	For the given tsv file giving an Ne estimate table output by
	pgdriveneestimator.py, we return a dictionary with keys, 
	"pop" and "loci", giving a list of string versions of the subsample
	values for each.
	'''
	ls_pop_subsample_values=None
	ls_loci_subsample_values=None
	o_ne_file=NeEstimationTableFileManager( s_tsv_file )

	ls_pop_subsample_values=o_ne_file.pop_sample_values
	ls_loci_subsample_values=o_ne_file.loci_sample_values

	return { "pop":ls_pop_subsample_values,
				"loci":ls_loci_subsample_values }
#end get_subsample_values_lists_from_tsv_file

def return_when_def_is_true( def_with_boolean_return, dv_args=None, f_sleeptime_in_seconds=0.05 ):
	'''
	This def returns when the call to the def given by the first arg
	returns True.

	Param def_to_test, ref to ta def that returns True or false.
	Param args, a dict of the arguments needed (keys are param
		names, values are the args for each param).  If set to (default)
		None, then no args are passed to the def.
	Param i_sleeptime.  Sleep interval, in seconds, between calls to the arg.
	'''

	while not call_with_or_without_args( def_with_boolean_return, dv_args ):	
		time.sleep( f_sleeptime_in_seconds )
	#end while return is False

	return

#end return_when_def_is_true

def get_traceback_info_about_offending_code( o_traceback_object ):
	'''
	2017_04_27
	This def was created to help trace errors in the
	pgdriveneestimator.py module that are caught by
	the def do_estimate, which is running on a separate
	process a map_async call, and so tracebacks are not spilled to
	stdout.
	'''

	s_msg=""

	TOTAL_FIELDS=4

	IDX_FILE=0
	IDX_LINE_NUM=1
	IDX_DEF=2
	IDX_TXT=3

	ls_categories=[ "file", "line", "function", "text" ]

	l_tup_trace=traceback.extract_tb( o_traceback_object )

	'''
	We want the last tuple in the traceback list:
	'''

	ls_fields=[]
	if len ( l_tup_trace ) > 0:
		i_last_idx=len( l_tup_trace ) - 1
		tup_info=l_tup_trace[ i_last_idx ]
		ls_fields.append( tup_info[ IDX_FILE ] ) 
		ls_fields.append( str( tup_info[ IDX_LINE_NUM ] ) )
		ls_fields.append( tup_info[ IDX_DEF ]  )
		ls_fields.append( tup_info[ IDX_TXT ] ) 
	else:
		ls_fields=[ "no_info" for idx in range( TOTAL_FIELDS ) ]
	#end if we have info
	s_combined_info=[]

	for idx in range( TOTAL_FIELDS ):
		s_combined_info.append( ls_categories[idx] + ": " + ls_fields[idx] )
	#end for each field

	s_msg=", ".join( s_combined_info )

	return s_msg
#end get_traceback_info_about_offending_code

def call_with_or_without_args( def_to_call, dv_args ):
	'''
	Helper for def return_when_def_is_true.
	This def checks dv_args and if its value is None,
	it calls param def_to_call without any arguments,
	otherside calls with dv_args as param list,
	key=paramater name, value=paramater value.
	'''

	if dv_args is None:
		return ( def_to_call() )
	else:
		return ( def_to_call( **dv_args ) )
	#end if no args, else args present

#end call_with_or_without_args

def get_current_python_executable():
	s_path=sys.executable
	return s_path
#end get_current_python_executable

def get_memory_virtual_available():
	tup_meminfo=psutil.virtual_memory()
	return tup_meminfo.available
#end get_memory_virtual_available

def get_roots_quadratic( f_a, f_b, f_c ):

	lf_roots=[]

	for i_coeff in [ 1, -1 ]:
		#quadratic equation
		try:
			lf_roots.append( ( -f_b + i_coeff * npsqrt( f_b**2 - 4*f_a*f_c ) )/2*f_a ) 
		except Exception as oex:

			if i_coeff==1:
				s_formula="( -b + sqrt( b^2 - 4ac ) )/2a"
			else:
				s_formula="( -b - sqrt( b^2 - 4ac ) )/2a"
			#end if adding top 2 terms, else subtraction

			s_msg="In pgutilities, def get_roots_quadratic, error calculating root, " \
						+ "with a = " + str( f_a ) + ", b = " + str( f_b ) + ", c = " \
						+  str( f_c ) + ", and using formula: "  + s_formula + ".\n" \
						+ "Exception thrown with message: " + str( oex ) + "."
			raise Exception( s_msg )
	#end for each sign

	return lf_roots

#end get_roots_quadratic

def get_dirichlet_allele_dist_for_expected_het( f_expected_het,  
													i_num_alleles, 
														f_tolerance=0.001 ):
	'''
	Heuristic uses the dirichlet distribution to find a set
	of i_num_alleles allele frequencies whose expected heterozygosity
	is within f_tolerance of f_expected_het.

	The alpha value assignment determined by the ranges seen below
	was constructed using trials, using script testdiri.py (in our
	programs supplementary_scripts directory).
	'''

	lf_freqs=None

	TRIALS=3000
	MAX_TRIALS=10

	f_myalpha=None

	if f_expected_het < 0.0:
		s_msg="The program currently does not " \
					+ "generate allele frequencies " \
					+ "for an expected heterozygosity " \
					+ "of zero."
		raise Exception( s_msg )

	elif f_expected_het > 0.85:
		s_msg="The program currently does not " \
					+ "generate allele frequencies " \
					+ "for an expected heterozygosity " \
					+ "greather than 0.85."
		raise Exception( s_msg )
	elif f_expected_het <= 0.01:
		f_myalpha=0.01
	elif f_expected_het <= 0.3:
		f_myalpha=0.05
	elif f_expected_het <= 0.7:
		f_myalpha=0.1
	else:
		f_myalpha=0.5
	#end if expected het 0, else over max else...

	b_achieved_het=False
	for i_trial_number in range( MAX_TRIALS ):

		if b_achieved_het:
			break
		#end if done, break

		for i_trial in range( TRIALS ):
			lf_these_freqs=dirichlet( [ f_myalpha ] * i_num_alleles )
			f_het=1-( sum ( [ f_freq * f_freq for f_freq in lf_these_freqs ] ) )

			if abs( f_expected_het - f_het ) <= f_tolerance: 
				lf_freqs=lf_these_freqs
				b_achieved_het=True
				break
			#end if
		#end for each trial
	#end for each trial number

	return lf_freqs 
#end get_dirichlet_allele_dist_for_expected_het

if __name__ == "__main__":
	for het in  [ 0.001, 0.003, 0.2, 0.3, 0.45, 0.55, 0.65, 0.85 ]:
		print( str(het) + ":--------------" )	
		dl= get_dirichlet_allele_dist_for_expected_het( het, 10 ) 
		print( "calc het: " + str( 1 - sum( [ x*x for x in dl ] ) ) )
	#end for each het
#end if main


