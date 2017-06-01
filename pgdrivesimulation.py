'''
Description
To use the non-gui portion of the simulation code,
this script is meant to provide a command-line
interface with which to do a simulation using
the PGInputSimupop, PGOpSimupop, and PGOuputSimupop
class objects.

This script was written in order to debug the 
simulation-related non-gui code, which is hard
to debug from the GUI, as it runs in a separate
thread (or python process).


2017_05_30. Continuing implementation of this module.
For simplicity and to retain parallelization for replicates,
I am changing the approach to use the same setup and
calls used by the pgguisimupop.py in def runSimulation.
'''

__filename__ = "pgdrivesimulation.py"
__date__ = "20170119"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os
import argparse as ap
import multiprocessing

import pgutilities as pgut
import pgparamset as pgparams
import pgsimupopresources as pgres
import pginputsimupop as pgin
import pgoutputsimupop as pgout
import pgopsimupop as pgop


class SimInputParamValueHolder(object):
	def __init__(self, model_name=None, 
					popSize=None, 
					ages=None, 
					isMonog=None, 
					forceSkip=None, 
					skip=None, 
					litter=None, 
					maleProb=None, 
					gammaAMale=None,
					gammaBMale=None,
					gammaAFemale=None,
					gammaBFemale=None,
					doNegBinom=None,
					survivalMle=None,
					survivalFemale=None,
					fecundityMale=None,
					startLambda=None,
					lbd=None,
					Nb_from_effective_size_section=None,
					NbNc=None,
					NbNe=None,
					NbVar=None,
					startAlleles=None,
					mutFreq=None,
					numMSats=None,
					numSNPs=None,
					reps=None,
					startSave=None,
					gens=None,
					cull_method=None,
					nbadjustment=None ):



		self.__values_by_param_name={ "model_name":model_name, 
									"popSize":popSize, 
									"ages":ages, 
									"isMonog":isMonog, 
									"forceSkip":forceSkip, 
									"skip":skip, 
									"litter":litter, 
									"maleProb":maleProb, 
									"gammaAMale":gammaAMale,
									"gammaBMale":gammaBMale,
									"gammaAFemale":gammaAFemale,
									"gammaBFemale":gammaBFemale,
									"doNegBinom":doNegBinom,
									"survivalMle":survivalMle,
									"survivalFemale":survivalFemale,
									"fecundityMale":fecundityMale,
									"startLambda":startLambda,
									"lbd":lbd,
									"Nb_from_effective_size_section":Nb_from_effective_size_section,
									"NbNc":NbNc,
									"NbNe":NbNe,
									"NbVar":NbVar,
									"startAlleles":startAlleles,
									"mutFreq":mutFreq,
									"numMSats":numMSats,
									"numSNPs":numSNPs,
									"reps":reps,
									"startSave":startSave,
									"gens":gens,
									"cull_method":cull_method }
							
		return
	#end __init__

	@property
	def paramvalues( self ):
		return self.__values_by_param_name
	#end paramvalues

#end class

					
class SimInputParamResetManager( object ):
	def __init__( self, o_input_object, o_param_value_holder):
		self.__valueholder=o_param_value_holder
		self.__inputobject=o_input_object

		'''
		Some parameters (e.g. those which are related to the Nb and N0 values)
		have private names inside the input object.
		'''
		self.__params_with_private_names={ \
				"Nb_from_effective_size_section":"_PGInputSimuPop__Nb_from_eff_size_info" }
		return
	#end __init__

	def resetInputParamValues( self ):
		for s_param_name in self.__valueholder.paramvalues:
			v_value=self.__valueholder.paramvalues[ s_param_name ]
			if v_value is not None:
				s_correct_param_name=s_param_name
				if s_param_name in self.__params_with_private_names:
					s_correct_param_name= \
							self.__params_with_private_names[ s_param_name ]
				#end if private name in input object
				try:
					setattr( self.__inputobject, s_correct_param_name, v_value )
				except Exception as oex:
					s_msg = "In pgdrivesimulation.py, SimInputParamValueHolder instance, "  \
									+ "def updateInputObject.  The program can't set the parameter " \
									+ "named, " + s_param_name + ", to value, " + str( v_value ) \
									+ ".  An Exception occured with message, " + str( oex )
					raise Exception( s_msg )				
				#end try to set attr, except
		#end for each param name
		return
	#end updateInputObject

#end class SimParamResetValues

def check_for_existing_output_files( s_output_base ):

	s_glob=s_output_base + "*"

	ls_exisiting_items=pgut.get_list_files_and_dirs_from_glob( s_glob  )

	if len( ls_exisiting_items ) > 0:
		s_msg="In module pgdrivesimulation.py, a check for existing items matching " \
							+ "the output base, " + s_output_base \
							+ ", found the followng:\n\n"  \
							+ str( ls_exisiting_items ) + ".\n\n" \
							+ "Please rename or delete these files, or change your " \
							+ "of your output base name."
		raise Exception( s_msg )
	#end if files exist

	return
#end check_for_existing_output_files

def get_params_file_location():


	s_params_file_name="resources/simupop.param.names"

	s_this_mod_path_and_name=os.path.abspath( __file__ )
	
	s_this_mod_path=os.path.dirname( s_this_mod_path_and_name )

	s_params_file_path_and_name=s_this_mod_path + os.sep + s_params_file_name

	if not os.path.exists( s_params_file_path_and_name ):
		s_msg="In pgdrivesimulation.py, def get_params_file_location, " \
						+ "the file simupop.param.names is not found.  " \
						+ "It is expected to be in a subdirectory called " \
						+ "\"resources\", inside the directory that holds " \
						+ "this module, that is, the main program directory."
		raise Exception
	#end if not such file, error

	return s_params_file_path_and_name
#end class get_params_file_location

def get_input_object( s_config_file, 
						s_life_table_file, 
						s_param_names_file, 
						lv_value_list, 
						i_Nb, 
						f_Nb_tolerance,
						i_replicates,
						i_startsave ):

	o_paramInfo=pgparams.PGParamSet( s_param_names_file )

	o_lifeTableInfo=None

	#If there is no life table file, we assume
	#all parameters are set in the config file.
	if s_life_table_file != "none":
		o_lifeTableInfo=pgres.PGSimuPopResources( [ s_life_table_file ] )
	#end if we have a life table file name

	o_simInput=pgin.PGInputSimuPop( s_config_file, o_lifeTableInfo, o_paramInfo ) 

	o_simInput.makeInputConfig()

	#Reset any values the user passed in the command.

	if [ lv_value_list, i_Nb, f_Nb_tolerance, i_replicates]  != [ None, None, None, None ]:
		'''
		2017_06_01.  We ignore lv_value_list since it is not currently
		added to the argument list.
		'''
		o_value_holder = SimInputParamValueHolder( \
											Nb_from_effective_size_section=i_Nb,
											NbVar=f_Nb_tolerance,
											reps=i_replicates,
											startSave=i_startsave )

		o_input_manager = SimInputParamResetManager( o_simInput, o_value_holder )

		o_input_manager.resetInputParamValues()

	#end if value list is not None

	return o_simInput

#end def get_input_object

def drive_sims( s_config_file, 
					s_life_table_file,  
					s_output_base, 
					lv_value_list, 
					i_replicates,
					i_Nb,
					f_Nb_tolerance,
					i_startsave,
					i_processes ):

	check_for_existing_output_files( s_output_base )

	s_param_names_file=get_params_file_location()

	s_output_dir=os.path.dirname( os.path.abspath( s_output_base ) )

	if not( os.path.exists( s_output_dir ) ):
		s_msg="In pgdrivesimulation.py, def run_simulations, " \
				+ "the program cannot write the temp config file " \
				+ "because the curren output directory name, " \
				+  s_output_dir  \
				+ ", does not exist as a path."
		raise Exception( s_msg )
	#end if not a path
			
	s_temp_file_name=pgut.get_temp_file_name( s_parent_dir=s_output_dir )

	if pgut.is_windows_platform():
		s_temp_file_name = pgut.fix_windows_path( s_temp_file_name )
	#end if windows, fix path

	s_temp_config_file_for_running_replicates=s_temp_file_name

	print( "Creating Input object...." )

	o_input_object=get_input_object( s_config_file, 
						s_life_table_file, 
						s_param_names_file, 
						lv_value_list,
						i_Nb,
						f_Nb_tolerance,
						i_replicates,
						i_startsave )

	print( "Writing a temp configuration file for the simulation..." )

	o_input_object.writeInputParamsAsConfigFile( s_temp_config_file_for_running_replicates )

	'''
	2017_05_30. Because this code is adapted from the pgguisimupop.py def
	runSimulation, we create this multiproc event only because the
	pgutilities def signature requires it.  In the gui, the call to pgut.
	do_simulation_reps_in_subprocesses was made in a python mulitprocessing
	process instance, so that this event was settable if the user hit cancel
	button.  Here, however, we are simply blocking this def while the sim
	runs.
	'''
	sim_multi_process_event=multiprocessing.Event()

	print( "Running the simulation in a new python process..." )

	pgut.do_simulation_reps_in_subprocesses( sim_multi_process_event, 
									o_input_object.reps, 
									i_processes,
									s_temp_config_file_for_running_replicates,
									[ s_life_table_file ],
									s_param_names_file,
									s_output_base,
									b_use_gui_messaging = False )
	print( "Simulation complete. Removing temporary configuration file..." )
	
	pgut.remove_files( [ s_temp_config_file_for_running_replicates ] )

	return
#end def drive_sims

if __name__ == "__main__":

	REQUIRED_SHORT=[ "-c", "-l",  "-o" ] 

	REQUIRED_LONG=["--configfile", "--lifetable",  "--outputbase" ] 

	VALUE_LIST_IS_IMPLEMENTED=False

	OPT_SHORT=[  "-n" , "-t", "-r", "-s", "-p" ]
	OPT_LONG=[ "--nb", "--nbtolerance", "--replicates", "--startsave", "--processes"  ]


	s_chelp="configuration file.  Typically one of the files in the \"resources\\simulation\" " \
							+ "subdirectory of the main program directory, and with a name ending in " \
							+ "\"conf.with.model.name\", or a *.conf file written by our program " \
							+ "after a simulation has been run."

	s_lhelp="life table file.  You can typically find the life table that matches your " \
						+ "configuration files \"model\" entry (e.g. wfrog, grizzley) in the " \
						+ "\"resources\" subdirectory inside the programs main directory. "\
						+ "The life table files have names ending with \"life table info.\"  " \
						+ "You can use \"none\" in place of the life table file name " \
						+ "if the configuration file was written by a run of our " \
						+ "program (i.e. has all the needed parameter settings)."

	s_ohelp="file giving the base name for output files (resulting files will have extensions " \
																		+ "*.genepop and *.conf)."

	s_phelp="Number of processes to use.  Default is one.  A sensible maximum is the total " \
									"number of cores in your machine, or fewer if you need to accomodate other " \
									"processes. The unit of parallelization is the replicate." 
	s_rhelp="Number of replicates to run.  Integer. This will overwrite " \
									+ "the replicates (\"reps\") value in the configuration file."
	s_nhelp="Nb value.  Integer. This will overwrite the Nb value in the configuration file."

	s_shelp="Start save. Integer. Repro cycle number at which to start recording results. " \
								+ "This will overwrite the \"startSave\" value in the configuration file."

	s_thelp="Nb tolerance.  Float. This will overwrite the nb tolerance value (\"NbVar\") in the configuration file."

	'''
	2017_06_01. We are not yet showing this option, for now just offering "replicates" and "Nb" as optional settings.
	'''
	s_vhelp="Optional, Not Yet Implemented.  This is a list of parameter_name=value pairs, comma delimited, " \
		+ "which will replace the values in the config file and " \
		+ "life table (if used)."

	s_vhelp_table_of_parameters=""

	

	#Optional values, defaults if not supplied:
	lv_value_list=None
	i_processes=1
	i_Nb=None
	f_Nb_tolerance=None
	i_replicates=None
	i_startsave=None

	REQUIRED_HELP=[ s_chelp, s_lhelp, s_ohelp ]

	OPT_HELP=[ s_nhelp, s_thelp, s_rhelp, s_shelp, s_phelp ]

	o_parser=ap.ArgumentParser()

	o_arglist=o_parser.add_argument_group( "args" )

	i_total_nonopt=len( REQUIRED_SHORT )

	for idx in range( i_total_nonopt ):
	    o_arglist.add_argument( \
	            REQUIRED_SHORT[ idx ],
	            REQUIRED_LONG[ idx ],
	            help=REQUIRED_HELP[ idx ],
	            required=True )
	#end for each arg

	i_total_opt=len( OPT_SHORT )

	for idx in range( i_total_opt ):
		o_parser.add_argument( \
						OPT_SHORT[ idx ],
						OPT_LONG[ idx ],
						help=OPT_HELP[ idx ],
						required=False )
	#end for ech optional

	o_args=o_parser.parse_args()

	s_config_file=o_args.configfile
	s_life_table_file=o_args.lifetable
	s_output_base=o_args.outputbase

	if o_args.processes is not None:
		i_processes=int( o_args.processes )
	#end ef process arg 

	if o_args.replicates is not None:
		i_replicates=int( o_args.replicates )
	#end if replicates arg

	
	if o_args.nb is not None:
		i_Nb=int( o_args.nb )
	#end if Nb arg supplied


	if o_args.nbtolerance is not None:
		f_Nb_tolerance=float( o_args.nbtolerance )
	#end if  Nb tolerance value supplied

	if o_args.startsave is not None:
		i_startsave=int( o_args.startsave )
	#end if start save value supplied

	drive_sims( s_config_file, 
				s_life_table_file, 
				s_output_base, 
				lv_value_list,
				i_replicates,
				i_Nb,
				f_Nb_tolerance,
				i_startsave,
				i_processes )

#end if main

