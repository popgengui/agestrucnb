'''
Description
This module/class wraps the controls and plotting
window used to manipulate and see boxplots
based on the output of the *tsv file produced
by pgdriveneestimations, giving LDNe Ne/Nb 
estimations and related quantities.
'''
from __future__ import print_function
from future import standard_library

__filename__ = "pgboxplotinterface.py"
__date__ = "20170929"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

'''
We need the tkinter.Scale widget,
not the ttk.Scale, so we need the
tkinter space name, otherwise
the ttk boject will be instantiated:
'''
import tkinter as tki
from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog as tkfd
'''
2017_10_19.  So I can access
the TclError class in def
__destroy_widgets
'''
import tkinter

import sys
import os
import re

import agestrucne.pgutilities as pgut
from agestrucne.pgguiutilities import PGGUIInfoMessage

from agestrucne.pgplottingframe import PGPlottingFrameBoxplotFromFileManager
from agestrucne.pgframecontainerscrolled import FrameContainerScrolled
from agestrucne.pgneestimationtablefilemanager import NeEstimationTableFileManager
from agestrucne.pgneestimationtableselectioncombo import PGNeEstTableColumnSelectionCombo
from agestrucne.pgneestimationtableselectioncombo import PGNeEstTableValueSelectionCombo
from agestrucne.pgkeyvalueframe import KeyValFrame
from agestrucne.pgscalewithentry import PGScaleWithEntry

class PGNeEstimationBoxplotInterface( object ):

	'''
	These names allow a more self-explanantory set of field names
	instead of the column headers in the tsv file.
	'''
	ALIASES_BY_COLNAMES=\
			NeEstimationTableFileManager.COLUMN_NAME_ALIASES_BY_COLUMN_NAME
	COLNAMES_BY_ALIASES=\
			NeEstimationTableFileManager.COLUMN_NAMES_BY_ALIAS

	GROUP_BY_COLUMNS=[ 'original_file' , 
						'pop', 
						'indiv_count',
						'sample_value', 
						'replicate_number', 
						'loci_sample_value',
						'loci_replicate_number' ]

	Y_AXIS_VALUE_COLUMNS=[ 'ne_est_adj', '95ci_low', '95ci_high', 'est_ne'  ]

	VALUE_FILTERABLE_COLUMNS=[ 'original_file','replicate_number',
								'loci_replicate_number','sample_value', 
														'loci_sample_value' ]

	VALUE_FILTERABLE_COLUMNS_SORT_VALUES_NUMERICALLY = [ False, True, True, False, False ]

	ROW_NUM_SUBFRAME_TSV_FILE_LOADER=0
	ROW_NUM_SUBFRAME_GROUPBY=1
	ROW_NUM_SUBFRAME_FILTER=2
	ROW_NUM_SUBFRAME_Y_VALUE=3
	ROW_NUM_SUBFRAME_SAVE_PLOT=3
	ROW_NUM_PLOT=4 

	ROW_NUM_GROUPBY_LABELS=0
	ROW_NUM_GROUPBY_COMBOS=1
	ROW_NUM_FILTER_LABELS=0
	ROW_NUM_FILTER_COMBOS=1
	ROW_NUM_YVAL_LABEL=0
	ROW_NUM_YVAL_LOWER_SCALE_LABEL=0
	ROW_NUM_YVAL_UPPER_SCALE_LABEL=0
	ROW_NUM_YVAL_COMBO=1
	ROW_NUM_YVAL_UPPER_SCALE=1
	ROW_NUM_YVAL_LOWER_SCALE=1
	ROW_NUM_SAVE_PLOT_BUTTON=1

	NUM_VALS_IN_SCALE=3000

	COLNUM_SUBFRAME_TSV_LOADER=0
	COLNUM_SUBFRAME_Y_VALUE=0
	COLNUM_SUBFRAME_FILTER=0
	COLNUM_SUBFRAME_GROUPBY=0
	COLNUM_SUBFRAME_SAVE_PLOT=1

	COLNUM_YVAL_LOWER_SCALE_LABEL=1
	COLNUM_YVAL_UPPER_SCALE_LABEL=2
	COLNUM_YVAL_LOWER_SCALE=1
	COLNUM_YVAL_UPPER_SCALE=2
	COLNUM_SAVE_PLOT_BUTTON=2

	COLSPAN_SUBFRAME_TSV_LOADER=3
	COLSPAN_SUBFRAME_GROUPY=4
	COLSPAN_SUBFRAME_FILTER=10
	COLSPAN_SUBFRAME_Y_VALUE=1
	COLSPAN_SUBFRAME_SAVE_PLOT=1
	COLSPAN_PLOT=20

	SUBFRAME_STYLE="groove"
	SUBFRAME_PADDING=10
	LABEL_PADDING=8

	PLOT_FIGURE_DOTS_PER_INCH=100

	DELIM_GROUPBY_FIELDS = \
			NeEstimationTableFileManager.DELIM_GROUPED_FIELD_NAMES

	def __init__( self, 
			o_master_frame = None,
			s_tsv_file_name = None, 
			i_plot_width=None,
			i_plot_height=None ):

		self.__master_frame=o_master_frame
		self.__tsv_file_name=s_tsv_file_name
		self.__plot_width=i_plot_width
		self.__plot_height=i_plot_height
		self.__tsv_file_manager=None
		self.__plotframe=None

		self.__labels=None
		self.__comboboxes=None
		self.__buttons=None
		self.__subframes=None
		self.__scales=None

		if self.__plot_width is None \
					or self.__plot_height is None:
			self.__get_auto_plot_size()
		#end if we are missing one or more plot
		#size dimensions

		self.__setup_tsv_file_loader()

		if self.__tsv_file_name is not None \
				and self.__tsv_file_name != "None":
			if self.__looks_like_a_tsv_file_with_data_lines( self.__tsv_file_name ):		
				self.__make_tsv_file_manager()
				self.__setup_plotting_interface()
			else:
				s_msg="In PGNeEstimationBoxplotInterface instance, " \
						+ "def __init__, the tsv file passed to this object " \
						+ ", " + self.__tsv_file_name + ", "  \
						+ "does not appear to be a tsv file with data line in it. " \
						+ "No tsv file will be loaded."
				PGGUIInfoMessage( self.__master_frame, s_msg )
			#end if the file looks right
		#end if the file name is not None

		return
	#end __init__

	def __setup_tsv_file_loader( self ):

		ENTRY_WIDTH=70
		LABEL_WIDTH_NONWIN=10
		LABEL_WIDTH_WINDOWS=12

		i_label_width=LABEL_WIDTH_NONWIN

		if pgut.is_windows_platform():
			i_label_width=LABEL_WIDTH_WINDOWS
		#end if using windows, need wider label

		o_myc=PGNeEstimationBoxplotInterface

		self.__tsv_file_loader_subframe=LabelFrame( self.__master_frame,
														padding=o_myc.SUBFRAME_PADDING,
														relief=o_myc.SUBFRAME_STYLE,
														text="*tsv file" )

		self.__tsv_loader_keyval=KeyValFrame( s_name="Load tsv file", 
							v_value=self.__tsv_file_name,
							o_type=str,
							v_default_value="",
							o_master=self.__tsv_file_loader_subframe,
							i_entrywidth=ENTRY_WIDTH,
							i_labelwidth=i_label_width,
							b_is_enabled=False,
							s_entry_justify='left',
							s_label_justify='left',
							s_button_text="Select",
							def_button_command=self.__load_tsv_file,
							b_force_disable=False,
							s_tooltip = "Load a tsv file, output from an Nb/Ne Estimation run" )

		#The entry box should be disabled, but
		#we want the lable non-grayed-out:
		self.__tsv_loader_keyval.setLabelState( "enabled" )
		self.__tsv_loader_keyval.grid( row=0, sticky=( NW ) )
		
		self.__tsv_file_loader_subframe.grid( row=o_myc.ROW_NUM_SUBFRAME_TSV_FILE_LOADER, 
										column=o_myc.COLNUM_SUBFRAME_TSV_LOADER, 
										columnspan=o_myc.COLSPAN_SUBFRAME_TSV_LOADER,
										sticky=( N,W ) )

		return
	#end __setup_tsv_file_loader
	
	def __load_tsv_file( self ):

		#dialog returns sequence:
		s_tsv_file=tkfd.askopenfilename(  \
				title='Load an Ne Estmation *.tsv file' )

		if pgut.dialog_returns_nothing( s_tsv_file ):
			return
		#end if no file selected, return with no change
		#in tsv file loaded

		if self.__looks_like_a_tsv_file_with_data_lines( s_tsv_file ):

			self.__tsv_file_name = s_tsv_file
			'''
			We need to destroy the plot frame before
			re-setting up the combo boxes:
			'''
			if self.__plotframe is not None:
				if hasattr( self.__plotframe, "destroy" ):
					self.__plotframe.destroy()

					self.__plotframe=None
				else:
					s_msg= "In PGNeEstimationBoxplotInterface instance, " \
							+ "def __load_tsv_file, plotframe obj is not none " \
							+ "but has no destroy attribute" 
					raise Exception( s_msg )
				#end if plot frame has destroy method, else has
			self.__destroy_all_widgets()
			self.__setup_tsv_file_loader()
			self.__make_tsv_file_manager()
			self.__setup_plotting_interface()	

		else:
			s_message = "The program cannot load the selected file:" \
								+ "\n" + s_tsv_file + "\n" \
								+ "It does not appear to be a *.tsv " \
								+ "file with data lines." 
			PGGUIInfoMessage( self.__master_frame, s_message )
			return
		#end if the file looks invalid
								
		return
	#end __load_tsv_file	

	def __looks_like_tsv_file( self, s_tsv_file_name ):
		'''
		This def is a heuristic, very approximate,
		for deciding whether is it likely that the file is 
		a valid *tsv file as generated by our NeEstimation
		functions. We use the header and test forthe column
		names that this class uses to group and filter
		the data.
		'''

		b_verdict=True

		o_myc=PGNeEstimationBoxplotInterface
		o_tsvc=NeEstimationTableFileManager

		ls_column_names_to_test=o_myc.GROUP_BY_COLUMNS + o_myc.Y_AXIS_VALUE_COLUMNS

		o_tsv=open( s_tsv_file_name, 'r' )
		s_header=o_tsv.readline()
		o_tsv.close()

		ls_header_fields = s_header.strip().split( o_tsvc.DELIM_TABLE )

		for s_name in ls_column_names_to_test:

			if s_name not in ls_header_fields:
				b_verdict=False
				break
			#end if column name missing
		#end for each column name to test

		return b_verdict
	#end __looks_like_tsv_file

	def __looks_like_a_tsv_file_with_data_lines( self, s_file_name ):
		'''
		Another simple heuristic added to the header check
		in __looks_like_tsv_file, to avoid loading
		empty *tsv files  i.e. header is correct
		but no data lines follow.
		'''
		b_return_value=False

		if self.__looks_like_tsv_file( s_file_name ) == True:
			o_tsvc=NeEstimationTableFileManager

			o_file=open( s_file_name, 'r' )
			#read the header:
			s_header=o_file.readline()
			ls_vals=s_header.split( o_tsvc.DELIM_TABLE )
			i_num_fields=len( ls_vals )
			ls_second_line=o_file.readline()

			if ls_second_line is not None:
				ls_second_line_values=ls_second_line.split( o_tsvc.DELIM_TABLE )
				i_num_values=len( ls_second_line_values )
				if i_num_values == i_num_fields:
					b_return_value=True
				#end if value count equals field count
			#end if we have a second line
		#end if the file looks like a tsv file

		return b_return_value
	#end __looks_like_a_tsv_file_with_data_lines

	def __get_auto_plot_size( self ):
		o_myc=PGNeEstimationBoxplotInterface
	
		WINDOW_MARGIN=0.0

		WIDTH_PROPORTION=0.90
		HEIGHT_PROPORTION=0.90

		i_width=self.__master_frame.winfo_screenwidth()
		i_height=self.__master_frame.winfo_screenheight()

		if self.__plot_width is None:
			f_width_pixels=( i_width * WIDTH_PROPORTION ) * ( 1 - WINDOW_MARGIN ) 
			self.__plot_width=int( f_width_pixels / o_myc.PLOT_FIGURE_DOTS_PER_INCH )
		#end if no plot width provided

		if self.__plot_height is None:
			f_height_pixels=( i_height * HEIGHT_PROPORTION ) * ( 1 - WINDOW_MARGIN )
			self.__plot_height=int( f_height_pixels / o_myc.PLOT_FIGURE_DOTS_PER_INCH )
		#end if no plot height provided

		return
	#end __get_auto_plot_size

	def __setup_plotting_interface( self ):

		self.__make_subframes()
		self.__make_labels()
		self.__make_combos()
		self.__make_scales()
		self.__make_buttons()
		self.__make_plot()
		self.__set_master_frame_grid_weights()

		return
	#end __setup_plotting_interface

	def __destroy_all_widgets( self ):

		for do_widget_dict in [ self.__subframes, 
								self.__labels,
								self.__comboboxes,
								self.__scales,
								self.__buttons ]:

			if do_widget_dict is not None:
				if len( do_widget_dict ) > 0:
					self.__destroy_widgets( do_widget_dict )
				#end if at least one item dict
			#end if dict exists
		#end for each widget dict
	#end __destroy_all_widgets

	def __set_master_frame_grid_weights( self ):
		'''
		2017_10_09.  Not yet in use.
		'''
		return
	#end __set_master_frame_grid_weights

	def __make_tsv_file_manager( self ):

		self.__tsv_file_manager=\
				NeEstimationTableFileManager( self.__tsv_file_name )

		return
	#end __make_tsv_file_manager 

	def __make_subframes( self ):
		
		if self.__subframes is not None:
			self.__destroy_widgets( self.__subframes )
		#end if subframes exist

		self.__subframes={}

		o_myc=PGNeEstimationBoxplotInterface
		FRAME_STYLE=o_myc.SUBFRAME_STYLE
		GROUPBY_FRAME_LABEL="Group Data"
		GROUPBY_FILTER_FRAME_LABEL="Grouped Data Filters"
		Y_VALUE_FRAME_LABEL="Y-axis Data"
		SAVE_PLOT_FRAME_LABEL="Save Plot"

		FRAME_PADDING=PGNeEstimationBoxplotInterface.SUBFRAME_PADDING

		self.__subframes[ 'groupby' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=GROUPBY_FRAME_LABEL )

		self.__subframes[ 'groupby_filter' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=GROUPBY_FILTER_FRAME_LABEL )

		self.__subframes[ 'y_value' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=Y_VALUE_FRAME_LABEL )

		self.__subframes[ 'save_plot' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=SAVE_PLOT_FRAME_LABEL )

		self.__subframes[ 'groupby' ].grid( row=o_myc.ROW_NUM_SUBFRAME_GROUPBY, 
													column=o_myc.COLNUM_SUBFRAME_GROUPBY, 
													columnspan=o_myc.COLSPAN_SUBFRAME_GROUPY, 
													sticky=(N,W) )

		self.__subframes[ 'groupby_filter' ].grid( row=o_myc.ROW_NUM_SUBFRAME_FILTER, 
														column=o_myc.COLNUM_SUBFRAME_FILTER, 
														columnspan=o_myc.COLSPAN_SUBFRAME_FILTER, 
														sticky=(N,W) )

		self.__subframes[ 'y_value' ].grid( row=o_myc.ROW_NUM_SUBFRAME_Y_VALUE, 
													column=o_myc.COLNUM_SUBFRAME_Y_VALUE, 
													columnspan=o_myc.COLSPAN_SUBFRAME_Y_VALUE, 
													sticky=(N,W) )

		self.__subframes[ 'save_plot' ].grid( row=o_myc.ROW_NUM_SUBFRAME_SAVE_PLOT, 
													column=o_myc.COLNUM_SUBFRAME_SAVE_PLOT, 
													columnspan=o_myc.COLSPAN_SUBFRAME_SAVE_PLOT, 
													sticky=(N,W) )
		return
	#end __make_subframes

	def __make_labels( self ):

		self.__labels={}

		o_myc=PGNeEstimationBoxplotInterface

		self.__labels[ 'group1' ] = Label( self.__subframes[ 'groupby' ], text="Group-by", padding=o_myc.LABEL_PADDING )
		self.__labels[ 'group2' ] = Label( self.__subframes[ 'groupby' ], text="Group-by", padding=o_myc.LABEL_PADDING )
		self.__labels[ 'group3' ] = Label( self.__subframes[ 'groupby' ], text="Group-by", padding=o_myc.LABEL_PADDING )
		self.__labels[ 'group4' ] = Label( self.__subframes[ 'groupby' ], text="Group-by", padding=o_myc.LABEL_PADDING )

		self.__labels[ 'group1' ].grid( row = o_myc.ROW_NUM_GROUPBY_LABELS, column = 0, sticky=( N,W ) )
		self.__labels[ 'group2' ].grid( row = o_myc.ROW_NUM_GROUPBY_LABELS, column = 1, sticky=( N,W ) )
		self.__labels[ 'group3' ].grid( row = o_myc.ROW_NUM_GROUPBY_LABELS, column = 2, sticky=( N,W ) )
		self.__labels[ 'group4' ].grid( row = o_myc.ROW_NUM_GROUPBY_LABELS, column = 3, sticky=( N,W ) )

		self.__value_filterable_combo_labels={}
		i_colnum_val_filt_labels=0
		for s_value_filterable_column in PGNeEstimationBoxplotInterface.VALUE_FILTERABLE_COLUMNS:
			ALIASES=PGNeEstimationBoxplotInterface.ALIASES_BY_COLNAMES

			s_label_key="filterable_" + s_value_filterable_column

			self.__labels[ s_label_key ] = \
							Label( self.__subframes[ 'groupby_filter' ], 
													text=ALIASES[ s_value_filterable_column ], 
													padding=o_myc.LABEL_PADDING )

			self.__labels[ s_label_key ].grid (  row = o_myc.ROW_NUM_FILTER_LABELS, 
													column=i_colnum_val_filt_labels )
			i_colnum_val_filt_labels += 1
		#end for each value filterable column

		self.__labels[ 'select_y_variable' ] = Label( self.__subframes[ 'y_value' ], 
															text= "Y axis value" , 
#															padding=o_myc.LABEL_PADDING)
#	
#		self.__labels[ 'y_lower_scale' ]=Label( self.__subframes[ 'y_value' ], 
#												text="Lower limit Y axis values", 
#														padding=o_myc.LABEL_PADDING )
#		
#		self.__labels[ 'y_upper_scale' ]=Label( self.__subframes[ 'y_value' ], 
#												text="Upper limit Y axis values", 
														padding=o_myc.LABEL_PADDING )
	

		self.__labels[ 'select_y_variable' ].grid( row = o_myc.ROW_NUM_YVAL_LABEL, 
																column=0, sticky=( N,W ) )

#		self.__labels[ 'y_lower_scale' ].grid( row=o_myc.ROW_NUM_YVAL_LOWER_SCALE_LABEL, 
#												column=o_myc.COLNUM_YVAL_LOWER_SCALE_LABEL, 
#																			sticky=( N,W ) )
#
#		self.__labels[ 'y_upper_scale' ].grid( row=o_myc.ROW_NUM_YVAL_UPPER_SCALE_LABEL, 
#												column=o_myc.COLNUM_YVAL_UPPER_SCALE_LABEL, 
#																				sticky=( N,W ) )

		return
	#end __make labels

	def __make_combos( self ):

		self.__comboboxes={}

		o_myc=PGNeEstimationBoxplotInterface

		ls_group_cols_to_include=o_myc.GROUP_BY_COLUMNS
		
		self.__comboboxes[ 'group1' ] = PGNeEstTableColumnSelectionCombo( \
													o_master=self.__subframes[ 'groupby' ], 
													o_tsv_file_manager=self.__tsv_file_manager, 
													def_to_call_on_selection_change=self.__on_group_by_selection_change,
													ls_column_names_to_show_excluding_others=ls_group_cols_to_include )

		self.__comboboxes[ 'group2' ] = PGNeEstTableColumnSelectionCombo( \
													o_master=self.__subframes[ 'groupby' ], 
													o_tsv_file_manager=self.__tsv_file_manager, 
													def_to_call_on_selection_change=self.__on_group_by_selection_change,
													ls_column_names_to_show_excluding_others=ls_group_cols_to_include )

		self.__comboboxes[ 'group3' ] = PGNeEstTableColumnSelectionCombo( \
													o_master=self.__subframes[ 'groupby' ], 
													o_tsv_file_manager=self.__tsv_file_manager, 
													def_to_call_on_selection_change=self.__on_group_by_selection_change,
													ls_column_names_to_show_excluding_others=ls_group_cols_to_include )

		self.__comboboxes[ 'group4' ] = PGNeEstTableColumnSelectionCombo( \
													o_master=self.__subframes[ 'groupby' ], 
													o_tsv_file_manager=self.__tsv_file_manager, 
													def_to_call_on_selection_change=self.__on_group_by_selection_change,
													ls_column_names_to_show_excluding_others=ls_group_cols_to_include )
		
		self.__comboboxes[ 'group1' ].grid( row=1, column=0, sticky=( N,W ) )
		self.__comboboxes[ 'group2' ].grid( row=1, column=1, sticky=( N,W ) )
		self.__comboboxes[ 'group3' ].grid( row=1, column=2, sticky=( N,W ) )
		self.__comboboxes[ 'group4' ].grid( row=1, column=3, sticky=( N,W ) )

		i_column_count=0

		for s_value_filterable_column in o_myc.VALUE_FILTERABLE_COLUMNS:

			b_sort_this_col_numerically = \
					o_myc.VALUE_FILTERABLE_COLUMNS_SORT_VALUES_NUMERICALLY[ i_column_count ]
			
			s_combo_key="filterable_" + s_value_filterable_column
			
			self.__comboboxes[ s_combo_key ] = \
								PGNeEstTableValueSelectionCombo( self.__subframes[ 'groupby_filter' ],
															o_tsv_file_manager=self.__tsv_file_manager, 
															s_tsv_col_name=s_value_filterable_column, 
															def_to_call_on_selection_change=self.__on_filter_value_combo_change,
															b_sort_numerically=b_sort_this_col_numerically )

			self.__comboboxes[ s_combo_key ].grid ( \
													row = o_myc.ROW_NUM_FILTER_COMBOS, 
													column=i_column_count )
			i_column_count += 1
		#end for each value filterable column

		ls_y_variable_column=PGNeEstimationBoxplotInterface.Y_AXIS_VALUE_COLUMNS

		self.__comboboxes[ 'select_y_variable' ]=PGNeEstTableColumnSelectionCombo( \
													o_master=self.__subframes[ 'y_value' ], 
													o_tsv_file_manager=self.__tsv_file_manager, 
													def_to_call_on_selection_change=self.__on_y_variable_selection_change,
													ls_column_names_to_show_excluding_others=ls_y_variable_column,
													b_add_none_selection=False )

		self.__comboboxes[ 'select_y_variable' ].grid( row=o_myc.ROW_NUM_YVAL_COMBO, 
																column=0, sticky=( N,W ) )

		return
	#end __make_combos

	def __get_group_by_column_names( self ):

		ls_group_by_column_names=[]

		for s_value in [ self.__comboboxes[ 'group1' ].current_value,
						self.__comboboxes[ 'group2' ].current_value,
						self.__comboboxes[ 'group3' ].current_value,
						self.__comboboxes[ 'group4' ].current_value ]:

			if s_value != "None":
				ls_group_by_column_names.append( s_value )
			#end if group by combo box selected value not "None"
		#end for each value

		if len( ls_group_by_column_names ) > 0:
			ls_group_by_column_names=list( set( ls_group_by_column_names ) )
		else:
			'''
			With this value the plotting frame
			will plot one box showing the dist
			for all of the data.
			'''
			ls_group_by_column_names=None
		#end if no column selected use default
		
		return ls_group_by_column_names
	#end __get_group_by_column_names

	def __get_x_label( self, ls_group_by_column_names ):
		s_x_label=None

		ALIASES=\
			PGNeEstimationBoxplotInterface.ALIASES_BY_COLNAMES

		if ls_group_by_column_names is not None \
				and len( ls_group_by_column_names ) > 0:

			ls_sorted_names=sorted( ls_group_by_column_names )

			ls_aliases_for_names=[ ALIASES[ s_name ] for s_name in ls_sorted_names  ]

			s_x_label=PGNeEstimationBoxplotInterface.DELIM_GROUPBY_FIELDS.join( ls_aliases_for_names )

		else:
			s_x_label="ungrouped"
		
		#end if names else none
		return s_x_label

	#end __get_x_label

	def __get_y_label( self, s_current_combo_y_value ):

		ALIASES=\
			PGNeEstimationBoxplotInterface.ALIASES_BY_COLNAMES

		s_y_label=None

		if s_current_combo_y_value in ALIASES:
			s_y_label=ALIASES[ s_current_combo_y_value ]
		else:
			s_y_label=s_current_combo_y_value
		#end

		return s_y_label
	#end __get_y_label
	
	def __make_scales( self ):

		SCALE_LENGTH=150
		o_myclass=PGNeEstimationBoxplotInterface

		df_min_max=self.__get_range_unfiltered_y_data()
		f_resolution=self.__get_scale_resolution( df_min_max[ "min" ], df_min_max[ "max" ] )
		f_bigincrement=self.__get_scale_bigincrement( df_min_max[ "min" ], df_min_max[ "max" ] )

		'''
		Note that we want the tkinter.Scale, not the ttk.Scale, which lacks
		many of the former's handy attributes.
		'''

		o_y_lower_value_scale=PGScaleWithEntry( 
							o_master_frame= self.__subframes[ 'y_value' ], 
							f_scale_from=df_min_max[ "min" ], 
							f_scale_to = df_min_max["max"],
							def_scale_command=self.__on_y_scale_change,
							v_orient=HORIZONTAL,
							f_resolution=f_resolution,
							f_bigincrement=f_bigincrement,
							i_scale_length=SCALE_LENGTH,
							s_scale_label="lower limit y axis values")
	
		o_y_lower_value_scale.scale.set( df_min_max[ "min" ] )
		o_y_lower_value_scale.grid( row=o_myclass.ROW_NUM_YVAL_LOWER_SCALE, 
											column=o_myclass.COLNUM_YVAL_LOWER_SCALE, 
																		sticky=( N,W ) )

		o_y_upper_value_scale=PGScaleWithEntry( 
							o_master_frame= self.__subframes[ 'y_value' ], 
							f_scale_from=df_min_max[ "min" ], 
							f_scale_to = df_min_max["max"],
							def_scale_command=self.__on_y_scale_change,
							v_orient=HORIZONTAL,
							f_resolution=f_resolution,
							f_bigincrement=f_bigincrement,
							i_scale_length=SCALE_LENGTH,
							s_scale_label="upper limit y axis values")


		o_y_upper_value_scale.scale.set( df_min_max[ "max" ] )
		o_y_upper_value_scale.grid( row=o_myclass.ROW_NUM_YVAL_UPPER_SCALE, 
											column=o_myclass.COLNUM_YVAL_UPPER_SCALE, 
																			sticky=( N,W ) )
		
		self.__scales={ 'y_value_lower':o_y_lower_value_scale, 'y_value_upper':o_y_upper_value_scale }
		return
	#end __make_scales

	def __get_range_unfiltered_y_data( self ):

		df_min_max={ "min":None, "max":None }

		ls_y_values=self.__tsv_file_manager.getUnfilteredTableAsList( b_skip_header=True,
											ls_exclusive_inclusion_cols=[ \
														self.__comboboxes[ 'select_y_variable' ].current_value ] )

		for s_val in ls_y_values:
			if s_val != "inf" and s_val != "NA":

				try:
					f_val=float( s_val )
				except:
					s_msg="In PGNeEstimationBoxplotInterface instance, " \
								+ "def __get_range_unfiltered_y_data, " \
								+ "the program could not convert the value, " \
								+ s_val + " into a numeric (float) type."
					raise Exception( s_msg )
				#end try...except

				df_min_max[ "min" ] = f_val if df_min_max[ "min"] is None \
									or f_val < df_min_max[ "min" ] else df_min_max[ "min" ]
				df_min_max[ "max" ] = f_val if df_min_max[ "max"] is None \
									or f_val > df_min_max[ "max" ] else df_min_max[ "max" ]
			#end if s_val not inf

		#end for each value	

		return df_min_max
	#end __get_range_unfiltered_y_data

	def __get_scale_resolution( self, f_min, f_max ):
		f_resolution=None
		o_myc=PGNeEstimationBoxplotInterface
		f_range_size=( f_max-f_min )
		f_resolution=f_range_size/o_myc.NUM_VALS_IN_SCALE

		if f_resolution < 1:
			f_resolution = 1
		#end if res less than unity

		return f_resolution
	#end __get_scale_resolution

	def __get_scale_bigincrement( self, f_min, f_max ):
		f_bigincrement=10
		return f_bigincrement
	#end __get_scale_bigincrement

	def __update_y_scales( self ):

		if self.__comboboxes is not None and 'select_y_variable' in self.__comboboxes:
			
			df_min_max=self.__get_range_unfiltered_y_data()

			f_resolution=self.__get_scale_resolution( df_min_max[ 'min' ], df_min_max[ 'max' ]  )
			f_bigincrement=self.__get_scale_bigincrement( df_min_max[ 'min' ], df_min_max[ 'max' ] )

			'''
			Note that the order of these re-settings matters, because,
			if the current resolution (in cases where this reset is called
			after a change in y variable) is larger than the range
			we got from __get_range_unfiltered_y_data, then
			the min (from)  and max (to) will be both set to 0.0. Hence,
			we must reset the resolution before resetting the from and to.
			'''
			self.__scales[ 'y_value_lower' ].scale[ 'resolution' ] = f_resolution
			self.__scales[ 'y_value_lower' ].scale[ 'bigincrement' ] = f_bigincrement	
			self.__scales[ 'y_value_lower' ].scale[ 'from' ] = df_min_max[ "min" ] 	
			self.__scales[ 'y_value_lower' ].scale[ 'to' ]=df_min_max[ "max" ] 
			self.__scales[ 'y_value_lower' ].scale.set( df_min_max[ "min" ] )

			self.__scales[ 'y_value_upper' ].scale[ 'resolution' ] = f_resolution
			self.__scales[ 'y_value_upper' ].scale[ 'bigincrement' ] = f_bigincrement
			self.__scales[ 'y_value_upper' ].scale[ 'from' ] = df_min_max[ "min" ] 	
			self.__scales[ 'y_value_upper' ].scale[ 'to' ]=df_min_max[ "max" ] 
			self.__scales[ 'y_value_upper' ].scale.set( df_min_max[ "max" ] )

		#end if the y var combo has been created
	#end __update_y_scales

	def __make_plot( self ):
		o_myc=PGNeEstimationBoxplotInterface
		ls_group_by_column_names = self.__get_group_by_column_names()

		'''
		These fetch the aliases for better labelling on th plot:
		'''
		s_x_label=self.__get_x_label( ls_group_by_column_names )
		s_y_label=self.__get_y_label( self.__comboboxes[ 'select_y_variable' ].current_value )

		'''
		We need to filter out NA's in the y variable.  As the user usese scales and combos to 
		filter data, in the update defs in this class, the  filters will also filter out NA's.
		'''

		self.__tsv_file_manager.setFilter( self.__comboboxes[ 'select_y_variable'].current_value,
																lambda x : x != "NA" )

		self.__plotframe=PGPlottingFrameBoxplotFromFileManager( o_master_frame=self.__master_frame,
																	o_tsv_file_manager=self.__tsv_file_manager,
																	b_do_animate=False,
																	s_y_value_colname= \
																			self.__comboboxes[ 'select_y_variable' ].current_value,
																	ls_group_by_column_names=ls_group_by_column_names,
																	v_init_data={ 'labels':["no_data"], 'value_lists':[[0]] },
																	s_xlabel=s_x_label,
																	s_ylabel=s_y_label,
																	i_figure_dpi=o_myc.PLOT_FIGURE_DOTS_PER_INCH,
																	f_figure_width=self.__plot_width,
																	f_figure_height=self.__plot_height,
																	def_to_convert_labels=self.__convert_labels )
		
		self.__plotframe.grid( row=PGNeEstimationBoxplotInterface.ROW_NUM_PLOT, 
												column=0, columnspan=o_myc.COLSPAN_PLOT, sticky=( N,W ) )

		self.__update_results()
		return
	#end __make_plot

	def __make_buttons( self ):

		o_myc=PGNeEstimationBoxplotInterface

		self.__buttons={}

		self.__buttons[ 'save_plot_to_file' ]=Button( \
				self.__subframes[ 'save_plot' ],
				text="Save",
				command=self.__on_click_save_plot_button )

		self.__buttons[ 'save_plot_to_file' ].grid( \
									row =o_myc.ROW_NUM_SAVE_PLOT_BUTTON,
									column=o_myc.COLNUM_SAVE_PLOT_BUTTON,
									sticky=( N,W ) )

		return
	#end __make_save_file_button

	def __on_click_save_plot_button( self ):

		if self.__plotframe is not None:
			if hasattr( self.__plotframe, "savePlotToFile" ):
			
				o_outputfile=tkfd.asksaveasfile( \
						title='Save plot to file' )
				#if no dir selected, return	

				if o_outputfile is None:
					return
				else:
					s_filename=o_outputfile.name
					o_outputfile.close()
					self.__plotframe.savePlotToFile( s_filename )
				#end if plotframe exists	
			#end if no dir selected
			return
	#end __on_click_save_plot_button

	def __on_group_by_selection_change( self, s_column_name, s_value, o_tsv_file_manager  ):

		if self.__plotframe is not None:
			ls_group_by_column_names=self.__get_group_by_column_names()
			s_x_label=self.__get_x_label( ls_group_by_column_names )
			s_y_label=self.__get_y_label( self.__comboboxes[ 'select_y_variable' ].current_value )

			self.__plotframe.setGroupByColumnNames(ls_group_by_column_names )	
			self.__plotframe.setYValueColumnName( self.__comboboxes[ 'select_y_variable' ].current_value )
			self.__plotframe.setXLabel( s_x_label )
			self.__plotframe.setYLabel( s_y_label )
			self.__update_results()
		#end if plot frame exists
		return
	#end __on_group_by_selection_change	

	def __on_y_variable_selection_change( self, s_column_name, s_value, o_tsv_file_manager ):
		o_myc=PGNeEstimationBoxplotInterface

		'''
		When the variable for the y value changes,
		we need to clear any filters imposed by the
		Scale object setting a limit on the value for
		any formerly selected y values.  However,
		we still filter out non-numeric values.
		As of 2017_10_20, the only non-numeric
		values for the y-variables are "NA."
		'''

		ls_non_convertable_vals=[ "NA" ]

		for s_name in o_myc.Y_AXIS_VALUE_COLUMNS:
			self.__tsv_file_manager.setFilter( s_name, lambda x : x not in ls_non_convertable_vals )
		#end for each y-val column variable, reset filter.

		self.__update_y_scales()

		self.__on_group_by_selection_change( s_column_name, s_value, o_tsv_file_manager )
		return
	#end __on_y_variable_selection_change

	def __on_filter_value_combo_change( self, s_column_name, s_val, o_tsv_file  ):

		if s_val == "All":
			self.__tsv_file_manager.setFilter( s_column_name, lambda x:True )
		else:
			self.__tsv_file_manager.setFilter( s_column_name, lambda x:x==s_val )
		#end if All values accepted, else filter
		
		if self.__plotframe is not None:
			self.__update_results()
		#end if we have a plot frame, replot

		return
	#end __on_filter_value_combo_change

	def __on_y_scale_change(self, o_event=None ):
		'''
		We use the local def instead of a simple lambda
		because we need to check for nonnumeric value
		(NA).
		'''
		def is_valid_y( s_value ):
			b_valid=False
			if s_value in ["NA"]:
				b_valid=False
			else:
				f_value=float( s_value )
				if f_value <= float( self.__scales[ 'y_value_upper'].scale.get() ) \
						and f_value >= float( self.__scales[ 'y_value_lower' ].scale.get() ):
					b_valid=True
				#end if float in range
			#end if
			return b_valid
		#end local def is_valid_y

		self.__tsv_file_manager.setFilter( \
						self.__comboboxes[ 'select_y_variable' ].current_value, 
																	is_valid_y )

		if self.__plotframe is not None:
			self.__update_results()
		#end if we have a plotframe, replot the data
		return		
	#end __on_y_scale_change

	def __convert_labels( self, ls_labels, ls_field_list ):

		MAX_LABEL_LEN=25
		MIN_FILE_NAME_LABEL_LEN=5
		TRUNCATED_FILE_PREFIX="..."

		o_myc=PGNeEstimationBoxplotInterface
		if ls_field_list is not None:
			if 'original_file' in ls_field_list:
				idx_file_name=ls_field_list.index( 'original_file' )

				for idx in range( len( ls_labels ) ):
					s_label=ls_labels[ idx ]
					s_new_label=s_label
					i_label_len=len ( s_label )	
					if i_label_len > MAX_LABEL_LEN:
						i_tot_possible_chars_to_trim=i_label_len - MAX_LABEL_LEN
						ls_vals=s_label.split( o_myc.DELIM_GROUPBY_FIELDS )
						s_orig_file=ls_vals[ idx_file_name ]
						i_len_orig_file=len( s_orig_file )
						i_len_minus_tot_poss=i_len_orig_file-i_tot_possible_chars_to_trim
						i_trim_to_this_len=max( MIN_FILE_NAME_LABEL_LEN, i_len_minus_tot_poss )
						s_trimmed_file_name=s_orig_file[ -1*i_trim_to_this_len : i_len_orig_file ]
						s_trimmed_file_name=TRUNCATED_FILE_PREFIX + s_trimmed_file_name
						s_new_label=s_label.replace( s_orig_file, s_trimmed_file_name )
						ls_labels[ idx ] = s_new_label
					#end if label too long
			#ende if orig file in list
			return
		#end if file name is in labels		

		return
	#end __convert_labels

	def __update_plot( self ):
		self.__plotframe.animate()
		return
	#end __update_plot

	def __update_results( self ):
		'''
		This def is meant to eventually call
		def __update_plot asynchronously, and 
		give the user a wait message while the plot
		updates.  It is not yet implemented.
		'''
		self.__update_plot()
	#end __update_results

	def __destroy_widgets( self, do_dict_of_widgets ):
		for s_widget_name in do_dict_of_widgets:

			o_widget=do_dict_of_widgets[ s_widget_name ]	

			try:
				if hasattr( o_widget, "grid_forget" ):
					o_widget.grid_forget()
				#end if has grid forget

				if hasattr( o_widget, 'destroy' ):
					o_widget.destroy()	
				#end if has destroy def

			except tkinter._tkinter.TclError as tkerr:
				s_tkmsg=str( tkerr )
				s_msg="Warning:  in PGNeEstimationBoxplotInterface instance, " \
							+ "def __destroy_widgets, " \
							+ "Failed to forget and destroy widgets keyed to " \
							+ s_widget_name + ".  Tkinter Error message is: " \
							+ s_tkmsg + "\n"

				sys.stderr.write( s_msg )
			#end try...except	
		#end for each widget

		return
	#end __destroy_widgets

	def cleanup( self ):
		'''
		This def is called by the pghostnotebook.py instance
		when user wants to exit.
		'''
		for s_widget_type in [ "labels", 
									"comboboxes", 
									"buttons", 
									"subframes" ]:
			s_attr_name="_PGNeEstimationBoxplotInterface__" \
								+  s_widget_type
		
			if hasattr( self, s_attr_name ):

				do_dict_of_widgets=getattr( self, s_attr_name )

				if do_dict_of_widgets is not None:
					self.__destroy_widgets( do_dict_of_widgets )
				#end if dict exists

				setattr( self, s_attr_name, None )
			#end if we have the attribute

		#end for each widget type created by this class

		if self.__master_frame is not None:
			if hasattr( self.__master_frame, "destroy" ):
				self.__master_frame.destroy()
				self.__master_frame=None
			#end if not yet destroyed
		#end if master frame exits

		return
	#end def cleanup

#end PGNeEstTableValueSelectionCombo

if __name__ == "__main__":
	s_tsv_file="/home/ted/documents/source_code/python/negui/temp_data/frogs.estimates.ldne.tsv"
	omaster=Tk()

	o_myinterface=PGNeEstimationBoxplotInterface( o_master_frame=omaster,
													s_tsv_file_name=s_tsv_file )

	omaster.mainloop()

#end if name is main

