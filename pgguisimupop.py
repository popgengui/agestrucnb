'''
Description
A PGGUIApp object with widgets that manage a simuPop simulation
'''
__filename__ = "pgsimupopper.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False
VERY_VERBOSE=False

DO_PUDB=False

INIT_ENTRY_CONFIG_FILE=()

SIM_RUNNING_MSG="Simulation in progress"

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
from pgguiutilities import KeyListComboFrame
from pgguiutilities import KeyCategoricalValueFrame
from pgguiutilities import PGGUIInfoMessage
from pgguiutilities import PGGUIYesNoMessage
from pgguiutilities import PGGUIErrorMessage
from pgutilityclasses import IndependantSubprocessGroup
from pgutilityclasses import FloatIntStringParamValidity
import pgutilities as pgut

import os
import multiprocessing
import subprocess

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

	MAX_CHARS_BASENAME=18

	def __init__( self,  o_parent,  s_param_names_file=None, 
							s_life_table_file_glob="resources/*life.table.info",
							s_name="simupop_gui",
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
		#we set this before spawning __op_process,
		#so that on cancel-sim, we can
		#notify op_process and it can 
		#clean up its subprocesses and 
		#output:
		self.__sim_multi_process_event=None

		#we have a default output name,
		#so we can init the output
		#immediately
		self.__setup_output()



		self.__simulation_is_in_progress=False

		self.__total_processes_for_sims=i_total_processes_for_sims

		#we hold references to all subframes
		#except the run-button subframe,
		#so that we can enable/disable
		#according to the simulation-run state
		#(not yet implemented, 2016_08_05

		self.__category_frames=None

		#we also hold refernces to the keyvalue
		#frames that hold param values.  This
		#allows us to communicate with the entry
		#boxes via param name.
		self.__param_key_value_frames=None


		self.__run_state_message=""
		self.__init_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )
	
		return
	#end __init__

	def __init_run_sub_subframe( self, b_force_disable = False ):
		'''
		Setup the run button and the processes text box.
		As of 2016_08_31, these chores are still done in 
		def __init_interface.  Need to implement this to
		simplify def __init_interface,
		'''
		pass
		return
	#end of __init_run_sub_subframe

			
	def __init_interface( self, b_force_disable = False ):
		'''
		param b_force_disable, if set to true,
			will set all the KeyValueFrame text entry
			boxes do state "disabled."  This is useful
			to show user when the interface is busy
			computing a simulation, and keeps user
			from editing values when the sim is 
			being run (though, besides any user
			misperceptions, such editign would not
			affect the current sim, but rather would
			be applied to any subsequent run.)

		'''
		
		ENTRY_WIDTH=70
		LABEL_WIDTH=20
		LOCATIONS_FRAME_PADDING=30
		LOCATIONS_FRAME_LABEL="Load/Run"
		LOCATIONS_FRAME_STYLE="groove"
		RUNBUTTON_PADDING=07	

		o_file_locations_subframe=LabelFrame( self,
				padding=LOCATIONS_FRAME_PADDING,
				relief=LOCATIONS_FRAME_STYLE,
				text=LOCATIONS_FRAME_LABEL )

		i_row=0

		o_run_sub_subframe=Frame( o_file_locations_subframe )

		self.__run_button=Button( o_run_sub_subframe, command=self.__on_click_run_or_cancel_simulation_button )
		
		i_tot_procs=pgut.get_cpu_count()

		o_tot_process_validator=FloatIntStringParamValidity( \
					"proccess total",
					int, self.__total_processes_for_sims, 
					1, i_tot_procs )

		o_tot_process_kv=KeyValFrame( s_name="Processes", 
						v_value=self.__total_processes_for_sims,
						o_type=int,
						v_default_value="",
						o_master=o_run_sub_subframe,
						o_associated_attribute_object=self,
						s_associated_attribute="_PGGuiSimuPop" \
									+ "__total_processes_for_sims",
						s_entry_justify='left',
						s_label_justify='left',
						s_button_text="Select",
						b_force_disable=b_force_disable,
						o_validity_tester= o_tot_process_validator,
						s_tooltip = "Simulation can use one process per replicate, " \
								+ "but set to no more than the total number " \
								+ "of processors in your computer." )

		o_tot_process_kv.grid( row=i_row, column=0, sticky=( NW ) )

		self.__run_button.grid( row=i_row, column=1, sticky=( NW ), padx=RUNBUTTON_PADDING )

		self.__run_state_label=Label( o_run_sub_subframe, text=self.__run_state_message )

		self.__run_state_label.grid( row=i_row, column=2, sticky=( SW ) )

		o_run_sub_subframe.grid( row=i_row, sticky=( NW ) )

		i_row += 1
		
		s_curr_config_file=self.__config_file.get()

		v_config_file_val="None" if s_curr_config_file == "" else s_curr_config_file

		o_config_kv=KeyValFrame( s_name="Load Configuration File:", 
						v_value=v_config_file_val,
						v_default_value="",
						o_type=str,
						o_master=o_file_locations_subframe,
						i_entrywidth=ENTRY_WIDTH,
						i_labelwidth=LABEL_WIDTH,
						b_is_enabled=False,
						s_entry_justify='left',
						s_label_justify='left',
						s_button_text="Select",
						def_button_command=self.load_config_file,
						b_force_disable=b_force_disable )

		o_config_kv.grid( row=i_row, sticky=( NW ) )

		i_row+=1

		o_outdir_kv=KeyValFrame( s_name="Select Output directory", 
					v_value=self.__output_directory.get(), 
					v_default_value="",
					o_type=str,
					o_master=o_file_locations_subframe,
					i_entrywidth=ENTRY_WIDTH,
					i_labelwidth=LABEL_WIDTH,
					b_is_enabled=False,
					s_entry_justify='left',
					s_label_justify='left', 
					s_button_text="Select",
					def_button_command=self.select_output_directory,
					b_force_disable=b_force_disable )

		o_outdir_kv.grid( row= i_row, sticky=( NW ) )

		i_row+=1
	
		o_basename_validity_tester=FloatIntStringParamValidity( "output_base", 
				str, self.output_base_name, 1, 
				PGGuiSimuPop.MAX_CHARS_BASENAME )
		
		self.__outbase_kv=KeyValFrame( s_name="Output files base name: ", 
					v_value=self.output_base_name, 
					o_type=str,
					v_default_value="",
					o_master=o_file_locations_subframe, 
					o_associated_attribute_object=self,
					s_associated_attribute="output_base_name",
					def_entry_change_command=self.__setup_output,
					i_entrywidth=ENTRY_WIDTH,
					i_labelwidth=LABEL_WIDTH,
					s_entry_justify='left',
					s_label_justify='left',
					o_validity_tester=o_basename_validity_tester,
					b_force_disable=b_force_disable ) 

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
	
		di_order_num_by_section_name={}

		#reduncancy in these assignments
		#is ignored, we simply reassign
		#the number each time we encounter
		#the name -- as the two should always
		#be identical
		for s_tag in self.__input.param_names.tags:
			s_section_name=self.__input.param_names.getConfigSectionNameFromTag( s_tag )
			s_order_number=self.__input.param_names.getSectionOrderFromTag( s_tag )
			di_order_num_by_section_name[ s_section_name ]=int( s_order_number )
		#end for each tag
		
		for s_key in do_category_frames:
			o_frame=do_category_frames[ s_key ]
			if s_key=="none":
				i_frame_order_number=len( do_category_frames )
			else:
				i_frame_order_number=di_order_num_by_section_name[ s_key ]
			#end if categore is "none" then place in last row

			i_cat_frame_row=FIRST_ROW_NUMBER_FOR_CATEGORY_FRAMES + ( i_frame_order_number - 1 )
			o_frame.grid( row=i_cat_frame_row, sticky=(NW), pady=GRID_SPACE_VERTICAL )
			o_frame.grid_columnconfigure( 0, weight=1 )
			o_frame.grid_rowconfigure( 0, weight=1 )
			i_cat_frame_row+=1
		#end for each catgory frame
	#end __place_category_frames
			

	def __load_values_into_interface( self, b_force_disable=False ):
		'''
		in isolating the attributes
		that are strictly model params
		(and not defs or other non-param 
		attributes) I found help at:
		http://stackoverflow.com/questions/9058305/getting-attributes-of-a-class

		param b_force_disable, if True, will, for each entry box or radio button
		created by KeyValFrame or KeyCategoricalValueFrame,  override the defalut 
		enabled/disabled state (as set by their attribute "isenabled", so that 
		all are disabled.
		'''
		MAXLABELLEN=200
		WIDTHSMALL=21
		WIDTHBIG=21
		LENSMALL=20

		LABEL_WIDTH = [ WIDTHSMALL if i<LENSMALL else WIDTHBIG for i in range( MAXLABELLEN ) ] 
		PARAMETERS_CBOX_WIDTH=15

		'''
		When we look for config file attributes
		in the PGInputSimuPop member, that are o
		settable input parameters, we want
		to ignore constants, declared
		in the object with this prefix
		'''
		PREFIX_FOR_INPUT_CONSTANTS="CONST_"

		#for parameters in this section, we set enabled 
		#flag to false for the KeyValFrame entry box:
		CONFIG_INFO_SECTION_NAME="Configuration Info"

		#For params (if any) not in the input
		#objects paramset instance (from the
		#file simupop.param.names)
		DEFAULT_CONTROL_TYPE=pgps.PGParamSet.CONTROL_TYPE_ENTRY_BOX


		self.__param_key_value_frames={}

		i_row=0

		o_input=self.__input
		
		ls_input_params=[ s_param for s_param in dir( o_input ) if not( s_param.startswith( "_" ) ) \
											and not( s_param.startswith( PREFIX_FOR_INPUT_CONSTANTS ) )  ]

		ls_tags=o_input.param_names.tags

		ls_sections=[  o_input.param_names\
					.getConfigSectionNameFromTag( s_tag )  for s_tag in ls_tags ]

		#clear existing category frames (if any): 
		self.__clear_grid_below_row( self, 1 )

		#make frames, one for each category of parameter
		#(currently, "population", "configuration", "genome", "simulation"
		self.__category_frames=self.__make_category_subframes( \
				set( ls_sections ) )	

		for s_param in ls_input_params:
			
			PADPIX=0

			i_row+=1

			i_len_labelname=None

			if VERBOSE == True:
				o_def_to_run_on_value_change=self.__test_value
			#end if VERBOSE

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

			if o_input.param_names is None:
				s_msg=" In PGOpSimuPop, " \
						+ "def __load_values_into_interface, " \
						+ "member __input has missing PGParamset " \
						+ "instance."
				raise Exception( s_msg )
			#end of no param_set object

			if not( o_input.param_names.isInSet( s_param ) ):
					s_msg=" In PGOpSimuPop, " \
						+ "def __load_values_into_interface, " \
						+ "member __input members PGParamset " \
						+ "instance has no param, " + s_param + "."
					raise Exception( s_msg )
			#end if param not in param_names objectd

			b_param_is_in_param_set=True
			
			'''
			This call requires we get all
			the values from the param tag,
			but we'll only use the ones we
			need (see below):
			'''

			( s_longname,
				s_section_name,
				i_param_section_order_number,
				i_param_column_number,
				i_param_position_in_order,
				v_default_value,
				o_param_type,
				v_min_value,
				v_max_value,
				s_tooltip,
				s_param_control_type,
				s_param_control_list,
				s_param_validity_expression,
				s_param_assoc_def ) = \
						o_input.param_names.getAllParamSettings( s_param )
				#end if param is in paramset



			#if no specific def is to be called on value change
			#then we default to the def that shows current param vals:
			def_to_call_on_change=self.__test_value

			if s_param_assoc_def != "None":
				try:
					
					def_to_call_on_change=getattr( self, s_param_assoc_def )

				except:
					s_msg="In PGGuiSimuPop instance, def __load_values_into_interface, " \
								+ "for param, " + s_param \
								+ ", unable to find input def for param's associated def string: " \
								+ s_param_assoc_def + "."
					raise Exception( s_msg )
			#end if s_associated_def not None


			#If it is in the param names we don't suppress as long as the
			#param is not tagged as "suppress"
			if s_section_name != "suppress":

				o_frame_for_this_param=None

				if s_section_name not in self.__category_frames:
					o_frame_for_this_param=self.__category_frames[ "none" ]
				else:
					o_frame_for_this_param=self.__category_frames[ s_section_name ]
				#end if no nametag or name tag not in frame categories

				i_len_labelname=len( s_longname ) if s_longname is not None else len( s_param )
				i_width_labelname=LABEL_WIDTH[ i_len_labelname ]

				b_allow_entry_change = True

				if s_section_name == CONFIG_INFO_SECTION_NAME:
					b_allow_entry_change=False
				#end if input param is type config info, disable

				s_attribute_to_update=s_param

				if s_param == "N0":
					if o_input.N0IsCalculatedFromEffectiveSizeInfo():
						b_allow_entry_change=False
						s_attribute_to_update=None	
					#end if we're calculating N0
				#end if param is "N0"

				#we send in the input object to the KeyValFrame (or similar class)
				#instance so it will be the object whose attribute (with name s_param)
				#is reset when user resets the value in the KeyValFrame:
				if s_param_control_type == pgps.PGParamSet.CONTROL_TYPE_ENTRY_BOX:

					i_entry_width=len(v_val) if type( v_val ) == str else 7

					s_entry_justify='left' if type( v_val ) == str else 'right' 

					o_kv=KeyValFrame( s_name=s_param, 
								v_value=v_val, 
								v_default_value=v_default_value,
								o_type=o_param_type,
								o_master=o_frame_for_this_param, 
								o_associated_attribute_object=self.__input,
								s_associated_attribute=s_attribute_to_update,
								def_entry_change_command=def_to_call_on_change,
								i_labelwidth=i_width_labelname,	
								s_label_name=s_longname,
								i_entrywidth = i_entry_width,
								s_entry_justify=s_entry_justify,
								b_is_enabled=b_allow_entry_change,
								b_force_disable=b_force_disable,
								s_tooltip=s_tooltip )
						
				elif s_param_control_type == pgps.PGParamSet.CONTROL_TYPE_COMBO_BOX:

					qs_control_list=eval( s_param_control_list )

					i_current_item_number=None

					if v_val not in qs_control_list:
						s_msg="Current value for parameter " \
							 	+ s_param + " is not found " \
								+ "among the values listed as valid: " \
								+ str( qs_control_list ) + ""
						raise Exception( s_msg )
					else:
						#KeyListComboFrame init expects 1-based value, so
						#we increment the python, zero-based index
						i_current_item_number=qs_control_list.index( v_val )
						i_current_item_number +=1
					#end if v_val not in value list

					o_kv=KeyListComboFrame( s_name=s_param,
								qs_choices=qs_control_list,
								i_default_choice_number=i_current_item_number,
								o_master=o_frame_for_this_param,
								s_associated_attribute=s_attribute_to_update,
								o_associated_attribute_object=self.__input,
								def_on_new_selection=def_to_call_on_change,
								i_labelwidth=i_width_labelname,
								i_cbox_width=PARAMETERS_CBOX_WIDTH,
								s_label_justify='left',
								s_label_name=s_longname,
								s_tooltip=s_tooltip,
								b_is_enabled=True,
								b_force_disable=b_force_disable )

				elif s_param_control_type == pgps.PGParamSet.CONTROL_TYPE_BOOL_RADIO_BUTTONS:

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
							def_on_button_change=def_to_call_on_change,
							i_labelwidth=i_width_labelname,
							s_label_name=s_longname,
							b_buttons_in_a_row = True,
							b_is_enabled=b_allow_entry_change,
							b_force_disable=b_force_disable,
							s_tooltip=s_tooltip )

				else:
					s_msg="In PGGuiSimuPop instance, def " \
							+ "__load_values_into_interface, " \
							+ "unknown control type spcified: " \
							+ s_param_control_type + "."
					raise Exception( s_msg )

				#end if control type entry, else combobox, else bool radio button, else unknown

				o_kv.grid( row=i_row, sticky=(NW) )
				self.__param_key_value_frames[ s_param ] = o_kv

			#end if section name not "suppress"
		#end for each input param

		self.__place_category_frames( self.__category_frames )
		self.grid_columnconfigure( 0, weight=1 )
		self.grid_rowconfigure( 0, weight=1 )

		return
	#end __load_values_into_interface

	def onCullMethodSelectionChange( self ):
		'''
		Not implemented, 2016_11_01.  May
		not need to add any code here, since
		KeyListComboFrame control object resets
		the attribute in the input object
		automatically.
		'''

		if VERY_VERBOSE:
			self.__test_value()
		#end if very verbose

		return
	#end __on_cull_method_selection_change

	def load_config_file( self, event=None ):
		s_current_value=self.__config_file.get()
		s_config_file=tkfd.askopenfilename(  \
				title='Load a configuration file' )

		if pgut.dialog_returns_nothing( s_config_file ):
			return
		#end if no file selected, return

		self.__config_file.set(s_config_file)
		try:
			self.__setup_input()
		except Exception as oe:
			if s_config_file != INIT_ENTRY_CONFIG_FILE: 
				s_msg="Problem loading configuration.\n" \
						+ "File: " + str( s_config_file ) + "\n\n" \
						+ "Details: " \
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

	def updateN0EntryBox( self ):
		'''
		N0 parameter updates differently according to
		whether it is simply taken from a config file's
		pop section, or, alternatively, calculated from
		params Nb,Nb/Nc as given by an "effective_size"
		section in a life table or config file, and also
		using input params maleProb, survivalMale, and
		survivalFemale.  In the latter
		case, the keyvalue frame will be disabled and its entrybox
		will be manually updated from this def.  
		'''
		if self.__input.N0IsCalculatedFromEffectiveSizeInfo():
			'''
			Nb is a property, calculated or just returned
			depending on its source (effec size or hus a value
			given in the pop section). The property def in
			our __input member will test the state and calculate
			N0 accordingly:
			'''

			i_current_n0_val=self.__input.N0

			self.__param_key_value_frames[ "N0" ].manuallyUpdateValue( i_current_n0_val )
		#end if N0 is calc'd from effective size info

		if VERY_VERBOSE:
			self.__test_value()
		#end if very verbose, show param values

		return
	#end updateN0EntryBox

	def __get_life_table_file_list( self, s_glob_expression ):
		self.__life_table_files = \
			pgut.get_list_files_and_dirs_from_glob( s_glob_expression )
		return
	#end def __get_life_table_file_list

	def select_output_directory( self, event=None ):

		s_outputdir=tkfd.askdirectory( \
				title='Select a directory for file output' )
		
		if pgut.dialog_returns_nothing( s_outputdir ):
			return
		#end if no directory selected, return

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

	def __validate_output_base_name( self ):

		MAX_CHARS_OUTPUT_FILE_BASENAME=18
		s_msg=""

		if ( len( self.__basename ) > MAX_CHARS_OUTPUT_FILE_BASENAME ):
				s_msg="Please limit the output file base name to " \
						+ str( MAX_CHARS_OUTPUT_FILE_BASENAME ) \
						+ " characters."
		#end if length exceeds maximum

		return s_msg	
	#end __validate_output_base_name

	def __test_value( self, v_keyval_frame_value_update=None ):
		'''
		for debugging
		'''
		if VERY_VERBOSE:

			ls_input_params=[ s_param for s_param in dir( self.__input ) 
									if not( s_param.startswith( "_" ) )  ]
			
			for s_param in ls_input_params:
				print s_param + "\t" + str( getattr( self.__input, s_param ) )
			#end for each param

		#end if VERBOSE			
	#end __test_value

	def __setup_op( self, v_keyval_frame_value_update=None ):
		self.__setup_output()
		return
	#end __make_op

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

	def __get_default_output_base_name( self ):

		'''
		Compacting default name, as of 2016_08_11,
		need to make sure the output base name is
		as small as possble, to keep the resulting
		genepop file name under 31 chars, as NeEstimation
		currently can't handle input file names >31 chars.
		'''
		s_mytime=pgut.get_date_time_string_dotted()	
		return "sim." + s_mytime.replace( ".", "" )
	#end __get_default_output_base_name

	def __get_default_output_directory( self ):
		return pgut.get_current_working_directory()
	#end __get_default_output_directory

	def __check_progress_operation_process( self ):
		if self.__op_process is not None:
			if self.__op_process.is_alive():
				if VERY_VERBOSE:
					print ( "checking and process found alive" )
				#endif very verbose, print

				self.__simulation_is_in_progress = True
				self.__update_run_state_message()
				self.__run_state_label.configure( text=self.__run_state_message  )
				self.after( 500, self.__check_progress_operation_process )
			else:
				if VERY_VERBOSE:
					print( "checking and process not None but not alive" )
					print( "value of temp config file attribute: " \
								+ str( self.__temp_config_file_for_running_replicates ) )
				#end if very verbose, print

				self.__simulation_is_in_progress = False

				#found in the neestimator gui that the op_process 
				#as object will persist long past finishing the estimation.  
				#In this case if the user closes the whole gui or the tab 
				#for this instance, then the cleanup will read the 
				#op_process as alive, and will remove output files, even 
				#though the process has finished.  While I did not see this
				#problem here, for the PGGuiSimuPop.op_process, 
				#I'm nonetheless setting the "dead"
				#process and its corresponding event to None:
				self.__op_process=None
				self.__sim_multi_process_event=None
				self.__run_state_message=""
				self.__init_interface( b_force_disable=False )
				self.__load_values_into_interface( b_force_disable=False )

				if VERY_VERBOSE:
					print ( "removing temporary config file" )
				#end if very verbose

				self.__remove_temporary_config_file()

			#end if process alive else not

			self.__set_controls_by_run_state( self.__get_run_state() )

		else:
			if VERY_VERBOSE:	
				print( "process found to be None" )
			#endif very verbose, pring

			self.__simulation_is_in_progress = False
			self.__run_state_message=""
			self.__init_interface( b_force_disable=False )
			self.__load_values_into_interface( b_force_disable=False )

			self.__set_controls_by_run_state( self.__get_run_state() )

		#end if process not None else None

		return
	#end __check_progress_operation_process

	def __remove_temporary_config_file( self ):
			if self.__temp_config_file_for_running_replicates is not None:
				if os.path.exists( self.__temp_config_file_for_running_replicates ):
					os.remove( self.__temp_config_file_for_running_replicates )
					self.__temp_config_file_for_running_replicates = None
				else:
					s_msg = "In PGGuiSimuPop instance, def __remove_temporary_config_file, " \
							+ "attribued __temp_config_file_for_running_replicates is not None, " \
							+ "but is not a valid, existing file. Current value: " \
							+ str( self.__temp_config_file_for_running_replicates ) + "." 
					raise Exception( s_msg )
				#end if path exits
			#end if config file attr is not none
	#end __remove_temporary_config_file

	def __cancel_simulation( self ):
		if self.__op_process is not None:
			if self.__sim_multi_process_event is not None:
				#signal op_process that we want to kill all the sim subprocesses:
				#(see def __do_operation)
				self.__sim_multi_process_event.set()
			else:
				self.__op_process.terminate()
		else:
			s_msg="Could not cancel the simulation.  " \
					+ "The simulation process and/or its communication event was not found." 
			sys.stderr.write( "Warning: " + s_msg + "\n" )
		#end if op_process is not None
		
		return
	#end __cancel_simulation

	def __on_click_run_or_cancel_simulation_button( self, event=None ):
		if self.__simulation_is_in_progress:
			o_mbox=PGGUIYesNoMessage( self , "Are you sure you want to cancel " \
					+ "the simulation and remove all output files?" )
			b_answer = o_mbox.value
			if b_answer:
				self.__cancel_simulation()
				self.__simulation_is_in_progress=False
				self.__set_controls_by_run_state( self.__get_run_state() )

			#end if yes
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

	def __set_controls_by_run_state( self, i_run_state ):

		if i_run_state==PGGuiSimuPop.RUN_NOT_READY:
			self.__run_button.config( text="Run Simulation", state="disabled" ) 
		elif i_run_state==PGGuiSimuPop.RUN_READY:
			self.__run_button.config( text="Run Simulation", state="enabled" )
		elif i_run_state==PGGuiSimuPop.RUN_IN_PROGRESS:
			self.__run_button.config( text="Cancel Simulation", state="enabled" )
		else:
			s_msg="In PGGuiSimuPop instance, __set_run_state: " \
					"unknown run state value: " + str( i_run_state )
			raise Exception( s_msg )
		#end if run state not ready, else ready, else in progress, else error
		
		return
	#end def __set_controls_by_run_state

	def __output_files_exist_with_current_output_basename(self):
		b_files_exist=False
		ls_files=pgut.get_list_files_and_dirs_from_glob( self.__output.basename + "*" )
		if len( ls_files ) != 0:
			b_files_exist=True
		#end if len not zero
		return b_files_exist
	#end __output_files_exist_with_current_output_basename

	def runSimulation( self ):
		try:

			if self.__output is None \
				or self.__input is None:
				s_msg="Simulation not ready to run.  Input or Output parameters " \
						+ "have not been set" 
				sys.stderr.write( s_msg + "\n" )
				PGGUIInfoMessage( self, s_msg )
				return	
			#end if output or input is None

			self.__setup_op()

			'''
			this check was added in case a user completed a simulation,
			then accidentally hit "run simulation" button again without
			changing anything in the interface, and then (very quickly) 
			hit the "cancel simulation" button -- initiating a file removal
			before the program has reached the point at which which the
			PGOutputSimuPop object could abort the run by throwing an 
			exception that the output files already exist.
			The following check is meant to halt the sim before any
			separate processes are even started (and so no multiprocessing
			event will cause cancel prompt and cleanup on "yes" ).
			'''
			if self.__output_files_exist_with_current_output_basename():
				s_msg="The program can't start the simulation. Output files " \
						+ "already exist with current " \
						+ "path and basename: " + self.__output.basename + ".  " \
						+ "\nTo start a new simulation please do one of the following:\n" \
						+ "1. Remove or rename the output files.\n" \
						+ "2. Rename the output files base name or output directory." 

				sys.stderr.write( s_msg + "\n" )
				
				PGGUIInfoMessage( self, s_msg )
				return
			#end if output files exist	

			#input file to reaplace the orig config file
			#as well as the attr/value dict originally passed to each 
			#process.  We need to set this temp file name attribute
			#in this instance before spawning a multiprocessing.process
			#in do_operation, else it will not appear during call backs
			#to __check_progress_operation_process, in which we delete
			#the temp file when sim processes are finished
			self.__temp_config_file_for_running_replicates=str( uuid.uuid4() ) 
			
			self.__input.writeInputParamsAsConfigFile( \
				self.__temp_config_file_for_running_replicates )

			#we pass a ref to this object to the target (def in pgutilities, do_simulation_reps_in_subprocesses) 
			#for op_process, #Then, from this object instance can call "set()" on the event, 
			#after, for example #an __on_click_run_or_cancel_simulation_button->__cancel_simulation()
			#sequence, so that the event will to pass True and then the ref in
			#op_process will return True when the op_process interrog 
			#o_event.is_set()  and it can accordingly clean
			#up its collection of subprocess.Popen processes 
			self.__sim_multi_process_event=multiprocessing.Event()

			#our sim run(s) should not block the main gui, so we
			#run it(them) in one or more python.subprocesses:
			self.__op_process=multiprocessing.Process( target=pgut.do_simulation_reps_in_subprocesses, 
						 args=( self.__sim_multi_process_event, 
							self.__input.reps, 
							self.__total_processes_for_sims,
							self.__temp_config_file_for_running_replicates,
							self.__life_table_files,
							self.__param_names_file,
							self.__output.basename ) ) 

			self.__op_process.start()

			self.__simulation_is_in_progress=True

			#Need some padding in front, or
			#it's too close to the run button:
			self.__run_state_message="  " + SIM_RUNNING_MSG

			self.__set_controls_by_run_state( self.__get_run_state() )

			self.__init_interface( b_force_disable=True )
			self.__load_values_into_interface( b_force_disable=True )

			self.after( 500, 
					self.__check_progress_operation_process )
		except Exception as oex:
			PGGUIErrorMessage( o_parent=self, s_message= \
					oex.__class__.__name__ + ", " + str( oex ) )
			raise oex 
		#end try . . . except
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

	def cleanup( self ):
		self.__cancel_simulation()
		self.__remove_temporary_config_file()
	#end cleanup
#end class PGGuiSimuPop
