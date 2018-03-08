#!/usr/bin/env python
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

import agestrucne.pgparallelopmanager as pgpar
import agestrucne.pgutilities as pgut
import agestrucne.pgparamset as pgparams
import agestrucne.pgsimupopresources as pgres
import agestrucne.pginputsimupop as pgin
import agestrucne.pgoutputsimupop as pgout
import agestrucne.pgopsimupop as pgop

OUTPUT_USE_HET_FILTER=3

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
					nbadjustment=None,
					het_filter=None,
					do_het_filter=None,
					het_init_snp=None,
					het_init_msat=None ):

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
									"cull_method":cull_method,
									"het_filter":het_filter,
									"do_het_filter":do_het_filter,
									"het_init_snp":het_init_snp,
									"het_init_msat":het_init_msat }
							
		return
	#end __init__

	@property
	def paramvalues( self ):
		return self.__values_by_param_name
	#end paramvalues

#end class SimInputParamValueHolder
					
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
							+ "output base name."
		raise Exception( s_msg )
	#end if files exist

	return
#end check_for_existing_output_files

def get_params_file_location():


	s_params_file_name="resources/simupop.param.names"

	'''
	2017_11_20.  Having packed the modules inside
	the agestrucne folder, and also automated the
	installation using pypi and setuptools, this 
	script is now automatically placed in a scrips
	or executable subdir separage from the package
	subdirectory.  Hence, we need to use a non-exectutable
	module to get the path to the agestrucne installation
	directory (and, so, too, the resources subdir).	Arbitrarily 
	we'll use the pgparamset module to get the path to the 
	installation:
	'''
	s_this_mod_path_and_name=os.path.abspath( pgparams.__file__ )
	
	s_this_mod_path=os.path.dirname( s_this_mod_path_and_name )

	s_params_file_path_and_name=s_this_mod_path + os.sep + s_params_file_name

	if not os.path.exists( s_params_file_path_and_name ):
		s_msg="In pgdrivesimulation.py, def get_params_file_location, " \
						+ "the file simupop.param.names is not found.  " \
						+ "It is expected to be in a subdirectory called " \
						+ "\"resources\", inside the directory that holds " \
						+ "this module, that is, the main program directory."
		raise Exception ( s_msg )
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
						i_startsave,
						i_burnin,
						i_total_cycles,
						b_do_het_filter,
						s_het_filter,
						i_popsize,
						s_cull_method,
						i_num_snps,
						f_het_init_snp,
						i_num_msats,
						f_het_init_msat ):

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

	'''
	2017_06_01.  We ignore lv_value_list since it is not currently
	added to the argument list from the command line.
	'''
	o_value_holder = SimInputParamValueHolder( \
										Nb_from_effective_size_section=i_Nb,
										NbVar=f_Nb_tolerance,
										reps=i_replicates,
										startSave=i_startsave,
										startLambda=i_burnin,
										gens=i_total_cycles,
										do_het_filter=b_do_het_filter,
										het_filter=s_het_filter,
										popSize=i_popsize,
										cull_method=s_cull_method,
										numSNPs=i_num_snps,
										het_init_snp=f_het_init_snp,
										numMSats=i_num_msats,
										het_init_msat = f_het_init_msat )


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
					i_burnin,
					i_processes,
					i_total_cycles,
					i_output_mode,
					s_het_filter,
					i_popsize,
					s_cull_method,
					i_num_snps,
					f_het_init_snp,
					i_num_msats,
					f_het_init_msat ):

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
						i_Nb=i_Nb,
						f_Nb_tolerance=f_Nb_tolerance,
						i_replicates=i_replicates,
						i_startsave=i_startsave,
						i_burnin=i_burnin,
						i_total_cycles = i_total_cycles,
						b_do_het_filter=( i_output_mode==OUTPUT_USE_HET_FILTER ),
						s_het_filter=s_het_filter,
						i_popsize=i_popsize,
						s_cull_method=s_cull_method,
						i_num_snps=i_num_snps,
						f_het_init_snp=f_het_init_snp,
						i_num_msats=i_num_msats,
						f_het_init_msat=f_het_init_msat )


	print( "Writing a temp configuration file for the simulation..." )

	o_input_object.writeInputParamsAsConfigFile( s_temp_config_file_for_running_replicates )

	'''
	2017_05_30. Because this code is adapted from the pgguisimupop.py def
	runSimulation, we create this multiproc event only because the
	pgparallelopmanager (used to be in pgutilities ) def signature requires it.  
	In the gui, the call to  do_simulation_reps_in_subprocesses was made 
	in a python mulitprocessing process instance, so that this event was 
	settable if the user hit cancel button.  Here, however, we are simply 
	blocking this def while the sim runs.
	'''
	sim_multi_process_event=multiprocessing.Event()

	print( "Running the simulation in a new python process..." )

	#The op object recognizes only ORIG or GENEPOP only,
	#and assumes genepop only for het filter output.
	if i_output_mode in ( pgop.PGOpSimuPop.OUTPUT_GENEPOP_ONLY, OUTPUT_USE_HET_FILTER ):
		i_output_mode=pgop.PGOpSimuPop.OUTPUT_GENEPOP_ONLY
	#end if output type is genepop only

	'''
	2017_11_12.  We have moved the defs that parallel-process the sim ops
	from pgutilities to pgparallelopmanager.
	'''
	pgpar.do_simulation_reps_in_subprocesses( sim_multi_process_event, 
									o_input_object.reps, 
									i_processes,
									s_temp_config_file_for_running_replicates,
									[ s_life_table_file ],
									s_param_names_file,
									s_output_base,
									b_use_gui_messaging = False,
									i_output_mode = i_output_mode )

	print( "Simulation complete. Removing temporary configuration file..." )
	
	pgut.remove_files( [ s_temp_config_file_for_running_replicates ] )

	return
#end def drive_simso

if __name__ == "__main__":

	REQUIRED_SHORT=[ "-c", "-l",  "-o" ] 

	REQUIRED_LONG=["--configfile", "--lifetable",  "--outputbase" ] 

	VALUE_LIST_IS_IMPLEMENTED=False

	OPT_SHORT=[ "-b", "-n" , "-t", "-r", "-s", "-p", "-g", "-u", "-z", "-i", "-m", "-e", "-H", "-M", "-T" ]

	OPT_LONG=[ "--burnin", "--nb", "--nbtolerance", "--replicates", "--startsave", "--processes" , 
													"--cycles", "--outputmode", "--hetfilter", 
													"--popsize", "--cullmethod", "--numsnps", 
													"--hetinitsnp", "--nummsats", "--hetinitmsat" ]


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
	
	s_bhelp="Burn-in cycles.  Number of the repro cycle at which to start applying Nb tolerance test.  " \
								+ "This will overwrite the burn-in setting " \
								+ "(i.e. \"startLambda\") in the configuration file."

	s_ghelp="Total cycles.  Total number of cycles to be run in the simulation.  This will overwrite this setting " \
								+ "(i.e. \"gens\") in the configuration file."

	s_mhelp="Cull method.  Accepts either \"equal_sex_cull\" or \"survival_rates\" (the original cull method).  This " \
								+ "value will replace the \"cull_method\" value in the configuraation file."


	'''
	2017_06_01. We are not yet showing this option, for now just offering "replicates" and "Nb" as optional settings.
	'''
	s_vhelp="Optional, Not Yet Implemented.  This is a list of parameter_name=value pairs, comma delimited, " \
		+ "which will replace the values in the config file and " \
		+ "life table (if used)."

	s_uhelp="Output mode, Integer, 1 = original output (3 files from the original program, but which " \
										+ "currently are deleted, which makes this mode currently unneeded), " \
										+ ", 2 = conf and genepop file only (the default), " \
										+ "3 = conf and genepop file with het filter"
	s_zhelp="Het filter.  Ignored unless OUTPUTMODE (-u) is set to 3. " \
								+ "String of 3 comma-separated numbers of the  form \"n,x,t\", " \
								+ "where n is a float that gives a minimum " \
								+ "value for mean heterozygosity (mean het), " \
								+ "x is a float giving a maximum mean het value, " \
								+ "and t is an integer giving total for number of pop sections " \
								+ "to save.  For each population generated by the sim, the " \
								+ "mean expected heterozygosity  is calulated, and, " \
								+ "if found to be in range, then the pop is recorded to the output "\
								+ "genepop file. See the manual for details on this parmeter." 
	s_ihelp="Pop size.  The size of the initial population.  This value will replace the \"popSize\" value in the " \
				+ "configuration file."

	s_ehelp="Number of SNPs.  Set the number of SNPs for the simulation.  This value will replace the \"numSNPs\" value " \
				+ "in the configuration file."
	
	s_Hhelp="Initial expected heterozygosity for SNPs.  This value will replacde the \"init_het_snp\" value in the configuration file."

	s_Mhelp="Number of mirosats.  Set the number of microsatellites for the simulation.  This value will replace the \"numMSats\" " \
			 	+ "value in the configuration file."

	s_Thelp="Initial expected heterozygosity for Microsats.  This value will replace the \"init_het_msat\" " \
				+ "value in the configuration file.  Values valid in interval (0.0,0.85]"

	s_vhelp_table_of_parameters=""

	#Optional values, defaults if not supplied:
	lv_value_list=None
	i_processes=1
	i_Nb=None
	f_Nb_tolerance=None
	i_replicates=None
	i_startsave=None
	i_burnin=None
	i_total_cycles=None
	i_output_mode=pgop.PGOpSimuPop.OUTPUT_GENEPOP_ONLY
	s_hetfilter=None
	i_popsize=None
	s_cull_method=None
	i_num_snps=None
	f_het_init_snp=None
	i_num_msats=None
	f_het_init_msat=None

	REQUIRED_HELP=[ s_chelp, s_lhelp, s_ohelp ]

	OPT_HELP=[ s_bhelp, s_nhelp, s_thelp, s_rhelp, 
				s_shelp, s_phelp, s_ghelp, s_uhelp, 
				s_zhelp, s_ihelp, s_mhelp, s_ehelp,
				s_Hhelp, s_Mhelp, s_Thelp ]

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

	if o_args.burnin is not None:
		i_burnin = int( o_args.burnin )
	#end if burnin arg supplied		

	if o_args.nb is not None:
		i_Nb=int( o_args.nb )
	#end if Nb arg supplied

	if o_args.nbtolerance is not None:
		f_Nb_tolerance=float( o_args.nbtolerance )
	#end if  Nb tolerance value supplied

	if o_args.startsave is not None:
		i_startsave=int( o_args.startsave )
	#end if start save value supplied

	if o_args.cycles is not None:
		i_total_cycles=int( o_args.cycles )
	#end if cycles supplied

	if o_args.outputmode is not None:
		i_output_mode=int( o_args.outputmode )
	#end if output mode set
	
	if o_args.hetfilter is not None:
		s_hetfilter = o_args.hetfilter
	#end if hetfilter string supplied

	if o_args.popsize is not None:
		i_popsize = int( o_args.popsize )
	#end if popsize set

	if o_args.cullmethod is not None:
		s_cull_method=o_args.cullmethod
	#end if cull method set

	if o_args.numsnps is not None:
		i_num_snps=int( o_args.numsnps )
	#end if num snps set

	if o_args.hetinitsnp is not None:
		f_het_init_snp=float( o_args.hetinitsnp )
	#end if het_init_snp set
	
	if o_args.hetinitmsat is not None:
		f_het_init_msat=float( o_args.hetinitmsat )
	#end if het_init_snp set

	if o_args.nummsats is not None:
		i_num_msats=int( o_args.nummsats )
	#end if num msats set	

	drive_sims( s_config_file, 
				s_life_table_file, 
				s_output_base, 
				lv_value_list,
				i_replicates=i_replicates,
				i_Nb=i_Nb,
				f_Nb_tolerance=f_Nb_tolerance,
				i_startsave=i_startsave,
				i_burnin=i_burnin,
				i_processes=i_processes, 
				i_total_cycles=i_total_cycles,
				i_output_mode=i_output_mode,
				s_het_filter=s_hetfilter,
				i_popsize=i_popsize,
				s_cull_method=s_cull_method,
				i_num_snps=i_num_snps,
				f_het_init_snp=f_het_init_snp,
				i_num_msats=i_num_msats,
				f_het_init_msat=f_het_init_msat )
			

#end if main

