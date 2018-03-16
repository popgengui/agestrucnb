'''
Description
A PGGuiApp object with widgets that manage an Ne-estimation using
a pgopsimupop object, itself calling Tiago's pygenomics.popgen.ne2.controller
object.
'''
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
__filename__ = "pgguineestimator.py"
__date__ = "20160805"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False
VERY_VERBOSE=False

ESTIMATION_RUNNING_MSG="Estimation in progress"

ATTRIBUTE_DEMANLGER="_PGGuiNeEstimator__"

#managing the list of genepop files as a tkinter.StringVar,
#so that we convert the sequence garnered by
#the tkfiledialog "getfilenames" into a delimited list
#of files.  Then, to populate the genepop file list box, we can 
#split on the delimiter:
DELIMITER_GENEPOP_FILES=","

#Accesssed in both def __set_initial_file_info
#and __give_user_nbne_value_message
INIT_GENEPOP_FILE_NAME="none"

ROW_NUM_FILE_LOCATIONS_FRAME=0
ROW_NUM_FILE_INFO_FRAME=1
ROW_NUM_PARAMETERS_FRAME=2
ROW_NUM_SAMPLING_PARAMS_FRAME=3 
ROW_NUM_LOCI_SAMPLING_PARAMS_FRAME=4 
ROW_NUM_VIZ_PARAMS_FRAME=5

COL_NUM_PARAMETERS_FRAME=0
COL_NUM_SAMPLING_PARAMS_FRAME=0
COL_NUM_LOCI_SAMPLING_PARAMS_FRAME=0
COL_NUM_VIZ_PARAMS_FRAME=0

from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog as tkfd

import sys
import os

#need a seperate, non-blocking
#process for the neestimations
#(see def runEstimator)
import multiprocessing

#killing the neestimation pool
#takes some signalling and sleeping
#see def __cancel_neestimation 
import time

import agestrucne.pgguiapp as pgg
import agestrucne.pgutilities as pgut
import agestrucne.pgparamset as pgps
import agestrucne.pgdriveneestimator as pgdn
'''
2017_03_27.  Used by def __create_temporary_directory_name()
to get a uniq name for the directory.
'''
import uuid

#these are the lowest-level interface frames
#that take input from the user and update
#this gui's attributes:
from agestrucne.pgkeyvalueframe import KeyValFrame
from agestrucne.pgkeylistcomboframe import KeyListComboFrame
from agestrucne.pgkeycheckboxvalueframe import KeyCheckboxValueFrame

from agestrucne.pgguiutilities import FredLundhsAutoScrollbar
from agestrucne.pgguiutilities import PGGUIInfoMessage
from agestrucne.pgguiutilities import PGGUIYesNoMessage
from agestrucne.pgguiutilities import PGGUIErrorMessage

from agestrucne.pgutilityclasses import FloatIntStringParamValidity
from agestrucne.pgutilityclasses import ValueValidator
from agestrucne.pgdriveneestimator import MAX_GENEPOP_FILE_NAME_LENGTH
#See def runEstimator
from agestrucne.pgutilityclasses import NeEstimatorSamplingSchemeParameterManager 
from agestrucne.pgutilityclasses import NeEstimatorLociSamplingSchemeParameterManager
#This is to check for Nb/Ne ratios present in genepop file headers
from agestrucne.pgutilityclasses import NbNeReader

from agestrucne.pglineregressconfigfilemaker import PGLineRegressConfigFileMaker

class PGGuiNeEstimator( pgg.PGGuiApp ):
	'''
	Subclass of PGGuiApp builds a gui,
	makes a PGInputNeEstimator and PGOutNeEstimator	
	object, then, on user command runs an (Ld)Ne-Estimation
	using a PGOpNeEstimator object.
	objects, then on user command 	
	'''

	#possible states of the gui:
	RUN_NOT_READY=0
	RUN_READY=1
	RUN_IN_PROGRESS=2
	
	def __init__( self, o_parent, 
						s_param_names_file,
						s_name="ne_estimator_gui",
						i_total_processes_for_est=1):

		'''
		param o_parent is the tkinter window that hosts this gui.  
			It is meant to be the same parent as that 
			which hosts other pg interfaces, like pgguisimupop objects.
		param s_param_names_file is the file that contains short and long 
			param names, used to make a PGParamSet object, in turn used to 
			setup the gpdriveneestimator call.
		param s_name gives the parent PGGuiApp's name 
			(currently, Fri Aug  5 16:48:08 MDT 2016, of no importance).
		param i_total_processes_for_est, integer given the number of processes 
			to assign to the ne-estimation, which does each population 
			in each genepop file in a separate python, mulitiprocessing.process.
		'''
				
		pgg.PGGuiApp.__init__( self, s_name, o_parent )

		self.__param_names_file=s_param_names_file

		self.__simulation_is_in_progress=False

		#ref to the PGParamSet object
		#created using the param_names_file:
		self.__param_set=None
		
		#a string giving a list 
		#of input files:
		self.__genepopfiles=StringVar()

		#variables for the output
		self.__output_directory=StringVar()

		self.__processes=i_total_processes_for_est

		#no StringVar because we want
		#the KeyValFrame to set this
		#directly:
		self.output_base_name=""

		#displays the current list of
		#genepop files loaded and ready
		#to run:
		self.__genepop_files_listbox=None

		#python multiprocessing.Process
		#spawned in def runEstimator:
		self.__op_process=None

		self.__estimation_in_progress=False
		self.__plotting_program_needs_to_be_run=False

		'''
		2017_03_27
		This attribute is to be set and then passed 
		to the code that runs the ne estimator, in order
		to (better than before) manage the intermediate
		files the estimator writes.
		'''
		self.__temporary_directory_for_estimator=None

		self.__run_state_message=""

		#A way to access one of the interface
		#input control groups, such as "filelocations",
		#or "parameters"
		self.__interface_subframes={}

		'''
		A way to access one of the objecta that
		controls the param-value in one or more 
		entry/list/combo boxes.  This added on 2016_10_31, 
		to get access to their tooltip objects, 		
		as some of these were persisting after accessing,
		then leaving the reloading the param boxes (in particular
		the combo boxes). Although the tooltip problem
		was solved by simpler changes in the CreateToolTip
		class itself, but we'll keep this attribute and append
		the objects (kv frames, as created in load_parm defs)
		in case the direct access to these controls is needed.
		'''
		self.__param_value_frames_by_attr_name={}

		#create interface
		self.__get_param_set( s_param_names_file )
		self.__set_initial_file_info()
		self.__init_interface()
		self.__load_param_interface()
		self.__update_genepopfile_sampling_params_interface()
		self.__update_genepopfile_loci_sampling_params_interface()
		
		self.__set_controls_by_run_state( self.__get_run_state() )
		return
	#end __init__

	def __get_param_set( self, s_param_names_file ):
		self.__param_set=pgps.PGParamSet( s_param_names_file )
		return
	#end __get_param_set

	def __set_initial_file_info( self ):
		
		INIT_OUTPUT_DIRECTORY=pgut.get_current_working_directory()
		INIT_OUTPUT_FILES_BASE_NAME="nb.out." \
				+ pgut.get_date_time_string_dotted()

		self.__genepopfiles.set( INIT_GENEPOP_FILE_NAME )
		self.__output_directory.set( INIT_OUTPUT_DIRECTORY )
		self.output_base_name=INIT_OUTPUT_FILES_BASE_NAME

		return
	#end __set_initial_file_info

	def __on_click_run_or_cancel_neestimation_button( self ):
		try:
			if self.__estimation_in_progress:
				o_mbox=PGGUIYesNoMessage( self , 
							"Are you sure you want to cancel " \
						+ "the Ne estimation and remove all of its output files?" )
				b_answer = o_mbox.value
				if b_answer:
					self.__cancel_neestimation()
					self.__estimation_in_progress=False
					self.__set_controls_by_run_state( self.__get_run_state() )
				#end if yes
			else:

				if self.__params_look_valid( b_show_message=True ):

					self.runEstimator()

				#end if params look valid
			#end if sim in progress else not
		except Exception as oex:

			o_traceback=sys.exc_info()[ 2 ]
			s_trace=pgut.get_traceback_info_about_offending_code( o_traceback )
			s_msg="In PGGuiNeEstimator instance, " \
						+ " def __on_click_run_or_cancel_neestimation_button, " \
						+ "an exception was caught with message: " \
						+ str( oex ) + ".\n" \
						+ "Error origin: " + s_trace

			PGGUIErrorMessage( self,  s_msg )
			raise (oex)
		#end try ... except

		return

	#end __on_click_run_or_cancel_neestimation_button

	def __convert_genepop_file_to_neestimator_basename( self, s_genepop_file ):

			'''
			For intermediate NeEstimator input/output files,
			pgdriveneestimator replaces dot chars in the file
			name with underscores (adaptation to the Ne2L
			programs file-truncation in nameing output files
			(see pgdriveneestimator)
			'''

			s_filename_no_path=pgut.get_basename_from_path( s_genepop_file )
			s_filename_dots_replaced=s_filename_no_path.replace( ".", 
							pgdn.INPUT_FILE_DOT_CHAR_REPLACEMENT )

			s_dirname_genepop_file = \
					pgut.get_dirname_from_path( s_genepop_file )

			s_pathsep=pgut.get_separator_character_for_current_os()	

			s_reformatted_genepop_file_base=s_pathsep.join( \
					[ s_dirname_genepop_file, s_filename_dots_replaced ] )

			return s_reformatted_genepop_file_base
	#end __convert_genepop_file_to_neestimator_basename

	def __get_existing_output_files( self ):

		ls_existing_outfiles=[]

		s_path_sep=pgut.get_separator_character_for_current_os()

		s_output_base_with_path=self.__output_directory.get()  \
				+ s_path_sep \
				+ self.output_base_name

		ls_output_file_names=[ s_output_base_with_path + "." \
				+ pgut.NE_ESTIMATION_MAIN_TABLE_FILE_EXT, 
				s_output_base_with_path + "." \
				+ pgut.NE_ESTIMATION_SECONDARY_OUTPUT_FILE_EXT ]

		#If the output files exist, collect their names
		#for return value list.
		for s_filename in ls_output_file_names:
			ls_matching_existing=pgut.get_list_files_and_dirs_from_glob( s_filename )
			ls_existing_outfiles += ls_matching_existing
		#end for each
		'''
		20170710.  This REM out is not deleted yet because I am not sure that 
		it is yet completely expendable.  We may want to replace it with a 
		search for current intermediates, which will require new code. Note
		that the pgdriveneestimator.py module no longer names intermediate files 
		after parent genepop files, and, further, that new sessions will be run
		in uniquely named temporary directories.
		'''
#		s_genepop_files=self.__genepopfiles.get()
#
#		ls_genepop_files=s_genepop_files.split( DELIMITER_GENEPOP_FILES )
#
#		#Now we collect the names of any existing intermediate files
#		#produced during a previous run:
#		for s_genepop_file in ls_genepop_files:	
#
#			for s_tag in pgdn.NE_ESTIMATOR_AND_LDNE_OUTPUT_FILE_TAGS \
#					+ [ pgdn.NE_ESTIMATOR_AND_LDNE_OUTPUT_FILES_GENERAL_TAG + "*" ]: 
#
#				s_reformatted_filename = \
#						self.__convert_genepop_file_to_neestimator_basename ( \
#																	s_genepop_file )	
#				#glob basename plus wildcard, ending
#				#with ne-estimator file tag.   (Wildcard
#				#is needed because pgdriveneestimator.py
#				#will have added sample/replicate/popnun fields
#				#to the output file basename:
#				s_glob=s_reformatted_filename + "*" + s_tag 
#
#				ls_nefiles=pgut.get_list_files_and_dirs_from_glob( s_glob )
#
#				if VERY_VERBOSE:
#					print( "In def __get_existing_output_files: " )
#					print ( "   with glob: " + s_glob )
#					print ( "   got files: " + str( ls_nefiles ) )
#				#end if very verbose
#
#				ls_existing_outfiles += ls_nefiles
#
#			#end for each NeEstimator file tag

		return ls_existing_outfiles
	#end __get_existing_output_files

	def __remove_output_files( self, ls_files_to_remove):


		if VERY_VERBOSE:
			print( "removing files: " + str( ls_files_to_remove ) )
		#end if very verbose

		pgut.remove_files( ls_files_to_remove )

		return
	#end __remove_output_files

	def __remove_temporary_directory_used_by_estimator( self ):

		if VERY_VERBOSE:
			print ( "testing to remove temporary directory for estimator: " \
						+ str( self.__temporary_directory_for_estimator ) )
		#end if very verbose

		if self.__temporary_directory_for_estimator is not None:
			if os.path.exists( self.__temporary_directory_for_estimator ):
				try:
					pgut.remove_directory_and_all_contents( \
							self.__temporary_directory_for_estimator )
					#end if path exists, remove
				except Exception as oex:
					'''
					Note that we don't propogate the exception, since
					it will simply truncate the callers def and return
					with the GUI still intact, but in a state that may 
					be incorrect.  Hence we just tell the caller that the temporary
					directory was not removed.
					'''
					s_msg="The program failed to remove the temporary " \
								+ "directory used to run the Nb/Ne estimator.  " \
								+ "Temporary directory name:\n" \
								+ self.__temporary_directory_for_estimator
					PGGUIErrorMessage( self, s_msg )
				#end try...except
			self.__temporary_directory_for_estimator=None
		#end if the attribute has a non-None value

		return
	#end __remove_temporary_directory_used_by_estimator

	def __cancel_neestimation( self ):

		SLEEPTIME_WAITING_FOR_EVENT_CLEAR=0.25

		TIMEOUT_WAITING_FOR_EVENT_TO_CLEAR=0o5

		if self.__op_process is not None:
			
			#Process event created in def runEstimator,
			#passed to pgutitlities.run_driveneestimator_in_new_process,
			#which then passes into pgdriveneestimator.py -- the latter
			#will test it while the process.Pool def map_async is running,
			#and if set will kill the process pool:
			if self.__neest_multi_process_event is not None:
				try:
					if VERY_VERBOSE==True:
						print( "In def __cancel_neestimation, setting event" )
					#end if very verbose

					self.__neest_multi_process_event.set()
				except Exception as oex:
					s_msg = "In PGGuiNeEstimator instance, def " \
							+ "__cancel_neestimation, Exception after " \
							+ "setting multi process event: " \
							+ str( oex ) + "."
					PGGUIErrorMessage( self, s_msg )
					sys.stderr.write( s_msg + "\n" )
				#end try, except
			#end if event is not none

			#after we hear back from op_process via the event being
			#cleared (after we set it), we can terminate op_process:
			try:
				if VERY_VERBOSE:
					print( "In def __cancel_neestimation, " \
								+ "sleeping before terminating proc." )
				#end if very verbose

				f_starttime=time.time()

				while self.__neest_multi_process_event.is_set() \
						and time.time() - f_starttime < \
						TIMEOUT_WAITING_FOR_EVENT_TO_CLEAR:

					if VERY_VERBOSE:
						print( "In def __cancel_neestimation, " \
									+ "in while loop in gui while event is set" )
					#end if very verbose

					time.sleep( SLEEPTIME_WAITING_FOR_EVENT_CLEAR )
				#end while

				if VERY_VERBOSE:
					if self.__neest_multi_process_event.is_set():
						print( "In def __cancel_neestimation, " \
								+ "timed out waiting for event to clear -- even still set. " \
								+ "Terminating op_process " )
					else:
						print( "In def __cancel_neestimation, event now clear. " \
								+ "Terminating op_process..." )
					#end if op_process management def in pgutilities.py not clear the event, else did
				#end if very verbose

				self.__op_process.terminate()
			except Exception as oex:
					s_msg = "in PGGuiNeEstimator instance in def " \
							+ "__cancel_neestimation, Exception after " \
							+ "terminating the process that starts " \
							+ " the estimation: "  \
							+ str( oex ) + "."
					PGGUIErrorMessage( self, s_msg )
					sys.stderr.write( s_msg + "\n" )
			#end try, except

			ls_output_files=self.__get_existing_output_files()

			self.__remove_output_files( ls_output_files )

			self.__remove_temporary_directory_used_by_estimator()

			if VERY_VERBOSE:
				print ( "In def __cancel_neestimation,  " \
							+ "removing the following output files: " \
							+ str( ls_output_files ) )
			#end if very vergbose

		else:
			s_msg="No Ne estimation run process found.  No run was cancelled."
			sys.stderr.write( s_msg  + "\n"  )
		#end if process exists cancel, else message
		return
	#end __cancel_neestimation

	def __get_list_bad_genepop_file_names( self ):

		MSG_NOT_EXIST=": file does not exist"
		MSG_NAME_TOO_LONG=": file name cannot exceed " \
					+ str( MAX_GENEPOP_FILE_NAME_LENGTH ) \
					+ " characters."
		ls_bad_filenames=[]
		s_genepopfiles=self.__genepopfiles.get()	
		
		ls_genepopfiles=s_genepopfiles.split( DELIMITER_GENEPOP_FILES )

		for s_file in ls_genepopfiles:

			s_basename=pgut.get_basename_from_path( s_file )
			if not ( pgut.does_exist_and_is_file( s_file ) ):
				ls_bad_filenames.append( s_file + MSG_NOT_EXIST )	
			elif len( s_basename )\
					> MAX_GENEPOP_FILE_NAME_LENGTH:
				ls_bad_filenames.append( s_basename + MSG_NAME_TOO_LONG )
			#end if bad filename
		#end for each file
	
		return ls_bad_filenames
	#end __get_list_bad_genepop_file_names

	def __validate_pop_and_loci_number_ranges( self ):
		'''
		2017_05_29.  This def is created to
		validate the pop and loci number range parameters.
		This will be called by def __params_look_valid.
		If invalid ranges are found, then it returns
		a string of messages specifying the error.
		Otherwise it returns an empty list.

		'''

		ls_invalidity_messages=[]

		i_minpop=self.__scheme_all_min_pop_number
		i_maxpop=self.__scheme_all_max_pop_number
		i_minloci=self.__locischeme_all_min_loci_number
		i_maxloci=self.__locischeme_all_max_loci_number
	
		dtup_ranges={ "Pop number" : ( i_minpop, i_maxpop ), 
						"Loci number" : ( i_minloci, i_maxloci ) }
		
		for s_num_range in dtup_ranges:
			i_thismin=dtup_ranges[ s_num_range ][ 0 ]
			i_thismax=dtup_ranges[ s_num_range ][ 1 ]
			if i_thismin < 1 \
					or i_thismin > i_thismax:

				ls_invalidity_messages.append( "Invalid range " \
								+ "entered for " + s_num_range \
								+ ": " + str( i_thismin ) \
								+ " to " + str( i_thismax ) \
								+ "." )
			#end if range invald
		#end for each range		

		return ls_invalidity_messages

	#end __validate_pop_and_loci_number_ranges

	def __params_look_valid( self, b_show_message=False ):

		'''
		As of 2016_08_09, this is rudimentary
		validation.  May need to be more
		fine-grained checking, as users encounter
		problem using the interface.
		'''

		b_valid=True

		s_base_msg="The program is not ready for Ne estimation.  " \
				+ "Please note the invalid parameter values:\n\n"

		ls_bad_filenames=self.__get_list_bad_genepop_file_names()

		ls_invalidity_messages=[]

		'''
		2017_05_29.  The first check is the pop and loci number ranges.
		'''
		ls_invalid_pop_or_loci_number_ranges=self.__validate_pop_and_loci_number_ranges()

		if len( ls_invalid_pop_or_loci_number_ranges ) > 0:
			ls_invalidity_messages += ls_invalid_pop_or_loci_number_ranges
			b_valid=False
		#end if invalid ranges

		BULLET="**"

		if len( ls_bad_filenames ) > 0:

			ls_invalidity_messages.append( BULLET +  "Genepop files:\n" \
					+ "\n".join( [ s_name for s_name in ls_bad_filenames ] ) )
			b_valid=False

		#end if one or more bad file names

		s_seperator=pgut.get_separator_character_for_current_os()
		s_current_output_dir=self.__output_directory.get()

		s_dir_and_basename=s_seperator.join( [ s_current_output_dir, 
												self.output_base_name ] )

		ls_existing_outfiles=pgut.get_list_files_and_dirs_from_glob( \
				s_dir_and_basename + "*" ) 

		if len( ls_existing_outfiles ) > 0:

			ls_invalidity_messages.append( \
					BULLET + "Files matching the output " \
					+ "directory and basename already exist.\n" \
					+ "Please rename either the existing files " \
					+ "or the basename/directory params.  " \
					+ "Existing files: " \
					+ "\n".join( ls_existing_outfiles ) )
			b_valid=False
		#end if outfiles exist

		#If one or more of the loaded genepop files
		#has existing intermiediate files produced
		#by a pgdriveneestimator.py run, then we want
		#to abort, since behavior of the NeEstimator given
		#existing files can cause errors, and intermediate
		#genepop files may have been (however unlikely)
		#truncated or mangled in an interrupted run:
		ls_existing_intermediate_files=\
				self.__get_existing_output_files()

		if len( ls_existing_intermediate_files ) > 0:
			ls_invalidity_messages.append( BULLET \
					+ "Intermediate files from " \
					+ "an interrupted run exist:\n" \
					+ "\n".join( ls_existing_intermediate_files )
					+ "\n\nPlease either move/remove the intermediate files " \
					+ "or load genepop files whose names do not prefix the "
					+ "intermediate files." )
			b_valid=False
		#end if we have existing intermediate files
	
		if self.__minallelefreq > 1.0 or self.__minallelefreq < 0:
			ls_invalidity_messages.append( BULLET + "Minimum allele frequence " \
					+ "value must be > 0.0 and <= 1.0.\n" \
					+ "Current value: " + str( self.__minallelefreq ) + "." )
			b_valid=False
		#end if invalid min allele freq

		i_num_cpus=pgut.get_cpu_count()

		#if no reported cpus, assume 1
		if i_num_cpus < 1:
			i_num_cpus = 1
		#end if nu cpus < 1

		if self.__processes < 1 or self.__processes > i_num_cpus:
			ls_invalidity_messages.append(  BULLET + "Number of prcesses must be at least 1 and " \
					+ "no more than " + str( i_num_cpus ) + ".  " \
					+ "Current value: " + str( self.__processes ) + "." )
			b_valid=False
		#end if process total invalid

		if not b_valid:
			s_info_msg=s_base_msg + "\n\n".join( ls_invalidity_messages )
			PGGUIInfoMessage( self, s_info_msg )
		#end if any invalidity

		return b_valid
	#end __params_look_valid
	
	def __get_nbne_ratio_as_string_for_call_to_estimator( self ):
		'''
		2017_02_13, implementing a bias adjustment in Nb estimations
		(via LDNE), that uses new parameter Nb/Ne ratio.  This new parm
		in our Nb estimation interface is used only if the value
		is not found in the genepop file header (via parse code in 
		pgdriveneestimator.py).
		'''
		s_value="none"
		f_real_tol=1e-90
		'''
		If the value is non-zero, then we return it's string value, 
		If the value is zero, but the flag to do bias adjust is True,
		then the user is indicating the bias adjustment should be
		done using the Nb/Ne vals in the the genepop file header,
		so we send the 0.0 string value.  Otherwise, we return "None". 
		'''
		if self.__nbne > f_real_tol:
			s_value=str( self.__nbne )
		elif self.__nbne == 0.0 and self.__do_bias_adjustment == True:
			s_value=str( self.__nbne )
		#end if non-zero, or zero but doing bias adjustment
		
		return s_value
	#end __get_nbne_ratio_as_string_for_call_to_estimator

	def __make_temporary_directory_for_estimator( self, s_parent_directory ):

		self.__temporary_directory_for_estimator = \
					pgut.get_temporary_directory( s_parent_dir=s_parent_directory,
													s_prefix=( "tmp_est" ) )

		return
	#end __make_temporary_directory_for_estimator

	def runEstimator( self ):

		'''
		Creates a multiprocessing.Process instance, assigns to member
		self.__op_process.  Creates a multiprocessing.event and passes
		it to the utility function that then calls the driver that
		performs parallized Ne estimations.
		'''

		if VERBOSE:
			print( "in runEstimator..." )
			self.__test_values()
		#end if very verbose

		#Object assembles the sample-scheme related args needed for 
		#the call to the pgdriveneestimator.py module, used by
		#the run_driveneestimator_in_new_process def called below.

		o_sample_args=NeEstimatorSamplingSchemeParameterManager( o_pgguineestimator=self, 
																	s_attr_prefix=ATTRIBUTE_DEMANLGER )

		s_validation_error_message=o_sample_args.validateArgs()

		if s_validation_error_message is not None:
			s_msg="\n\nIn PGGuiNeEstimator instance, def runEstimator, " \
					"There is an invalid value in the pop sampling " \
					"parameters.  Please check that the following " \
					"criteria are met:\n\n" + s_validation_error_message \
					+ ".\n\n"
		
			raise Exception( s_msg )
		#end if invalid args
		
		#we return the sample-scheme-specific args as a sequence of strings:
		qs_sample_scheme_args=o_sample_args.getSampleSchemeArgsForDriver()

		'''
		For loci sampling (as of 2016_10_08) we have no schemes,
		only the entery "none" for the scheme attribute.
		But neestimator needs a scheme-params args (any string), so:
		'''
		#old version with no samp sechemes except "none":
		#s_loci_sampling_scheme_arg="none"
		'''
		Revisions 2016_11_07 now use new pgutility class 
		NeEstimatorLociSamplingSchemeParameterManager
		to get loci sampling args:
		'''
		o_loci_sampling_args= \
				NeEstimatorLociSamplingSchemeParameterManager( o_pgguineestimator= self,
																s_attr_prefix=ATTRIBUTE_DEMANLGER )

		
		s_validation_error_message=o_loci_sampling_args.validateArgs()

		if s_validation_error_message is not None:
			s_msg="\n\nIn PGGuiNeEstimator instance, def runEstimator, " \
					"There is an invalid value in the loci sampling " \
					"parameters.  Please check that the following " \
					"criteria are met:\n\n" + s_validation_error_message \
					+ ".\n\n"
		
			raise Exception( s_msg )
		#end if invalid args

		qs_loci_sample_scheme_args=o_loci_sampling_args.getSampleSchemeArgsForDriver()

		'''
		2017_02_13. New param nbne ratio needs processing to get correct value.
		'''
		s_nbne_ratio=self.__get_nbne_ratio_as_string_for_call_to_estimator()

		'''
		2017_04_14. New parameter tells pgdriveneestimator.py whether to run
		the Nb bias adjustment, aside from whether there is a value present
		either in the s_nbne_ratio set here, or in  the header(s) of input genpop
		file(s).
		'''
		s_do_nb_bias_adjustment=str( self.__do_bias_adjustment )

		self.__neest_multi_process_event=multiprocessing.Event()

		'''
		2017_03_27.  New class attribute __temporary_directory_for_estimator
		allows easier cleanup of intermediate files created by the estimator.
		The directory is a subdirectory inside the current output directory:
		'''
		self.__make_temporary_directory_for_estimator( self.__output_directory.get() )

		'''
		2018_03_15. We add new parameter used in the call
		to LDNe2, boolean value self.__monogamy. We put
		the arg in the order just after the allele_freq
		parmameter.
		'''

		self.__op_process=multiprocessing.Process( \
				target=pgut.run_driveneestimator_in_new_process,
					args= ( \
							self.__neest_multi_process_event,
							self.__genepopfiles.get(),
							qs_sample_scheme_args,
							self.__minallelefreq,
							self.__monogamy,
							self.__replicates,
							qs_loci_sample_scheme_args,
							self.__loci_replicates,
							self.__processes,
							self.__runmode,
							s_nbne_ratio,
							s_do_nb_bias_adjustment,
							self.__output_directory.get() \
									+ "/" \
									+ self.output_base_name,
							self.__temporary_directory_for_estimator ) )

		self.__op_process.start()
		self.__set_controls_by_run_state( self.__get_run_state() )
		self.__init_interface( b_force_disable=True )
		self.__load_param_interface( b_force_disable=True )
		self.__update_genepopfile_sampling_params_interface( b_force_disable=True )
		self.__update_genepopfile_loci_sampling_params_interface( b_force_disable=True )
		self.__run_state_message="  " + ESTIMATION_RUNNING_MSG
		self.__plotting_program_needs_to_be_run=True 
		self.after( 500, self.__check_progress_operation_process )

		if VERY_VERBOSE:
			print( "running estimator" )
		#end if very verbose

		return
	#end runEstimator

	def __get_genepop_files_value_for_textbox( self ):
		'''
		This def was added 20170710 to solve a problem
		in the GUI in Windows machines.  When many
		genepop file names are loaded into the interface
		via the def __load_genepop_files, say over a few hundered,
		then the Windows machine GUI becomes non-responsive.
		In the case of a low powered machine, and many
		files, the GUI could freeze it indefintely.  The
		blocking occurs, apparently, when a large string
		is given to a textbox as it's value.  Linux 
		seemed to be immune from the problem.
		'''
		MAX_NUM_FILE_NAMES_IN_TEXTBOX=10

		s_value_for_textbox=""

		s_current_genepop_files_value=self.__genepopfiles.get()

		i_num_files_selected=\
				len( s_current_genepop_files_value.split( DELIMITER_GENEPOP_FILES ) )
		
		if i_num_files_selected > MAX_NUM_FILE_NAMES_IN_TEXTBOX:
			ls_files=s_current_genepop_files_value.split( DELIMITER_GENEPOP_FILES )
			s_value_for_textbox=DELIMITER_GENEPOP_FILES.join( ls_files[ 0:MAX_NUM_FILE_NAMES_IN_TEXTBOX ] + [ "..."] )
		else:
			s_value_for_textbox=s_current_genepop_files_value
		#end if our list of genepop files is too large, else not

		return s_value_for_textbox
	#end __get_genepop_files_value_for_textbox

	def __init_file_locations_interface( self, b_force_disable=False ):
		'''
		2017_04_28.  Some labels, with widths sized on linux,
		are too small in Windows, so that text gets truncated.
		'''
		b_is_windows_platform=pgut.is_windows_platform()
		ENTRY_WIDTH=70
		LABEL_WIDTH= 22 if b_is_windows_platform else 20
		LOCATIONS_FRAME_PADDING=30
		LOCATIONS_FRAME_LABEL="Load/Run"
		LOCATIONS_FRAME_STYLE="groove"
		RUNBUTTON_PADDING=0o7	

		o_file_locations_subframe=LabelFrame( self,
				padding=LOCATIONS_FRAME_PADDING,
				relief=LOCATIONS_FRAME_STYLE,
				text=LOCATIONS_FRAME_LABEL )

		self.__interface_subframes[ "filelocations" ] = o_file_locations_subframe
		i_row=0

		'''
		To keep the run/cancel button close to
		a label that is a (primiive) progress message
		we put themn in a frame that itself, will be
		inside the file-locations subframe.
		'''
		o_run_sub_subframe=Frame( o_file_locations_subframe )

		i_tot_procs=pgut.get_cpu_count()

	
		'''
		2017_10_19. Instead of defaulting to 1.0, 
		we'll use half the available cpus.
		'''
		if self.__processes is None:
			i_floor=int( i_tot_procs/2.0 )
			self.__processes=1 if i_floor == 0 else i_floor
		#end assign min if not set


		o_tot_process_validator=FloatIntStringParamValidity( \
					"proccess total",
					int, self.__processes, 
					1, i_tot_procs )

		o_tot_process_kv=KeyValFrame( s_name="Total processes: ", 
						v_value=self.__processes,
						o_type=int,
						v_default_value="",
						o_master=o_run_sub_subframe,
						o_associated_attribute_object=self,
						s_associated_attribute="_PGGuiNeEstimator__processes",
						s_entry_justify='left',
						s_label_justify='left',
						s_button_text="Select",
						b_force_disable=b_force_disable,
						o_validity_tester= o_tot_process_validator,
						s_tooltip = "Ne estimator can allocate one process " \
								+ "for each pop, and within pop, each subsample " \
								+ "percentate or remove-N value or replicate. " )
		#The label should always be non-grayed-out:
		o_tot_process_kv.setLabelState( "enabled" )

		o_tot_process_kv.grid( row=i_row, column=0, sticky=( NW ) )

		self.__run_button=Button( o_run_sub_subframe, 
						command= \
							self.__on_click_run_or_cancel_neestimation_button )
		
		self.__run_button.grid( row=i_row, column=1, sticky=( NW ), padx=RUNBUTTON_PADDING )

		#this label will have text showing when an estimation
		#is running:
		self.__run_state_label=Label( o_run_sub_subframe, text=self.__run_state_message )

		self.__run_state_label.grid( row=i_row, column=2, sticky=( SW ) )

		o_run_sub_subframe.grid( row=i_row, sticky=( NW ) )

		i_row += 1
		
		'''
		20170710.  This call is added to avoid the KeyValFrame
		having to load a very large string into its text box.  On
		Windows machines, especially underpowered machines,
		this caused a prolonged block of the main gui thread
		on all graphical updates.
		'''
		s_value_for_textbox=self.__get_genepop_files_value_for_textbox()

		o_config_kv=KeyValFrame( s_name="Load genepop files", 
						v_value=s_value_for_textbox,
						o_type=str,
						v_default_value="",
						o_master=o_file_locations_subframe,
						i_entrywidth=ENTRY_WIDTH,
						i_labelwidth=LABEL_WIDTH,
						b_is_enabled=False,
						s_entry_justify='left',
						s_label_justify='left',
						s_button_text="Select",
						def_button_command=self.__load_genepop_files,
						b_force_disable=b_force_disable,
						s_tooltip = "Load genepop files" )

		'''
		We override the disabled setting for the label.  While
		the entry box should always be disabled, the label should
		be enabled.
		'''
		o_config_kv.setLabelState( "enabled" )

		o_config_kv.grid( row=i_row, sticky=( NW ) )

		i_row+=1

		o_outdir_kv=KeyValFrame( s_name="Select output directory", 
					v_value=self.__output_directory.get(), 
					o_type=str,
					v_default_value="",
					o_master=o_file_locations_subframe,
					i_entrywidth=ENTRY_WIDTH,
					i_labelwidth=LABEL_WIDTH,
					b_is_enabled=False,
					s_entry_justify='left',
					s_label_justify='left', 
					s_button_text="Select",
					def_button_command=self.__select_output_directory,
					b_force_disable=b_force_disable )

		'''
		The label is enabled as for the "Load genepop files" entrybox.
		'''
		o_outdir_kv.setLabelState( "enabled" )

		o_outdir_kv.grid( row= i_row, sticky=( NW ) )

		i_row+=1

		self.__outbase_kv=KeyValFrame( s_name="Output files base name: ", 
					v_value=self.output_base_name, 
					v_default_value="",
					o_type=str,
					o_master=o_file_locations_subframe, 
					i_entrywidth=ENTRY_WIDTH,
					i_labelwidth=LABEL_WIDTH,
					s_associated_attribute="output_base_name",
					o_associated_attribute_object=self,
					def_entry_change_command=self.__test_values,
					s_entry_justify='left',
					s_label_justify='left',
					b_force_disable=b_force_disable ) 

		self.__outbase_kv.grid( row=i_row, sticky=( NW ) )

		o_file_locations_subframe.grid( row=ROW_NUM_FILE_LOCATIONS_FRAME,
										sticky=(NW) )
		o_file_locations_subframe.grid_columnconfigure( 0, weight=1 )
		o_file_locations_subframe.grid_rowconfigure( 0, weight=1 )
	#end __init_file_locations_interface

	def __init_file_info_interface( self ):

		LISTBOX_WIDTH=50
		LISTBOX_HEIGHT=5

		#as of 2016_08_08, tried to set foreground before and after
		#enabling/disabling in def __update_genepop_file_listbox(),
		#and also changing foreground using listbox.configitem, but
		#i guess when in disabled state, these values are ignored,
		#and the font color defaults to a barely readable light gray
		#(in Linux at least):

		LISTBOX_FOREGROUND="black"

		#this will affect the disabled state's background, 
		#but due to having found no way to change the light grey
		#forground of the disabled font, I'll default here to
		#white for now:
		LISTBOX_BACKGROUND="white"

		LOCATIONS_FRAME_PADDING=10
		LOCATIONS_FRAME_LABEL="Genepop Files Loaded for Estimation"
		LOCATIONS_FRAME_STYLE="groove"

		o_file_info_subframe=LabelFrame( self,
				padding=LOCATIONS_FRAME_PADDING,
				relief=LOCATIONS_FRAME_STYLE,
				text=LOCATIONS_FRAME_LABEL )

		self.__interface_subframes[ "fileinfo" ]=o_file_info_subframe 

		i_row=0

		o_scrollbar_vert=FredLundhsAutoScrollbar( o_file_info_subframe,
												orient=VERTICAL )

		self.__genepop_files_listbox=Listbox( o_file_info_subframe, 
										width=LISTBOX_WIDTH,
										height=LISTBOX_HEIGHT,
										background=LISTBOX_BACKGROUND,
										foreground=LISTBOX_FOREGROUND )

		o_scrollbar_vert.config( command=self.__genepop_files_listbox.yview )
		o_scrollbar_vert.grid( row=0, column=2, sticky=( N, S ) )

		self.__update_genepop_file_listbox()

		self.__genepop_files_listbox.grid( row=i_row, sticky=( NW ) )

		o_file_info_subframe.grid( row=ROW_NUM_FILE_INFO_FRAME,
										sticky=(NW) )

		o_file_info_subframe.grid_columnconfigure( 0, weight=1 )
		o_file_info_subframe.grid_rowconfigure( 0, weight=1 )

	#end __init_file_info_interface

	def __update_genepop_file_listbox( self ):
		self.__genepop_files_listbox.config( state="normal" )

		#clear the list box of current entries:

		self.__genepop_files_listbox.delete( 0, END )

		s_genepopfiles=self.__genepopfiles.get()

		ls_files=s_genepopfiles.split( DELIMITER_GENEPOP_FILES )	

		ls_basenames=[ pgut.get_basename_from_path( s_file ) \
										for s_file in ls_files ]

		ls_basenames.sort()

		for s_basename  in ls_basenames:
			self.__genepop_files_listbox.insert( END, s_basename )
			self.__genepop_files_listbox.itemconfig( END, foreground="white" )
		#end for each basename

		self.__genepop_files_listbox.config( state="disabled" )

		return
	#end __update_genepop_file_listbox

	def __init_interface( self, b_force_disable=False ):
		'''
		Create the controls first needed, 
		like those to get file locations,
		and the listbox that diplays the loaded
		genepop files.

		param b_force_disable, when true, is passed to
		the file-locations interface controls, which
		are subsequencly all set to disable.
		'''
		
		self.__init_file_locations_interface( b_force_disable )
		self.__init_file_info_interface()	

		self.grid_columnconfigure( 0, weight=1 )
		self.grid_rowconfigure( 0, weight=1 )

		return
	#end __init_interface

	def __get_max_longname_length( self ):
		'''
		long names are the parameter names
		used as labels in the interface.  
		We size all parameter labels to the longest.
		'''

		i_max_len=0

		i_max_len=max( [  len(s_name) for s_name in \
				self.__param_set.longnames ] ) 

		return i_max_len

	#end __get_max_longname_length

	def __create_validity_checker( self, v_init_value, s_validity_expression ):
		o_checker=ValueValidator( s_validity_expression, v_init_value )

		if not o_checker.isValid():
			s_msg="In PGGuiNeEstimator instance, " \
						+ "def __create_validity_checker, " \
						+ "invalid initial value when setting up, " \
						+ "validator object.  Validation message: " \
						+ o_checker.reportInvalidityOnly() + "."
			PGGUIErrorMessage( self, s_msg )
			raise Exception( s_msg )
		#end if not valid init value, exception

		return o_checker
	#end __create_validity_checker

	def __load_param_interface( self, 
							b_force_disable=False, 
							s_sampling_scheme_to_load="None" ):
		if VERY_VERBOSE:
			print( "in __load_param_interface")
		#end if very verbose

		PARAMETERS_FRAME_PADDING=30
		PARAMETERS_FRAME_LABEL="Parameters"
		PARAMETERS_FRAME_STYLE="groove"
		PAD_LABEL_WIDTH=0
		LABEL_WIDTH=self.__get_max_longname_length() \
				+ PAD_LABEL_WIDTH
		ENTRY_WIDTH_NON_STRING=7
		PARAMETERS_CBOX_WIDTH=20
		GRID_SPACE_HORIZ=10

		ls_params=self.__param_set.getShortnamesOrderedBySectionNumByParamNum()

		o_params_subframe=LabelFrame( self,
				padding=PARAMETERS_FRAME_PADDING,
				relief=PARAMETERS_FRAME_STYLE,
				text=PARAMETERS_FRAME_LABEL )
		self.__interface_subframes[ "params" ] =o_params_subframe

		i_row=0

		for s_param in ls_params:

			'''
			Tells which section (bordered) interface this param
			entry box or combo box or radio button should
			be placed.  As of 2016_09_15, all are in the "Paramaters" 
			section, unless marked as "suppress" in which case we
			do not offer the param for input
			'''
			'''
			This call returns
			the values from the param tag,
			but we'll only use the ones we
			need (see below):
			'''

			( s_param_longname,
				s_param_interface_section,
				i_param_section_order_number,
				i_param_column_number,
				i_param_position_in_order,
				v_param_default_value,
				o_param_type,
				v_param_min_value,
				v_param_max_value,
				s_param_tooltip,
				s_param_control_type,
				s_param_control_list,
				s_param_validity_expression,
				s_param_assoc_def,
				s_param_control_state,
				s_def_on_loading ) = \
						self.__param_set.getAllParamSettings( s_param )

			#Note that the o_param_type returned from above call
			#is, for list params, the list item type, so we
			#need this check to see if it's a list. 
			b_param_is_list=self.__param_set.paramIsList( s_param )
		
			#The name used in this PGGuiNeEstimator instance
			#to hold the parameter value (as updated by
			#the control frame (most often KeyValFrame).
			s_attr_name=ATTRIBUTE_DEMANLGER + s_param

			'''
			This will be passed to the entrybox or cbox, etc
			Control class (most often KeyValFrame).  We
			test use the current value if the attribure 
			exists in this PGGuiNeEstimator instance, 
			else use default (and create the new atttr):
			'''
			v_value_for_entry_control=None
			s_state_to_use=None

			if  hasattr( self, s_attr_name ):
				v_value_for_entry_control=getattr( self, s_attr_name )
				'''
				We also want to retain the state flag:
				'''

				if self.__param_frame_reference_is_available( s_param ):
					b_current_val_for_enabled=\
							self.__get_enabled_state_flag_value_for_param_control( s_param )

					if b_current_val_for_enabled==True:
						s_state_to_use="enabled"
					else:
						s_state_to_use="disabled"
					#end if flag is true, else not		
				else:
					s_state_to_use=s_param_control_state
				#end if frame ref exists

			else:
				setattr( self, s_attr_name, v_param_default_value )
				v_value_for_entry_control=v_param_default_value
				s_state_to_use=s_param_control_state
			#end if not has attr

			if s_param_interface_section != "Parameters" \
					or s_param_interface_section.startswith( "suppress" ):

				if s_param_interface_section == "suppress_and_set":
					setattr( self, s_attr_name, v_param_default_value ) 
				#end set value if interface section indicates suppress and set
					
				continue
			#end if param is to be suppressed, or is a sampling param

			#we use the first entry in the list
			#as the default value for the list editor
			#(used by the KeyValFrame object):

			if b_param_is_list:
				i_len_default_list=len( v_param_default_value )
				v_param_default_value=None if i_len_default_list == 0  else v_param_default_value[ 0 ]
			#end if param is list

#			if VERY_VERBOSE:
#				print ( "in test, param name: " + s_param )
#				print ( "in test, param value type: " +	str( o_param_type ) )
#				print ( "in test, param value: " +	str(  v_param_default_value ) )
			#end if VERY_VERBOSE

			i_width_this_entry= len( v_param_default_value ) if o_param_type == str \
					else ENTRY_WIDTH_NON_STRING

			s_this_entry_justify="left" if o_param_type == str \
					else "right"

			o_this_keyval=None

			v_default_item_value=v_param_default_value

			if b_param_is_list and v_param_default_value is not None:
				v_default_item_value=v_param_default_value[ 0 ]
			#end if the param is a list
		
			o_validity_checker=None

			if s_param_validity_expression != "None":
				'''
				Note that validity checker needs the "item" value,
				always equal to the default value, except when
				the latter is a list, in which case it is the first
				list item in the default value
				'''

				o_validity_checker=self.__create_validity_checker( v_default_item_value, 
																	s_param_validity_expression )
			#end if expression is not "None"

			v_param_assoc_def=None

			if s_param_assoc_def != "None":

				if hasattr( self, s_param_assoc_def ):
					v_param_assoc_def = getattr( self, s_param_assoc_def )
				else:
					s_msg="In PGGuiNeEstimator instance, def, __load_params_interface, " \
							+ "for parameter, " + s_param_longname \
							+ ", the parameter ParamSet object indicates that this parameter has a " \
							+ "def associated with it called, " \
							+ s_param_assoc_def + ".  This object does not have " \
							+ "a def by that name."
					raise Exception( s_msg )
				#end if we have the associated def, else error
			#end if there is a non-None value for s_param_assoc_def	

			if s_param_control_type=="entry":		
				'''
				Note that, unlike the interface presented
				by PGGuiSimuPop, for the NeEstimator interface
				we want to offer list editing, and so set
				the KeyValFrame param b_use_list_editor to True.
				(No list editor is used if tne param type is 
				not a list )
				'''	

				#Default call when entry box changed:
				def_on_entry_change=v_param_assoc_def \
									if v_param_assoc_def is not None \
													else self.__test_values

				if s_param_assoc_def != "None":
					def_on_entry_change=getattr( self,  s_param_assoc_def )
				#end if we have a named def in the param set

				o_this_keyval=KeyValFrame( s_name=s_param_longname,
					v_value=v_value_for_entry_control,
					o_type=o_param_type,
					v_default_value=v_default_item_value,
					o_master=o_params_subframe,
					o_associated_attribute_object=self,
					def_entry_change_command=def_on_entry_change,
					s_associated_attribute=s_attr_name,
					i_entrywidth=i_width_this_entry,
					i_labelwidth=LABEL_WIDTH,
					b_is_enabled=( s_state_to_use == "enabled" ),
					s_entry_justify=s_this_entry_justify,
					s_label_justify='left',
					s_tooltip=s_param_tooltip,
					o_validity_tester=o_validity_checker,
					b_force_disable=b_force_disable,
					b_use_list_editor=True )

			elif s_param_control_type.startswith( "cbox" ):
				s_state_this_cbox=None
				if s_param_control_type=="cboxnormal":
					s_state_this_cbox="normal"
				elif s_param_control_type=="cboxreadonly":
					s_state_this_cbox="readonly"
				else:
					s_msg="In PGGuiNeEstimator instance, " \
								+ "def __load_params_interface, " \
								+ "cbox control name not recognized: " \
								+ s_param_control_type + "."
					raise Exception ( s_msg )
				#end if cbox with normal state, else readonly

				qs_control_list=eval( s_param_control_list )

				def_on_combo_choice_change=None
			
				#we need to have it call our sample scheme updating
				#def when a new choice is made in the combobox		
				#if none supplied we default to the test values def
				if v_param_assoc_def is None:
					def_on_combo_choice_change=self.__test_values
				else:
					def_on_combo_choice_change=v_param_assoc_def
				#end if def is "None"

				#end if this is the genepop sample scheme combo box, else not

				i_current_item_number=1
				
				'''
				We select a combo box item number
				different than default=1, if we
				already have a current value for
				this param (attribute in our self instance)
				'''
				
				if hasattr( self, s_attr_name ): 

					s_value=getattr( self, s_attr_name )

					if s_value not in qs_control_list:
						s_msg="Current value for parameter " \
									+ s_param + " is not found " \
									+ "among the values listed as valid: " \
									+ str( qs_control_list ) + "."
						raise Exception( s_msg )
					else:
						#KeyListComboFrame init expects 1-based value, so
						#we increment the python, zero-based index
						i_current_item_number=qs_control_list.index( s_value )
						i_current_item_number +=1
					#end if current value not in value list
				#end if we have this attribute already

				o_this_keyval=KeyListComboFrame( s_name=s_param_longname,
							qs_choices=qs_control_list,
							i_default_choice_number=i_current_item_number,
							o_master=o_params_subframe,
							s_associated_attribute=s_attr_name,
							o_associated_attribute_object=self,
							def_on_new_selection=def_on_combo_choice_change,
							i_labelwidth=LABEL_WIDTH,
							i_cbox_width=PARAMETERS_CBOX_WIDTH,
							s_label_justify='left',
							s_tooltip=s_param_tooltip,
							b_is_enabled=( s_state_to_use == "enabled" ),
							b_force_disable=b_force_disable,
							s_state=s_state_this_cbox )

			elif s_param_control_type=="checkbutton":

				v_def_on_button_change=self.__test_values

				if v_param_assoc_def is not None:
					v_def_on_button_change=v_param_assoc_def
				#end if we have a def to call when the val changes

				o_this_keyval=KeyCheckboxValueFrame( s_name=s_param_longname,
														v_value=v_value_for_entry_control,
														o_master=o_params_subframe, 
														s_associated_attribute=s_attr_name,
														o_associated_attribute_object=self,
														def_on_button_change=v_def_on_button_change,
														i_labelwidth=15,
														b_is_enabled=( s_state_to_use == "enabled" ),
														s_label_justify='right',
														s_label_name=None,
														b_force_disable=b_force_disable,
														s_tooltip = s_param_tooltip )
			
			elif s_param_control_type=="radiobutton":
				raise Exception( "radio button key val not yet implemented for neestimator gui" )
			else:
				s_message="In PGGuiNeEstimator instance, " \
						+ "def load_param_interface, " \
						+ "unknownd control type read in " \
						+ "from param set: " \
						+ s_param_control_type + "."
				raise Exception( s_message )
			#end if control is entry, else cbox, else radiobutton, else unknown
		
			o_this_keyval.grid( row=i_row + ( i_param_position_in_order - 1 ), sticky=( NW ) )

			#Keep a reference to this param frame frame keyed to its attribute name
			self.__param_value_frames_by_attr_name[ s_attr_name ] = o_this_keyval

		#end for each param

		o_params_subframe.grid( row=ROW_NUM_PARAMETERS_FRAME, 
					column=COL_NUM_PARAMETERS_FRAME,
					sticky=(NW), padx=GRID_SPACE_HORIZ )

		o_params_subframe.grid_columnconfigure(0, weight=1 )
		o_params_subframe.grid_rowconfigure( 0, weight=1 )

		self.grid_columnconfigure( 1, weight=1 )
		self.grid_rowconfigure( 0, weight=1 )
		return
	#end __load_param_interface

	def __load_genepopfile_sampling_params_interface( self, 
											s_section_keyname="Sampling",
											b_force_disable=False ):
		if VERY_VERBOSE:
			print ( "in __load_genepopfile_sampling_params_interface " \
						+ "with keyname" + s_section_keyname + "." )
		#end if very verbose

		PARAMETERS_FRAME_PADDING=30
		PARAMETERS_FRAME_LABEL="Pop Sampling Parameters"
		PARAMETERS_FRAME_LOCI_SAMPLING_LABEL="Loci Sampling Parameters"
		PARAMETERS_FRAME_STYLE="groove"
		PAD_LABEL_WIDTH=0
		
		'''
		This subframe was originally part of the gneral param interface
		created in def __load_param_interface.  Because the sampling param
		interface is re-created on a change in the item choicein the sampling
		scheme combo box, we need a way to create it without recreating the
		combobox (to avoid recursive callback to the def that needs to 
		recreate these sampling-scheme-specific parameters.
		'''

		LABEL_WIDTH=self.__get_max_longname_length() \
				+ PAD_LABEL_WIDTH

		ENTRY_WIDTH_NON_STRING=7

		GRID_SPACE_HORIZ=10
	
		s_section_label=None
		s_subframe_key=None
		s_sampling_scheme_to_load=None
		i_section_row=None
		i_section_col=None

		if s_section_keyname == "Sampling":
			s_section_label=PARAMETERS_FRAME_LABEL
			s_subframe_key="samplingparams"
			s_sampling_scheme_to_load=self.__sampscheme
			i_section_row=ROW_NUM_SAMPLING_PARAMS_FRAME
			i_section_col=COL_NUM_SAMPLING_PARAMS_FRAME
		elif s_section_keyname == "LociSampling":
			s_section_label=PARAMETERS_FRAME_LOCI_SAMPLING_LABEL
			s_subframe_key="locisamplingparams"
			s_sampling_scheme_to_load=self.__locisampscheme
			i_section_row=ROW_NUM_LOCI_SAMPLING_PARAMS_FRAME
			i_section_col=COL_NUM_LOCI_SAMPLING_PARAMS_FRAME
		else:
				s_msg="In PGGuiNeEstimator instance, def __load_genepopfile_sampling_params_interface, " \
								+ "unknown value for def arg s_section_keyname.  Value passed: " \
								+ s_section_keyname + "."
				raise Exception( s_msg )
		#end if section keyname "Sampling, else LociSampling, else error"

		if s_subframe_key in self.__interface_subframes:
				self.__interface_subframes[ s_subframe_key ].grid_remove()
				self.__interface_subframes[ s_subframe_key ].destroy()
		#end if subframe already exists, get rid of it.

		o_samplingparams_subframe=LabelFrame( self,
					padding=PARAMETERS_FRAME_PADDING,
					relief=PARAMETERS_FRAME_STYLE,
					text=s_section_label )

		self.__interface_subframes[ s_subframe_key ]=o_samplingparams_subframe

		i_row=0

		ls_params=self.__param_set.getShortnamesOrderedBySectionNumByParamNum()

		for s_param in ls_params:

			v_init_value_for_keyval_control=None
			o_this_keyval=None

			( s_param_longname,
				s_param_interface_section,
				i_param_section_order_number,
				i_param_column_number,
				i_param_position_in_order,
				v_param_default_value,
				o_param_type,
				v_param_min_value,
				v_param_max_value,
				s_param_tooltip,
				s_param_control_type,
				s_param_control_list,
				s_param_validity_expression,
				s_param_assoc_def,
				s_param_control_state,
				s_def_on_loading ) = \
						self.__param_set.getAllParamSettings( s_param )

			b_param_is_list=self.__param_set.paramIsList( s_param )

			if not( s_param_interface_section.startswith( s_section_keyname ) ):
				continue
			#end if param is not in the section as identified by the keyname
			#passed by caller (or default param value).

			if s_param_interface_section.startswith( s_section_keyname ):
				s_this_param_sampling_scheme=s_param_interface_section.replace( s_section_keyname, "" )
				if s_this_param_sampling_scheme != s_sampling_scheme_to_load \
						and s_this_param_sampling_scheme != "All":
					continue
				#end if not the sampling scheme to load, and not an all-schemes sampling param
			#end if this is a sampling-scheme-specific parameter

			s_attr_name=ATTRIBUTE_DEMANLGER + s_param

			#KeyValFrame object needs a default value
			#in addition to the initial value of the param.
			#This value will match athat of the param default
			#value, except in the case of a list, in which
			#it will be the first item in the list given by
			#the param default value:
			v_default_item_value=v_param_default_value

			if b_param_is_list and v_param_default_value is not None:
				v_default_item_value=v_param_default_value[ 0 ]
			#end if the param is a list

			o_validity_checker=None

			#we use the first entry in the list
			#as the default value for the list editor
			#(used by the KeyValFrame object):

			if VERY_VERBOSE:
				print ( "in test, param name: " + s_param )
				print ( "in test, param value type: " +	str( type( v_param_default_value ) ) )
				print ( "in test, param value: " +	str(  v_param_default_value ) )
			#end if VERY_VERBOSE

			i_width_this_entry= len( v_param_default_value ) if type( v_param_default_value ) == str \
					else ENTRY_WIDTH_NON_STRING

			s_this_entry_justify="left" if type( v_param_default_value ) == str \
					else "right"

			b_attr_val_exists=hasattr( self, s_attr_name )
		
			if b_attr_val_exists:
				v_init_value_for_keyval_control=getattr( self, s_attr_name )
			else:
				v_init_value_for_keyval_control=v_param_default_value
				setattr( self, s_attr_name, v_param_default_value )
			#end if attr already exists, fill control with existing val
			#else init with default
	
			if s_param_validity_expression != "None":
				o_validity_checker=self.__create_validity_checker( \
															v_default_item_value,
															s_param_validity_expression ) 
			#end if param validity expression not "None"

			def_on_change=None

			if s_param_assoc_def == "None":
				def_on_change=self.__test_values
			else:
				def_on_change=getattr( self, s_param_assoc_def )
			#end if param's associated def is None else not None

			if s_param_control_type=="entry":		
				'''
				Note that, unlike the interface presented
				by PGGuiSimuPop, for the NeEstimator interface
				we want to offer list editing, and so set
				the KeyValFrame param b_use_list_editor to True.
				'''	
				o_this_keyval=KeyValFrame( s_name=s_param_longname,
					v_value=v_init_value_for_keyval_control,
					o_type=o_param_type,
					v_default_value=v_default_item_value,
					o_master=o_samplingparams_subframe,
					o_associated_attribute_object=self,
					def_entry_change_command=def_on_change,
					s_associated_attribute=s_attr_name,
					i_entrywidth=i_width_this_entry,
					i_labelwidth=LABEL_WIDTH,
					b_is_enabled=( s_param_control_state == "enabled" ),
					s_entry_justify=s_this_entry_justify,
					s_label_justify='left',
					s_tooltip=s_param_tooltip,
					b_force_disable=b_force_disable,
					o_validity_tester=o_validity_checker,
					b_use_list_editor=True )
			else:
				s_msg="In PGGuiNeEstimator instance, " \
						+ "def __load_genepopfile_sampling_params_interface " \
						+ ", param " + s_param + " has control type, " \
						+ s_param_control_type + ".  Currently only the Entry " \
						+ "box is implemented for the genepop file sampling " \
						+ "parameter interface."
				raise Exception( s_msg )
			#end if control type is entry, else error

			o_this_keyval.grid( row=i_row + ( i_param_position_in_order - 1 ), sticky=( NW ) )

			#So we can access attributes/defs for this frame: 
			self.__param_value_frames_by_attr_name[ s_attr_name ] = o_this_keyval
		#end for each parameter

		o_samplingparams_subframe.grid( row=i_section_row, 
										column=i_section_col,
										sticky=(NW), 
										padx=GRID_SPACE_HORIZ )

		o_samplingparams_subframe.grid_columnconfigure(0, weight=1 )
		o_samplingparams_subframe.grid_rowconfigure( 0, weight=1 )

		self.grid_columnconfigure( 1, weight=1 )
		self.grid_rowconfigure( 0, weight=1 )
		return
	#end __load_genepopfile_sampling_params_interface

	def __update_genepopfile_sampling_params_interface( self, b_force_disable=False ):
		self.__load_genepopfile_sampling_params_interface( s_section_keyname="Sampling",
																b_force_disable=b_force_disable )
		return
	#end __update_genepopfile_sampling_params_interface

	def __update_genepopfile_loci_sampling_params_interface( self, b_force_disable=False ):
		self.__load_genepopfile_sampling_params_interface( s_section_keyname="LociSampling",
																b_force_disable=b_force_disable )
		return
	#end __update_genepopfile_loci_sampling_params_interface

	def __clear_grid_below_row(self, o_frame, i_row ):

		for o_item in o_frame.grid_slaves():
			if int( o_item.grid_info()["row"]) > i_row:
				o_item.destroy()
			#end if row below i_row
		#end for each grid item
		return
	#end __clear_grid_below_row
			
	def __get_run_state( self ):
		if self.__estimation_in_progress:
			return PGGuiNeEstimator.RUN_IN_PROGRESS
		else:
			return PGGuiNeEstimator.RUN_READY
		#end if in progress else not
		return
	#end __get_run_state

	def __place_category_frames( self, do_category_frames ):
		#the file locations labelframe has row 0, 
		#(see __init_interface), so:
		FIRST_ROW_NUMBER_FOR_CATEGORY_FRAMES=1
		GRID_SPACE_VERTICAL=10
	
		for s_key in do_category_frames:
			o_frame=do_category_frames[ s_key ]
			if s_key=="none":
				i_frame_order_number=len( do_category_frames )
			else:
				 
				i_frame_order_number=int( \
							self.__param_set.getSectionOrderFromTag( s_key ) )
			#end if categore is "none" then place in last row

			i_cat_frame_row=FIRST_ROW_NUMBER_FOR_CATEGORY_FRAMES \
										+ ( i_frame_order_number - 1 )
			o_frame.grid( row=i_cat_frame_row, sticky=(NW), \
										pady=GRID_SPACE_VERTICAL )
			o_frame.grid_columnconfigure( 0, weight=1 )
			o_frame.grid_rowconfigure( 0, weight=1 )
			i_cat_frame_row+=1
		#end for each catgory frame
	#end __place_category_frames

	def __test_values( self ):
		'''
		for debugging
		'''

		if VERBOSE:
			print( "----- printing current parameter values -----" )
			ls_input_params=self.__param_set.shortnames		

			for s_param in ls_input_params:
				s_attrname=ATTRIBUTE_DEMANLGER + s_param
				if hasattr( self, s_attrname ):
					print ( s_param + "\t" \
							+ str( getattr( self, s_attrname ) ) )
				else:
					print( s_param+ "\tcurrently has no value" )
			#end for each param

			print( "output_base_name\t" + self.output_base_name )

			print ( "----- done printing current parameter values -----" )
		#end if verbose

		return
	#end __test_values

	def __load_genepop_files( self ):

		#dialog returns sequence:
		tup_genepop_files=tkfd.askopenfilenames(  \
				title='Load one or more genepop file(s)' )

		if pgut.dialog_returns_nothing(  tup_genepop_files ):
			return
		#end if no files selected

		'''
		If the askopenfilenames dialog did  not return a tuple, 
		then we assume it returned a unicode string,
		per the Windows bug noted at https://bugs.python.org/issue5712 

		Revision 2017_02_15, removed an if statement, which was 
		processing all tup_genepop_files returned from the askopenfilenames
		call.  It was an or statement starting with "If True"
		added as temp code.  The temp code was never removed, because
		as both tuples and unicode strings are properly processed 
		with the splitlist operation and the path correction for windows.
		'''
		tup_genepop_files=self.tk.splitlist( tup_genepop_files )

		#A test to fix path mangling downstream:
		s_temp_tup=()
		for s_path in tup_genepop_files:
			s_path=pgut.fix_windows_path( s_path )
			s_temp_tup+=( s_path, )
		#end for each path

		tup_genepop_files=s_temp_tup

		#string of files delimited, for member attribute 
		#that has type tkinter.StringVar
		s_genepop_files=DELIMITER_GENEPOP_FILES.join( \
								tup_genepop_files )

		self.__genepopfiles.set(s_genepop_files)

		self.__init_interface()
		self.__load_param_interface()
		self.__update_genepopfile_sampling_params_interface()
		self.__update_genepopfile_loci_sampling_params_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )

		s_nbne_state=self.__get_state_of_control( "nbne" )

		if s_nbne_state == "enabled":
			self.__evaluate_nbne_value()
		#end if nbne is enabled, set the value

		if VERY_VERBOSE:
			print ( "In def load_genepop_files, new genepop files value: " \
					+ self.__genepopfiles.get() )
			print ( "after loading genepop files" )
			self.__test_values()
		#end if very verbose

		return
	#end __load_genepop_files

	def __select_output_directory( self ):
		s_outputdir=tkfd.askdirectory( \
				title='Select a directory for file output' )
		#if no dir selected, return	

		#If user clicks on the "Cancel" button,
		#the message box returns an emtpy tuple.
		if pgut.dialog_returns_nothing ( s_outputdir ):
			return
		#end if no dir selected
		
		self.__output_directory.set( s_outputdir )
		self.__init_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )

		return
	#end __select_output_directory

	def __setup_output( self ):
		return
	#end __setup_output

	def __enable_or_disable_frames( self, b_do_enable ):
		'''
		As of 2016_08_08, not yet implemented.
		'''
		return
	#end __enable_or_disable_frames

	def __set_controls_by_run_state( self, i_run_state ):

		if i_run_state==PGGuiNeEstimator.RUN_NOT_READY:
			self.__run_button.config( text="Run Nb Estimation", 
													state="disabled" ) 
			self.__enable_or_disable_frames( b_do_enable=False )
		elif i_run_state==PGGuiNeEstimator.RUN_READY:
			self.__run_button.config( text="Run Nb Estimation", 
													state="enabled" )
			self.__enable_or_disable_frames( b_do_enable=True )
		elif i_run_state==PGGuiNeEstimator.RUN_IN_PROGRESS:
			self.__run_button.config( text="Cancel Nb Estimation", 
														state="enabled" )
			self.__enable_or_disable_frames( b_do_enable=False )
		else:
			s_msg="In PGGuiNeEstimator instance, " \
					+ "__set_controls_by_run_state: " \
					"unknown run state value: " + str( i_run_state )
			raise Exception( s_msg )
		#end if run state not ready, else ready, else in progress, 
		#else error
		return
	#end __set_controls_by_run_state

	def __update_run_state_message( self ):
		MAX_DOTS=10

		if self.__run_state_message != "":
			i_len_msg=len( self.__run_state_message )
			
			i_len_dots_stripped=len ( \
					self.__run_state_message.rstrip( "." ) )

			i_curr_num_dots=i_len_msg - i_len_dots_stripped

			if i_curr_num_dots >= MAX_DOTS:
				self.__run_state_message = \
						self.__run_state_message.rstrip( "." ) + "."
			else:
				self.__run_state_message += "."
			#end if max dots reached or exceeded, else not
		return
	#end __update_run_state_message

	def __check_progress_operation_process( self ):

		if self.__op_process is not None:
			if self.__op_process.is_alive():
				if VERY_VERBOSE:
					print ( "in __check_progress_operation_process, " \
							+ "process found alive" )
				#endif very verbose, pring

				'''
				This test is added after revisions to pgdriveneestimator.py 
				(2016_11_26) that check for a hung process pool, and in which
				if the pool times out, pgdrive def "execute_ne_for_each_sample"
				sets the multiprocessing event.  We test for it here, and terminate 
				the process if found.
				'''
				if self.__neest_multi_process_event is not None:
					if self.__neest_multi_process_event.is_set():
						self.__op_process.terminate()
						self.__op_process = None
						ls_output_files=self.__get_existing_output_files()
						self.__remove_output_files( ls_output_files )
						self.__remove_temporary_directory_used_by_estimator()
						self.__estimation_in_progress=False
						self.__set_controls_by_run_state( self.__get_run_state() )
						'''
						We want this def to be called after we've terminated
						the process, so that the GUI controls get reset:
						'''
						self.after( 500, self.__check_progress_operation_process )
						return
				#end if we have a multi processing event, check state

				self.__estimation_in_progress = True
				self.__update_run_state_message()
				self.__run_state_label.configure( text=self.__run_state_message )
				self.after( 500, self.__check_progress_operation_process )
			else:
				if VERY_VERBOSE:
					print( "In def __check_progress_operation_process, " \
								+ "process not None but not alive" )
				#end if very verbose, print

				self.__estimation_in_progress = False

				'''
				I found that the process as object will persist
				long past finishing.  In this case if the user
				closes the whole gui or the tab for this instance,
				then the cleanup will read the op_process as alive,
				and will remove output files, even though the process
				has finished:
				'''
				self.__op_process=None
				self.__neest_multi_process_event=None
				self.__remove_temporary_directory_used_by_estimator()
				self.__run_state_message=""
				self.__init_interface( b_force_disable = False )
				self.__load_param_interface( b_force_disable = False )
				self.__update_genepopfile_sampling_params_interface( b_force_disable = False )
				self.__update_genepopfile_loci_sampling_params_interface( b_force_disable = False )

			#end if process alive else not

			self.__set_controls_by_run_state( self.__get_run_state() )

		else:
			if VERY_VERBOSE:	
				print( "In def __check_progress_operation_process, " \
							+ "process found to be None." )
			#endif very verbose, pring
			self.__remove_temporary_directory_used_by_estimator()
			self.__estimation_in_progress = False
			self.__run_state_message=""
			self.__init_interface( b_force_disable = False )
			self.__load_param_interface( b_force_disable = False )
			self.__update_genepopfile_sampling_params_interface( b_force_disable = False )
			self.__update_genepopfile_loci_sampling_params_interface( b_force_disable = False )

			self.__set_controls_by_run_state( self.__get_run_state() )

		#end if process not None else None

		return
	#end __check_progress_operation_process

	def cleanup( self ):
		self.__cancel_neestimation()
		return
	#end cleanup

	def onChangeInNbBiasAdjustmentFlag( self ):
		'''
		2017_04_14.  This def was added to be associated with the checkbox
		that give True or False, whether to do an Nb bias adjustment.  We 
		want to disable the Nb/Ne ratio entry when the checkbox has updated
		our local copy of the flag to false.
		'''
		
		s_param_name="nbne"

		s_nbne_ratio_attribute_name=ATTRIBUTE_DEMANLGER + s_param_name

		if s_nbne_ratio_attribute_name not in self.__param_value_frames_by_attr_name:
			s_msg="In PGGuiNeEstimator instance, def onChangeInNbBiasAdjustmentFlag, " \
						+ "the program cannot find a key value frame associated " \
						+ "with the attribute name: " + s_nbne_ratio_attribute_name + "."
			PGGUIErrorMessage( self, s_msg )
			raise Exception( s_msg )
		#end if no key val frame for the nb/ne ratio param

		o_keyvalueframe=self.__param_value_frames_by_attr_name[ s_nbne_ratio_attribute_name ]

		if self.__do_bias_adjustment == False:
			o_keyvalueframe.setStateControls( "disabled" )
			o_keyvalueframe.setLabelState( "disabled" )
		else:
			o_keyvalueframe.setStateControls( "enabled" )
			o_keyvalueframe.setLabelState( "enabled" )
			'''
			This call will check the input genepop files (if any)
			and the current value in the interface entry for Nb/Ne,
			and will reset it if interface is zero and a unique
			value is available in the input file headers.
			'''
			self.__evaluate_nbne_value()
		#end if we are not doing a bias adjustment, else we are 

		return
	#end def onChangeInNbBiasAdjustmentFlag

	def onChangeInMonogamyFlag( self ):
		'''
		2018_03_15.  This def was added to be associated with the checkbox
		that give True or False, whether to send LDNe2's monogamy=True or
		monogamy=False. Currently there is no action needed when the flag
		state is changed.
		'''
		pass
	
		return
	#end def onChangeInMonogamyFlag


	def __get_handle_to_param_frame( self, s_param_name ):

		o_frame=None

		s_nbne_ratio_attribute_name=ATTRIBUTE_DEMANLGER + s_param_name

		if s_nbne_ratio_attribute_name in self.__param_value_frames_by_attr_name:
			
			o_frame=self.__param_value_frames_by_attr_name[ s_nbne_ratio_attribute_name ]

		#end if frame exists

		return o_frame

	#end __get_handle_to_param_frame

	def __param_frame_reference_is_available( self, s_param_name ):
		o_frame=self.__get_handle_to_param_frame( s_param_name )
		return ( o_frame is not None )
	#end __param_frame_reference_is_available


	def __get_enabled_state_flag_value_for_param_control( self, s_param_name ):

		b_return_value=None

		o_frame=self.__get_handle_to_param_frame( s_param_name )

		if o_frame is None:
			s_msg= "In PGGuiNeEstimator instance, " \
						+ "def __get_enabled_state_flag_value_for_param_control, " \
						+ "the program cannot find a key value frame associated " \
						+ "with the parameter: " + s_param_name + "."
			PGGUIErrorMessage( self, s_msg )
			raise Exception( s_msg )
		#end if frame is not found

		b_return_value=o_frame.is_enabled

		return b_return_value
	#end __get_enabled_state_flag_value_for_param_control

			
	def __get_state_of_control( self, s_param_name ):
		'''
		2017_04_18.  Called by __load_genepop_files, to see if the
		nbne ratio is enabled (meaning the user wants to do a bias adjustment).
		If so, the new input file(s) need to be tested against the interface
		entry.
		'''

		o_keyvalueframe=s_return_value=self.__get_handle_to_param_frame( s_param_name ) 

		if o_keyvalueframe is None:
			s_msg="In PGGuiNeEstimator instance, def __get_state_of_control, " \
						+ "the program cannot find a key value frame associated " \
						+ "with the parameter: " + s_param_name + "."
	
			PGGUIErrorMessage( self, s_msg )

			raise Exception( s_msg )
		#end if no frame with this param name

		ls_states=o_keyvalueframe.getControlStates()

		if set( ls_states ) == { "enabled" }:
			s_return_value="enabled"
		elif set( ls_states ) == { "disabled" }:
			s_return_value="disabled"
		else:
			s_msg="In PGGuiNeEstimator instance, def __get_state_of_control, " \
							+ "the control state has an unexpected set of values: " \
							+ str( ls_states ) + "."
			PGGUIErrorMessage( self, s_msg )
			raise Exception( s_msg )
		return  s_return_value
	#end __get_state_of_control

	def __get_nbne_values_from_genepop_file_headers( self ):

		lf_nbne_values=[]
		dli_file_number_by_nbne_value={}
		i_total_files_read=0
		if self.__genepopfiles is not None:
			s_genepop_files=self.__genepopfiles.get()
			ls_genepop_files=s_genepop_files.split( DELIMITER_GENEPOP_FILES )

			for s_genepop_file in ls_genepop_files:

				if os.path.isfile( s_genepop_file ):
					i_total_files_read+=1
					o_nbne_reader=NbNeReader( s_genepop_file )

					v_ratio=o_nbne_reader.nbne_ratio

					if v_ratio in dli_file_number_by_nbne_value:
						dli_file_number_by_nbne_value[ v_ratio ].append( i_total_files_read )
					else:
						dli_file_number_by_nbne_value[ v_ratio ] = [ i_total_files_read ]
					#end if we have already recorded this value in another file, else new
				#end if file exists		
			#end for each file name
		#end if we have genepop file names
		dlv_value_by_file_number_list={}

		'''
		We convert the dict to another that will be more human-
		readable when we include in a message to the reader.
		'''
		if len( dli_file_number_by_nbne_value ) == 1:

			li_file_numbers=list( dli_file_number_by_nbne_value.values() )[ 0 ]
			i_total_files=len( li_file_numbers )

			i_min=min( li_file_numbers )
			i_max=max( li_file_numbers )

			if i_total_files==1:
				s_this_file_list="File "
			else:
				s_this_file_list="Files "  + str( i_min ) + "-" + str( i_max )
			#end if for the single Nb/Ne ratio there is one file only, else a range

			v_val=list( dli_file_number_by_nbne_value.keys() ) [ 0 ] 
			dlv_value_by_file_number_list[ s_this_file_list ] = v_val
		else:
			for v_val in dli_file_number_by_nbne_value:
				li_file_numbers=dli_file_number_by_nbne_value[ v_val ]
				s_this_file_list="File number(s) " + \
							",".join( str(i_num) for i_num in li_file_numbers ) 
				dlv_value_by_file_number_list[ s_this_file_list ] = v_val
		#end if only 1 value, else multiple

		return dlv_value_by_file_number_list 

	#end __get_nbne_values_from_genepop_file_headers		

	def __evaluate_nbne_value( self, b_manually_update=True ):

		s_msg=None

		f_reltol=1e-90

		v_value_in_files=None

		dlv_nbne_values_by_file_numbers= \
					self.__get_nbne_values_from_genepop_file_headers()

		if self.__nbne < f_reltol:
			if len( dlv_nbne_values_by_file_numbers ) == 1:

				f_ratio_val=list( dlv_nbne_values_by_file_numbers.values() ) [ 0 ]

				if f_ratio_val is not None:
					o_frame=self.__get_handle_to_param_frame( "nbne" )
					if o_frame is None:
						s_msg="In PGGuiNeEstimator instance, def __evaluate_nbne_value, " \
								+ "The control frame for the Nb/Ne ratio entry box "  \
								+ "is not found."
						PGGUIErrorMessage( self, s_msg )
						raise Exception( s_msg )
					else:
					
						if b_manually_update:
							s_msg="The program found an Nb/Ne ratio in your input file(s), " \
									+ "and is loading it into the Nb/Ne entry box.  " \
									+ "You can replace it with any non-zero value if " \
									+ "you want to override the ratio given in your input file(s)."
							o_frame.manuallyUpdateValue( f_ratio_val )
						else:
							s_msg="The program found an Nb/Ne ratio in your input file(s): " \
									+ str( f_ratio_val ) + ".\n" \
									+ "  You can enter any non-zero value in the interface Nb/Ne ratio " \
									+ "to override it.  If you leave the bias adjustment checkbox checked, " \
									+ "and enter zero in the Nb/Ne ratio entry box, the program will" \
									+ "perform an Nb bias adjustment using the value found in your input file(s)."						
						#end if we should manually update, else not
					#end if we can't find the nbne frame, else set it
				#end if non-None value, update the entry

			elif len( dlv_nbne_values_by_file_numbers ) == 0:
				#There are no nb/ne ratio values in the header. Do nothing.
				pass
			else:
				s_msg="The program found the following values for Nb/Ne among your input " \
							+ "genepop files:\n" + str( dlv_nbne_values_by_file_numbers ) + "\n" \
							+ "If you leave the Nb/Ne ratio in the interface set to zero, " \
							+ "and check the box that indicates you want to do a " \
							+ "bias adjustment, each genepop file's Nb/Ne ratio will be " \
							+ "used to perform a bias adjustment on that file's estimates."
			#end if a single nb/ne value, else if no nb/ne values, else multiple values
		else:
			i_num_values_in_files=len( dlv_nbne_values_by_file_numbers )
			if i_num_values_in_files > 0:
				if i_num_values_in_files==1:
					v_value_in_files=list( dlv_nbne_values_by_file_numbers.values() )[0]
					if v_value_in_files is not None:
						if abs( v_value_in_files - self.__nbne ) > f_reltol:
							if b_manually_update:
								#The entry in the interface differs from a 
								#uniq value found in the genepop files.
								s_msg="The program found an Nb/Ne ratio given in your input " \
											+ "genepop files:\n" + str( dlv_nbne_values_by_file_numbers ) + ".\n" \
											+ "Any non-zero entry you set in the Nb/Ne ratio interface " \
											+ "entry box will override the value found in your input files. " \
											+ "Would you like to use the value found in your input files? " 
								o_msgbox=PGGUIYesNoMessage( self, s_msg )

								b_response=o_msgbox.user_response

								#reset msg to None, since we no longer need any
								#message sent to the user:
								s_msg=None

								if b_response==True:
									o_nbne_control_frame=self.__get_handle_to_param_frame( "nbne" )
									if o_nbne_control_frame is not None:
										o_nbne_control_frame.manuallyUpdateValue( v_value_in_files )
									else:
										s_msg="In PGGuiNeEstimator instance, def __evaluate_nbne_value, " \
											+ "The control frame for the Nb/Ne ratio entry box "  \
											+ "is not found."
										PGGUIErrorMessage( self, s_msg )
										raise Exception( s_msg )
									#end if frame exists, else error
								#end if user responds "yes"
							else:
								s_msg="The program found an Nb/Ne ratio given in your input " \
											+ "genepop files:\n" + str( dlv_nbne_values_by_file_numbers ) + ".\n" \
											+ "Any non-zero entry you set in the Nb/Ne ratio interface " \
											+ "entry box will override the value found in your input files.\n"  \
											+ "If you set the interface value to zero, but leave the bias adjustment " \
											+ "checkbox checked, the program will do a bias adjustment using the "  \
											+ "value found in your input files.\n"
							#end if we should ask the user if we should manually update, else just show a messgae
						#end if the value in the interface does not match the one in the inpu files
				else:
					s_msg="The program found Nb/Ne ratio values in the headers in your genepop " \
							+ "input files:\n" + str( dlv_nbne_values_by_file_numbers ) + "\n"  \
							+ "The non-zero ratio currently set " \
							+ "in the interface will override the value(s) found in the " \
							+ "genepop file header lines.  To use the values given in the genepop files " \
							+ "set the value in the interface to zero, but keep the bias-adjustment " \
							+ "checkbox checked."
				#end if there is one value in files, else not	
			#end if there is at least one nb/ne ratios in the genepop file headers
		#end if interface nb/ne ratio is set to zero, else not	

		if s_msg is not None:
			PGGUIInfoMessage( self, s_msg )
		#end if s_msg is not None

		return
	#end __evaluate_nbne_value

	def onNbNeRatioChange( self ):
		'''
		2017_04_20.  Currently no action on value change.
		'''
		return
	#end onNbNeRatioChange

#end class PGGuiNeEstimator 

if __name__ == "__main__":

	import sys
	ls_args=[ "param names file" ]
	from tkinter import *
	from tkinter.ttk import *

	s_usage=pgut.do_usage_check( sys.argv, ls_args )
	 
	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	s_param_file=sys.argv[1]

	mymaster=Tk()

	o_me=PGGuiNeEstimator( mymaster, s_param_file )

	o_me.grid()

	mymaster.mainloop()
	pass
#end if main

