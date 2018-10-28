'''
Description
A PGGUIApp object with widgets that manage a simuPop simulation
'''

from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import range
__filename__ = "pgsimupopper.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False
VERY_VERBOSE=False
VERY_VERY_VERBOSE=False

DO_PUDB=False

INIT_ENTRY_CONFIG_FILE=()

SIM_RUNNING_MSG="Simulation in progress"

if DO_PUDB:
	from pudb import set_trace; set_trace()
#end if debug

import agestrucne.pgmenubuilder as pgmb
import agestrucne.pgguiapp as pgg
import agestrucne.pgsimupopresources as pgsr
import agestrucne.pginputsimupop as pgin
import agestrucne.pgparamset as pgps
import agestrucne.pgoutputsimupop as pgout

from agestrucne.pgkeyvalueframe import KeyValFrame
from agestrucne.pgkeylistcomboframe import KeyListComboFrame
from agestrucne.pgkeycategoricalvalueframe import KeyCategoricalValueFrame
from agestrucne.pgkeycheckboxvalueframe import KeyCheckboxValueFrame

from agestrucne.pgguiutilities import PGGUIInfoMessage
from agestrucne.pgguiutilities import PGGUIYesNoMessage
from agestrucne.pgguiutilities import PGGUIErrorMessage
from agestrucne.pgutilityclasses import IndependantSubprocessGroup
from agestrucne.pgutilityclasses import FloatIntStringParamValidity
from agestrucne.pgutilityclasses import ValueValidator

import agestrucne.pgutilities as pgut
import agestrucne.pgparallelopmanager as pgpar
'''
2018_07_27.  We use a static method in this class
to check whether a user-supplied loci info file
has allele frequencies or not:
'''
import agestrucne.pgsimupoplociinfo as pgsli

import sys
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

from tkinter import *
#since we import all names from Tkinter,
#and ttk, we get the ttk widgets
#with their better styling,#automaitcally
#. (see #https://docs.python.org/2/library/ttk.html)
from tkinter.ttk import *

import tkinter.filedialog as tkfd

'''
2017_05_05. Aids in defs onCullMethodSelectionChange,
and onUpdateMaleProb, to properly set
the male probablity number and the enabled/disabled
state its entry box, given the cull method selected.

2018_05_07.  We've changed the name "equal_sex_ratio"
to "maintain_distribution".  Also we'll now use the
constants in the PGInputSimuPop class, so lower the
number of places these text values are assigned:
'''
#CBOX_EQUAL_SEX_RATIO_TEXT="equal_sex_ratio"
#CBOX_SURVIVAL_RATE_TEXT="survival_rates"
CBOX_EQUAL_SEX_RATIO_TEXT=pgin.PGInputSimuPop.CONST_CULL_METHOD_EQUAL_SEX_RATIOS
CBOX_SURVIVAL_RATE_TEXT=pgin.PGInputSimuPop.CONST_CULL_METHOD_SURVIVIAL_RATES

'''
2018_06_02.  New parameter input.loci_file_name has a default value
that signifies no file name.  We need to test for this value and so
we import the module's constant that sets this string:
'''
from agestrucne.pgsimupoplociinfo import NO_LOCI_FILE


'''
2018_06_02. To manage the state of controls related to loci totals,
as a fucntion of the state of the new parameter use_loci_file flag,
which, when true, makes these parameters irrelevant:
'''
LOCI_RELATED_TOTALS_CONTROLS=[ "numSNPs", "numMSats", "numChroms", "startAlleles" ]

'''
2018_07_27. Having added an option for users to add a 4th column
in a loci info file, giving allele frequencies, we now need
to manage the state of the het init controls, which will be
disabled when the user wants to use their provided frequencies.
'''
ALLELE_FREQ_INIT_RELATED_CONTROLS=[ "het_init_snp", "het_init_msat" ]

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
	this class depends on code in the pgparallelopmanager.py
	(used to be pgutilities.py)
	module, which has a def that makes a system call to 
	instantiate a new python interpreter, and call a script,
	do_sim_replicate.py, which then calls another def in 
	pgutilities.py, which builds and runs a PGOpSimuPop object.
	
	'''

	#possible states of the gui:
	RUN_NOT_READY=0
	RUN_READY=1
	RUN_IN_PROGRESS=2

	'''
	Note, 2017_01_15.  This max Was set to 18 to comply with 
	a max 31 character limit of file length (18 + chars needed 
	to add extensions) of the input genepop files and the derived 
	intermediate input files to NeEstimator.  With changes to the 
	NeEstimator file handling in pgdriveneestimator.py, we can 
	remove this limit, but still impose, pro forma a large max.
	'''
	MAX_CHARS_BASENAME=500

	def __init__( self,  o_parent,  s_param_names_file=None, 
							s_life_table_file_glob=None,
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

		#input object PGInputSimuPop used to make the
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
		
		'''
		2017_04_28.  For label width's sized on Linux, 
		some Windows labels truncate text.
		'''
		b_is_windows_platform=pgut.is_windows_platform()

		ENTRY_WIDTH=70
		LABEL_WIDTH=22 if b_is_windows_platform else 20
		LOCATIONS_FRAME_PADDING=30
		LOCATIONS_FRAME_LABEL="Load/Run"
		LOCATIONS_FRAME_STYLE="groove"
		RUNBUTTON_PADDING=0o7	

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

		'''
		Though we don't want the Entry box enabled, we want the
		label to show:
		'''
		o_config_kv.setLabelState( "enabled" )
		o_config_kv.grid( row=i_row, sticky=( NW ) )

		i_row+=1

		o_outdir_kv=KeyValFrame( s_name="Select output directory", 
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
		
		o_outdir_kv.setLabelState("enabled" )

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
		
		#Despite sometimes disabling the text entry,
		#we want the label always to show non-grayed-out.
		self.__outbase_kv.setLabelState( "enabled" )

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
		

		'''
		2018_05_26. We add a subframe to go inside the genome subframe, to keep
		the flag and file loader controls for the loci file together:
		'''
		self.__loci_file_sub_subframe=Frame( do_category_frames[ "Genome" ] )
		self.__loci_file_sub_subframe.grid()

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

	def __is_param_that_needs_a_control( self, s_param, v_val ):
		'''
		2018_10_23.  This code was extracted from def __load_values_into_interface
		so that we can call it from def __get_sorted_list_of_params_that_need_controls,
		and deliver back to __load_values_into_interface a list both filtered to only
		relevant controls as well as sorted into a proper order of addition into the
		interface.
		'''

		b_needs_a_control=True

		#we don't display this if its a def
		#or a function (and so not a parameter)
		if inspect.isroutine( v_val ):
			b_needs_a_control=False
		#end if def or function

		if  type( v_val ) == str:
			if v_val.startswith( "<bound method" ):
				b_needs_a_controls= False
			#end if method, skip
		#end if the value is a string

		#if not a routine or bound method, 
		#check to make sure it is a valid param:

		if b_needs_a_control==True:
			if self.__input.param_names is None:
				s_msg=" In PGGuiSimuPop instance, " \
						+ "def __is_param_that_needs_a_control, " \
						+ "member __input has missing PGParamset " \
						+ "instance."
				raise Exception( s_msg )
			#end of no param_set object

			if not( self.__input.param_names.isInSet( s_param ) ):
					s_msg=" In PGGuiSimuPop instance, " \
						+ "def __is_param_that_needs_a_control, " \
						+ "member __input members PGParamset " \
						+ "instance has no param, " + s_param + "."
					raise Exception( s_msg )
			#end if param not in param_names objectd
		#end if looks like param, validate

		return b_needs_a_control
	#end __is_param_that_needs_a_control

	def __get_sorted_list_of_params_that_need_controls( self, ls_input_params ):
		'''
		2018_10_23. Added this call as preprocessing of the param list to
		order controls within subframes by delivering a list such that
		the iterative creation of controls in def __load_values_into_interface
		will order the controls in accordance with the row order as entered
		in the simupop_param_names file.
		'''
		ls_sorted_param_list=[]

		i_param_count=0

		dds_params_by_section_by_row_position={}

		for s_param in ls_input_params:

			v_val=getattr( self.__input, s_param )

			if ( self.__is_param_that_needs_a_control( s_param, v_val ) ):

				i_param_count+=1

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
					s_param_assoc_def,
					s_param_control_state,
					s_def_on_loading ) = \
							self.__input.param_names.getAllParamSettings( s_param )
			
		
				if s_section_name not in dds_params_by_section_by_row_position:
					dds_params_by_section_by_row_position[ s_section_name ]=\
											{ i_param_position_in_order:s_param }
				else:

					#each param position number should be unique within a section:
					if i_param_position_in_order in dds_params_by_section_by_row_position[ s_section_name ]:
						s_msg="In PGGuiSimuPop instance, def __get_sorted_list_of_params_that_need_controls, " \
								+ "The program found at least two params in section " + s_section_name \
								+ ", at position " + str( i_param_position_in_order ) + "." 
						raise Exception( s_msg )
					#end if we've already seen this section/postion combo, then non-unique placement error

					dds_params_by_section_by_row_position[ s_section_name][ \
											i_param_position_in_order ] = s_param 
				#end if new section else not

			#end if control is needed, add param to dict

		#end for each param

		#how we put each param in a list, so that it will be created
		#by def __load_values_into_interface in the correct order
		#within its subframe (exs: Genome, Population).

		for s_section in dds_params_by_section_by_row_position:
			ds_param_by_position=dds_params_by_section_by_row_position[ s_section ]
			li_sorted_postion_numbers=list( ds_param_by_position.keys() )
			li_sorted_postion_numbers.sort()
			for i_postion_number in li_sorted_postion_numbers:
				ls_sorted_param_list.append( \
						ds_param_by_position[ i_postion_number ] )
			#end for each postion	
		#end for each section
		return ls_sorted_param_list 
	#end __get_sorted_list_of_params_that_need_controls

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

		'''
		2017_04_28.  Label widths sized for Linux are sometimes too small in windows,
		so that text gets truncated.
		'''
		b_is_windows_platform=pgut.is_windows_platform()

		MAXLABELLEN=200
		WIDTHSMALL= 23 if b_is_windows_platform else 21
		WIDTHBIG= 24 if b_is_windows_platform else 21
		LENSMALL= 22 if b_is_windows_platform else 20

		'''
		2017_05_20.  For the configuration file info fields, so that their width
		is not initialized to a small value:
		'''
		DEFAULT_WIDTH_LONG_TEXT=40

		LABEL_WIDTH = [ WIDTHSMALL if i<LENSMALL else WIDTHBIG for i in range( MAXLABELLEN ) ] 
		PARAMETERS_CBOX_WIDTH=15
		
		DEFAULT_WIDTHS_FOR_SOME_TEXT_PARAMS={ "model_name":DEFAULT_WIDTH_LONG_TEXT, 
												"config_file":DEFAULT_WIDTH_LONG_TEXT }

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

		'''
		2017_04_20.  After making the default behaiour
		that when the control is disabled, so is the label,
		we will override by re-enabling the label for
		our interface.
		'''
		LABEL_ALWAYS_ENABLED=True

		self.__param_key_value_frames={}

		i_row=0

		o_input=self.__input
		
		ls_input_params=[ s_param for s_param in dir( o_input ) \
								if not( s_param.startswith( "_" ) ) \
									and not( s_param.startswith( PREFIX_FOR_INPUT_CONSTANTS ) )  ]

		ls_tags=o_input.param_names.tags

		ls_sections=[  o_input.param_names\
					.getConfigSectionNameFromTag( s_tag )  for s_tag in ls_tags ]

		#clear existing category frames (if any): 
		self.__clear_grid_below_row( self, 1 )

		#make frames, one for each category of parameter
		#(currently, "population", "configuration", "genome", "simulation"
		self.__remove_current_category_frames()
		self.__category_frames=self.__make_category_subframes( \
				set( ls_sections ) )	

		ls_input_params_that_need_controls=\
				self.__get_sorted_list_of_params_that_need_controls( ls_input_params )

		for s_param in ls_input_params_that_need_controls:
			
			PADPIX=0

			i_row+=1

			i_len_labelname=None

			if VERBOSE == True:
				o_def_to_run_on_value_change=self.__test_value
			#end if VERBOSE

			v_val=getattr( o_input, s_param )
		
			
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
				s_param_assoc_def,
				s_param_control_state,
				s_def_on_loading ) = \
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
				elif s_param == "loci_file_name" or s_param == "use_loci_file":
					o_frame_for_this_param=self.__loci_file_sub_subframe
				else:
					o_frame_for_this_param=self.__category_frames[ s_section_name ]
				#end if no nametag or name tag not in frame categories

				i_len_labelname=len( s_longname ) if s_longname is not None else len( s_param )
				i_width_labelname=LABEL_WIDTH[ i_len_labelname ]

				'''
				As of 2017_01_23, the param set (PGParamSet instance)
				now includeds a control state (see above, call to 
				getAllParamSettings), set either to enabled
				or disabled.  Hence we default to its setting, 
				though we keep the tests below that can change it, 
				in case these are conditions not anticipated by 
				the resource/simupop.param.names file that gives 
				the ParamSet object its parameter settings.
				'''
				b_allow_entry_change = ( s_param_control_state == "enabled" )

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
				
				if s_param_validity_expression != "None":
					'''
					Note that validity checker needs the "item" value,
					always equal to the default value, except when
					the latter is a list, in which case it is the first
					list item in the default value
					'''

					o_validity_checker=self.__create_validity_checker( v_default_value, 
																		s_param_validity_expression )
				#end if expression is not "None"

				#we send in the input object to the KeyValFrame (or similar class)
				#instance so it will be the object whose attribute (with name s_param)
				#is reset when user resets the value in the KeyValFrame:
				if s_param_control_type == "entry":

					i_entry_width=None

					if type( v_val ) == str:
						i_entry_width=len( v_val )
					elif s_param == "nbadjustment":
						i_entry_width=len( v_val ) + 10
					else:
						i_entry_width=7
					#end if string param type, else nbadjustment list, else other

					if  s_param in DEFAULT_WIDTHS_FOR_SOME_TEXT_PARAMS:
						if i_entry_width < DEFAULT_WIDTHS_FOR_SOME_TEXT_PARAMS[ s_param ]:
							i_entry_width=DEFAULT_WIDTHS_FOR_SOME_TEXT_PARAMS[ s_param ]
						#end if param's width is less than the default
					#end if this param has a long-text default width
						
					s_entry_justify='left' if type( v_val ) == str else 'right' 
					'''
					2017_02_07
					Still need to implement the
					validity checker arg, as done in
					pgguineestimator.py, but we are
					currently not presenting the litter skip
					lists as lists, which makes the 
					validity expression fail for such params.

					2017_03_09. Now using the validity checker,
					having changed many of the list param
					expressions to "x is None or ([valid type and range])".
					See the file simupop.param.names in the resources dir.
					'''

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
								o_validity_tester=o_validity_checker,
								b_force_disable=b_force_disable,
								s_tooltip=s_tooltip,
								b_use_list_editor=True if s_param=="nbadjustment" else False )

				elif s_param_control_type=="entrywithbutton":

					'''
					2018_05_26. This control type was added with the addition to the genome
					subframe, the ability of the user to use, in place of numSNPs and numChroms,
					a file that gives loci information.  We copied the code to setup the "entrywithbutton"
					control from the pgguineestimator.py, and, becausez it is a large piece of code,
					offload it into a separate def:
					'''
					o_kv=self.__setup_entry_with_button( \
								s_param=s_param,
								s_param_longname = s_longname,
								v_value_for_entry_control=v_val,
								o_param_type=o_param_type,
								v_default_item_value=v_default_value,
								o_subframe=o_frame_for_this_param,
								s_attr_name=s_attribute_to_update,
								o_attribute_object=self.__input,
								i_width_this_entry=i_entry_width,
								i_this_label_width=i_width_labelname,
								s_state_to_use=b_allow_entry_change,
								s_this_entry_justify='left',
								s_param_tooltip=s_tooltip,
								o_validity_checker=o_validity_checker,
								b_force_disable=b_force_disable,
								b_use_list_editor=True,
								o_param_assoc_def=def_to_call_on_change )

				#cbox types are specified as cboxreadonly or cboxnormal, so we test for prefix:	
				elif s_param_control_type.startswith( "cbox" ):
					'''
					As of 2016_11_25, there are two types of combobox
					'''
					s_state_this_cbox=None
					if s_param_control_type == "cboxnormal":
						s_state_this_cbox="normal"
					elif s_param_control_type == "cboxreadonly":
						s_state_this_cbox="readonly"
					else:
						s_msg="In PGGuiSimuPop, def __load_values_into_interface, " \
									+ "unknown cbox control type: " \
									+ s_param_control_type + "."
						raise Exception( s_msg )
					#end if normal, else readonly cbox

					qs_control_list=eval( s_param_control_list )

					i_current_item_number=None

					if v_val not in qs_control_list:
						s_msg="Current value for parameter " \
							 	+ s_param + ", " + str( v_val ) \
								+ ", is not found " \
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
								s_state=s_state_this_cbox,
								b_force_disable=b_force_disable )

				elif s_param_control_type == "boolradio":

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

				elif s_param_control_type=="checkbutton":
				
					'''
					Unlike for the key-value frame, here We use the longname 
					for param s_name, as that becomes the label text for the
					Checkbutton object.  We also send in an empty string for the
					label name, since it is not needed.
					'''
					o_kv=KeyCheckboxValueFrame( s_name=s_longname,
										v_value=v_val,
										o_master=o_frame_for_this_param, 
										s_associated_attribute=s_attribute_to_update,
										o_associated_attribute_object=self.__input,
										def_on_button_change=def_to_call_on_change,
										i_labelwidth=i_width_labelname,
										b_is_enabled=b_allow_entry_change,
										s_label_justify='right',
										s_label_name="",
										b_force_disable=b_force_disable,
										s_tooltip = s_tooltip )

				else:
					s_msg="In PGGuiSimuPop instance, def " \
							+ "__load_values_into_interface, " \
							+ "unknown control type spcified: " \
							+ s_param_control_type + "."
					raise Exception( s_msg )

				#end if control type entry, else combobox, else bool radio button, 
				#else check button, else unknown

				if LABEL_ALWAYS_ENABLED:
					o_kv.setLabelState( "enabled" )
				#end if labels should always be non-grayed-out

				'''
				2018_05_26. We've put a subframe inside the Genome
				to hold the flag and entry box for the loci info
				file.  We want the controls in this order:
				'''
				i_final_row=i_row	
				if s_param=="use_loci_file":
					i_final_row=1
				elif s_param=="loci_file_name":
					i__final_row=2
				#end if it's a pram we put in a sub-subframe, 
				#then we want the indicated order 

				o_kv.grid( row=i_final_row, sticky=(NW) )
				self.__param_key_value_frames[ s_param ] = o_kv

				#Execute the def to be run on loading the param,
				#if any.
				if s_def_on_loading != "None":
					o_mydef=getattr( self, s_def_on_loading )
					o_mydef()
				#end if we need to execute a def on loading
			#end if section name not "suppress"
		#end for each input param

		self.__place_category_frames( self.__category_frames )
		self.grid_columnconfigure( 0, weight=1 )
		self.grid_rowconfigure( 0, weight=1 )
		
		'''
		2018_06_02.  Now that all params have controls, we
		need to reset loci related totals according to the 
		state of the use_loci_file flag:
		'''
		if not( b_force_disable ):
			self.__reset_controls_whose_state_depends_on_state_of_other_controls()
		#end if not force disabling all controls, reset other-control-state-dependant controls
		return
	#end __load_values_into_interface

	def __reset_controls_whose_state_depends_on_state_of_other_controls( self ):
		'''
		2018_06_02. This def was added to manage the inititalization of loci-related 
		controls, whose enabled state depends on the state of our new param, 
		use_loci_file. Note that improvements in this code may include moving
		code from other defs that set control states depending on others' states.

		'''
		self.__initialize_state_of_loci_related_totals_controls()
		return
	#end __reset_controls_whose_state_depends_on_state_of_other_controls

	def onCullMethodSelectionChange( self ):
		'''
		Not implemented, 2016_11_01.  May
		not need to add any code here, since
		KeyListComboFrame control object resets
		the attribute in the input object
		automatically.

		2017_01_05  We add code that tests for
		the cull method value.  If it is 
		"equal_sex_ratio", we disable the
		"Probability male birth" text box,
		to indicate that the sex birth ratio
		will be set to 50/50 (i.e. the call
		to InitSex in the simulation will be
		maleProb=0.5).

		2018_06_24. Note that "equal_sex_ratio"
		has been changed to "maintain_distribution," but
		we're using a constant that is set in the pginputsimupop
		module, so we pick up the change automatically.
		'''
		f_reltol = 1e-99	

		if self.__input is not None:

			b_have_cullmethod_attr=hasattr( self.__input, "cull_method" )
			b_have_maleprob_attr=hasattr(  self.__input, "maleProb" )
			b_have_access_to_control="maleProb" in self.__param_key_value_frames

			#We ignore the returned value, which simply describes the action taken (if not None).
			s_result=self.__disable_or_enable_maleprob_according_to_cull_method()

			if b_have_cullmethod_attr  \
							and b_have_maleprob_attr \
							and b_have_access_to_control:
		

				if self.__input.cull_method == CBOX_EQUAL_SEX_RATIO_TEXT:

					o_this_kv=self.__param_key_value_frames[ "maleProb" ]

					if abs( self.__input.maleProb - 0.5 ) > f_reltol:
						o_this_kv.manuallyUpdateValue( 0.5 )
					#end if current value is not 0.5, set it manually
				#end if cull method is set to equal sex ratio, reset male prob to 0.5 
			#end if we have a cull_method attribute, a male prob attribute, 
			#and access to the maleProb entry control
		#end if we have an input object

		if VERY_VERBOSE:
			self.__test_value()
		#end if very verbose

		return
	#end __on_cull_method_selection_change

	def load_config_file( self, event=None ):

		try:
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
							+ "Exception: " + str( oe ) 
					o_diag=PGGUIInfoMessage( self, s_msg )
				#end if entry not None
				return
			#end try ... except

			self.__init_interface()
			self.__load_values_into_interface()
			self.__set_controls_by_run_state( self.__get_run_state() )
		except Exception as oex:
			o_traceback=sys.exc_info()[ 2 ]
			s_trace= \
				pgut.get_traceback_info_about_offending_code( o_traceback )

			s_msg="In PGGuiSimuPop instance, def load_config_file " \
					+ "an exception was raised: " + str( oex ) \
					+ "\nwith traceback info: " + s_trace

			PGGUIErrorMessage( self, s_msg )

			raise ( oex )

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
		if s_glob_expression is not None:
			self.__life_table_files = \
				pgut.get_list_files_and_dirs_from_glob( s_glob_expression )
		#end if we have a glob to get life table files	
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
			#note that we can pass None value in for o_model_resources,
			#and as long as the config file has evaluate-able values for
			#all of its options, we still get a valid PGInputSimuPop object:
			o_pgin=pgin.PGInputSimuPop( self.__config_file.get(), o_model_resources, o_param_names ) 
			
			o_pgin.makeInputConfig()

			'''
			We give the user an info box when the N0 value is not
			calculated (i.e. we have no Nb/Nc and Nb value in a
			section called "effective_size_info" in either the
			configuration file or the life table (if life table is
			available).
			'''

			b_using_effective_size_info = o_pgin.has_effective_size_info()

			if not b_using_effective_size_info:
				s_message="The loaded configuration info has no \"effective_size_info\" " \
											+ "with values for Nb/Nc and Nb.\n" \
											+ "As a result the N0 value is not calculated, " \
											+ "and can be set directly in the N0 text box."

				PGGUIInfoMessage( self, s_message )
			#end not using effective size info

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
				print(s_param + "\t" + str( getattr( self.__input, s_param ) ))
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

		2017_01_15, we now return the original default
		with the dots.
		'''
		s_mytime=pgut.get_date_time_string_dotted()	
		return "sim." + s_mytime
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

	def __validate_het_filter_string( self, s_filter_string ):

		DELIM=","
		NUM_FIELDS=3
		FIELD_TYPES=[ float, float, int ]
		IDX_MIN=0
		IDX_MAX=1
		IDX_TOTAL=2
		ls_problems=[]

		ls_values=s_filter_string.split( "," )

		lv_typed_values=[]

		if len( ls_values ) != NUM_FIELDS:
			ls_problems.append( "The filter should have " \
									+ "3, comma-separated fields." )
		else:
			for idx in range( NUM_FIELDS ):
				try:

					lv_typed_values.append( FIELD_TYPES[idx]( ls_values[ idx ] ) )

				except ( TypeError, ValueError ) as oet:
					ls_problems.append( "value for item " \
								+ str( idx + 1 ) \
								+ ", \"" + ls_values[ idx ] \
								+ "\", should be of type " \
								+ str( FIELD_TYPES[ idx ] ) \
								+ "." )
			#end for each value
			
			if len( ls_problems ) == 0:
				if lv_typed_values[IDX_MIN] > lv_typed_values[IDX_MAX]:
					ls_problems.append( \
							"Value for minimum, " + ls_values[ IDX_MIN ] \
								+ ", should be less than or equal to " \
								+ " the value for the maximum, " \
								+ str( ls_values[ IDX_MAX ] ) + "." )
				elif lv_typed_values[ IDX_TOTAL ] < 0:
					ls_problems.append( "The value for total pops to save, " \
											+ str( lv_typed_values[ IDX_TOTAL ]  \
											+ " should be greater than or equal to " \
											+ "zero." ) )
				#end if min > max, elif total lt zero
			#end if we have no problems so far.
		#end if we have the proper number of values
		
		v_return_value=None
		if len( ls_problems ) > 0:
			 v_return_value = ls_problems
		#end if no problems return None

		return v_return_value
	#end __validate_het_filter_string

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

			b_looks_good, s_consistency_msg=self.__input.valuesAreConsistent()


			if not b_looks_good:

				PGGUIInfoMessage( self, "Some input values are inconsisent.\n\n" + s_consistency_msg )

				return
			#end return after message if inconsistent input found

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

			'''
			input file to reaplace the orig config file
			as well as the attr/value dict originally passed to each 
			process.  We need to set this temp file name attribute
			in this instance before spawning a multiprocessing.process
			in do_operation, else it will not appear during call backs
			to __check_progress_operation_process, in which we delete
			the temp file when sim processes are finished

			2017_04_21.  Add the output directory path to the temp config
			filename.  This allows the file to be written even if the user's
			current directory is not writeable. We also no use a tempfile
			created file rather than the uuid naming.
			'''

			s_output_dir=os.path.dirname( self.__output.basename )


			if not( os.path.exists( s_output_dir ) ):
				s_msg="In PGGuiSimuPop instance, def runSimulation, " \
							+ "the program cannot write the temp config file " \
							+ "because the curren output directory name, " \
							+ self.__output.basename  \
							+ ", does not exist as a path."
				raise Exception( s_msg )
			#end if not a path
			
			s_temp_file_name=pgut.get_temp_file_name( s_parent_dir=s_output_dir )

			if pgut.is_windows_platform():
				s_temp_file_name = pgut.fix_windows_path( s_temp_file_name )
			#end if windows, fix path

			self.__temp_config_file_for_running_replicates=s_temp_file_name

			self.__input.writeInputParamsAsConfigFile( \
				self.__temp_config_file_for_running_replicates )

			'''
			We pass a ref to this object to the target (def in pgparallelopmanager, formerly
			in pgutilities, do_simulation_reps_in_subprocesses) for op_process. Then, from 
			this object instance can call "set()" on the event, after, 
			for example, an __on_click_run_or_cancel_simulation_button->__cancel_simulation()
			sequence, so that the event will to pass True and then the ref in
			op_process will return True when the op_process interrog 
			o_event.is_set()  and it can accordingly clean
			up its collection of subprocess.Popen processes 
			'''
			self.__sim_multi_process_event=multiprocessing.Event()

			'''
			2017_08_08.  We have added to the pgopsimupop.py code an optinal output mode argument and
			a mode-dependant pop filter, so that we need to now use the optional args added to the
			do_simulation_reps_in_subprocesses def -- including the gui messaging flag, in order
			to correctly pass a complete arg set:

			2017_09_04. We have eliminated the het filter string as an arg passed to the pgutilities
			def.  It now will be accessed directly from the input config file.
			
			2017_11_12. We now call the new mod pgparallelopmanager.py, which now has the defs that
			used to be in pgutilities, and which use pgopsimupop and similar modules.

			2018_03_08. We disable gui messaging, as it looks like Nb tolerance failures will be common
			enough that errors can potentially block entire runs, without the user manually clicking
			on the error messages (i.e. number of error dialogs raised is greather than the number of
			cores in use, so that no new replicates can be started).
			'''
			#b_do_use_gui_messaging=True
			b_do_use_gui_messaging=False
			i_output_mode=pgpar.pgsim.PGOpSimuPop.OUTPUT_GENEPOP_ONLY
			s_het_filter_string=None

			if self.__input.do_het_filter==True:
				s_het_filter_string=self.__input.het_filter
				ls_invalidity_msgs=self.__validate_het_filter_string( s_het_filter_string )
				if ls_invalidity_msgs is not None:
					s_invalidity_msgs="\n\n".join(ls_invalidity_msgs )
					PGGUIInfoMessage( self, "The heterozygosity filter " \
											+ "string should be of form \"min,max,total\" " \
											+ "but is not consistent.\n\n" \
											+ s_invalidity_msgs )
					return
				#end if bad filter string
			#end if we have a het filter
		
			#our sim run(s) should not block the main gui, so we
			#run it(them) in one or more python.subprocesses:
			self.__op_process=multiprocessing.Process( target=pgpar.do_simulation_reps_in_subprocesses, 
						 args=( self.__sim_multi_process_event, 
							self.__input.reps, 
							self.__total_processes_for_sims,
							self.__temp_config_file_for_running_replicates,
							self.__life_table_files,
							self.__param_names_file,
							self.__output.basename,
							b_do_use_gui_messaging,
							i_output_mode ) ) 

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

	def __remove_current_category_frames( self ):
		'''
		2017_01_16  This def was created to solve
		the problem of the "Configuration Info" labeled
		subframe in the interface showing its last position
		when a config file with a shortere name is loaded
		after a config file with a longer name was loaded.
		This suggested that the old frame was persisiting.

		These callsd to LabelFrame's destroy() def were originall
		preceeded by a call to grid_remove(), in imitation of the
		subframe removal code in def __load_genepopfile_sampling_params_interface
		in pgguineestimator.py.  I found, however, that calls to grid_remove
		for the subframe objectds in the self.__category_frames dict
		resulted in an error stateing "bad window path."  
		'''

		if self.__category_frames is not None:
			for s_key in self.__category_frames:
				if self.__category_frames[ s_key ] is not None:
					self.__category_frames[ s_key ].destroy()
				#end if frame not none
		#end if we have category frames
		return
	#end __remove_current_category_frames
	def cleanup( self ):
		self.__cancel_simulation()
		self.__remove_temporary_config_file()
	#end cleanup

	def __create_validity_checker( self, v_init_value, s_validity_expression ):
		'''
		2017_02_07. This def added as I incrementally bring the param handling in this interface 
		closer to that used in pgguisimupop.py.  This will allow the application of
		test expressions in the simupop.param.names resources file, to the params.
		
		2017_03_08. To accomodate the new pginputsimupop attribite nbadjustment, a list
		of strings that requrire a more complicated validity test than do the other params
		that require a simple boolean expression, we have revised class ValueValudator
		(in module pgutilityclasses) to use either a ref to a def, or the (original)
		string boolean expression, as the validator.
		'''

		o_checker=None
		try:

			if VERY_VERBOSE:
				print( "-------------" )
				print( "testing for attribute arg: " + s_validity_expression )
			#end if very verbose

			#We assume the expression arg is a string boolean expression:
			v_validity_expression=s_validity_expression

			#We reassign to a ref to a def is its an existing
			if hasattr( self, s_validity_expression ):

				if VERY_VERBOSE: 
					print( "---------------" )
					print( "setting valid express to attr, " + s_validity_expression )
				#end if very verbose

				v_validity_expression=getattr( self, s_validity_expression )

				if not callable( v_validity_expression ):
					s_msg="In PGGuiSimupop instance, " \
							+ "def __create_validity_checker, " \
							+ "the validity expression argument " \
							+ "evaluated to a non-callable attribute: " \
							+ str( v_validity_expression ) + "/"
					raise Exception( s_msg )
				#end if not callable
			#end if expression is an attribute of this object
					
			o_checker=ValueValidator( v_validity_expression, v_init_value )

			if not o_checker.isValid():
				s_msg="In PGGuiSimuPop instance, " \
							+ "def __create_validity_checker, " \
							+ "invalid initial value when setting up, " \
							+ "validator object.  Validation message: " \
							+ o_checker.reportInvalidityOnly() + "."
				PGGUIErrorMessage( self, s_msg )
				raise Exception( s_msg )
			#end if not valid init value, exception
		except Exception as oex:
			s_msg=str( oex )	
			PGGUIErrorMessage( self, s_msg )
			raise ( oex )
		#end try...except

		return o_checker
	#end __create_validity_checker

	def onChangeInMonogamyCheckbox( self ):
		'''
		For testing only, as of 2017_04_19.
		'''
		if VERY_VERY_VERBOSE:		
			print( "current type for isMonog: " + str( type ( self.__input.isMonog ) ) )
			print( "current value for isMonog: " + str( self.__input.isMonog ) )
		#end if VERY_VERY_VERBOSE	
		return
	#end onChangeInMonogamyCheckbox

	def __disable_or_enable_maleprob_according_to_cull_method(self):
		s_result=None

		if hasattr( self.__input, "cull_method" ):

			if "maleProb" in self.__param_key_value_frames:

				o_this_kv=self.__param_key_value_frames[ "maleProb" ]

				if self.__input.cull_method == CBOX_EQUAL_SEX_RATIO_TEXT:

					o_this_kv.setStateControls( "disabled" )

					s_result="disabled"

				elif self.__input.cull_method == CBOX_SURVIVAL_RATE_TEXT:
					'''
					If the control was initialized with "isenabled" as true,
					and if the force_disable is also true, then the current
					state of controls, if they are disabled, must be due to
					a former change to equal sex ratio.  Now we have a different
					cull setting, so we can, in that case, re-enable:

					
					2017_05_05. We have changed the keyvalue text box setStateControls def
					so that the is_enabled attribute is updated according to the state
					passed in the def.  This means that we can no longer test the 
					attribute to get it's initial value.  We now just make sure that
					force disable is False, and assume that we should enable the control
					under this cull method.
					'''
					if not o_this_kv.force_disable:

						o_this_kv.setStateControls( "enabled" )

						s_result="enabled"
					#end if we should enable

				else:
					'''
					If we have added or changed the cbox text choices, but have not
					updated this def, we will show the error, but enable the male prob
					of birth text box.
					'''
					s_msg = "In PGGuiSimuPop instance, " \
								+ "def __disable_or_enable_maleprob_according_to_cull_method " \
								+ "the selected cull method is not recognized.  The " \
								+ "current known methods are " + CBOX_SURVIVAL_RATE_TEXT \
								+ " and " + CBOX_EQUAL_SEX_RATIO_TEXT + ".  Hence the " \
								+ "program does not know whether to disable the " \
								+ "entry box for Probability of Male Birth."
					PGGUIErrorMessage( self, s_msg )
					o_this_kv.setStateControls( "enabled" )

					if o_this_kv.force_disable == False:
						o_this_kv.setStateControls( "enabled" )
						s_result="enabled"
					#end if not force diabled	
				#end if  
			#end if maleProb control frame exists
		#end if cull_method attribute exists
		return s_result
	#end __disable_or_enable_maleprob_according_to_cull_method

	def onUpdateMaleProb( self ):
		'''
		2017_05_05. This def was added because,
		when the conf file loaded defalts to the
		cull method "equal_sex_ratio," and it's 
		cbox is created before the input.maleProb
		entry box is created, then the latter
		can't be set to disabled, and equal to 0.5,
		its proper state when the cull method is 
		"equal_sex_ratio." (Note as of  2018_05_07,
		"equal_sex_ratio" now renamed in the GUI
		and conf files as "maintain_distribution").
		'''
		s_result=self.__disable_or_enable_maleprob_according_to_cull_method()	
		#we also need to recalculate the N0
		self.updateN0EntryBox()
	#end def onUpdateMaleProb

	def onLoadingMaleProb( self ):
		'''
		2017_05_05.  The initial value of
		this parameter depends on the value of the
		cull method parameter. 
		'''
		f_reltol=1e-99
		
		s_result=self.__disable_or_enable_maleprob_according_to_cull_method()
		
		if hasattr( self.__input, 'cull_method' ):
			if self.__input.cull_method==CBOX_EQUAL_SEX_RATIO_TEXT:
				f_curr_prob=self.__input.maleProb
				if abs( f_curr_prob - 0.5 ) > f_reltol:
					o_kv=self.__param_key_value_frames[ 'maleProb' ]
					o_kv.manuallyUpdateValue( 0.5 )
				#end if non-0.5 value
			#end if cull method set to equal_sex_ratio	
		#end if the cull_method attribute exists

		return
	#end onLoadingMaleProb

	def onLoadingHetFilter( self ):
		self.onChangeInHetFilterFlag()
	#end onLoadingHetFilter

	def onChangeInHetFilterFlag( self ):
		'''
		2017_08_08.  This def was added to be associated with the checkbox
		that gives True or False, whether to filter pops by mean expected
		heterozygosity.  We want to disable the het filter string entry 
		when the checkbox has updated our local copy of the flag to false.
		'''

		s_het_filter_attribute_name="het_filter"

		if s_het_filter_attribute_name not in self.__param_key_value_frames:
			s_msg="In PGGuiSimuPop instance, def onChangeInHetFilterFlag, " \
						+ "the program cannot find a key value frame associated " \
						+ "with the attribute name: " + s_het_filter_attribute_name + "."
			PGGUIErrorMessage( self, s_msg )
			raise Exception( s_msg )
		#end if no key val frame for the nb/ne ratio param

		o_keyvalueframe=self.__param_key_value_frames[ s_het_filter_attribute_name ]

		if self.__input.do_het_filter == False or self.__simulation_is_in_progress:
			o_keyvalueframe.setStateControls( "disabled" )
			o_keyvalueframe.setLabelState( "disabled" )
			o_keyvalueframe.setEntryFontColor( "gray" )
		else:
			o_keyvalueframe.setStateControls( "enabled" )
			o_keyvalueframe.setLabelState( "enabled" )
			o_keyvalueframe.setEntryFontColor( "black" )
		#end if we are not doing a bias adjustment, else we are 

		return
	#end def onChangeInHetFilterFlag

	def __on_change_in_use_loci_file_flag( self ):
		'''
		2018_05_26. Now allowing input of a file giveing loci info.
		'''
		s_param_name="loci_file_name"

		if s_param_name not in self.__param_key_value_frames:
			s_msg="In PGGuiSimuPop instance, def __on_change_in_use_loci_file_flag, " \
						+ "the program cannot find a key value frame associated " \
						+ "with the param name: " + s_param_name + "."
			PGGUIErrorMessage( self, s_msg )
			raise Exception( s_msg )
		#end if no key val frame for the nb/ne ratio param

		o_loci_file_control=self.__param_key_value_frames[ "loci_file_name" ]

		if self.__input.use_loci_file == False:
			self.__disable_loci_file_controls( o_loci_file_control )
			self.__set_state_of_loci_related_totals_controls( "enabled" )
			'''
			2018_07_27.  We add controls to manage new option of including
			allele frequencies in a user supplied loci info file.
			'''
			self.__set_state_of_allele_frequency_init_controls( "enabled" )
			#end if we have user-supplied allele freqs
		else:
			self.__enable_loci_file_controls( o_loci_file_control )

			self.__set_state_of_loci_related_totals_controls( "disabled" )

			if self.__user_loci_file_has_allele_frequencies():

				self.__set_state_of_allele_frequency_init_controls( "disabled" )

			#end if we have user-supplied allele freqs
		#end if we are not using the chrom loci file, else we are 

		return
	#end __on_change_in_use_loci_file_flag

	def __set_state_of_loci_related_totals_controls( self, s_state ):

		lo_loci_related_total_controls=[]

		for s_param in LOCI_RELATED_TOTALS_CONTROLS:
			if s_param in self.__param_key_value_frames:
				lo_loci_related_total_controls.append( \
								self.__param_key_value_frames[ s_param ] )
			#end if we have a control for the param
		#end for each param

		s_entry_font_color="black" if s_state=="enabled" else "gray"

		for o_control in lo_loci_related_total_controls:
				o_control.setStateControls( s_state )
				o_control.setEntryFontColor( s_entry_font_color )
				o_control.setLabelState( s_state )
		#end for each loci total control	

		return
	#end __set_state_of_loci_related_totals_controls

	def __set_state_of_allele_frequency_init_controls( self, s_state ):

		lo_allele_freq_init_related_controls=[]

		for s_param in ALLELE_FREQ_INIT_RELATED_CONTROLS:
			if s_param in self.__param_key_value_frames:
				lo_allele_freq_init_related_controls.append( \
								self.__param_key_value_frames[ s_param ] )
			#end if we have a control for the param
		#end for each param

		s_entry_font_color="black" if s_state=="enabled" else "gray"

		for o_control in lo_allele_freq_init_related_controls:
				o_control.setStateControls( s_state )
				o_control.setEntryFontColor( s_entry_font_color )
				o_control.setLabelState( s_state )
		#end for each loci total control	

		return
	#end __set_state_of_loci_related_totals_controls


	def __on_button_press_load_loci_file( self ):
		'''
		2018_05_26. Now allowing input of a file giveing loci info.
		This code is from pgguineestimator, 
		def __on_button_press_load_chrom_loci_file
		For new parameter that loads path/name
		of a loci info file, used by LDNe2 to
		eval only loci pairs whose members are associated
		with different chromosomes.
		'''
		try:
			s_current_value=self.__input.loci_file_name

			s_loci_file_name=tkfd.askopenfilename(  \
					title='Load a loci info file' )

			if pgut.dialog_returns_nothing( s_loci_file_name ):
				return
			#end if no file selected, return
			
			self.__param_key_value_frames[ "loci_file_name" \
								].manuallyUpdateValue( s_loci_file_name ) 
			
			'''
			This was added 2018_07_28 to add a check for allele frequencies
			in a loaded loci file.
			'''
			self.__on_loading_user_loci_file()

		except Exception as oex:
			o_traceback=sys.exc_info()[ 2 ]
			s_trace= \
				pgut.get_traceback_info_about_offending_code( o_traceback )

			s_msg="In PGGuiSimuPop instance, " \
					+ "def __on_button_press_load_loci_file " \
					+ "an exception was raised: " + str( oex ) \
					+ "\nwith traceback info: " + s_trace

			PGGUIErrorMessage( self, s_msg )

			raise ( oex )

		#end try...except
		return
	#end __on_button_press_load_loci_file

	def __setup_entry_with_button( self,
									s_param,
									s_param_longname,
									v_value_for_entry_control,
									o_param_type,
									v_default_item_value,
									o_subframe,
									s_attr_name,
									o_attribute_object,
									i_width_this_entry,
									i_this_label_width,
									s_state_to_use,
									s_this_entry_justify,
									s_param_tooltip,
									o_validity_checker,
									b_force_disable,
									b_use_list_editor,
									o_param_assoc_def ):

		'''
		2018_05_26. This code was copied from pgguineestimator.py, 
		for the parameter that gives a name of a loci info.  For this
		control, we disable the entry, and instead of assigning the
		pgparamset member s_param_assoc_def to the def_entry_change_command
		param of the keyvalframe, we assign to def_button_command 
		parameter.  We also apply the param label to the button:
		'''

		#For the entrywithbutton config, we use this
		#as the button command rather than the entry
		#change def::
		def_for_button_press=o_param_assoc_def \
							if o_param_assoc_def is not None \
											else self.__test_values

#		if o_param_assoc_def != "None":
#			def_on_entry_change=getattr( self,  s_param_assoc_def )
#		#end if we have a named def in the param set

		'''
		This should be automated, but so far this is the only
		entry with label implemented via the keyvalframe class.
		'''
		s_label_name=None
		if  s_param=="loci_file_name":
			i_width_this_entry=70
			s_button_text="Load loci file"
			#we let the button's text serve as the label
			s_label_name=""
			i_this_label_width=0
		#end if this is the chrom loci file entry control
		
		o_this_keyval=KeyValFrame( s_name=s_param_longname,
			v_value=v_value_for_entry_control,
			o_type=o_param_type,
			v_default_value=v_default_item_value,
			o_master=o_subframe,
			def_entry_change_command=None,
			o_associated_attribute_object=o_attribute_object,
			s_associated_attribute=s_attr_name,
			i_entrywidth=i_width_this_entry,
			i_labelwidth=i_this_label_width,
			b_is_enabled=( s_state_to_use == "enabled" ),
			s_entry_justify=s_this_entry_justify,
			s_label_justify='left',
			s_tooltip=s_param_tooltip,
			o_validity_tester=o_validity_checker,
			b_force_disable=b_force_disable,
			b_use_list_editor=True,
			s_button_text = s_param_longname,
			def_button_command = def_for_button_press,
			s_label_name=s_label_name )

		'''
		2018_04_27. As above, this should be automated by
		adding to fields in the param.names file, but for now
		we treat it as a special case.  On init we keep all of its
		component states, except the label, disabled, and let the 
		user enable with the new checkbox that sets the flag 
		__usechromfile:				
		
		'''

		if s_param=="loci_file_name":

			b_enable_if_no_flag_attribute = \
						not( b_force_disable ) \
						and s_state_to_use == "enabled" 
		
			b_have_flag_attribute=hasattr( self.__input, "use_loci_file" )

			if b_have_flag_attribute:
				if self.__input.use_loci_file and not( b_force_disable ):
					self.__enable_loci_file_controls( o_this_keyval )
					self.__set_state_of_loci_related_totals_controls( "disabled" )
					'''
					2018_07_28. We now, if the loci file exists, also check to see
					if it includes allele freqs, and, if so, we disable the het init
					frequency controls for allele freq initialization:
					'''
					if self.__user_loci_file_has_allele_frequencies():
						self.__set_state_of_allele_frequency_init_controls( "disabled" )
					#end if we have user-suppied allele frequencies			 
				else:
					self.__disable_loci_file_controls( o_this_keyval )
					if not( b_force_disable ):
						self.__set_state_of_loci_related_totals_controls( "enabled" )
						self.__set_state_of_allele_frequency_init_controls( "enabled" )
				#end if flag true, else false

			elif b_enable_if_no_flag_attribute:
				self.__enable_loci_file_controls( o_this_keyval )
				self.__set_state_of_loci_related_totals_controls( "disabled" )
				if self.__user_loci_file_has_allele_frequencies():
					self.__set_state_of_allele_frequency_init_controls( "disabled" )
				#end if user loci file has allele freqs
			else:
				self.__disable_loci_file_controls( o_this_keyval )
				if not(b_force_disable):
					self.__set_state_of_loci_related_totals_controls( "enabled" )
					self.__set_state_of_allele_frequency_init_controls( "enabled" )
			#end if b_have_flag_attribute

		return o_this_keyval
	#def __setup_entry_with_button	

	def __enable_loci_file_controls( self, o_keyval ):
		o_keyval.setLabelState("enabled" )
		o_keyval.setEntryState( "disabled" )
		o_keyval.setButtonState( "enabled" )
		o_keyval.setEntryFontColor( "black" )
		return
	#end __enable_loci_file_controls

	def __disable_loci_file_controls( self, o_keyval ):
		o_keyval.setButtonState( "disabled" )
		o_keyval.setEntryFontColor( "gray" )
		o_keyval.setButtonState( "disabled" )
		return
	#end __disable_loci_file_controls

	def __initialize_state_of_loci_related_totals_controls( self ):
		'''
		2018_06_02. When the flag for the use_loci_file parameter is True, 
		we want to disable the loci related total controls.
		'''
		if hasattr( self.__input, "use_loci_file" ):
			if self.__input.use_loci_file == True:
				self.__set_state_of_loci_related_totals_controls( "disabled" )
				'''
				2018_07_27. When the user loci file also contains allele
				frequencies, we disable the het-init controls.
				'''
				if self.__user_loci_file_has_allele_frequencies():
					self.__set_state_of_allele_frequency_init_controls( "disabled" )
				#end if the user is supplying allele freqs
			else:
				self.__set_state_of_loci_related_totals_controls( "enabled" )
				self.__set_state_of_allele_frequency_init_controls( "enabled" )
			#end if we are using a loci file
		#end if we have the flag telling whether we use a loci file
		return
	#end __initialize_state_of_loci_related_totals_controls

	'''
	2018_07_27. We're adding an option to supply allele frequencies as a 
	4th field in a loci,chrom,postiion[,frequency] file. This gui class
	needs to know if they are supplied in order to properly disable
	allele-frequency controls that will be unused due to the freqs
	being already supplied
	'''
	def __user_loci_file_has_allele_frequencies( self ):

		if self.__input.loci_file_name == NO_LOCI_FILE:
			return False
		#end if no file, then no frequencies

		b_user_does_supply_allele_freqs= \
				pgsli.PGSimupopLociInfoFileManager.\
					quickCheckShowsFrequencyData( self.__input.loci_file_name )

		return b_user_does_supply_allele_freqs
	#end def __user_loci_file_has_allele_frequencies

	'''
	Now that the user_loci_file may or may not include allele frequencies, we need to check
	each time a loci file is loaded, and, if allele frequencies are found, we disable the 
	controls that take het values for automatic inititalization of allele frequencies:
	'''

	def __on_loading_user_loci_file( self ):

		if self.__user_loci_file_has_allele_frequencies():
			self.__set_state_of_allele_frequency_init_controls( "disabled" )

		else:
			self.__set_state_of_allele_frequency_init_controls( "enabled" )
		#end if the user loci file has allele frequencies
		
		return
	#end __on_loading_user_loci_file

#end class PGGuiSimuPop
