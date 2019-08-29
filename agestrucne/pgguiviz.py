'''
Description
This module is an interface to execute Brian Trethewey's plotting
program(s) using an existing *tsv file containing Ne estimations
produced by the pgdrivenestimator.py code,
most often called by the pgguineestimator.py GUI interface.
'''
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from builtins import range
__filename__ = "pgguiviz.py"
__date__ = "20161209"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False
VERY_VERBOSE=False
KEEP_CONFIG_FILE=False

VIZ_RUNNING_MSG="Plotting in progress"

ATTRIBUTE_DEMANLGER="_PGGuiViz__"

ROW_NUM_FILE_LOCATIONS_FRAME=0
ROW_NUM_FILE_INFO_FRAME=1
ROW_NUM_VIZ_TYPE_SELECTION_FRAME=2
COL_NUM_VIZ_TYPE_SELECTION_FRAME=0
ROW_NUM_VIZ_PARAMS_FRAME=3
COL_NUM_VIZ_PARAMS_FRAME=0

'''
Constants for loading combo boxes
and for calling regression plot with
a filtered tsv file, according to user
selected subsample values for pop and loci.
'''
VIZ_TYPES_REQUIRING_SUBSAMPLE_SELECTION=[ "Regression" ]
POP_SELECT_SUBSAMPLE_ATTR="selected_pop_subsample_value"
POP_SELECT_LABEL="Pop subsample value"
LOCI_SELECT_SUBSAMPLE_ATTR="selected_loci_subsample_value"
LOCI_SELECT_LABEL="Loci subsample value"



'''
A default file name for the 
input tsv file (likely refers
to a non-existent file). 
This is needed for intitialization
of the file-load control, and
also for the def,
__add_subsample_selection_controls.
'''

INIT_TSV_FILE_NAME="none"

from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog as tkfd
import sys

#Support asynchronous running
#of the Viz programs:
import time
import multiprocessing

import agestrucne.pgguiapp as pgg
import agestrucne.pgutilities as pgut
import agestrucne.pgparamset as pgps

#these are the lowest-level interface frames
#that take input from user and update
#this gui's attributes:
from agestrucne.pgkeyvalueframe import KeyValFrame
from agestrucne.pgkeylistcomboframe import KeyListComboFrame

from agestrucne.pgguiutilities import FredLundhsAutoScrollbar
from agestrucne.pgguiutilities import PGGUIInfoMessage
from agestrucne.pgguiutilities import PGGUIYesNoMessage
from agestrucne.pgguiutilities import PGGUIErrorMessage
from agestrucne.pgguiutilities import PGGUIMessageWaitForResultsAndActionOnCancel

from agestrucne.pgutilityclasses import ValueValidator

from agestrucne.pglineregressconfigfilemaker import PGLineRegressConfigFileMaker

class PGGuiViz( pgg.PGGuiApp ):
	'''
	Subclass of PGGuiApp builds a gui,
	interface to allow users to set up
	and run Brian Trethewey's Viz programs.

	As of 2016_12_09, these are run in a 
	Popen generated subprocess, as implemented
	in the pgutilities.py module.
	'''
	#possible states of the gui:
	RUN_NOT_READY=0
	RUN_READY=1
	RUN_IN_PROGRESS=2
	
	def __init__( self, o_parent, 
						s_param_names_file,
						s_name="viz_gui",
						i_total_processes_for_viz=1):

		'''
		param o_parent is the tkinter window that hosts this gui.  
			It is meant to be the same parent as that 
			which hosts other pg interfaces, like pgguisimupop objects.
		param s_param_names_file is the file that contains short and long 
			param names, used to make a PGParamSet object, in turn used to 
			setup the viz plotting call.
		param s_name gives the parent PGGuiApp's name 
			(currently, Fri Aug  5 16:48:08 MDT 2016, of no importance).
		param i_total_processes_for_est, integer given the number of processes 
			to assign to the ne-estimation, which does each population 
			in each genepop file in a separate python, mulitiprocessing.process.
		'''
				
		pgg.PGGuiApp.__init__( self, s_name, o_parent )

		self.__param_names_file=s_param_names_file

		#ref to the PGParamSet object
		#created using the param_names_file:
		self.__param_set=None
		
		#a string giving a list 
		#of input files:
		self.__tsv_file=StringVar()

		#variables for the output
		self.__output_directory=StringVar()

		#currently not used, as plotting
		#is serially programmed
		self.__processes=i_total_processes_for_viz

		#no StringVar because we want
		#the KeyValFrame to set this
		#directly:
		self.output_base_name=""

		'''
		In case user wants to plot regression,
		and the tsv file has more than one
		subsample value for pop and/or loci,
		we update these whenever the user
		loads a tsv file.:
		'''
		self.__pop_subsample_values=[]
		self.__loci_subsample_values=[]
	
		#These attributes will be assigned and accessed
		#when the above lists have > 1 value for pop or loci:
		setattr( self, ATTRIBUTE_DEMANLGER + POP_SELECT_SUBSAMPLE_ATTR, None )
		setattr( self, ATTRIBUTE_DEMANLGER + LOCI_SELECT_SUBSAMPLE_ATTR, None )

		#displays the current tsv file ready
		#to run:
		self.__tsv_file_listbox=None

		#python multiprocessing.Process
		#spawned in def runViz:
		self.__op_process=None
		#Event to signal when plotting
		#is to be aborted.
		self.__multi_process_event=None
		self.__op_in_progress=False

		self.__run_state_message=""
		self.__run_button=None

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
		class itself, we'll keep this attribute and append
		the objects (kv frames, as created in load_parm defs)
		in case the direct access to these controls is needed.
		'''
		self.__param_value_frames_by_attr_name={}

		'''
		Objects associated with the asyncronous
		fetching of tsv (ne-estimation table) file
		info about number of pop and loci subsample
		values, in order to get user input for
		regression plotting (if needed).
		'''
		self.__subsample_fetcher_process_pool=None
		self.__subsample_fetcher_map_result=None

		#create interface
		self.__get_param_set( s_param_names_file )
		self.__set_initial_file_info()
		self.__init_interface()
		self.__load_viz_type_selection_interface()
		self.__load_params_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )
		return
	#end __init__

	def __get_param_set( self, s_param_names_file ):
		self.__param_set=pgps.PGParamSet( s_param_names_file )
		return
	#end __get_param_set


	def __set_initial_file_info( self ):
		
		INIT_OUTPUT_DIRECTORY=pgut.get_current_working_directory()
		INIT_OUTPUT_FILES_BASE_NAME="viz.out." \
				+ pgut.get_date_time_string_dotted()

		self.__tsv_file.set( INIT_TSV_FILE_NAME )

		self.__output_directory.set( INIT_OUTPUT_DIRECTORY )
		self.output_base_name=INIT_OUTPUT_FILES_BASE_NAME

		return
	#end __set_initial_file_info

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

	def __init_file_locations_interface( self, b_force_disable=False ):
		ENTRY_WIDTH=70
		LABEL_WIDTH=20
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

		if self.__processes is None:
			self.__processes=1
		#end assign min if not set

		self.__run_button=Button( o_run_sub_subframe, 
						command= \
							self.__on_click_run_or_cancel_viz_button )
		
		self.__run_button.grid( row=i_row, column=1, sticky=( NW ), padx=RUNBUTTON_PADDING )

		#this label will have text showing when an estimation
		#is running:
		self.__run_state_label=Label( o_run_sub_subframe, text=self.__run_state_message )

		self.__run_state_label.grid( row=i_row, column=2, sticky=( SW ) )

		o_run_sub_subframe.grid( row=i_row, sticky=( NW ) )

		i_row += 1
		
		o_config_kv=KeyValFrame( s_name="Load tsv file", 
						v_value=self.__tsv_file.get(),
						o_type=str,
						v_default_value="",
						o_master=o_file_locations_subframe,
						i_entrywidth=ENTRY_WIDTH,
						i_labelwidth=LABEL_WIDTH,
						b_is_enabled=False,
						s_entry_justify='left',
						s_label_justify='left',
						s_button_text="Select",
						def_button_command=self.__load_tsv_file,
						b_force_disable=b_force_disable,
						s_tooltip = "Load a tsv file, output from an Nb/Ne Estimation run" )

		#The entry box should be disabled, but
		#we want the lable non-grayed-out:
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

		o_outdir_kv.setLabelState( "enabled" )

		o_outdir_kv.grid( row= i_row, sticky=( NW ) )

		o_file_locations_subframe.grid( row=ROW_NUM_FILE_LOCATIONS_FRAME,
										sticky=(NW) )
		o_file_locations_subframe.grid_columnconfigure( 0, weight=1 )
		o_file_locations_subframe.grid_rowconfigure( 0, weight=1 )
	#end __init_file_locations_interface

	def __init_file_info_interface( self ):

		LISTBOX_WIDTH=50
		LISTBOX_HEIGHT=5

		'''
		For color issues see pgguineestimator.py, def 
		of same name.
		'''
		LISTBOX_FOREGROUND="black"
		LISTBOX_BACKGROUND="white"

		LOCATIONS_FRAME_PADDING=10
		LOCATIONS_FRAME_LABEL="tsv file loaded for vizualization"
		LOCATIONS_FRAME_STYLE="groove"

		o_file_info_subframe=LabelFrame( self,
				padding=LOCATIONS_FRAME_PADDING,
				relief=LOCATIONS_FRAME_STYLE,
				text=LOCATIONS_FRAME_LABEL )

		self.__interface_subframes[ "fileinfo" ]=o_file_info_subframe 

		i_row=0

		o_scrollbar_vert=FredLundhsAutoScrollbar( o_file_info_subframe,
												orient=VERTICAL )

		self.__tsv_file_listbox=Listbox( o_file_info_subframe, 
										width=LISTBOX_WIDTH,
										height=LISTBOX_HEIGHT,
										background=LISTBOX_BACKGROUND,
										foreground=LISTBOX_FOREGROUND )

		o_scrollbar_vert.config( command=self.__tsv_file_listbox.yview )
		o_scrollbar_vert.grid( row=0, column=2, sticky=( N, S ) )

		self.__update_tsv_file_listbox()

		self.__tsv_file_listbox.grid( row=i_row, sticky=( NW ) )

		o_file_info_subframe.grid( row=ROW_NUM_FILE_INFO_FRAME,
										sticky=(NW) )

		o_file_info_subframe.grid_columnconfigure( 0, weight=1 )
		o_file_info_subframe.grid_rowconfigure( 0, weight=1 )

	#end __init_file_info_interface

	def __load_viz_type_selection_interface( self, b_force_disable = False ):


		VIZ_TYPE_PARAM_NAME="viztype"

		VIZ_TYPE_SUBFRAME_KEY="typeselection"


		PARAMETERS_FRAME_PADDING=30
		PARAMETERS_FRAME_LABEL="Set Viz Type"
		PARAMETERS_CBOX_WIDTH=10
		PARAMETERS_FRAME_STYLE="groove"

		PAD_LABEL_WIDTH=0
		GRID_SPACE_HORIZ=10

		try: 

			if VIZ_TYPE_SUBFRAME_KEY in self.__interface_subframes:
					self.__interface_subframes[ VIZ_TYPE_SUBFRAME_KEY ].grid_remove()
					self.__interface_subframes[ VIZ_TYPE_SUBFRAME_KEY ].destroy()
			#end if subframe already exists, get rid of it.

			o_viz_type_subframe=LabelFrame( self,
					padding=PARAMETERS_FRAME_PADDING,
					relief=PARAMETERS_FRAME_STYLE,
					text=PARAMETERS_FRAME_LABEL )

			self.__interface_subframes[ VIZ_TYPE_SUBFRAME_KEY ]= \
												o_viz_type_subframe

			s_param_control_type=self.__param_set.getGUIControlForParam( VIZ_TYPE_PARAM_NAME )
			s_param_control_list=self.__param_set.getControlListForParam( VIZ_TYPE_PARAM_NAME )
			s_param_assoc_def=self.__param_set.getAssocDefForParam( VIZ_TYPE_PARAM_NAME )
			s_param_longname=self.__param_set.getLongnameForParam( VIZ_TYPE_PARAM_NAME )
			s_param_tooltip=self.__param_set.getToolTipForParam( VIZ_TYPE_PARAM_NAME )
			s_param_control_state=self.__param_set.getControlStateForParam( VIZ_TYPE_PARAM_NAME )

			s_attr_name=ATTRIBUTE_DEMANLGER + VIZ_TYPE_PARAM_NAME

			dvs_param_values=self.__param_set.getTypedParamValues( VIZ_TYPE_PARAM_NAME )

			v_param_default_value=dvs_param_values[ 'default' ]

			i_label_width=len( s_param_longname ) + PAD_LABEL_WIDTH

			i_row=0

			'''
			As of 2016_12_13, the param set for this Vis interface
			takes its param details from a param set that is the
			combined set for PGGuiNeEstimator instances, so we
			adapt the callback def for the combobox for this new class.
			'''
			if "_PGGuiNeEstimator__" in s_param_assoc_def:
				s_param_assoc_def=s_param_assoc_def.replace( "_PGGuiNeEstimator__", ATTRIBUTE_DEMANLGER )
			#end if the def is named to be part of the Ne Estimator GUI, we
			#change its name for this class instance.

			s_state_this_cbox=None
			if s_param_control_type=="cboxnormal":
				s_state_this_cbox="normal"
			elif s_param_control_type=="cboxreadonly":
				s_state_this_cbox="readonly"
			else:
				s_msg="In PGGuiViz instance, " \
							+ "def __load_viz_type_selection_interface, " \
							+ "cbox control name not recognized: " \
							+ s_param_control_type + "."
				raise Exception ( s_msg )
			#end if cbox with normal state, else readonly
			qs_control_list=eval( s_param_control_list )

			def_on_combo_choice_change=None
		
			#we need to have it call our sample scheme updating
			#def when a new choice is made in the combobox		
			#if none supplied we default to the test values def
			if s_param_assoc_def == "None":
				def_on_combo_choice_change=self.__test_values
			else:
				def_on_combo_choice_change=getattr( self,  s_param_assoc_def )
			#end if def is "None"
		
			i_current_item_number=1

			o_validity_checker=None
		
			'''
			We select a combo box item number
			different than default=1, if we
			already have a current value for
			this param (attribute in our self instance)
			'''
			if hasattr( self, s_attr_name ): 

				s_value=getattr( self, s_attr_name )

				if s_value not in qs_control_list:
					if o_validity_checker is not None:
						o_validity_checker.value=s_value
						if  not o_validity_checker.isValid():
							s_msg=self.__validity_checker.reportInvalidityOnly()
							PGGUIInfoMessage( self, s_msg + "\nResetting to default value." )
							setattr( self, s_attr_name, v_param_default_value )
						#end if invalid current value
					#end if validity checker exists
				else:
					i_index=qs_control_list.index( s_value )
					i_current_item_number=i_index+1
					#end if current value not in value list
			else:
				setattr( self, s_attr_name, v_param_default_value )
			#end if we have this attribute already, else assign default

			o_this_keyval=KeyListComboFrame( s_name=s_param_longname,
						qs_choices=qs_control_list,
						i_default_choice_number=i_current_item_number,
						o_master=o_viz_type_subframe,
						s_associated_attribute=s_attr_name,
						o_associated_attribute_object=self,
						def_on_new_selection=def_on_combo_choice_change,
						i_labelwidth=i_label_width,
						i_cbox_width=PARAMETERS_CBOX_WIDTH,
						s_label_justify='left',
						s_tooltip=s_param_tooltip,
						b_is_enabled=( s_param_control_state == "enabled" ),
						o_validity_tester=o_validity_checker,
						s_state=s_state_this_cbox,
						b_force_disable=b_force_disable )

			o_this_keyval.grid( row=i_row, sticky=( NW ) )
			
			#Keep a reference to this param frame frame keyed to its attribute name
			self.__param_value_frames_by_attr_name[ s_attr_name ] = o_this_keyval

			o_viz_type_subframe.grid( row=ROW_NUM_VIZ_TYPE_SELECTION_FRAME, 
						column=COL_NUM_VIZ_TYPE_SELECTION_FRAME,
						sticky=(NW), padx=GRID_SPACE_HORIZ )

			o_viz_type_subframe.grid_columnconfigure(0, weight=1 )
			o_viz_type_subframe.grid_rowconfigure( 0, weight=1 )

			self.grid_columnconfigure( 1, weight=1 )
			self.grid_rowconfigure( 0, weight=1 )

		except Exception as oex:
			s_msg="In PGGuiViz instance, " \
						+ "__load_viz_type_selection_interface, " \
						+ "exception: " + str( oex )
			PGGUIErrorMessage( self, s_msg )
			raise ( oex )
		#end try ... except
	# end __load_viz_type_selection_interface

	def __add_subsample_selection_controls( self, o_subframe, 
												i_row_number=0, 
												i_label_width_used_by_caller=0,
												b_force_disable=False ):

		PAD_LABEL_WIDTH=0
		PARAMETERS_CBOX_WIDTH=10

		i_label_width_to_use_if_we_add_control=max(  len( POP_SELECT_LABEL ) + PAD_LABEL_WIDTH, 
														len( LOCI_SELECT_LABEL ) + PAD_LABEL_WIDTH , 
														i_label_width_used_by_caller  ) 

		ls_values=[ self.__pop_subsample_values, self.__loci_subsample_values ] 
		ls_labels=[ POP_SELECT_LABEL , LOCI_SELECT_LABEL ]
		ls_attributes=[ POP_SELECT_SUBSAMPLE_ATTR, LOCI_SELECT_SUBSAMPLE_ATTR ]
		ls_tooltips=[ "Regression will be computed on population samples at this subsample value.",
						"Regression will be computed on loci samples at this subsample value." ]
		i_row_increment=0

		s_combo_box_state="readonly"

		i_label_width_used=None
		
		try: 
			for idx in range( len( ls_values ) ): 
				if len( ls_values[idx] ) > 1:
					i_label_width_used=i_label_width_to_use_if_we_add_control

					s_attribute_name=ATTRIBUTE_DEMANLGER + ls_attributes[ idx ] 

					o_this_keyval=KeyListComboFrame( s_name=ls_labels[ idx ],
								qs_choices=ls_values[idx], 
								i_default_choice_number=1,
								o_master=o_subframe,
								s_associated_attribute=s_attribute_name,
								o_associated_attribute_object=self,
								def_on_new_selection=self.__test_values,
								i_labelwidth=i_label_width_to_use_if_we_add_control,
								i_cbox_width=PARAMETERS_CBOX_WIDTH,
								s_label_justify='left',
								s_tooltip=ls_tooltips[ idx ],
								b_is_enabled=True,
								o_validity_tester=None,
								s_state=s_combo_box_state,
								b_force_disable=b_force_disable )

					o_this_keyval.grid( row=i_row_number + i_row_increment, sticky=( NW ) )

					self.__param_value_frames_by_attr_name[ s_attribute_name ] = o_this_keyval

					i_row_increment+=1
				#end if len > 1
		except Exception as oex:
			s_msg="In PGGuiViz instance, " \
						+ "def __add_subsample_selection_controls, " \
						+ "exception raised: " + str( oex ) + "."
			sys.stderr.write( s_msg + "\n" )
			raise oex
		#end try...except
		#We return the number of rows used to add subsample controls:
		i_return_label_width=i_label_width_used if i_label_width_used is not None \
														else i_label_width_used_by_caller
		return	i_row_increment, i_return_label_width
	#end __add_subsmmple_selection_controls

	def __write_subsampled_tsv_file( self ):
		return
	#end __write_subsampled_tsv_file

	def __load_params_interface( self, b_force_disable = False ):	

		if VERY_VERBOSE:
			print( "in __load_params_interface")
		#end if very verbose

		PARAMETERS_FRAME_PADDING=30
		PARAMETERS_FRAME_STYLE="groove"
		PAD_LABEL_WIDTH=0
		LABEL_WIDTH=self.__get_max_longname_length() \
				+ PAD_LABEL_WIDTH
		ENTRY_WIDTH_STRING=20
		ENTRY_WIDTH_NONSTRING=10
		PARAMETERS_CBOX_WIDTH=20
		GRID_SPACE_HORIZ=10
		VIZ_SUBFRAME_KEY="viz"

		try:

			ls_params=self.__param_set.getShortnamesOrderedBySectionNumByParamNum()

			PARAMETERS_FRAME_LABEL=None
			s_section_name=None

			if self.__viztype=="Regression":
				PARAMETERS_FRAME_LABEL="Regression Plotting"
				s_section_name="VizRegress" 
			elif self.__viztype == "Subsample":
				PARAMETERS_FRAME_LABEL="Subsample Plotting"
				s_section_name="VizSubsample"
			else:
				'''
				As of 2016_11_24, we implement regression 
				as fully as possible, subsample not ready,
				and further types yet unknown:
				'''
				s_msg="In PGGuiViz instance, " \
						+ "def __load_params_interface, " \
						+ "attribute __viztype has unknown value: " \
						+ str( self.__viztype ) + "."
				raise Exception( s_msg )
			#end if viz type is Regresssion, else Subsample, else error


			if VIZ_SUBFRAME_KEY in self.__interface_subframes:
					self.__interface_subframes[ VIZ_SUBFRAME_KEY ].grid_remove()
					self.__interface_subframes[ VIZ_SUBFRAME_KEY ].destroy()
			#end if subframe already exists, get rid of it.


			o_params_subframe=LabelFrame( self,
					padding=PARAMETERS_FRAME_PADDING,
					relief=PARAMETERS_FRAME_STYLE,
					text=PARAMETERS_FRAME_LABEL )

			self.__interface_subframes[ VIZ_SUBFRAME_KEY ]= \
											o_params_subframe

			#First we add add subsample value selection controls,
			#if needed.
			i_rows_used_for_subsampling_selection=0
			i_max_label_width=LABEL_WIDTH

			if  self.__viztype in VIZ_TYPES_REQUIRING_SUBSAMPLE_SELECTION:
				i_rows_used_for_subsampling_selection, i_max_label_width= \
						self.__add_subsample_selection_controls( o_params_subframe, 0, 
																		LABEL_WIDTH, 
																		b_force_disable  )	
			#end if we need to add subsample selection controls

			#We add param controls starting at the first
			#row number below subsampiing selection controls
			#(if any).
			i_row=i_rows_used_for_subsampling_selection

			for s_param in ls_params:

				'''
				Tells which section (bordered) interface this param
				entry box or combo box or radio button should
				be placed.  As of 2016_09_15, all are in the "Regress" 
				section. 			

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
			
				#The name used in this PGGuiViz instance
				#to hold the parameter value (as updated by
				#the control frame (most often KeyValFrame).
				s_attr_name=ATTRIBUTE_DEMANLGER + s_param

				'''
				This will be passed to the entrybox or cbox, etc
				Control class (most often KeyValFrame).  We
				test use the current value if the attribure 
				exists in this PGGuiViz instance, 
				else use default (and create the new atttr):
				'''
				v_value_for_entry_control=None

				if  hasattr( self, s_attr_name ):
					v_value_for_entry_control=getattr( self, s_attr_name )
				else:
					setattr( self, s_attr_name, v_param_default_value )
					v_value_for_entry_control=v_param_default_value
				#end if not has attr

				if not ( s_param_interface_section == "VizAll" \
							or s_param_interface_section == s_section_name ):
					continue
				#end if param is common to all Viz schemes,
				#or is part of the section given,
				#or is the viz type combo box param

				#we use the first entry in the list
				#as the default value for the list editor
				#(used by the KeyValFrame object):

				if b_param_is_list:
					i_len_default_list=len( v_param_default_value )
					v_param_default_value=None if i_len_default_list == 0  else v_param_default_value[ 0 ]
				#end if param is list

				if VERY_VERBOSE:
					print ( "in test, param name: " + s_param )
					print ( "in test, param value type: " +	str( o_param_type ) )
					print ( "in test, param value: " +	str(  v_param_default_value ) )
				#end if VERY_VERBOSE

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
					def_on_entry_change=self.__test_values

					if s_param_assoc_def != "None":
						def_on_entry_change=getattr( self,  s_param_assoc_def )
					#end if we have a named def in the param set

					i_entry_width_this_param=ENTRY_WIDTH_STRING if o_param_type==str \
																else ENTRY_WIDTH_NONSTRING

					o_this_keyval=KeyValFrame( s_name=s_param_longname,
						v_value=v_value_for_entry_control,
						o_type=o_param_type,
						v_default_value=v_default_item_value,
						o_master=o_params_subframe,
						o_associated_attribute_object=self,
						def_entry_change_command=def_on_entry_change,
						s_associated_attribute=s_attr_name,
						i_entrywidth=i_entry_width_this_param,
						i_labelwidth=i_max_label_width,
						b_is_enabled= ( s_param_control_state == "enabled" ),
						s_entry_justify=s_this_entry_justify,
						s_label_justify='left',
						s_tooltip=s_param_tooltip,
						o_validity_tester=o_validity_checker,
						b_force_disable=b_force_disable,
						b_use_list_editor=True )

				elif s_param_control_type.startswith("cbox"):
					s_state_this_cbox=None
					if s_param_control_type=="cboxnormal":
						s_state_this_cbox="normal"
					elif s_param_control_type=="cboxreadonly":
						s_state_this_cbox="readonly"
					else:
						s_msg="In PGGuiViz instance, " \
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
					if s_param_assoc_def == "None":
						def_on_combo_choice_change=self.__test_values
					else:
						def_on_combo_choice_change=getattr( self,  s_param_assoc_def )
					#end if def is "None"

				
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
							if o_validity_checker is not None:
								o_validity_checker.value=s_value
								if not o_validity_checker.isValid():
									s_msg=self.__validity_checker.reportInvalidityOnly()
									PGGUIInfoMessage( self, s_msg + "\nResetting to default value." )
									setattr( self, s_attr_name, v_default_item_value )
								else:
									if s_state_this_cbox == "normal":
										#Validity checker evals as valid,
										#so the current attribute value is added to the cbox list:
										qs_control_list, i_current_item_number = self.__add_value_to_cbox_tuple_and_return_index( \
												 qs_control_list, s_value ) 
										i_current_item_number += 1
									else:
										s_msg="In PGGuiViz instance, def __load_params_interface, " \
														+ "invalid combobox value found for param, " \
														+ s_attr_name + ", with value: " + s_value + ".  " \
														+ "Resetting to default value."  
										PGGUIInfoMessage( self, s_msg  )
										setattr( self, s_attr_name, v_default_item_value )
									#end if normal cbox, add new value, else error
								#end if invalid current value, else add it to control list
							else:
								if s_state_this_cbox == "normal":
									#Validity checker evals as valid,
									#so the current attribute value is added to the cbox list:
									qs_control_list, i_current_item_number=self.__add_value_to_cbox_tuple_and_return_index( \
																						qs_control_list, s_value )
									i_current_item_number += 1
								else:
									s_msg="In PGGuiViz instance, def __load_params_interface, " \
													+ "invalid combobox value found for param, " \
													+ s_attr_name + ", with value: " + s_value + ".  " \
													+ "Resetting to default value."  
									PGGUIInfoMessage( self, s_msg  )
									setattr( self, s_attr_name, v_default_item_value )
								#end if normal cbox, add new value, else error

							#end if valididty checker not None, else value is 
							#automatically treated as valid
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
								i_labelwidth=i_max_label_width,
								i_cbox_width=PARAMETERS_CBOX_WIDTH,
								s_label_justify='left',
								s_tooltip=s_param_tooltip,
								b_is_enabled=( s_param_control_state == "enabled" ),
								o_validity_tester=o_validity_checker,
								s_state=s_state_this_cbox,
								b_force_disable=b_force_disable )

				elif s_param_control_type=="radiobutton":
					raise Exception( "radio button key val not yet implemented for neestimator gui" )
				else:
					s_message="In PGGuiViz instance, " \
							+ "def __load_params_interface, " \
							+ "unknownd control type read in " \
							+ "from param set: " \
							+ s_param_control_type + "."
					raise Exception( s_message )
				#end if control is entry, else cbox, else radiobutton, else unknown

				o_this_keyval.grid( row=i_row + ( i_param_position_in_order - 1 ), sticky=( NW ) )

				#Keep a reference to this param frame frame keyed to its attribute name
				self.__param_value_frames_by_attr_name[ s_attr_name ] = o_this_keyval

			#end for each param

			o_params_subframe.grid( row=ROW_NUM_VIZ_PARAMS_FRAME, 
						column=COL_NUM_VIZ_PARAMS_FRAME,
						sticky=(NW), padx=GRID_SPACE_HORIZ )

			o_params_subframe.grid_columnconfigure(0, weight=1 )
			o_params_subframe.grid_rowconfigure( 0, weight=1 )

			self.grid_columnconfigure( 1, weight=1 )
			self.grid_rowconfigure( 0, weight=1 )

		except Exception as oex:
	
				s_msg = "In PGGuiViz instance, "  \
							+ "def __load_params_interface, " \
							+ "an exception was raised: " \
							+ str( oex ) + "."
				PGGUIErrorMessage( self, s_msg )
				raise( oex )
		#end try...except
		return
	#end __load_params_interface

	def __add_value_to_cbox_tuple_and_return_index(  self, \
											qs_control_list, s_new_value ):

		qs_control_list += ( s_new_value, )

		i_index_number=qs_control_list.index( s_new_value )

		return qs_control_list, i_index_number
	#end __add_value_to_cbox_tuple_and_return_index

	def __update_viz_params_interface( self, b_force_disable=False ):
		'''
		An interface-like def, to comply with the associated def value in the original
		param set file used for Viz params, which is a combined param set, used
		by PGGuiNeEstimator instances.  The set needs to specify the "vis_params" in the def name, 
		to distringuish the call from other param categories (loci or 
		pop sampling, for example).
		'''
		self.__load_params_interface( b_force_disable )
		return
	#end __update

	def __update_params_interface( self, b_force_disable=False ):
		self.__load_params_interface(	b_force_disable=b_force_disable )
		return
	#end __update_vis_params_interface

	def __on_click_run_or_cancel_viz_button( self ):

		if self.__op_in_progress:
			o_mbox=PGGUIYesNoMessage( self , 
						"Are you sure you want to cancel " \
					+ "the analysis and remove all of its output files?" )
			b_answer = o_mbox.value

			if b_answer:
				self.__cancel_viz()
				self.__op_in_progress=False
				self.__set_controls_by_run_state( self.__get_run_state() )
			#end if yes
		else:
			if self.__params_look_valid( b_show_message=True ):
				self.runViz()
			#end if params look valid
		#end if sim in progress else not

		return

	#end __on_click_run_or_cancel_viz_button

	def __params_look_valid( self, b_show_message = False ):
		'''
		As of 2016_12_13, minimal param check performed.
		'''
		s_tsv_file=self.__tsv_file.get()
		b_result=False
		s_msg=""

		if s_tsv_file.lower()=="none":
			b_result=False
			if b_show_message:
				s_msg+="The tsv file name, " + s_tsv_file  \
								+ ", is not valid." 
			#end if show message
		else:
			b_result=True
		#end if tsv vile is string "none"
		
		if s_msg != "":
			PGGUIInfoMessage( self, "Invalid parameter:\n" + s_msg )
		#end if s_msg

		return b_result

		return True
	#end __params_look_valid

	def __write_viz_config_file( self ):

		o_config_maker=PGLineRegressConfigFileMaker( self )
		o_config_maker.writeConfigFile()
		
		return o_config_maker
	#end __write_viz_config_file

	def __run_viz_by_type( self, s_config_file ):
		try: 
			
			s_estimates_table=self.__tsv_file.get()
		
			'''
			These two subsample values should be non-None only if
			the loaded file has > 1 pop or loci subsample value,
			and the viz type is one requiring selecting one of each
			(as of 2016_12_20, only regression viztype requires the
			selection).

			If the gpgutilities.call_plotting_program_in_new_subprocess 
			evals them as non-None, it or its own called defs will
			write a tsv file filtered by this or these value(s).
			'''

			if self.__viztype in VIZ_TYPES_REQUIRING_SUBSAMPLE_SELECTION:
				s_selected_pop_sample_value= \
						getattr( self, ATTRIBUTE_DEMANLGER + POP_SELECT_SUBSAMPLE_ATTR )
				s_selected_loci_sample_value= \
						getattr( self, ATTRIBUTE_DEMANLGER + LOCI_SELECT_SUBSAMPLE_ATTR )

				if s_selected_pop_sample_value == None \
							and s_selected_loci_sample_value == None \
							and ( len( self.__pop_subsample_values ) > 1 \
									or len( self.__loci_subsample_values ) > 1 ):
					s_msg="In PGGuiViz instance, def __run_viz_by_type, " \
									+ "viz type, " + self.__viztype \
									+ ", requires subsample value selection. " \
									+ "The subsample values for both pop and loci " \
									+ "have \"None\" value, but multi values are found in " \
									+ "one or both.\n--pop values: " \
									+ str( self.__pop_subsample_values ) \
									+ "\n--loci values: " \
									+ str( self.__loci_subsample_values ) + "."
					raise Exception( s_msg )
				#end if multiple values for pop and/or loci subsamples
				#but no selection for either
			else:
				#Even if there are selected subsample values,
				#we set them to None for viz types not requiring
				#subsample value selection.
				s_selected_pop_sample_value = None
				s_selected_loci_sample_value = None
			#ened if subsampling value required

			self.__multi_process_event=multiprocessing.Event()

			self.__op_process=multiprocessing.Process( \
					target=pgut.call_plotting_program_in_new_subprocess,
									args=(  self.__viztype,
										s_estimates_table,
											s_config_file,
											s_selected_pop_sample_value,
											s_selected_loci_sample_value,
											self.__multi_process_event ) )

			self.__op_process.start()

			self.__set_controls_by_run_state( self.__get_run_state() )

			self.__init_interface( b_force_disable=True )
			self.__load_viz_type_selection_interface( b_force_disable=True )
			self.__update_params_interface( b_force_disable=True )
			self.__op_in_progress=True
			self.__run_state_message=" " + VIZ_RUNNING_MSG
			self.after( 500, self.__check_progress_operation_process )
		except Exception as oex:
			s_msg="In PGGuiViz instance, "  \
					+ "def __run_viz_by_type, " \
					+ "an exception was raised: " \
					+ str( oex ) + "."
			PGGUIErrorMessage( self, s_msg )

			raise( oex )
		#end try . . . except 
		return
	#end __run_viz_by_type

	def runViz( self ):
		try:
			o_config_file_writer=self.__write_viz_config_file()
			#we get the config file name from the writer,
			#so we can remove it after running the viz:
			s_config_file_name=o_config_file_writer.config_file_name
			self.__config_file_name=s_config_file_name

			self.__run_viz_by_type( s_config_file_name )
		except Exception as oex:
			s_msg = "In PGGuiViz instance, " \
							+ "def runViz, " \
							+ "an exception was raised: " \
							+ str( oex ) + "."
			PGGUIErrorMessage( self, s_msg )

			raise( oex )
		#end try ... except 
		return
	#end runviz

	def __check_progress_operation_process( self ):

		if self.__op_process is not None:
			if self.__op_process.is_alive():
				
				if VERY_VERBOSE:
					print ( "checking and process found alive" )
				#endif very verbose, print

				self.__op_in_progress = True
				self.__update_run_state_message()
				self.__run_state_label.configure( text=self.__run_state_message )
				self.after( 500, self.__check_progress_operation_process )
			else:
				if VERY_VERBOSE:
					print( "checking and process not None but not alive" )
				#end if very verbose, print

				self.__op_in_progress = False

				self.__op_process=None
				self.__run_state_message=""
				self.__init_interface( b_force_disable = False )
				self.__load_viz_type_selection_interface( b_force_disable = False )
				self.__load_params_interface( b_force_disable = False )
				if self.__config_file_name is not None:
					if KEEP_CONFIG_FILE == False:
						i_num_files_removed=pgut.remove_files( [ self.__config_file_name ] )
					#end if we are not keeping the config file
				#end if we have a config file, remove it
			#end if process alive else not
			self.__set_controls_by_run_state( self.__get_run_state() )
		else:
			if VERY_VERBOSE:	
				print( "process found to be None" )
			#endif very verbose, pring
			self.__op_in_progress = False
			self.__run_state_message=""
			self.__init_interface( b_force_disable = False )
			self.__load_viz_type_selection_interface( b_force_disable = False )
			self.__load_params_interface( b_force_disable = False )
			self.__update_genepopfile_sampling_params_interface( b_force_disable = False )
			self.__update_genepopfile_loci_sampling_params_interface( b_force_disable = False )
			self.__update_viz_params_interface( b_force_disable = False )
			self.__set_controls_by_run_state( self.__get_run_state() )

			#remove any existing config file:
			if self.__config_file_name is not None:
				if KEEP_CONFIG_FILE == False:
					#We do nothing for now with the return int
					#giving the number of files that were removed.
					i_num_files_removed=pgut.remove_files( [ self.__config_file_name ] )
				#end if we do not keep the config file
			#end if we have a config file, remove it

		#end if process not None else None

		return
	#end __check_progress_operation_process

	def __assign_subsample_process_results_and_reset_subsample_attributes( self, o_results=None ):

		if o_results is not None:

			ldls_subsample_values=self.__subsample_fetcher_map_result.get()

			'''
			The map_async call in 
			self.__get_subsample_values_lists_from_tsv_file_using_separate_process
			returns a list of results.  We always expect one result item only, 
			the return from a single call to 
			pgutilities.get_subsample_values_lists_from_tsv_file().
			'''

			i_num_results=len( ldls_subsample_values )

			if i_num_results != 1:
				s_msg="In PGGuiViz instance, " \
							+ "def __assign_subsample_process_" \
							+ "results_and_reset_subsample_attributes, " \
							+ "expecting a single result from the tsv file subsample " \
							+ "values fetching process, but found, " + str( i_num_results ) \
							+ "."
				raise Exception( s_msg )
			#end if non-unary result total
			dls_subsample_values= ldls_subsample_values[ 0 ]

			self.__pop_subsample_values=dls_subsample_values[ "pop" ]
			self.__loci_subsample_values=dls_subsample_values[ "loci" ]
			self.__pop_subsample_values.sort()
			self.__loci_subsample_values.sort()

		else:
			'''
			This def also gets called when the user cancels during
			the loading of a tsv file.  In this case we assign
			empty lists to the pop_subsampole value attributes,
			and None to the attributes that give user selection
			for pop and/or loci attributes.
			'''

			self.__reinitialize_subsample_values_as_emtpy()
		#end if results else reassign empty lists

		self.__subsample_fetcher_map_result=None
		self.__subsample_fetcher_process_pool=None

	#end __assign_subsample_process_results_and_reset_subsample_attributes

	def __reinitialize_subsample_values_as_emtpy( self ):
		self.__pop_subsample_values=[]
		self.__loci_subsample_values=[]
		setattr( self, ATTRIBUTE_DEMANLGER + POP_SELECT_SUBSAMPLE_ATTR, None )
		setattr( self, ATTRIBUTE_DEMANLGER + LOCI_SELECT_SUBSAMPLE_ATTR, None )
	#end __reinitialize_emtpy_subsample_values

	def __select_output_directory( self ):
		s_outputdir=tkfd.askdirectory( \
				title='Select a directory for file output' )
		#if no dir selected, return	

		#If user clicks "Cancel", an emtpy tuple is returned:
		if pgut.dialog_returns_nothing( s_outputdir ):
			return
		#end if no dir selected
		
		self.__output_directory.set( s_outputdir )
		self.__init_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )

		return
	#end __select_output_directory

	def __load_tsv_file( self ):

		#dialog returns sequence:
		s_tsv_file=tkfd.askopenfilename(  \
				title='Load an Ne Estmation *.tsv file' )

		if pgut.dialog_returns_nothing( s_tsv_file ):
			return
		#end if no file selected, return with no change
		#in tsv file loaded

		self.__tsv_file.set( s_tsv_file )
	
		self.__update_subsample_value_attributes()

		self.__init_interface()
		self.__load_viz_type_selection_interface()
		self.__load_params_interface()
		self.__set_controls_by_run_state( self.__get_run_state() )

		return
	#end __load_tsv_file

	def __update_subsample_value_attributes( self ):
		'''
		The tsv file (named by attr self.__tsv_file,
		is queried to get subsample values for pop
		and loci, and store them in the attributes. 

		This is performed on a separate process,
		since, if the tsv file is large, the
		GUI could be blocked for a comparatively
		long time.
		'''

		self.__get_subsample_values_lists_from_tsv_file_using_separate_process()

		return

	#end __update_subsample_value_attributes

	def __get_subsample_values_lists_from_tsv_file_using_separate_process( self ):

		'''
		We call the pgutilities def get_subsample_values_lists_from_tsv_file in a multiprocessing
		Pool -- alwyays with just one worker, but we use the Pool since it automates
		convenient retrieval of the return value.

		While the process pool is alive use we display a dialog box
		that self-destructs when the Pool process' map result is 
		ready (ready()==True).  If the user clicks "cancel" on the dialog,
		then we reset the tsv file to "none," and assign empt8y lists
		to the pop and loci subsample attribute lists.
		'''
	
		s_tsv_file=self.__tsv_file.get()

		self.__subsample_fetcher_process_pool=multiprocessing.Pool( 1 )

		self.__subsample_fetcher_map_result=self.__subsample_fetcher_process_pool.map_async( \
					pgut.get_subsample_values_lists_from_tsv_file,
					[ s_tsv_file ] )

		PGGUIMessageWaitForResultsAndActionOnCancel( \
										o_parent=self,
										s_message="Getting Nb estimation file info...",
										s_title="Loading File info",										
										def_boolean_signaling_finish=self.__subsample_fetcher_map_result.ready,
										def_on_cancel=self.__on_cancel_get_subsample_values )
		
		if self.__subsample_fetcher_map_result is not None:
			self.__assign_subsample_process_results_and_reset_subsample_attributes( self.__subsample_fetcher_map_result )
		#end if results exist

		return

	#end get_subsample_values_lists_from_tsv_file_using_separate_process

	def __on_cancel_get_subsample_values( self ):
		self.__tsv_file.set( "none" )
		self.__assign_subsample_process_results_and_reset_subsample_attributes( o_results=None )
		return
	#end __on_cancel_get_subsample_values

	def __update_tsv_file_listbox( self ):
		self.__tsv_file_listbox.config( state="normal" )

		#clear the list box of current entries:

		self.__tsv_file_listbox.delete( 0, END )

		s_tsv_file=self.__tsv_file.get()

		s_basename=pgut.get_basename_from_path( s_tsv_file ) 

		self.__tsv_file_listbox.insert( END, s_basename )

		self.__tsv_file_listbox.config( state="disabled" )

		return
	#end __update_tsv_file_listbox

	def __cancel_viz( self ):

		SLEEPTIME_WAITING_FOR_EVENT_CLEAR=0.25

		TIMEOUT_WAITING_FOR_EVENT_TO_CLEAR=0o5

		if self.__op_process is not None:
			
			if self.__multi_process_event is not None:
				try:
					if VERY_VERBOSE==True:
						print( "in cancel_viz, setting event" )
					#end if very verbose

					self.__multi_process_event.set()
				except Exception as oex:
					s_msg = "in PGGuiViz instance in def " \
							+ "__cancel_viz, Exception after " \
							+ "setting multi process event: " \
							+ str( oex ) + "."
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

				while self.__multi_process_event.is_set() \
						and time.time() - f_starttime < \
						TIMEOUT_WAITING_FOR_EVENT_TO_CLEAR:

					if VERY_VERBOSE:
						print( "in while loop in gui while event is set" )
					#end if very verbose

					time.sleep( SLEEPTIME_WAITING_FOR_EVENT_CLEAR )
				#end while

				if VERY_VERBOSE:
					if self.__multi_process_event.is_set():
						print( "timed out waiting for event to clear -- even still set. " \
								+ "Terminating op_process " )
					else:
						print( "event now clear. Terminating op_process..." )
					#end if op_process eval did not clear the event, else did
				#end if very verbose

				self.__op_process.terminate()
			except Exception as oex:
					s_msg = "in PGGuiViz instance in def " \
							+ "__cancel_viz, Exception after " \
							+ "terminating the process that starts " \
							+ " the viz: "  \
							+ str( oex ) + "."
					sys.stderr.write( s_msg + "\n" )
			#end try, except

			if self.__config_file_name is not None:
				if KEEP_CONFIG_FILE == False:
					#pgutilities def will check for path before calling remove.
					#If the file is not found, the return value is zero, else 1.
					i_num_files_removed = pgut.remove_files( [ self.__config_file_name ] )
				#end if we do not keep the config file
			#end if we have a config file name
			if VERY_VERBOSE:
				print ( "removing the following output file: " \
						+ self.__config_file_name )
			#end if very verbose

		else:
			s_msg="No viz run process found.  No run was cancelled."
			sys.stderr.write( s_msg  + "\n"  )
		#end if process exists cancel, else message
		return
	#end __cancel_viz

	def __remove_output_files( ls_output_files ):
		if VERY_VERBOSE:
			print( "removing files: " + str( ls_output_files ) )
		#end if very verbose
		pgut.remove_files( ls_output_files )
		return
	#end __remove_output_files

	def cleanup( self ):
		self.__cancel_viz()
		return
	#end cleanup

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
			s_msg="In PGGuiViz instance, " \
						+ "def __create_validity_checker, " \
						+ "invalid initial value when setting up, " \
						+ "validator object.  Validation message: " \
						+ o_checker.reportInvalidityOnly() + "."
			raise Exception( s_msg )
		#end if not valid default
		return o_checker
	#end __create_validity_checker

	def __test_values( self ):
		'''
		Other interfaces use this for debugging.
		Currently it is not implemented for this
		interface.
		'''
		return
	#end __test_values

	def __get_run_state( self ):
		if self.__op_in_progress:
			return PGGuiViz.RUN_IN_PROGRESS
		else:
			if self.__params_look_valid():
				return PGGuiViz.RUN_READY
			else:
				return PGGuiViz.RUN_NOT_READY 
		#end if in progress else not
		return
	#end __get_run_state

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

	def __set_controls_by_run_state( self, i_run_state ):

		if i_run_state==PGGuiViz.RUN_NOT_READY:
			self.__run_button.config( text="Run Viz", 
													state="disabled" ) 
			self.__enable_or_disable_frames( b_do_enable=False )
		elif i_run_state==PGGuiViz.RUN_READY:
			self.__run_button.config( text="Run Viz", 
													state="enabled" )
			self.__enable_or_disable_frames( b_do_enable=True )
		elif i_run_state==PGGuiViz.RUN_IN_PROGRESS:
			self.__run_button.config( text="Cancel Viz", state="enabled" )
			self.__enable_or_disable_frames( b_do_enable=False )
		else:
			s_msg="In PGGuiViz instance, " \
					+ "__set_controls_by_run_state: " \
					"unknown run state value: " + str( i_run_state )
			raise Exception( s_msg )
		#end if run state not ready, else ready, else in progress, 
		#else error
		return
	#end __set_controls_by_run_state

	def __enable_or_disable_frames( self, b_do_enable ):
		'''
		As of 2016_12_13, not yet implemented.
		'''
		return
	#end __enable_or_disable_frames
if __name__ == "__main__":
	pass
#end if main

