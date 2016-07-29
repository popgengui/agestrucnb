'''
Description
A PGGUIApp object with widgets that manage a simuPop simulation
'''
__filename__ = "pgsimupopper.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE_CONSOLE=True
VERY_VERBOSE_CONSOLE=True
DO_PUDB=False
INIT_ENTRY_CONFIG_FILE=()

if DO_PUDB:
	from pudb import set_trace; set_trace()
#end if debug

import pgmenubuilder as pgmb
import pgguiapp as pgg
import pgsimupopresources as pgsr
import pginputsimupop as pgin
import pgparamset as pgps
import pgoutputsimupop as pgout

from pgguiutilities import KeyValFrame
from pgguiutilities import KeyCategoricalValueFrame
from pgguiutilities import PGGUIInfoMessage
import pgutilities as pgut

#to help manage one process per replicate operation:
#(see def do_operation)
from pgutilityclasses import independantProcessGroup

import os
import multiprocessing
#to fetch all of the life tables
#for the pgsimupop:
import glob

#to help dynamically load input parameters
#by inspecting the input object:
import inspect

#to make a temp input config file,
#passed to the sub processes that will
#create and execute the sim objects:
import uuid

from Tkinter import *
#since we import all names from Tkinter,
#and ttk, we get the ttk widgets
#with their better styling,#automaitcally
#. (see #https://docs.python.org/2/library/ttk.html)
from ttk import *

import tkFileDialog as tkfd
class PGGuiSimuPop( pgg.PGGuiApp ):

	'''
	Subclass of PGGuiApp builds a gui,
	creates PGInputSimuPop and PGOutputSimuPop
	objects, then on user command runs a simulation 
	(one or more replicates) based on the parameters 
	supplied by the Input object, and to output files 
	as named by the basename in the PGOutputSimuPop object.  

	Note that for this class I abandoned my intended original 
	organization of the functionality for all  PGGuiApp objects.
	All subclasses of PGGUIApp objects were to contain an 
	AGPOperation object, in this case aPGOpSimuPop object, 
	which contains the code that actually uses Tiago Antao's 
	code to setup and run a SimuPOP session.  However, in 
	implenting replicate runs I encountered errors when
	trying to target a class method when spawning python
	multiprocessing.process objects from this object.  Further,
	I found non-independant instantiation of simupop populations 
	even when instantiating new PGOpSimuPop objects constructed
	in separate python multiprocessing.process instances.	
	Thus, parallel processing of simulation replicates required 
	the use of separate python instances for each replicate. 
	Thus currently (Wed Jul 27 18:35:05 MDT 2016),
	instead of manipulating its own PGOpSimuPop instances,
	this class depends on code in the pgutilities.py
	module, which has a def that makes a system call to 
	instantiate a new python interpreter, and call a script,
	do_sim_replicate.py, which then calls another def in 
	pgutilities.py, which builds and runs a PGOpSimuPop object.
	
	'''

	#possible states of the gui:
	RUN_NOT_READY=0
	RUN_READY=1
	RUN_IN_PROGRESS=2

	def __init__( self,  o_parent,  s_param_names_file=None, 
							s_life_table_file_glob="resources/*life.table.info",
							s_name="main_frame",
							i_total_processes_for_sims=1 ):
		'''
		param s_param_names_file is the file that contains short and long param
		names, used to make the PGParamSet object  member of the PGInputSimuPop 
		object
		'''

		#note this call to super does not work -- a look as stackoverflow
		#chatter about this indicates that because PGGUIApp inherits Frame,
		#that Frame must be an "old-style" class (does not inherit from "object")
		#--rem out super( PGGuiSimuPop, self ).__init__( o_parent )
		#instead of call to "super":
		pgg.PGGuiApp.__init__( self, s_name, o_parent )
		self.__config_file=StringVar()
		self.__output_directory=StringVar()
		self.__life_table_files=[]
		self.__get_life_table_file_list( s_life_table_file_glob )

		#we use the tkinter traceable variable
		#so that, when loaded into an entry box
		#we can auto update the value as it is 
		#user-edited:
		self.__output_directory.set( self.__get_default_output_directory() )

		self.output_base_name=self.__get_default_output_base_name() 

		#the PGOpSimuPop object:
		self.__operation=None
		self.__param_names_file=s_param_names_file

		#input object used to make the
		#operation object type PGOpSimuPop
		self.__input=None
		#output object used to
		#name and create the simulation
		#output files
		self.__output=None

		#when commanded to run the simulation(s)
		#a temporary configuration file
		#is created and used by each process
		#that is simulating.  We then want to
		#delete the file when the gui had 
		#ascertained that the sim is or sims
		#are done, so we need instance-level
		#access to the file name
		self.__temp_config_file_for_running_replicates=None

		#simulations performed on separate
		#process -- this ref to it will
		#enable checking whether in progress
		#or finished.  See def runSimulation:
		self.__op_process=None

		#we have a default output name,
		#so we can init the output
		#immediately
		self.__setup_output()

		#process in which simulation 
		#operation is running, assigned
		#after input and output params
		#have been created, and the 
		#PGOpSimuPop has been created
		#and prepared:
#		self.__operation_process=None
		self.__simulation_is_in_progress=False
		self.__total_processes_for_sims=i_total_processes_for_sims

		#we hold references to all subframes
		#except the run-button subframe,
		#so that we can enable/disable
		#according to the simulation-run state:

		self.__category_frames=None

		self.__init_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )
	
		return
	#end __init__

			
	def __init_interface( self ):

		
		ENTRY_WIDTH=50
		LABEL_WIDTH=20
		LOCATIONS_FRAME_PADDING=30
		LOCATIONS_FRAME_LABEL="Load/Run"
		LOCATIONS_FRAME_STYLE="groove"

		o_file_locations_subframe=LabelFrame( self,
				padding=LOCATIONS_FRAME_PADDING,
				relief=LOCATIONS_FRAME_STYLE,
				text=LOCATIONS_FRAME_LABEL )

		i_row=0

		self.__run_button=Button( o_file_locations_subframe, command=self.__on_click_run_or_cancel_simulation_button )
		
		self.__run_button.grid( row=i_row, sticky=( NW )	)

		i_row += 1
		
		s_curr_config_file=self.__config_file.get()

		v_config_file_val="None" if s_curr_config_file == "" else s_curr_config_file

		o_config_kv=KeyValFrame( "Load Configuration File:", 
						v_config_file_val,
						o_file_locations_subframe,
						i_entrywidth=ENTRY_WIDTH,
						i_labelwidth=LABEL_WIDTH,
						b_is_enabled=False,
						s_entry_justify='left',
						s_label_justify='left',
						s_button_text="Select",
						def_button_command=self.load_config_file )
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
					def_button_command=self.select_output_directory )

		o_outdir_kv.grid( row= i_row, sticky=( NW ) )

		i_row+=1
		
		self.__outbase_kv=KeyValFrame( s_name="Output files base name: ", 
					v_value=self.output_base_name, 
					o_master=o_file_locations_subframe, 
					i_entrywidth=ENTRY_WIDTH,
					i_labelwidth=LABEL_WIDTH,
					s_associated_attribute="output_base_name",
					o_associated_attribute_object=self,
					def_entry_change_command=self.__setup_output,
					s_entry_justify='left',
					s_label_justify='left' ) 

		self.__outbase_kv.grid( row=i_row, sticky=( NW ) )

		o_file_locations_subframe.grid( row=0, sticky=(NW) )
		o_file_locations_subframe.grid_columnconfigure( 0, weight=1 )
		o_file_locations_subframe.grid_rowconfigure( 0, weight=1 )

		self.grid_columnconfigure( 0, weight=1 )
		self.grid_rowconfigure( 0, weight=1 )

		return
	#end __init_interface

	def __clear_grid_below_row(self, o_frame, i_row ):

		for o_item in o_frame.grid_slaves():
			if int( o_item.grid_info()["row"]) > i_row:
				o_item.destroy()
			#end if row below i_row
		#end for each grid item
		return
	#end __clear_grid_below_row

	def __make_category_subframes( self, set_categories ): 

		PADDING_FOR_CATEGORY_FRAME=8
		STYLE_FOR_CATEGORY_FRAME="groove"
		BORDERWIDTH_FOR_CATEGORY_FRAME=2

		do_category_frames={}

		for s_tag in set_categories:
			if s_tag=="suppress":
				continue
			#end if param is not to be shown in the interface

			#param-name tags have the category text followed by semicolon, then
			#an int, 1,2,... giving its ordinal as to its order of appearance on
			#the interface, top to bottom:
			ls_tag_fields=s_tag.split( ";" )
			s_frame_label=ls_tag_fields[ 0 ]
			do_category_frames[ s_tag ] = LabelFrame( self, 
					padding=PADDING_FOR_CATEGORY_FRAME,
					relief=STYLE_FOR_CATEGORY_FRAME,
					borderwidth=BORDERWIDTH_FOR_CATEGORY_FRAME,
					text=s_frame_label )
		#end for each tag, make a corresponding frame

		#add an "other" frame for params without
		#categories, either missing from a params file
		#or not categoriezed in the file:
		do_category_frames[ "none" ] = LabelFrame( self, 
				padding=PADDING_FOR_CATEGORY_FRAME, 
				relief=STYLE_FOR_CATEGORY_FRAME,
				borderwidth=BORDERWIDTH_FOR_CATEGORY_FRAME,
				text="Other" )
		
		return do_category_frames
	#end __make_category_subframes

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
				ls_key_fields=s_key.split( ";" )
				s_frame_label=ls_key_fields[ 0 ]
				i_frame_order_number=int( ls_key_fields[ 1 ] )
			#end if categore is "none" then place in last row

			i_cat_frame_row=FIRST_ROW_NUMBER_FOR_CATEGORY_FRAMES + ( i_frame_order_number - 1 )
			o_frame.grid( row=i_cat_frame_row, sticky=(NW), pady=GRID_SPACE_VERTICAL )
			o_frame.grid_columnconfigure( 0, weight=1 )
			o_frame.grid_rowconfigure( 0, weight=1 )
			i_cat_frame_row+=1
		#end for each catgory frame
	#end __place_category_frames
			

	def __load_values_into_interface( self ):
		'''
		in isolating the attributes
		that are strictly model params
		(and not defs or other non-param 
		attributes) I found help at:
		http://stackoverflow.com/questions/9058305/getting-attributes-of-a-class
		'''

		MAXLABELLEN=200
		WIDTHSMALL=21
		WIDTHBIG=21
		LENSMALL=20

		LABEL_WIDTH = [ WIDTHSMALL if i<LENSMALL else WIDTHBIG for i in range( MAXLABELLEN ) ] 
		
		#for parameters with this tag, we set enabled 
		#flag to false for the KeyValFrame entry box:
		CONFIG_INFO_TAG_KEYWORD="Configuration Info"

		i_row=0

		o_input=self.__input
		
		ls_input_params=[ s_param for s_param in dir( o_input ) if not( s_param.startswith( "_" ) )  ]

		ls_tags=o_input.param_names.tags

		#clear existing category frames (if any): 
		self.__clear_grid_below_row( self, 1 )

		#make frames, one for each category of parameter
		#(currently, "population", "configuration", "genome", "simulation"
		self.__category_frames=self.__make_category_subframes( set( ls_tags ) )	


		for s_param in ls_input_params:
			
			PADPIX=0

			i_row+=1
			s_longname=None
			s_nametag=None
			i_len_labelname=None


			o_def_to_run_on_value_change=None

			if VERBOSE_CONSOLE == True:
				o_def_to_run_on_value_change=self.__test_value
			#end if VERBOSE_CONSOLE

			v_val=getattr( o_input, s_param )
			
			#we don't display this if its a def
			#or a function (and so not a parameter)
			if inspect.isroutine( v_val ):
				continue
			#end if def or function

			if  type( v_val ) == str:
				if v_val.startswith( "<bound method" ):
					continue
				#end if method, skip
			#end if the value is a string

			if o_input.param_names is not None:
				#returns None if this param has no longname,
				#and the KeyValFrame will ignore s_label_name if
				#its value is None, using instead the param name 
				#as given by s_param
				s_longname=o_input.param_names.longname( s_param )
				s_nametag=o_input.param_names.tag( s_param )
			#end if we have a set of param names

			#if not in the param names file, we don't want to suppress it,
			#and we also don't suppress as long as this param is not tagged
			#as "suppress"
			if s_nametag is None or s_nametag != "suppress":

				o_frame_for_this_param=None

				if s_nametag is None or s_nametag not in self.__category_frames:
					o_frame_for_this_param=self.__do_cateory_frames[ "none" ]
				else:
					o_frame_for_this_param=self.__category_frames[ s_nametag ]
				#end if no nametag or name tag not in frame categories

				i_len_labelname=len( s_longname ) if s_longname is not None else len( s_param )
				i_width_labelname=LABEL_WIDTH[ i_len_labelname ]

				b_allow_entry_change = True

				if s_nametag is not None:
					if CONFIG_INFO_TAG_KEYWORD in s_nametag:
						b_allow_entry_change=False
					#end if input param is type config info, disable
				#end if nametag exists

				#we send in the input object to the KeyValFrame (or KeyCategoricalValueFrame 
				#instance #so it will be the object whose attribute (with name s_param)
				#is reset when user resets the value in the KeyValFrame:
				if type( v_val ) != bool:

					i_entry_width=len(v_val) if type( v_val ) == str else 7
					s_entry_justify='left' if type( v_val ) == str else 'right' 

					
					o_kv=KeyValFrame( s_param, v_val, o_frame_for_this_param, 
							o_associated_attribute_object=self.__input,
							s_associated_attribute=s_param,
							def_entry_change_command=self.__test_value,
							i_labelwidth=i_width_labelname,	
							s_label_name=s_longname,
							i_entrywidth = i_entry_width,
							s_entry_justify=s_entry_justify,
							b_is_enabled=b_allow_entry_change )
						
				else:

					#we construct a KeyCategoricalValueFrame
					#instance, and set the default button to
					#Yes (true) or No (false) according to the
					#current value:
					i_default_mode=1
					if v_val==False:
						i_default_mode = 2
					#end if

					o_kv=KeyCategoricalValueFrame( s_name=s_param, 
							lq_modes=[ ( "Yes", True ), ( "No", False ) ],
							i_default_mode_number=i_default_mode,
							o_value_type=bool,
							o_master=o_frame_for_this_param, 
							s_associated_attribute=s_param,
							o_associated_attribute_object=self.__input,
							def_on_button_change=self.__test_value,
							i_labelwidth=i_width_labelname,
							s_label_name=s_longname,
							b_buttons_in_a_row = True,
							b_is_enabled=b_allow_entry_change)

				o_kv.grid( row=i_row, sticky=(NW) )
			#end if param has non-boolean value else boolean
		#end for each input param

		self.__place_category_frames( self.__category_frames )

		#end for each param

		self.grid_columnconfigure( 0, weight=1 )
		self.grid_rowconfigure( 0, weight=1 )

		return
	#end __load_values_into_interface

	def load_config_file( self, event=None ):
		s_current_value=self.__config_file.get()
		s_config_file=tkfd.askopenfilename(  title='Load a configuration file' )
		self.__config_file.set(s_config_file)
		try:
			self.__setup_input()
		except Exception as oe:
			if s_config_file != INIT_ENTRY_CONFIG_FILE: 
				s_msg="Problem loading configuration.\n" \
						+ "File: " + str( s_config_file ) + "\n\n" \
						+ "Details:\n\n" \
						+ "Exception: " + str( oe ) + "."
				o_diag=PGGUIInfoMessage( self, s_msg )
			#end if entry not None
			return
		#end try ... except
		self.__init_interface()
		self.__load_values_into_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )
		return
	#end load_config_file

	def __get_life_table_file_list( self, s_glob_expression ):
		self.__life_table_files=glob.glob( s_glob_expression )
		return
	#end def __get_life_table_file_list

	def select_output_directory( self, event=None ):
		s_outputdir=tkfd.askdirectory( title='Select a directory for file output' )
		self.__output_directory.set( s_outputdir )
		self.__init_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )
		return
	#end select_output_directory

	def __setup_input( self ):
		o_model_resources=None
		o_param_names=None
		o_pgin=None

		if len( self.__life_table_files ) > 0:
			o_model_resources=pgsr.PGSimuPopResources( self.__life_table_files )
		#end if we have a file list

		if self.__param_names_file is not None:
			o_param_names=pgps.PGParamSet( self.__param_names_file )
		#end if param_names_file is set

		try:
			#note that we can pass None value n for o_model_resources,
			#and as long as the config file has evaluatable values for
			#all of its options, we still get a valid PGInputSimuPop object:
			o_pgin=pgin.PGInputSimuPop( self.__config_file.get(), o_model_resources, o_param_names ) 
			o_pgin.makeInputConfig()
		except Exception as exc:
			self.__config_file.set("")
			self.__input=None
			self.__clear_grid_below_row( self, 0 )
			self.__init_interface()
			self.__set_controls_by_run_state( self.__get_run_state() )
			raise exc
		#end try to make input object

		self.__input=o_pgin
		return

	#end setup_input

	def __setup_output( self ):
		s_dir_and_base=self.__output_directory.get() + "/" + self.output_base_name 
		o_pgout=pgout.PGOutputSimuPop(  s_dir_and_base )
		self.__output=o_pgout
		return
	#end setup_output

	def __test_value( self ):
		'''
		for debugging
		'''
		ls_input_params=[ s_param for s_param in dir( self.__input ) if not( s_param.startswith( "_" ) )  ]
		
		for s_param in ls_input_params:
			print s_param + "\t" + str( getattr( self.__input, s_param ) )
		#end for each param

	#end __test_value

	def __setup_op( self ):
		self.__setup_output()
		return
	#end __make_op

	def __get_default_output_base_name( self ):
		import time
		s_mytime=time.strftime( '%Y.%m.%d.%H.%M.%S' )
		return "sim.output." + s_mytime
	#end __get_default_output_base_name

	def __get_default_output_directory( self ):
		return os.getcwd()
	#end __get_default_output_directory

	def __check_progress_operation_process( self ):

		if self.__op_process is not None:
			if self.__op_process.is_alive():
				if VERY_VERBOSE_CONSOLE:
					print ( "checking and process found alive" )
				#endif very verbose, pring

				self.__simulation_is_in_progress = True
				self.after( 500, self.__check_progress_operation_process )
			else:
				if VERY_VERBOSE_CONSOLE:
					print( "checking and process not None but not alive" )
					print( "value of temp config file attribute: " \
								+ self.__temp_config_file_for_running_replicates )
				#end if very verbose, print
				self.__simulation_is_in_progress = False
				if self.__temp_config_file_for_running_replicates is not None:
					if VERY_VERBOSE_CONSOLE:
						print( "temp config file value is not None" )
					if os.path.exists( self.__temp_config_file_for_running_replicates ):
						if VERY_VERBOSE_CONSOLE:
							print ( "removing temporary config file" )
						#end if very verbose
						os.remove( self.__temp_config_file_for_running_replicates )
						self.__temp_config_file_for_running_replicates = None
					else:
						s_msg="In PGGuiSimuPop instance, def " \
							+ "__check_progress_operation_process, attribute: " \
							+ "__temp_config_file_for_running_replicates " \
							+ " is not None but does not name an existing file."

						sys.stderr.write( "Warning: " +  s_msg + "\n" )
					#if path exists else warn
				#end if attribute for temp config file is not None
			#end if process alive else not

			self.__set_controls_by_run_state( self.__get_run_state() )

		else:
			if VERY_VERBOSE_CONSOLE:	
				print( "process found to be None" )
			#endif very verbose, pring

			self.__simulation_is_in_progress = False
			self.__set_controls_by_run_state( self.__get_run_state() )

		#end if process not None else None

		return
	#end __check_progress_operation_process

	def __do_operation( self ):

		'''
		After much trial and error, with multiprocessing.Pool
		consistently failing to run independant simulations,
		and succeeding when I used individual multiprocessing.Process
		instances, also noting that using multiprocessing.Queues to manage
		multiprocessing.Processes also failed to produce independant sims.

		My ultimate solution involved creating new python instances inside
		subprocess.call calls.  However, to manage the blocked process
		that results from each use of subprocess.call(), I'm  managing these
		with python multiprocess.process instances, according to a max-process
		paramter, by using a class that simply checks for living state of 
		each and adds new processes as available (see class 
		pgutilityclasses.independantProcessGroup).		

		This def assumes that attrbute self.__temp_config_file_for_running_replicates
		has a value suitable for naming a new temp config file (see def runSimulation).
		'''	
		i_total_replicates=self.__input.reps
		i_max_processes_to_use=self.__total_processes_for_sims

		#despite the fact that ultimately the sims are done in
		#new OS processes, using new python instances, we still
		#use python.multiprocess.process instances to wrap 
		#the OS processes, since we have more convenient control over
		#their management.  This def, itself the target for multi 
		#python.multiprocessing.processes, itself spawns an OS system
		#process:
		def_target=pgut.do_sim_replicate_on_separate_os_process

		self.__input.writeInputParamsAsConfigFile( \
				self.__temp_config_file_for_running_replicates )

		i_total_replicates_started=0
		i_current_total_living_processes=0

		o_process_manager=independantProcessGroup()

		while i_total_replicates_started < i_total_replicates:
			
			i_current_total_living_processes=o_process_manager.getTotalAlive()

			#considered using at time.sleep() command inside this while loop,
			#but, because the process calling this def has only this code as its
			#province, and so is not blocking the main
			#gui, I assume it can simply get tied up in the while without huring 
			#overall performance:

			while i_current_total_living_processes == i_max_processes_to_use:
				i_current_total_living_processes=o_process_manager.getTotalAlive()
			#end while all avail processes in use, recheck

			i_num_processes_avail=i_max_processes_to_use-i_current_total_living_processes

			seq_args=( self.__temp_config_file_for_running_replicates,
						",".join( self.__life_table_files ),
						self.__param_names_file,
						self.__output.basename,
						str( i_total_replicates_started ) )

			o_new_process=multiprocessing.Process(  target=def_target, args=seq_args)
			o_new_process.start()
			o_process_manager.addProcess( o_new_process )
			i_total_replicates_started += 1
		#end while process started < total replicates requested

		return
	#end __do_operation

	def __cancel_simulation( self ):
		self.__simulation_is_in_progress=False
		self.__set_controls_by_run_state( self.__get_run_state() )
		return
	#end __cancel_simulation

	def __on_click_run_or_cancel_simulation_button( self, event=None ):
		if self.__simulation_is_in_progress:
			self.__cancel_simulation()
		else:
			self.runSimulation()
		#end if sim in progress else not
		return
	#end __on_click_run_or_cancel_simulation_button

	def __get_run_state( self ):
		if self.__input is not None \
				and self.__output is not None:
			if self.__simulation_is_in_progress:
				return PGGuiSimuPop.RUN_IN_PROGRESS
			else:
				return PGGuiSimuPop.RUN_READY
			#end if in progress else not
		else:
			return PGGuiSimuPop.RUN_NOT_READY
		#end if input and output are not None else one or both 
	#end __get_run_state

	def __enable_or_disable_category_frames( self, b_do_enable ):
		'''
		As of Mon Jun 27 12:22:26 MDT 2016, not implemented.  I
		think I'll have to go into each subframe, and for each
		go into each KeyValueFrame child, and finally, disable its
		entry box(??)
		'''
		if self.__category_frames is not None:
			for o_frame in self.__category_frames.values():
				#o_frame.config( visible= b_do_enable )
				pass
			#end for each frame
		#end if frames exist
		return
	#end __enable_or_disable_category_frames

	def __set_controls_by_run_state( self, i_run_state ):

		if i_run_state==PGGuiSimuPop.RUN_NOT_READY:
			self.__run_button.config( text="Run Simulatin", state="disabled" ) 
			self.__enable_or_disable_category_frames( b_do_enable=False )
		elif i_run_state==PGGuiSimuPop.RUN_READY:
			self.__run_button.config( text="Run Simulation", state="enabled" )
			self.__enable_or_disable_category_frames( b_do_enable=True )
		elif i_run_state==PGGuiSimuPop.RUN_IN_PROGRESS:
			self.__run_button.config( text="Cancel Simulation", state="enabled" )
			self.__enable_or_disable_category_frames( b_do_enable=False )
		else:
			s_msg="In PGGuiSimuPop instance, __set_run_state: " \
					"unknown run state value: " + str( i_run_state )
			raise Exception( s_msg )
		#end if run state not ready, else ready, else in progress, else error
		
		return
	#end def __set_controls_by_run_state

	def runSimulation( self ):
		if self.__output is None \
			or self.__input is None:
			s_msg="Simulation not ready to run.  Input or Output parameters " \
					+ "have not been set" 
			sys.stderr.write( s_msg + "\n" )
		#end if output or input is None
		self.__setup_op()

		#input file to reaplace the orig config file
		#as well as the attr/value dict originally passed to each 
		#process.  We need to set this temp file name attribute
		#in this instance before spawning a multiprocessing.process
		#in do_operation, else it will not appear during call backs
		#to __check_progress_operation_process, in which we delete
		#the temp file when sim processes are finished
		self.__temp_config_file_for_running_replicates=str( uuid.uuid4() ) 

		self.__op_process=multiprocessing.Process( target=self.__do_operation )
		self.__op_process.start()

		self.__simulation_is_in_progress=True
		self.__set_controls_by_run_state( self.__get_run_state() )
		self.after( 500, 
				self.__check_progress_operation_process )

		return
	#end runSimulation

	def __show_input( self ):

		o_sim_frame=self.master.children[ 'simulation_input_frame' ]

		for s_key in self.__input.__dict__:
			o_this_label = \
				Label( o_sim_frame, text=s_key)
			o_this_entry=Entry( o_sim_frame )
			o_this_entry.insert( 0, str(  self.__input.__dict__[ s_key ] ) )
			o_sim_frame.add( o_this_label )
			o_sim_frame.add( o_this_entry)
		#end for each key

		return
	#end show_input_config
#end class PGGuiSimuPop
