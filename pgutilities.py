'''
Description
Support defs for the pop gen interface programs.
'''
from __future__ import absolute_import, division, print_function, unicode_literals

__filename__ = "pgutilities.py"
__date__ = "20160601"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os
import sys
import types
import copy_reg
import pgopsimupop as pgsim
import pgsimupopresources as pgrec
import pginputsimupop as pgin
import pgoutputsimupop as pgout
import pgparamset as pgpar
import pgdriveneestimator as pgne

import copy
import subprocess
import glob
import inspect
import time
import multiprocessing
import shutil

'''
psutil and signal are used below,
as tools for cancelling the subprocess
launched to do ne estimations. See def
run_driveneestimator_in_new_process.
'''
import signal
import psutil

#for def do_simulation_reps_in_subprocesses,
#used to detect windows, and 
#correct strings that give file paths:
import platform

from pgutilityclasses import IndependantSubprocessGroup 

VERBOSE=False

PYEXE_FOR_POPEN="python"
PROCESS_QUEUE_STOP_SIGN='STOP'
SIMULATION_OUTPUT_FILE_REPLICATE_TAG=".r"
DELIMITER_LIFE_TABLE_FILES=","

NE_ESTIMATION_MAIN_TABLE_FILE_EXT="ldne.tsv"
NE_ESTIMATION_SECONDARY_OUTPUT_FILE_EXT="ldne.msgs"

SYS_LINUX="linux"
SYS_WINDOWS="windows"
SYS_MAC="mac"

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

        if os.name=="posix":
            s_paths=os.environ.get( LINUX_PATH_VAR )
        elif os.name=="nt":
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
#
#def do_sim_replicate_on_separate_os_process( s_configuration_file,
#													s_life_table_files,
#													s_param_name_file,
#													s_outfile_basename,
#													s_replicate_number ):
#	
#	s_target_script="do_sim_replicate.py"
#	
#
#	subprocess.call( [ "python", s_target_script, 
#						s_configuration_file,
#						s_life_table_files, 
#						s_param_name_file, 
#						s_outfile_basename, 
#						s_replicate_number ] )
#	return
##end do_sim_replicate_on_separate_os_process
#

def prep_and_call_do_pgopsimupop_replicate( s_config_file, 
						s_life_table_files, 
						s_param_file, 
						s_output_base_name, 
						s_replicate_number ):
	'''	
	This def to be invoked in a subprocess.Popen command, as
	instantiated in a PGGuiSimuPop instance in do_operation.

	This def simply prepares the args for the call to def
	do_pgopsimupop_replicate_from_files (below).
	'''

	#de-stringify args for call to def below:
	ls_life_table_files = s_life_table_files.split( DELIMITER_LIFE_TABLE_FILES )
	i_replicate_number=int( s_replicate_number )

	do_pgopsimupop_replicate_from_files( s_config_file,
						ls_life_table_files,
						s_param_file,
						s_output_base_name,
						i_replicate_number )

	return
#end prep_and_call_do_pgopsimupop_replicate

def do_pgopsimupop_replicate_from_files(  s_configuration_file, 
												ls_life_table_files, 
												s_param_name_file, 
												s_outfile_basename, 
												i_replicate_number ):
	'''
	necessitated by fact that python2 (and 3?) was not able to pickle 
	a class-instance def to be used to run replicates of the pgopsimupop
	doOp().  Python also failed to pickle SWIG-based code used in Simupop.
	Thus the better design, in which  multiprocessing Pools would stay  encapsulated 
	inside a class object seem problematic, though may be implement-able using 
	reg_copy -- but I'm not confident in state of regcopy of imported simuPop code,
	and so  I think is the safer solution, though it
	does create a depandancy of the pgguisimupop object on this outside def.  

	Note that this def runs a simupop operation using all the param values as
	given in the config file arg, except for the "reps" attribute, with is reset to 1,
	whatever the value in the configuration file.

	Tue Jul 26 22:01:07 MDT 2016
	updated to be called by a driver that creates a new OS process, then calls this def to do the replicate.  No longer
	uses the dv_input_parm_values_by_attribute, but instead relies on reading a complete and up-to-date (i.e. all values
	as changed or edited on the gui interface) configuration files (that includes the "life table" params).
	'''

	s_tag_out=""

	NUMBER_FIRST_REPLICATE=1

	'''
	As of 2016_08_23 the *sim, *gen, *db files
	are not used, and clutter up the output directories,
	per other users comments
	'''

	#whether or not to remove the *sim *gen *db
	#files (original output from Tiago's code ), 
	#which leaves only a *conf and *genepop
	#files as output

	REMOVE_NON_GENEPOP_SIM_OUTPUT_FILES=True

	if i_replicate_number is not None:
		s_tag_out=SIMULATION_OUTPUT_FILE_REPLICATE_TAG + str( i_replicate_number )

	#end if rep number is not none

	o_resources=pgrec.PGSimuPopResources( ls_life_table_files )
	o_paramset=pgpar.PGParamSet( s_param_name_file )
	o_input=pgin.PGInputSimuPop( s_configuration_file, o_resources, o_paramset ) 
	o_input.makeInputConfig()

	b_write_conf_file=False

	#we only write the configuraton file if the replicate number is 1:
	if i_replicate_number == NUMBER_FIRST_REPLICATE:
		b_write_conf_file=True
	#end if first replicate number

	#reset reps to 1
	#as we are executing only one
	#replicate.  We assume this def
	#is being called as one of a number
	#of parallel process calls for
	#a set of replicates, the total 
	#known to the caller:
	o_input.reps=1

	o_output=pgout.PGOutputSimuPop( s_outfile_basename )

	o_new_pgopsimupop_instance=pgsim.PGOpSimuPop( o_input,
			o_output, 
			b_remove_db_gen_sim_files=REMOVE_NON_GENEPOP_SIM_OUTPUT_FILES,
			b_write_input_as_config_file=b_write_conf_file )

	o_new_pgopsimupop_instance.prepareOp( s_tag_out  )

	o_new_pgopsimupop_instance.doOp()

	return
#end do_pgopsimupop_replicate_from_files

def remove_simulation_replicate_output_files( s_basename ):
	'''
	When a sim is cancelled inside a PGGuiSimuPop
	object, this def is called
	to remove any output files produced by the
	do_pgopsimupop_replicate_from_files
	'''

	#type is to coerce python 3, despite fact that any iterable
	#would probably suffice:
	ls_output_extentions=list( \
			pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS.values() )

	for s_ext in ls_output_extentions:

		s_unzipped_file_pattern=s_basename + "*" \
				+ SIMULATION_OUTPUT_FILE_REPLICATE_TAG \
				+ "*" + s_ext

		ls_files_unzipped=glob.glob( s_unzipped_file_pattern )

		ls_files_zipped=glob.glob( s_unzipped_file_pattern \
				+ "." + pgout.PGOutputSimuPop.COMPRESSION_FILE_EXTENSION )

		for s_file in ls_files_unzipped + ls_files_zipped:
			os.remove( s_file )
		#end for each unzipped and zipped output file with this extension
	#end for each file ext

	return
#end remove_simulation_replicate_output_files

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
	elif "darwin" in s_os_plaform_name.lower():
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

def do_simulation_reps_in_subprocesses( o_multiprocessing_event,
			i_input_reps, 
			i_total_processes_for_sims,
			s_temp_config_file_for_running_replicates,
			ls_life_table_files,
			s_param_names_file,
			s_output_basename ):

	'''
	Failed to get independant initialization of population per-replicate
	when i used python's multiprocessing.process objects as hosts for 
	running replicates in parallel.  Solution as of now, 
	Sat Jul 30 22:38:42 MDT 2016, is to use OS processes via python's 
	subprocess module, creating them in this def, which gets its
	requisite info needed for the sim from the pgguisimupop instance
	that calls this def (this def is called by the GUI interface instance
	in a new python.multiprocessing.process instance, in order not to block the gui).

	Note that this def was originally inside the pgguisimupop instance that calls it,
	but on windows there was a pickling error not seen on linux or Mac.  Moving this
	target def for the python.multiprocessing.process outside the pgguisimupop instance
	seems to have solved the problem on windows (win 10).

	This def manages the replices via creating subprocesses, and 
	calling pgutilities.prep_and_call_do_pgopsimupop_replicate.

	'''	

	'''	
	Running this inside a try block allows us to notify GUI
	users of exceptions propogated from anywere inside the 
	simulation setup and execution code. When we catch exceptions 
	below, we send an error message to a gui message box, then
	re-raise the exception.	
	'''
	try:
		s_life_tables_stringified=",".join( ls_life_table_files )

		#if we're on windows, out strings of file
		#paths may be a mangled mix of unix and 
		#windows separators -- with errors resulting
		#downstream.  So we standardize:
		if is_windows_platform():
			s_life_tables_stringified= \
				fix_windows_path( s_life_tables_stringified )
			s_param_names_file= \
				fix_windows_path( s_param_names_file )				
			s_output_basename= \
				fix_windows_path( s_output_basename )	
		#end if windows, fix file path strings

		i_total_replicates_requested=i_input_reps

		i_max_processes_to_use=i_total_processes_for_sims


		#we use a python command for a -c arg in the Popen command (see below)
		#and these will be the same args for each replicate (we add the rep-number
		#arg below).  We stringify so that they can be Popen command args.  Some
		#are de-stringified by the pgutilities def before sending to pgop-creator
		seq_first_four_args_to_sim_call=( s_temp_config_file_for_running_replicates,
										s_life_tables_stringified,
										s_param_names_file,
										s_output_basename )
		
		i_total_replicates_started=0

		o_subprocess_group=IndependantSubprocessGroup()

		while i_total_replicates_started < i_total_replicates_requested:
			#see if we need to cancel:	
			if o_multiprocessing_event.is_set():

				if VERBOSE:
					print ( "received event in setup loop" )
				#end if VERBOSE

				o_subprocess_group.terminateAllSubprocesses()
				
				remove_simulation_replicate_output_files( s_output_basename )

				break

			else:

				i_number_subprocesses_alive=o_subprocess_group.getTotalAlive()

				i_number_subprocesses_available= \
						i_max_processes_to_use-i_number_subprocesses_alive

				i_number_replicates_to_go=i_total_replicates_requested - i_total_replicates_started

				i_number_subprocesses_to_start=i_number_subprocesses_available

				#reduce the number to start if we have fewer reps to go than avail procs:
				if i_number_subprocesses_available > i_number_replicates_to_go:
						i_number_subprocesses_to_start = i_number_replicates_to_go
				#end if fewer needed than available

				for idx in range( i_number_subprocesses_to_start ):

					i_total_replicates_started += 1
					
					#In the Popen call, rather than rely on a driver python script 
					#that would need to be in PATH, we'll simply
					#invoke python with a "-c" argument that imports the 
					#pgutilities module and executes the correct def:
			
					#complete the set of args used in the command by adding the
					#replicate number (recall need comma in sequence with single item,
					#to delineate sequence versus simple expression):
					seq_complete_arg_set=seq_first_four_args_to_sim_call + ( str( i_total_replicates_started ), )

					'''
					in case the negui mods are not in the default python 
					install dirs, then we need to add them to the sys.paths in
					any  spawned invocation of python exe -- seems that 
					the PYTHONPATH env var known to this parent process 
					is unknown to the "python" invocation via Popen.  
					We can get for and then add to our new python invocation
					the path to all negui modules by getting the
					path to this module:
					'''
					s_curr_mod_path = os.path.abspath(__file__)

					#path only (stripped off "/utilities.py" )
					#-- gives path to all negui mods:
					s_mod_dir=os.path.dirname( s_curr_mod_path )

					#need to fix the path if we're on windows:
					if is_windows_platform():
						s_mod_dir=fix_windows_path( s_mod_dir )
					#end if windows, fix path
					
					s_path_append_statements="import sys; sys.path.append( \"" \
							+ s_mod_dir + "\" );"

					s_python_command=s_path_append_statements + "import pgutilities;" \
										"pgutilities.prep_and_call_do_pgopsimupop_replicate" \
										+ "( \"%s\", \"%s\", \"%s\", \"%s\", \"%s\" )" %  seq_complete_arg_set

					o_new_subprocess=subprocess.Popen( [ PYEXE_FOR_POPEN, "-c", s_python_command ] )
					o_subprocess_group.addSubprocess( o_new_subprocess ) 
				#end for each idx of new procs
			#end if event is set else not
		#end while preplicates need to be started

		#we don't want to return untill all processes are done.
		#meantime test for cancel-request
		i_total_still_alive_after_creating_all=o_subprocess_group.getTotalAlive()

		while i_total_still_alive_after_creating_all > 0:
			if o_multiprocessing_event.is_set():

				if VERBOSE:
					print( "received event in final loop" )
				#end if verbose

				o_subprocess_group.terminateAllSubprocesses()
				remove_simulation_replicate_output_files( s_output_basename )
			#end if we are to cancel
			i_total_still_alive_after_creating_all=o_subprocess_group.getTotalAlive()
		#end while

	except Exception as oex:
		
		show_error_in_messagebox_in_new_process( oex, 
				s_msg_prefix = "Error caught by pgutilities, "
								+ "def __do_simulation_reps_in_subprocesses." )
		raise oex
	#end try...except...
	return
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
		b_is_nothing == ""
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
										i_replicates,
										qs_loci_sampling_scheme_args,
										i_loci_replicates,
										i_num_processes,
										s_runmode,
										s_outfile_basename,
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
	'''

	o_main_output=None
	o_secondary_output=None

	try:
		o_main_output=None
		o_secondary_output=None

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
		seq_arg_set=qs_files_args \
						+ qs_sample_scheme_args \
						+ ( str( f_min_allele_freq ), str( i_replicates ) ) \
						+ qs_loci_sampling_scheme_args \
						+ ( str( i_loci_replicates ), str( i_num_processes ), s_runmode ) 

		s_main_output_filename=s_outfile_basename + "." \
				+ NE_ESTIMATION_MAIN_TABLE_FILE_EXT

		s_secondary_output_filename=s_outfile_basename + "." \
				+ NE_ESTIMATION_SECONDARY_OUTPUT_FILE_EXT

		if is_windows_platform():
			s_main_output_filename=fix_windows_path( s_main_output_filename )
			s_secondary_output_filename=fix_windows_path( s_secondary_output_filename )
		#end if windows, fix paths

		seq_arg_set += ( s_main_output_filename,
								s_secondary_output_filename )

		o_subprocess=call_driveneestimator_using_subprocess( seq_arg_set )

		'''
		This def loops while calling poll() and tests timeout value, currently
		(2016_12_02)large enough to be irrelevant.  It also checks for the 
		callers multiprocesssing.event.set(), and kills the subprocess
		and its children in event.set(), then calls even.clear():
		'''
		manage_driveneestimator_subprocess( o_subprocess, o_multiprocessing_event )

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

def get_add_path_statment_for_popen():

	s_path_append_statement=None

	s_curr_mod_path = os.path.abspath(__file__)

	#path only (stripped off "/utilities.py" )
	#-- gives path to all negui mods:
	s_mod_dir=os.path.dirname( s_curr_mod_path )

	'''
	Found that windows python would claim no such
	module found in the import pgguiutilities 
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

def call_driveneestimator_using_subprocess( seq_arg_set ):

	QUOTE="\""
	s_path_statement=get_add_path_statment_for_popen()

	s_import_statement="import pgdriveneestimator as pgd;"

	s_arg_list=( QUOTE +"," + QUOTE ).join( seq_arg_set )
	s_arg_list=QUOTE + s_arg_list + QUOTE

	s_call_statement="pgd.mymain(" + s_arg_list + ");" 

	s_command=s_path_statement + s_import_statement + s_call_statement
	'''
	We use psuti version of Popen.  Having struggled with NeEstimation hangs and orphan processes,
	the psutil version seems better able to perform for this chore.  This from the docs for psutil
	module:
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
	if VERBOSE:
		print( "In pgutilities.py, def manage_driveneestimator_subprocess, " \
							+ "entered def with subprocess, " \
							+ str( o_subprocess ) + ", and event, "  \
							+ str( o_multiprocessing_event ) + "."  )
	#end if VERBOSE

	f_start_run=time.time()

	SLEEPTIMELOOP=3

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

def call_plotting_program_in_new_subprocess( s_type, s_estimates_table_file, 
														s_plotting_config_file, 
														o_multiprocessing_event ):
	try:

		s_curr_mod_path = os.path.abspath(__file__)

		#path only (stripped off "/utilities.py" )
		#-- gives path to all negui mods:
		s_mod_dir=os.path.dirname( s_curr_mod_path )

		'''
		Found that windows python would claim no such
		module found in the import pgguiutilities 
		statment, unless I replaced the windows os.sep
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

		s_import_statement="import pgutilities as pgu;"

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

	except Exception as oex:
		show_error_in_messagebox_in_new_process( oex, s_msg_prefix="In pgutilities.py, " \
						+ "def call_plotting_program_in_new_subprocess" )
		raise( oex )
	#end try...except
	return	
#enc call_plotting_program_in_new_subprocess


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

			import Viz.LineRegress
		
			Viz.LineRegress.neGrapher( s_estimates_table_file, s_plotting_config_file )
			Viz.LineRegress.neStats( s_estimates_table_file, s_plotting_config_file )
		elif s_type == "Subsample":

			import Viz.SubSamplePlot

			Viz.SubSamplePlot.subSamplePlotter( s_estimates_table_file, s_plotting_config_file  )

		else:
			s_msg = "In pgutilities.py, def run_plotting_program, " \
							+ "unknown plot type: " + s_type  + "."
			raise Exception( s_msg )
		#end if type is regression, else...
	except Exception as oex:
		show_error_in_messagebox_in_new_process( oex, s_msg_prefix="In pgutilities.py " \
						+ "def, run_plotting_program" )
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
	module found in the import pgguiutilities 
	statment, unless I replaced the windows os.sep
	char with linux "/".
	'''
	if is_windows_platform():
		s_mod_dir=fix_windows_path( s_mod_dir )
	#end if windows platform


	s_path_append_statements="import sys; sys.path.append( \"" \
						+ s_mod_dir + "\" );"

	s_import_statement="from pgguiutilities import PGGUIErrorMessage;"

	s_gui_statement="PGGUIErrorMessage( s_message=\"" + s_errormsg  + "\" )"


	s_command=s_path_append_statements + s_import_statement + s_gui_statement

	subprocess.Popen( [ PYEXE_FOR_POPEN, "-c" , s_command ] )

#end show_error_in_messagebox_in_new_process

if __name__ == "__main__":

    s_exec_name=sys.argv[ 1 ]

    print( confirm_executable_is_in_path( sys.argv[1] ) )

#end if main


