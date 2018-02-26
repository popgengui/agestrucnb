'''
Description
2017_11_12.  In order to resolve the circular import statements that
surfaced when I packaged the modules inside the agestrune subdirectory,
I've moved these defs from pgutilitiies.  In the older state, these required
that pgutilitites imports several of the pg modules, at least one of which
imports pgutilitities.  

This module's name pgparallelopmanager.py suggests it should manage
all of the ops (simulation, LDNe, and Viz), but for now only
has those defs which needed to be moved to solve  the import 
curcularity problem.  As such, pgutilities still has defs that
instantiate new processes for LDNe and Viz ops.
'''

from __future__ import absolute_import, division, print_function
from builtins import range


__filename__ = "pgparallelopmanager.py"
__date__ = "20171112"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False

import sys
import os
import subprocess

from agestrucne.pgutilityclasses import IndependantSubprocessGroup 

import agestrucne.pgutilities as pgut
import agestrucne.pgopsimupop as pgsim
import agestrucne.pgsimupopresources as pgrec
import agestrucne.pginputsimupop as pgin
import agestrucne.pgoutputsimupop as pgout
import agestrucne.pgparamset as pgpar

import glob

def prep_and_call_do_pgopsimupop_replicate( s_config_file, 
											s_life_table_files, 
											s_param_file, 
											s_output_base_name, 
											s_replicate_number,
											s_use_gui_messaging="True",
											s_output_mode=str( pgsim.PGOpSimuPop.OUTPUT_GENEPOP_ONLY ) ):
	'''	
	This def to be invoked in a subprocess.Popen command, as
	instantiated in a PGGuiSimuPop instance in do_operation.

	This def simply prepares the args for the call to def
	do_pgopsimupop_replicate_from_files (below).

	2017_05_30.  Added def parameter (string by necessity) s_use_gui_messaging with default
	(bool-converted) value True, so that our new module pgdrivesimulation.py can call
	this with this (bool-converted) value set to False, to avoid gui processing during
	a command line execution.

	2017_08_07.  Added def parameters s_output_mode and s_pop_het_filter_string, to
	allows caller to use new output mode selections and het pop filter in PGOpSimuPop instances.

	2017_09_04. Removed the het filter string from this def's arglist.  It will now
	be stored in the input object only.
	'''

	#de-stringify args for call to def below:
	ls_life_table_files = s_life_table_files.split( pgut.DELIMITER_LIFE_TABLE_FILES )
	i_replicate_number=int( s_replicate_number )

	b_use_gui_messaging=True if s_use_gui_messaging=="True" else False

	i_output_mode=int( s_output_mode )

	do_pgopsimupop_replicate_from_files( s_config_file,
						ls_life_table_files,
						s_param_file,
						s_output_base_name,
						i_replicate_number,
						b_use_gui_messaging =  b_use_gui_messaging,
						i_output_mode=i_output_mode )

	return
#end prep_and_call_do_pgopsimupop_replicate

def do_pgopsimupop_replicate_from_files(  s_configuration_file, 
												ls_life_table_files, 
												s_param_name_file, 
												s_outfile_basename, 
												i_replicate_number,
												b_use_gui_messaging=True, 
												i_output_mode=pgsim.PGOpSimuPop.OUTPUT_GENEPOP_ONLY ):
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

	2017_05_30. Added def param b_use_gui_messaging with default value True, to accomodate new
	module pgdrivesimulation.py which needs to call with False, to avoid gui messaging in
	a server setting.
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
		s_tag_out=pgut.SIMULATION_OUTPUT_FILE_REPLICATE_TAG + str( i_replicate_number )

	#end if rep number is not none

	'''
	2017_05_30.  To allow no life table, as implemented  in the new module
	pgdrivesimulation.py, we set the resources object to None, then test for 
	a life table name not equal to "none."  If found, then we 
	create a resource object.  Otherwise, pass it as None to the input object.

	'''
	o_resources=None

	if ls_life_table_files != [ "none" ]:
		o_resources=pgrec.PGSimuPopResources( ls_life_table_files )
	#end if we have life tables

	o_paramset=pgpar.PGParamSet( s_param_name_file )
	o_input=pgin.PGInputSimuPop( s_configuration_file, o_resources, o_paramset ) 
	
	o_input.makeInputConfig()
	
	b_write_conf_file=False
	b_write_nb_and_age_tables=False

	#we only write the configuraton file if the replicate number is 1:
	if i_replicate_number == NUMBER_FIRST_REPLICATE:
		b_write_conf_file=True
		'''
		2017_04_07.  These are files that, as the sim proceeds,
		write two tables, one giving the pwop Nb values, the 
		other giving a per-age cound of individuals for each pop.

		These were intitially temporoary included files for testing,
		but are useful enought to warrant inclusion in the output,
		at least for the first replicate.
		'''
		b_write_nb_and_age_tables=True
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

	'''
	2017_03_26. Note the added param in the init of
	the PGOpSimuPop object.  Module pgopsimupop now has a mod-level def
	to import and the pgguiutilities.PGGUI* classes and 
	set a flag so that exeptions and other info during the
	simulation will raise a message window.  Note that 
	when I tried to make the import of the PGGUI* message
	classed the default for pgopsimupop.py, then an import
	error was raised when I tried to start the main program
	(negui.py).  There must be some recursive import problem.
	Note that the import works file in this context, when
	the pgopsimupop.py module is imported in this separate
	python instance.

	2017_06_11. Note we have added a new parameter, b_is_replicate_1,
	to tell the pgopsimupop instance that it is the first replicate.
	This limits the number of warning gui's it will produce to one,
	about presence of lamba value in conf being unused (see __init__
	in pgopsimupop.py).
	'''

	o_new_pgopsimupop_instance=pgsim.PGOpSimuPop( o_input,
			o_output, 
			b_remove_db_gen_sim_files=REMOVE_NON_GENEPOP_SIM_OUTPUT_FILES,
			b_write_input_as_config_file=b_write_conf_file,
			b_do_gui_messaging=b_use_gui_messaging,
			b_write_nb_and_ages_files=b_write_nb_and_age_tables,
			b_is_replicate_1 = ( i_replicate_number == 1 ),
			i_output_mode=i_output_mode )

	o_new_pgopsimupop_instance.prepareOp( s_tag_out  )

	o_new_pgopsimupop_instance.doOp()

	return
#end do_pgopsimupop_replicate_from_files

def do_simulation_reps_in_subprocesses( o_multiprocessing_event,
										i_input_reps, 
										i_total_processes_for_sims,
										s_temp_config_file_for_running_replicates,
										ls_life_table_files,
										s_param_names_file,
										s_output_basename,
										b_use_gui_messaging=True,
										i_output_mode=pgsim.PGOpSimuPop.OUTPUT_GENEPOP_ONLY ):

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
	calling pgparallelopmanager.prep_and_call_do_pgopsimupop_replicate 
	(note: the call has been updated  2017_11_12, after the defs were
	moved from pgutilities into new module pgparallelopmanager.

	2017_05_30.  We added the def param b_use_gui_messaging=True, to allow
	this def to be called from a command line implentation (new module 
	pgdrivesimulation.py), and set the flag to false, without having to
	revise the call from the GUI pgguisimupop.py.


	'''	

	'''	
	Running this inside a try block allows us to notify GUI
	users of exceptions propogated from anywere inside the 
	simulation setup and execution code. When we catch exceptions 
	below, we send an error message to a gui message box, then
	re-raise the exception.	

	 
	2017_08_07.  I've added the params i_output_mode and s_pop_het_filter_string,
	to allow callers to this def to set these new parameters in the PGOpSimuPop
	object.

	'''

	try:
		s_life_tables_stringified=",".join( ls_life_table_files )

		#if we're on windows, out strings of file
		#paths may be a mangled mix of unix and 
		#windows separators -- with errors resulting
		#downstream.  So we standardize:
		if pgut.is_windows_platform():
			s_life_tables_stringified= \
				pgut.fix_windows_path( s_life_tables_stringified )
			s_param_names_file= \
				pgut.fix_windows_path( s_param_names_file )				
			s_output_basename= \
				pgut.fix_windows_path( s_output_basename )	
		#end if windows, fix file path strings

		i_total_replicates_requested=i_input_reps

		i_max_processes_to_use=i_total_processes_for_sims

		'''
		we use a python command for a -c arg in the Popen command (see below)
		and these will be the same args for each replicate (we add the rep-number
		arg below).  We stringify so that they can be Popen command args.  Some
		are de-stringified by the pgparallelopmanager (formerly in pgutilities)
		def before sending to pgop-creator.
		'''
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
				
					'''
					In the Popen call, rather than rely on a driver python script 
					that would need to be in PATH, we'll simply
					invoke python with a "-c" argument that imports the 
					pgparallelopmanager (formerly code was in pgutilities)
					module and executes the correct def:
			
					complete the set of args used in the command by adding the
					replicate number (recall need comma in sequence with single item,
					to delineate sequence versus simple expression):
					'''

					seq_complete_arg_set=seq_first_four_args_to_sim_call + ( str( i_total_replicates_started ), )

					'''
					2017_05_30.  We added this argument to def prep_and_call_do_pgopsimupop_replicate, to propgate
					to its call to def do_pgopsimupop_replicate_from_files.
					
					'''
					seq_complete_arg_set=seq_complete_arg_set + ( str( b_use_gui_messaging ), )

					'''
					2017_08_07.  We added args to allow caller to use diffeent output modes, 
					and, if using the filter output mode, to pass a string with parameters,
					for filtering pops by mean heterozygosity.  (See new additions to PGOpSimuPop code.)

					2017_09_04. We remove the s_pop_het_filter_string argument.  It has been removed from
					the arglist for initializing PGOpSimuPop instances, and instead those instances
					will access it directly from the PGInputSimuPop object.
					'''
					seq_complete_arg_set=seq_complete_arg_set + ( str( i_output_mode ), )


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
					if pgut.is_windows_platform():
						s_mod_dir=pgut.fix_windows_path( s_mod_dir )
					#end if windows, fix path
					
					s_path_append_statements="import sys; sys.path.append( \"" \
							+ s_mod_dir + "\" );"

					'''
					2017_11_12. The path statements used import pgutilities, but now we
					are using this new module pgparallelopmanager.
					'''
					s_python_command=s_path_append_statements + "import pgparallelopmanager as pgpar;" \
										"pgpar.prep_and_call_do_pgopsimupop_replicate" \
										+ "( \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\" )" %  seq_complete_arg_set

					o_new_subprocess=subprocess.Popen( [ pgut.PYEXE_FOR_POPEN, "-c", s_python_command ] )
					o_subprocess_group.addSubprocess( o_new_subprocess ) 
				#end for each idx of new procs
			#end if event is set else not
		#end while preplicates need to be started

		#we don't want to return until all processes are done.
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

		o_traceback=sys.exc_info()[ 2 ]
		s_err_info=pgut.get_traceback_info_about_offending_code( o_traceback )
		s_prefix_msg_with_trace="Error caught by pgparallelopmanager, " \
								+ "def __do_simulation_reps_in_subprocesses." \
								+ "\\nError origin info:\\n" \
								+ s_err_info 

		if b_use_gui_messaging:
			pgut.show_error_in_messagebox_in_new_process( oex, 
				s_msg_prefix = s_prefix_msg_with_trace )
		#end if use gui messaging

		s_msg=s_prefix_msg_with_trace + str( oex )
		raise Exception( oex )
	#end try...except...
	return
#end __do_simulation_reps_in_subprocesses

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

	'''
	2017_05_16. Added to remove the recently added age counts and 
	PWOP Nb estimates files created on rep 1 in the simulations.
	These files don't have replicate tags in their names, 
	so our glob should not include one.
	'''
	s_age_counts_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "age_counts" ]
	s_sim_nb_vals_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "sim_nb_estimates" ]

	ls_non_replicate_extensions=[ s_age_counts_ext, s_sim_nb_vals_ext ]

	for s_ext in ls_output_extentions:
		s_unzipped_file_pattern=None	
		if s_ext in ls_non_replicate_extensions:
			s_unzipped_file_pattern=s_basename + s_ext
		else:
			s_unzipped_file_pattern=s_basename + "*" \
					+ pgut.SIMULATION_OUTPUT_FILE_REPLICATE_TAG \
					+ "*" + s_ext
		#end if  non-replicate file name, else use replicate tag	

		ls_files_unzipped=glob.glob( s_unzipped_file_pattern )

		ls_files_zipped=glob.glob( s_unzipped_file_pattern \
				+ "." + pgout.PGOutputSimuPop.COMPRESSION_FILE_EXTENSION )

		for s_file in ls_files_unzipped + ls_files_zipped:
			os.remove( s_file )
		#end for each unzipped and zipped output file with this extension
	#end for each file ext

	return
#end remove_simulation_replicate_output_files

if __name__ == "__main__":
	pass
#end if main

