'''
Description
Support defs for the pop gen interface programs.
'''
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
import copy
import subprocess

PROCESS_QUEUE_STOP_SIGN='STOP'

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

def do_sim_replicate_on_separate_os_process( s_configuration_file,
													s_life_table_files,
													s_param_name_file,
													s_outfile_basename,
													s_replicate_number ):
	
	s_target_script="do_sim_replicate.py"
	

	subprocess.call( [ "python", s_target_script, 
						s_configuration_file,
						s_life_table_files, 
						s_param_name_file, 
						s_outfile_basename, 
						s_replicate_number ] )
	return
#end do_sim_replicate_on_separate_os_process


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
	as changed or edited on the gui interface)
	'''

	s_tag_out=""

	if i_replicate_number is not None:
		s_tag_out=".r" + str( i_replicate_number )
	#end if rep number is not none

	o_resources=pgrec.PGSimuPopResources( ls_life_table_files )
	o_paramset=pgpar.PGParamSet( s_param_name_file )
	o_input=pgin.PGInputSimuPop( s_configuration_file, o_resources, o_paramset ) 
	o_input.makeInputConfig()

	
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
			o_output )
	o_new_pgopsimupop_instance.prepareOp( s_tag_out  )
	o_new_pgopsimupop_instance.doOp()

	return
#end do_pgopsimupop_replicate_from_files
def get_listdir( s_parent_dir ):
	ls_dir_contents=os.listdir( s_parent_dir )
	return ls_dir_contents
#end get_listdir

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

if __name__ == "__main__":

    s_exec_name=sys.argv[ 1 ]

    print( confirm_executable_is_in_path( sys.argv[1] ) )

#end if main


