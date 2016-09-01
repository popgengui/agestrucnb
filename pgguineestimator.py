'''
Description
A PGGuiApp object with widgets that manage an Ne-estimation using
a pgopsimupop object, itself calling Tiago's pygenomics.popgen.ne2.controller
object.
'''

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

ROW_NUM_FILE_LOCATIONS_FRAME=0
ROW_NUM_FILE_INFO_FRAME=1
ROW_NUM_PARAMETERS_FRAME=0
COL_NUM_PARAMETERS_FRAME=1

from Tkinter import *
from ttk import *
import tkFileDialog as tkfd

#need a seperate, non-blocking
#process for the neestimations
#(see def runEstimator)
import multiprocessing

#killing the neestimation pool
#takes some signalling and sleeping
#see def __cancel_neestimation 
import time

import pgguiapp as pgg
import pgutilities as pgut
import pgparamset as pgps
import pgdriveneestimator as pgdn

from pgguiutilities import KeyValFrame
from pgguiutilities import KeyCategoricalValueFrame
from pgguiutilities import FredLundhsAutoScrollbar
from pgguiutilities import PGGUIInfoMessage
from pgguiutilities import PGGUIYesNoMessage

from pgutilityclasses import FloatIntStringParamValidity
from pgdriveneestimator import MAX_GENEPOP_FILE_NAME_LENGTH


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
						s_name="ne_estimator_gui" ):

		'''
		param o_parent is the tkinter window that hosts this gui.  I is meant to be the same parent as that which hosts other pg interfaces, like pgguisimupop objects.
		param s_param_names_file is the file that contains short and long param names, used to make a PGParamSet object, in turn used to setup the gpdriveneestimator call.
		param s_name gives the parent PGGuiApp's name (currently, Fri Aug  5 16:48:08 MDT 2016, of no importance).
		param i_total_processes_for_est, integer given the number of processes to assign to the ne-estimation, which does each population in each genepop file in a separate python, mulitiprocessing.process.
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
		#no StringVar because we want
		#the KeyValFrame to set this
		#directly:
		self.output_base_name=""

		#attributes for the parameters
		self.__sampscheme=None
		self.__sampparam=None
		self.__minpopsize=None
		self.__minallelefreq=None		
		self.__replicates=None
		self.__processes=None
		self.__runmode=None

		#displays the current list of
		#genepop files loaded and ready
		#to run:
		self.__genepop_files_listbox=None

		#python multiprocessing.Process
		#spawned in def runEstimator:
		self.__op_process=None

		self.__estimation_in_progress=False
		self.__run_state_message=""

		#create interface
		self.__get_param_set( s_param_names_file )
		self.__set_initial_file_info()
		self.__set_initial_param_values()
		self.__init_interface()
		self.__load_param_interface()
		
		self.__set_controls_by_run_state( self.__get_run_state() )
		return
	#end __init__


	def __get_param_set( self, s_param_names_file ):
		self.__param_set=pgps.PGParamSet( s_param_names_file )
		return
	#end __get_param_set

	def __set_initial_file_info( self ):
		
		INIT_GENEPOP_FILE_NAME="none"
		INIT_OUTPUT_DIRECTORY=pgut.get_current_working_directory()
		INIT_OUTPUT_FILES_BASE_NAME="nb.out." \
				+ pgut.get_date_time_string_dotted()


		self.__genepopfiles.set( INIT_GENEPOP_FILE_NAME )
		self.__output_directory.set( INIT_OUTPUT_DIRECTORY )
		self.output_base_name=INIT_OUTPUT_FILES_BASE_NAME

		return
	#end __set_initial_file_info


	def __set_initial_param_values( self ):

		for s_param_name in self.__param_set.shortnames:

			s_section_name=self.__param_set.getConfigSectionNameForParam( 
					s_param_name )
			
						
			s_init_val_as_string= \
					self.__param_set.getDefaultValueForParam( \
					s_param_name )

			s_attr_name_for_this_param=ATTRIBUTE_DEMANLGER + s_param_name

			#assign the value to the attribute name 	
			setattr ( self,   s_attr_name_for_this_param, 
						eval(  s_init_val_as_string  ) )
			#end if 

		#end for each param name, set inti val

		return
	#end __set_initial_param_values

	def __on_click_run_or_cancel_neestimation_button( self ):
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
		return

	#end __on_click_run_or_cancel_neestimation_button

	def __get_path_to_genepop_files( self ):

		s_genepop_files=self.__genepopfiles.get()

		ls_genepop_files=s_genepopfiles.split( DELIMITER_GENEPOP_FILES )

		ls_paths=[]

		for s_file in ls_genepop_files:
			s_path_no_filename=pgut.get_dirname_from_filename( s_file )

			ls_paths.append( s_path_no_filename )
		#end for each genepop file, get path

		set_uniq_paths=set( ls_paths )

		if len( set_uniq_paths ) != 1:
			s_msg="In PGGuiNeEstimator instance, def pgguineestimator, " \
					+ "non-uniq path to genepop files.  List of paths: " \
					+ str( ls_paths ) + "."
			sys.stderr.write( s_msg + "\n" )
		#end if nonuniq path

		#we don't abort even in non-uniq paths, but simply return the first:
		return ls_paths[0]
	#end __get_path_to_genepop_files

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

	def __get_output_file_names( self ):
		s_path_sep=pgut.get_separator_character_for_current_os()
		s_output_base_with_path=self.__output_directory.get()  \
				+ s_path_sep \
				+ self.output_base_name

		ls_output_file_names=[ s_output_base_with_path + "." \
				+ pgut.NE_ESTIMATION_MAIN_TABLE_FILE_EXT, 
				s_output_base_with_path + "." \
				+ pgut.NE_ESTIMATION_SECONDARY_OUTPUT_FILE_EXT ]


		s_genepop_files=self.__genepopfiles.get()

		ls_genepop_files=s_genepop_files.split( DELIMITER_GENEPOP_FILES )

		for s_genepop_file in ls_genepop_files:	

			for s_tag in pgdn.NE_ESTIMATOR_OUTPUT_FILE_TAGS:

				s_reformatted_filename = \
						self.__convert_genepop_file_to_neestimator_basename ( \
																	s_genepop_file )	

				#glob basename plus wildcard, ending
				#with ne-estimator file tag.   (Wildcard
				#is needed because pgdriveneestimator.py
				#will have added sample/replicate/popnun fields
				#to the ouput file basename:
				s_glob=s_reformatted_filename + "*" + s_tag 

				ls_nefiles=pgut.get_list_files_and_dirs_from_glob( s_glob )

				if VERY_VERBOSE:
					print ( "with glob: " + s_glob )
					print ( "got files: " + str( ls_nefiles ) )
				#end if very verbose

				ls_output_file_names += ls_nefiles

			#end for each NeEstimator file tag

			#to remove the intermediate genepop file names
			#(note that this glob, if preceeded by the
			#reformatted genepop filename, would match
			#all of the intermediate files, but we keep the 
			#NE_ESTIMATOR_OUTPUT_FILE_TAGS loop in order
			#to retain that precision, to make it easier
			#to simply remove this code, to retain the
			#intermediate genepop files
			s_glob=s_reformatted_filename + "*" \
					+ pgdn.GLOB_INTERMEDIATE_GENEPOP_FILE_TAGS
			ls_intermediate_genepop_files_and_other_matches = \
					pgut.get_list_files_and_dirs_from_glob( s_glob )

			for s_file in ls_intermediate_genepop_files_and_other_matches:
				#we only want files not already fetched using the NE_ESTIMATOR_OUTPUT_FILE_TAGS:
				if s_file not in ls_output_file_names:
					ls_output_file_names.append( s_file )
				#end if new intermediate file (we infer it must be 
				#an intermediate genepop file, if it matches the glob, but was not
				#already caught using the tags), then add
			#end for each file matched
		#end for each genepop file input, make glob for 
		#ne-estimator intermediate output files

		return ls_output_file_names
	#end __get_output_file_names

	def __remove_output_files( self, ls_files_to_remove):

		if VERY_VERBOSE:
			print( "removing files: " + str( ls_files_to_remove ) )
		#end if very verbose

		pgut.remove_files( ls_files_to_remove )
		return
	#end __remove_output_files

	def __cancel_neestimation( self ):

		SLEEPTIME_WAITING_FOR_EVENT_CLEAR=0.25

		TIMEOUT_WAITING_FOR_EVENT_TO_CLEAR=05

		if self.__op_process is not None:
			
			#Process event created in def runEstimator,
			#passed to pgutitlities.run_driveneestimator_in_new_process,
			#which then passes into pgdriveneestimator.py -- the latter
			#will test it while the process.Pool def map_async is running,
			#and if set will kill the process pool:
			if self.__neest_multi_process_event is not None:
				try:

					if VERY_VERBOSE==TRUE:
						print( "in cancel_neestimation, setting event" )
					#end if very verbose

					self.__neest_multi_process_event.set()
				except o_err as Exception:
					s_msg = "in PGGuiNeEstimator instance in def " \
							+ "__cancel_neestimation, Exception after " \
							+ "setting multi process event: " \
							+ str( o_err ) + "."
					sys.stderr.write( s_msg + "\n" )
				#end try, except
			#end if event is not none

			#after we hear back from op_process via the event being
			#cleared (after we set it), we can terminate op_process:
			try:
				if VERY_VERBOSE:
					print( "sleeping before terminating proc" )
				#end if very verbose

				f_starttime=time.time()

				while self.__neest_multi_process_event.is_set() \
						and time.time() - f_starttime < \
						TIMEOUT_WAITING_FOR_EVENT_TO_CLEAR:

					if VERY_VERBOSE:
						print( "in while loop in gui while event is set" )
					#end if very verbose

					time.sleep( SLEEPTIME_WAITING_FOR_EVENT_CLEAR )
				#end while

				if VERY_VERBOSE:
					if self.__neest_multi_process_event.is_set():
						print( "timed out waiting for event to clear -- even still set. " \
								+ "Terminating op_process " )
					else:
						print( "event now clear. Terminating op_process..." )
					#end if op_process' eval in pgdriveneestimator did not clear the event, else did
				#end if very verbose

				self.__op_process.terminate()
			except o_err as Exception:
					s_msg = "in PGGuiNeEstimator instance in def " \
							+ "__cancel_neestimation, Exception after " \
							+ "terminating the process that starts " \
							+ " the estimation: "  \
							+ str( o_err ) + "."
					sys.stderr.write( s_msg + "\n" )
			#end try, except

			ls_output_files=self.__get_output_file_names()

			self.__remove_output_files( ls_output_files )

			if VERY_VERBOSE:
				print ( "removing the following output files: " \
						+ str( ls_output_files ) )
			#end if very vergbose

		else:
			s_msg="Could not cancel the Ne estimation " \
					+ "run.  The process is not found."
			sys.stderr.write( "Warning: " + s_msg  + "\n"  )
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
		s_list_of_bad_filenames_with_messages=[]

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
		Should collect all errors and present all to user at once,
		but for now will just abort on the first encountered 
		invalid param.
		'''

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
		ls_existing_intermediate_files=self.__get_output_file_names()

		if len( ls_existing_outfiles ) > 0:
			ls_invalidity_messages.append( BULLET + "Intermedate files from " \
					+ "an interrupted run exist:\n" \
					+ "\n".join( ls_existing_intermediate_files )
					+ "\nPlease either move/remove the intermediate files " \
					+ "or load genepop files whose names do not prefix the "
					+ "intermediate files." )
		#end if we have existing intermediate files

		if self.__sampscheme not in ( "percent", "remove" ):
			ls_invalidity_messages.append( BULLET + "Unknown sample scheme value: " \
					+ self.__sampscheme + "." )
			b_valid=False
		#end if bad sample scheme
		
		if self.__minpopsize < 0:
			ls_invalidity_messages.append( BULLET + "Minimum population size (must be >= 0). " \
					+ "Current value: " + str( self.__minpopsize ) + "." )
			b_valid=False
		#end if invalid min pop size

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

		if self.__runmode not in [ "default" ] +  pgdn.DebugMode.MODES:
			ls_invalidity_messages.append( BULLET + "Unknown run mode: " + self.__runmode + "." )
			b_valid=False
		#end if 

		if not b_valid:
			s_info_msg=s_base_msg + "\n\n".join( ls_invalidity_messages )
			PGGUIInfoMessage( self, s_info_msg )
		#end if any invalidity

		return b_valid
	#end __validate_run

	def runEstimator( self ):

		'''
		Creates a multiprocessing.Process instance, assigns to member
		self.__op_process.  UsCreates a multiprocessing.event and passes
		it to th
		'''

		self.__neest_multi_process_event=multiprocessing.Event()

		self.__op_process=multiprocessing.Process( \

				target=pgut.run_driveneestimator_in_new_process,
					args= ( \
						self.__neest_multi_process_event,
						self.__genepopfiles.get(),
						self.__sampscheme,
						self.__sampparam,
						self.__minpopsize,
						self.__minallelefreq,
						self.__replicates,
						self.__processes,
						self.__runmode,
						self.__output_directory.get() \
								+ "/" \
								+ self.output_base_name ) )
		

		self.__op_process.start()
		self.__set_controls_by_run_state( self.__get_run_state() )
		self.__init_interface( b_force_disable=True )
		self.__load_param_interface( b_force_disable=True )
		self.__run_state_message="  " + ESTIMATION_RUNNING_MSG
		self.after( 500, self.__check_progress_operation_process )

		if VERY_VERBOSE:
			print( "running estimator" )
		#end if very verbose

		return

	#end runEstimator

	def __init_file_locations_interface( self, b_force_disable=False ):
		ENTRY_WIDTH=30
		LABEL_WIDTH=20
		LOCATIONS_FRAME_PADDING=30
		LOCATIONS_FRAME_LABEL="Load/Run"
		LOCATIONS_FRAME_STYLE="groove"

		o_file_locations_subframe=LabelFrame( self,
				padding=LOCATIONS_FRAME_PADDING,
				relief=LOCATIONS_FRAME_STYLE,
				text=LOCATIONS_FRAME_LABEL )

		i_row=0

		'''
		To keep the run/cancel button close to
		a label that is a (primiive) progress message
		we put themn in a frame that itself, will be
		inside the file-locations subframe.
		'''
		o_run_sub_subframe=Frame( o_file_locations_subframe )

		self.__run_button=Button( o_run_sub_subframe, 
						command= \
							self.__on_click_run_or_cancel_neestimation_button )
		
		self.__run_button.grid( row=i_row, sticky=( NW )	)

		#this label will have text showing when an estimation
		#is running:
		self.__run_state_label=Label( o_run_sub_subframe, text=self.__run_state_message )

		self.__run_state_label.grid( row=i_row, column=2, sticky=( SW ) )

		o_run_sub_subframe.grid( row=i_row, sticky=( NW ) )

		i_row += 1
		
		s_curr_config_file=self.__genepopfiles.get()

		o_config_kv=KeyValFrame( "Load Genepop Files", 
						self.__genepopfiles.get(),
						o_file_locations_subframe,
						i_entrywidth=ENTRY_WIDTH,
						i_labelwidth=LABEL_WIDTH,
						b_is_enabled=False,
						s_entry_justify='left',
						s_label_justify='left',
						s_button_text="Select",
						def_button_command=self.__load_genepop_files,
						b_force_disable=b_force_disable )

		o_config_kv.grid( row=i_row, sticky=( NW ) )

		i_row+=1

		o_outdir_kv=KeyValFrame( "Select Output directory", 
					self.__output_directory.get(), 
					o_file_locations_subframe,
					i_entrywidth=ENTRY_WIDTH,
					i_labelwidth=LABEL_WIDTH,
					b_is_enabled=False,
					s_entry_justify='left',
					s_label_justify='left', 
					s_button_text="Select",
					def_button_command=self.__select_output_directory,
					b_force_disable=b_force_disable )

		o_outdir_kv.grid( row= i_row, sticky=( NW ) )

		i_row+=1

		self.__outbase_kv=KeyValFrame( s_name="Output files base name: ", 
					v_value=self.output_base_name, 
					o_master=o_file_locations_subframe, 
					i_entrywidth=ENTRY_WIDTH,
					i_labelwidth=LABEL_WIDTH,
					s_associated_attribute="output_base_name",
					o_associated_attribute_object=self,
					def_entry_change_command=self.__test_value,
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

	def __update_basename( self, s_val ):
		self.__basename.set( s_val )
		return
	#end __update_basename

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

	def __load_param_interface( self, b_force_disable=False ):

		PARAMETERS_FRAME_PADDING=30
		PARAMETERS_FRAME_LABEL="Parameters"
		PARAMETERS_FRAME_STYLE="groove"
		PAD_LABEL_WIDTH=-3

		'''
		As of 2016_08_09, not ready for user to
		access these -- currently means the Ne estimation
		will involve no subsampling of pops in the genepop
		files, and output will be the standard table 
		ie DebugMode in pgdriveneestimator.py is set at
		"no_debug")
		'''
		HIDDEN_PARAMS=[ "sampscheme", "sampparam", "runmode" ]

		LABEL_WIDTH=self.__get_max_longname_length() \
				+ PAD_LABEL_WIDTH

		ENTRY_WIDTH_NON_STRING=7

		GRID_SPACE_HORIZ=10
		
		ls_params=self.__param_set.shortnames

		o_params_subframe=LabelFrame( self,
				padding=PARAMETERS_FRAME_PADDING,
				relief=PARAMETERS_FRAME_STYLE,
				text=PARAMETERS_FRAME_LABEL )

		i_row=0

		for s_param in ls_params:

			if s_param in HIDDEN_PARAMS:
				continue
			#end if hidden param

			s_attr_name=ATTRIBUTE_DEMANLGER + s_param
			v_val=eval (  "self." + s_attr_name )
			s_longname=self.__param_set.longname( s_param )
			s_tooltip=self.__param_set.getToolTipForParam( s_param )

			if VERY_VERBOSE:
				print ( "in test, param name: " + s_param )
				print ( "in test, param value type: " +	str( type( v_val ) ) )
				print ( "in test, param value: " +	str(  v_val ) )
			#end if VERY_VERBOSE

			i_width_this_entry= len( v_val ) if type( v_val ) == str \
					else ENTRY_WIDTH_NON_STRING
			s_this_entry_justify="left" if type( v_val ) == str \
					else "right"
			
			o_this_keyval=KeyValFrame( s_longname,
				v_val,
				o_params_subframe,
				o_associated_attribute_object=self,
				def_entry_change_command=self.__test_value,
				s_associated_attribute=s_attr_name,
				i_entrywidth=i_width_this_entry,
				i_labelwidth=LABEL_WIDTH,
				b_is_enabled=True,
				s_entry_justify=s_this_entry_justify,
				s_label_justify='left',
				s_tooltip=s_tooltip,
				b_force_disable=b_force_disable )

			o_this_keyval.grid( row=i_row, sticky=( NW ) )

			i_row += 1
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
				s_frame_label=\
						self.__param_set.getConfigSectionNameFromTag( s_key ) 
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

	def __test_value( self ):
		'''
		for debugging
		'''

		if VERBOSE:
			ls_input_params=self.__param_set.shortnames		

			for s_param in ls_input_params:
				s_attrname=ATTRIBUTE_DEMANLGER + s_param
				print ( s_param + "\t" \
						+ str( getattr( self, s_attrname ) ) )
			#end for each param

			print( "output_base_name\t" + self.output_base_name )
		#end if verbose

		return
	#end __test_value

	def __load_genepop_files( self ):

		s_current_value=self.__genepopfiles.get()

		#dialog returns sequence:
		q_genepop_filesconfig_file=tkfd.askopenfilenames(  \
				title='Load a genepop file' )

	
		if len( q_genepop_filesconfig_file ) == 0:
			return
		#end if no files selected

		#string of files delimited, for member attribute 
		#that has type tkinter.StringVar
		s_genepop_files=DELIMITER_GENEPOP_FILES.join( \
								q_genepop_filesconfig_file )
		self.__genepopfiles.set(s_genepop_files)

		self.__init_interface()
		self.__load_param_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )

		if VERY_VERBOSE:
			print ( "new genepop files value: " \
					+ self.__genepopfiles.get() )
		#end if very verbose

		return
	#end load_genepop_files

	def __select_output_directory( self ):
		s_outputdir=tkfd.askdirectory( \
				title='Select a directory for file output' )
		#if no dir selected, return	

		if s_outputdir=="":
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
					print ( "checking and process found alive" )
				#endif very verbose, pring
				self.__estimation_in_progress = True
				self.__update_run_state_message()
				self.__run_state_label.configure( text=self.__run_state_message )
				self.after( 500, self.__check_progress_operation_process )
			else:
				if VERY_VERBOSE:
					print( "checking and process not None but not alive" )
				#end if very verbose, print
				
				self.__estimation_in_progress = False

				#found that the process as object will persist
				#long past finishing.  In this case if the user
				#closes the whole gui or the tab for this instance,
				#then the cleanup will read the op_process as alive,
				#and will remove output files, even though the process
				#has finished:
				self.__op_process=None
				self.__neest_multi_process_event=None
				self.__run_state_message=""
				self.__init_interface( b_force_disable = False )
				self.__load_param_interface( b_force_disable = False )

			#end if process alive else not

			self.__set_controls_by_run_state( self.__get_run_state() )

		else:
			if VERY_VERBOSE:	
				print( "process found to be None" )
			#endif very verbose, pring

			self.__estimation_in_progress_is_in_progress = False
			self.__run_state_message=""
			self.__init_interface( b_force_disable = False )
			self.__load_param_interface( b_force_disable = False )


			self.__set_controls_by_run_state( self.__get_run_state() )

		#end if process not None else None

		return
	#end __check_progress_operation_process

	def cleanup( self ):
		self.__cancel_neestimation()
		return
	#end cleanup

#end class PGGuiNeEstimator


if __name__ == "__main__":

	import sys
	ls_args=[ "param names file" ]
	from Tkinter import *
	from ttk import *

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

