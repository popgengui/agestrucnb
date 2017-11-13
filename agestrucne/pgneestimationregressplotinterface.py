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

import sys
import os
import re
import multiprocessing

from natsort import realsorted

import agestrucne.pgutilities as pgut
from agestrucne.pgguiutilities import PGGUIInfoMessage
from agestrucne.pgguiutilities import PGGUIErrorMessage
from agestrucne.pgguiutilities import PGGUIMessageWaitForResultsAndActionOnCancel

from agestrucne.pgplottingframe import PGPlottingFrameRegressionLinesFromFileManager
from agestrucne.pgframecontainerscrolled import FrameContainerScrolled
from agestrucne.pgneestimationtablefilemanager import NeEstimationTableFileManager
from agestrucne.pgneestimationtableselectioncombo import PGNeEstTableColumnSelectionCombo
from agestrucne.pgneestimationtableselectioncombo import PGNeEstTableValueSelectionCombo
from agestrucne.pgkeyvalueframe import KeyValFrame
from agestrucne.pgregresstabletextframe import PGRegressTableTextFrame
from agestrucne.pgregressionstats import PGRegressionStats
from agestrucne.pgscalewithentry import PGScaleWithEntry

'''
See def __destroy_all_widgets.  Tkinter apparently
allows calls to their destroy() and forget() methods,
even when there is no longer a main application. Further,
they throw an error, which could then interrupt the rest of close
operations.  I have not yet found
the proper order in which to destroy the interface
to avoid such errors, and so catch them and, if this
flag is True, send their messages to stderr, without
raising an error.
'''
SHOW_WIDGET_DESTROY_ERRORS=False

class PGNeEstimationRegressplotInterface( object ):

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

	X_AXIS_VALUE_COLUMNS=[ 'pop', 'original_file' ]

	Y_AXIS_VALUE_COLUMNS=[ 'ne_est_adj', '95ci_low', '95ci_high', 'est_ne'  ]

	VALUE_FILTERABLE_COLUMNS=[ 'original_file','replicate_number',
								'loci_replicate_number','sample_value', 
														'loci_sample_value' ]

	VALUE_FILTERABLE_COLUMNS_SORT_VALUES_NUMERICALLY = [ False, True, True, False, False ]

	ROW_NUM_SUBFRAME_TSV_FILE_LOADER=0
	ROW_NUM_SUBFRAME_GROUPBY=1
	ROW_NUM_SUBFRAME_FILTER=2
	ROW_NUM_SUBFRAME_Y_VALUE=3
	ROW_NUM_SUBFRAME_X_VALUE=3
	ROW_NUM_SUBFRAME_PLOT=4 
	ROW_NUM_SUBFRAME_STATS_TEXT=4

	ROW_NUM_GROUPBY_LABELS=0
	ROW_NUM_GROUPBY_COMBOS=1
	ROW_NUM_FILTER_LABELS=0
	ROW_NUM_FILTER_COMBOS=1
	ROW_NUM_X_VALUE_LABEL=0
	ROW_NUM_YVAL_LABEL=0
	ROW_NUM_YVAL_LOWER_SCALE_LABEL=0
	ROW_NUM_YVAL_UPPER_SCALE_LABEL=0
	ROW_NUM_YVAL_COMBO=1
	ROW_NUM_YVAL_UPPER_SCALE=1
	ROW_NUM_YVAL_LOWER_SCALE=1
	ROW_NUM_SAVE_PLOT_BUTTON=1
	ROW_NUM_PLOT=0
	ROW_NUM_STATS_TEXT=0

	NUM_VALS_IN_SCALE=3000

	COLNUM_SUBFRAME_TSV_LOADER=0
	COLNUM_SUBFRAME_Y_VALUE=0
	COLNUM_SUBFRAME_X_VALUE=1
	COLNUM_SUBFRAME_FILTER=0
	COLNUM_SUBFRAME_GROUPBY=0
	COLNUM_SUBFRAME_PLOT=0
	COLNUM_SUBFRAME_STATS_TEXT=5

	COLNUM_YVAL_LOWER_SCALE_LABEL=1
	COLNUM_YVAL_UPPER_SCALE_LABEL=2
	COLNUM_YVAL_LOWER_SCALE=1
	COLNUM_YVAL_UPPER_SCALE=2
	COLNUM_SAVE_PLOT_BUTTON=0
	COLNUM_PLOT=0
	COLNUM_STATS_TEXT=0

	COLSPAN_SUBFRAME_TSV_LOADER=3
	COLSPAN_SUBFRAME_GROUPY=4
	COLSPAN_SUBFRAME_FILTER=8
	COLSPAN_SUBFRAME_Y_VALUE=1
	COLSPAN_SUBFRAME_X_VALUE=1
	COLSPAN_SUBFRAME_SAVE_PLOT=1
	COLSPAN_SUBFRAME_PLOT=4
	COLSPAN_SUBFRAME_STATS_TEXT=1

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
			i_plot_height=None,
			f_alpha=0.05,
			s_expected_slope="auto",
			f_significant_slope=0.0 ):

		self.__master_frame=o_master_frame
		self.__tsv_file_name=s_tsv_file_name
		self.__plot_width=i_plot_width
		self.__plot_height=i_plot_height
		self.__stats_text_width=None
		self.__stats_text_height=None
		self.__tsv_file_manager=None
		self.__regress_stats_maker=None
		self.__plotframe=None
		self.__statstext=None
		self.__alpha=f_alpha
		self.__expected_slope=s_expected_slope
		self.__significant_slope=f_significant_slope

		self.__labels=None
		self.__comboboxes=None
		self.__buttons=None
		self.__scales=None
		self.__entries=None
		self.__subframes=None

		'''
		When the user selects the file name field 
		for x-values, we convert each name to
		a numeric value for regression, using
		natsort, so that we assume the user's
		file names will sort according to
		a meaningful series, appropriate
		for regression.
		'''
		self.__file_name_numeric_value_table=None

		'''
		We want to update using a separate process 
		(ex: multiprocessing.processpool), but for now
		this is not yet in use.
		'''
		self.__update_in_progress=False

		if self.__plot_width is None \
					or self.__plot_height is None:
			self.__get_auto_plot_size()
		#end if we are missing one or more plot

		self.__get_auto_text_size()
		#size dimensions

		self.__setup_tsv_file_loader()

		if self.__tsv_file_name is not None \
				and self.__tsv_file_name != "None":
			if self.__looks_like_a_tsv_file_with_data_lines( self.__tsv_file_name ):		
				self.__make_tsv_file_manager()
				self.__setup_plotting_interface()
			else:
				s_msg="In PGNeEstimationRegressplotInterface instance, " \
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
	

		o_myc=PGNeEstimationRegressplotInterface

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
					s_msg= "In PGNeEstimationRegressplotInterface instance, " \
							+ "def __load_tsv_file, plotframe obj is not none " \
							+ "but has no destroy attribute" 
					raise Exception( s_msg )
				#end if plot frame has destroy method, else has
			self.__setup_tsv_file_loader()
			self.__make_tsv_file_manager()
			self.__destroy_all_widgets()
			self.__file_name_numeric_value_table=None
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

		o_myc=PGNeEstimationRegressplotInterface
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

		o_myc=PGNeEstimationRegressplotInterface
	
		WINDOW_MARGIN=0.0

		WIDTH_PROPORTION=0.50
		HEIGHT_PROPORTION=0.70

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

	def __get_auto_text_size( self ):

		o_myc=PGNeEstimationRegressplotInterface
	
		WINDOW_MARGIN=0.0

		WIDTH_PROPORTION=0.04
		HEIGHT_PROPORTION=0.04

		i_width=self.__master_frame.winfo_screenwidth()
		i_height=self.__master_frame.winfo_screenheight()

		if self.__stats_text_width is None:
			f_width_pixels=( i_width * WIDTH_PROPORTION ) * ( 1 - WINDOW_MARGIN ) 
			self.__stats_text_width=int( f_width_pixels)
		#end if no plot width provided

		if self.__stats_text_height is None:
			f_height_pixels=( i_height * HEIGHT_PROPORTION ) * ( 1 - WINDOW_MARGIN )
			self.__stats_text_height=int( f_height_pixels )
		#end if no plot height provided

		return
	#end __get_auto_text_size

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

	def __setup_plotting_interface( self ):

		self.__make_subframes()
		self.__make_labels()
		self.__make_combos()
		self.__make_entries()
		self.__make_scales()
		self.__make_buttons()
		'''
		The stats widget needs to be created 
		before the plot frame, so that the plot
		after creation, can call update_stats on
		an existing stats widget.
		'''
		self.__make_stats_text()
		self.__make_plot()
		self.__set_master_frame_grid_weights()

		return
	#end __setup_plotting_interface

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

		self.__subframes={}

		o_myc=PGNeEstimationRegressplotInterface
		FRAME_STYLE=o_myc.SUBFRAME_STYLE
		GROUPBY_FRAME_LABEL="Group Data"
		GROUPBY_FILTER_FRAME_LABEL="Data Filters"
		X_VALUE_FRAME_LABEL="X-axis Data"
		Y_VALUE_FRAME_LABEL="Y-axis Data"
		STATS_TEXT_FRAME_LABEL="Regression Stats"
		PLOT_FRAME_LABEL="Plot"

		FRAME_PADDING=PGNeEstimationRegressplotInterface.SUBFRAME_PADDING

		self.__subframes[ 'filter' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=GROUPBY_FILTER_FRAME_LABEL )

		self.__subframes[ 'y_value' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=Y_VALUE_FRAME_LABEL )

		self.__subframes[ 'x_value' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=X_VALUE_FRAME_LABEL )

		self.__subframes[ 'plot' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=PLOT_FRAME_LABEL )

		self.__subframes[ 'stats_text' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=STATS_TEXT_FRAME_LABEL )


		self.__subframes[ 'filter' ].grid( row=o_myc.ROW_NUM_SUBFRAME_FILTER, 
														column=o_myc.COLNUM_SUBFRAME_FILTER, 
														columnspan=o_myc.COLSPAN_SUBFRAME_FILTER, 
														sticky=(N,W) )

		self.__subframes[ 'y_value' ].grid( row=o_myc.ROW_NUM_SUBFRAME_Y_VALUE, 
													column=o_myc.COLNUM_SUBFRAME_Y_VALUE, 
													columnspan=o_myc.COLSPAN_SUBFRAME_Y_VALUE, 
													sticky=(N,W) )

		self.__subframes[ 'x_value' ].grid( row=o_myc.ROW_NUM_SUBFRAME_X_VALUE, 
													column=o_myc.COLNUM_SUBFRAME_X_VALUE, 
													columnspan=o_myc.COLSPAN_SUBFRAME_X_VALUE, 
													sticky=(N,W) )
		self.__subframes[ 'plot' ].grid( row=o_myc.ROW_NUM_SUBFRAME_PLOT, 
													column=o_myc.COLNUM_SUBFRAME_PLOT, 
													columnspan=o_myc.COLSPAN_SUBFRAME_PLOT, 
													sticky=(N,W) )

		
		self.__subframes[ 'stats_text' ].grid( row=o_myc.ROW_NUM_SUBFRAME_STATS_TEXT, 
													column=o_myc.COLNUM_SUBFRAME_STATS_TEXT, 
													sticky=(N,W) )
		return
	#end __make_subframes

	def __make_labels( self ):

		self.__labels={}

		o_myc=PGNeEstimationRegressplotInterface

		self.__labels[ 'x_value' ]= Label( self.__subframes[ 'x_value' ], 
									text="X axis variable", padding=o_myc.LABEL_PADDING )

		self.__labels[ 'x_value' ].grid( row = o_myc.ROW_NUM_X_VALUE_LABEL, column = 0, sticky=( N,W ) )

		self.__value_filterable_combo_labels={}
		i_colnum_val_filt_labels=0
		for s_value_filterable_column in PGNeEstimationRegressplotInterface.VALUE_FILTERABLE_COLUMNS:
			ALIASES=PGNeEstimationRegressplotInterface.ALIASES_BY_COLNAMES

			s_label_key="filterable_" + s_value_filterable_column

			self.__labels[ s_label_key ] = \
							Label( self.__subframes[ 'filter' ], 
													text=ALIASES[ s_value_filterable_column ], 
													padding=o_myc.LABEL_PADDING )

			self.__labels[ s_label_key ].grid (  row = o_myc.ROW_NUM_FILTER_LABELS, 
													column=i_colnum_val_filt_labels )
			i_colnum_val_filt_labels += 1
		#end for each value filterable column

		self.__labels[ 'select_y_variable' ] = Label( self.__subframes[ 'y_value' ], 
															text= "Y axis value" , 
															padding=o_myc.LABEL_PADDING)
	
	
		self.__labels[ 'select_y_variable' ].grid( row = o_myc.ROW_NUM_YVAL_LABEL, 
																column=0, sticky=( N,W ) )

		return
	#end __make labels

	def __make_combos( self ):

		self.__comboboxes={}

		o_myc=PGNeEstimationRegressplotInterface

		self.__comboboxes[ 'x_value' ] = PGNeEstTableColumnSelectionCombo( \
													o_master=self.__subframes[ 'x_value' ], 
													o_tsv_file_manager=self.__tsv_file_manager, 
													def_to_call_on_selection_change=\
																	self.__on_x_value_selection_change,
													ls_column_names_to_show_excluding_others=\
																		o_myc.X_AXIS_VALUE_COLUMNS,
													b_add_none_selection=False )
		'''
		We'll default to pop as the x value.
		'''
		if 'pop' in o_myc.X_AXIS_VALUE_COLUMNS:
			self.__comboboxes[ 'x_value' ].resetCurrentValue('pop')
		#end if 'pop' is an available x field, we set it as the initial value

		self.__comboboxes[ 'x_value' ].grid( row=1, column=0, sticky=( N,W ) )

		i_column_count=0

		for s_value_filterable_column in o_myc.VALUE_FILTERABLE_COLUMNS:

			b_sort_this_col_numerically = \
					o_myc.VALUE_FILTERABLE_COLUMNS_SORT_VALUES_NUMERICALLY[ i_column_count ]
			
			s_combo_key="filterable_" + s_value_filterable_column
			
			self.__comboboxes[ s_combo_key ] = \
								PGNeEstTableValueSelectionCombo( self.__subframes[ 'filter' ],
															o_tsv_file_manager=self.__tsv_file_manager, 
															s_tsv_col_name=s_value_filterable_column, 
															def_to_call_on_selection_change=self.__on_filter_value_combo_change,
															b_sort_numerically=b_sort_this_col_numerically )

			self.__comboboxes[ s_combo_key ].grid ( \
													row = o_myc.ROW_NUM_FILTER_COMBOS, 
													column=i_column_count )
			i_column_count += 1
		#end for each value filterable column

		ls_y_variable_column=PGNeEstimationRegressplotInterface.Y_AXIS_VALUE_COLUMNS

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

	def __make_entries( self ):
		return
	#end __make_entries

	def __get_x_label( self ):
		s_x_label=None

		ALIASES=\
			PGNeEstimationRegressplotInterface.ALIASES_BY_COLNAMES

		if self.__x_value_field_name is not None:
			if self.__x_value_field_name != "None":
				s_x_label=ALIASES[ self.__x_value_field_name ]
			#end if no tsv file column value for the field name
		#end if we have a field Name

		return s_x_label
	#end __get_x_label

	def __get_y_label( self, s_current_combo_y_value ):

		ALIASES=\
			PGNeEstimationRegressplotInterface.ALIASES_BY_COLNAMES

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

		o_myclass=PGNeEstimationRegressplotInterface

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
								ls_exclusive_inclusion_cols=\
									[ self.__comboboxes[ 'select_y_variable' ].current_value ] )

		for s_val in ls_y_values:
			if s_val != "inf" and s_val != "NA":

				try:
					f_val=float( s_val )
				except:
					s_msg="In PGNeEstimationRegressplotInterface instance, " \
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
		o_myc=PGNeEstimationRegressplotInterface
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

		o_myc=PGNeEstimationRegressplotInterface

		s_x_label=self.__get_x_label( )
		s_y_label=self.__get_y_label( self.__comboboxes[ 'select_y_variable' ].current_value )

		'''		
		Note that the x variable "pop" should always be an int, so we set no NA filter for x vals.
		'''
		self.__tsv_file_manager.setFilter( self.__comboboxes[ 'select_y_variable' ].current_value, 
																					lambda x : x != "NA" )	
		self.__plotframe=\
				PGPlottingFrameRegressionLinesFromFileManager( o_master_frame=self.__subframes[ 'plot' ],
											o_tsv_file_manager=self.__tsv_file_manager,
											def_to_convert_x_vals_to_numeric=\
													self.__convert_file_name_x_values_to_numeric_values,

											def_to_convert_y_vals_to_numeric=None,
											def_to_get_labels_for_x_vals=\
													self.__get_x_labels_for_numeric_values_representing_file_names,
											b_do_animate=False,
											s_x_value_colname=\
													self.__comboboxes[ 'x_value' ].current_value,
											s_y_value_colname= \
													self.__comboboxes[ 'select_y_variable' ].current_value,
											ls_group_by_column_names=None,
											tuple_args_for_animation_call=None,
											v_init_data={ 'line1:':{"x":None, "y": None } },
											s_xlabel=s_x_label,
											s_ylabel=s_y_label,
											i_figure_dpi=o_myc.PLOT_FIGURE_DOTS_PER_INCH,
											f_figure_width=self.__plot_width,
											f_figure_height=self.__plot_height )
		
		self.__plotframe.grid( \
					row=o_myc.ROW_NUM_PLOT, 
					column=o_myc.COLNUM_PLOT, 
					sticky=( N,W ) )

		self.__update_plot_and_stats_text()	
		return
	#end __make_plot

	def __make_stats_text( self ):

		o_myc=PGNeEstimationRegressplotInterface
		'''
		This gets the initial value of the flag
		Note that it gets reset when the x value
		variable changes.
		'''
		b_use_file_name_only_for_stats_table=( self.__x_value_field_name != 'original_file'  )

		self.__regress_stats_maker=PGRegressionStats( dltup_table=None,
															f_confidence_alpha=self.__alpha,
															v_significant_value=self.__significant_slope )

		self.__statstext=\
				PGRegressTableTextFrame( o_master=self.__subframes[ 'stats_text' ], 
												o_regress_table=self.__regress_stats_maker,
												i_text_widget_width=self.__stats_text_width, 
												i_text_widget_height=self.__stats_text_height,
												b_file_name_only_in_stats_table_col_1 = \
															b_use_file_name_only_for_stats_table )
		self.__statstext.grid( \
					row=o_myc.ROW_NUM_STATS_TEXT, 
					column=o_myc.COLNUM_STATS_TEXT, 
				 	sticky=( N,W ) )
		return
	#end __make_stats_text

	def __update_stats_text( self ):
		'''
		This def should be called after each call to
		the plotframe.animate() call, and otherwise not
		called, in order that the stats in the text box 
		always reflects the plotted lines in the plot frame3.

		Note that the plotframe and the stats maker objects
		both use the tsv_file_manager to fetch data, and
		the avove pairing of the calls thus ensures that the same
		state for the file manager will yield the data for both
		plot and text frame.
		'''
		
		if self.__tsv_file_manager is not None:
			if self.__plotframe is not None:
				ls_key_fields=[ s_field for s_field 
						in NeEstimationTableFileManager\
								.INPUT_FIELDS_ASSOC_WITH_ONE_ESTIMATE ]

				s_current_xvar=self.__plotframe.getXValueColumnName()
				s_current_yvar=self.__plotframe.getYValueColumnName()

				'''
				The file manager will return proper lists of xy values
				only if we key the xy pairs to fields that don't include
				the field providing x and y (else we get one data set for each xy pair).
				'''
				for s_varname in [ s_current_xvar, s_current_yvar ]:
					if s_varname in ls_key_fields:
						ls_key_fields.remove( s_varname )
					#end if varname is in the key fields
				#end for each varname

				ls_value_fields=[ s_current_xvar, s_current_yvar  ]

				dls_xy_data_by_key=self.__tsv_file_manager\
						.getDictDataLinesKeyedToColnames( ls_key_column_names=ls_key_fields,
															ls_value_column_names=ls_value_fields,
															b_skip_header=True )
				
				if s_current_xvar=='original_file':
					self.__convert_file_name_x_values_to_numeric_values( dls_xy_data_by_key )	
				#end if our x values are file names

				'''
				The statstext object has access to the stats maker,
				and will get the stats from the maker after we update.
				'''
				self.__regress_stats_maker\
						.setTsvFileManagerDictAsTable( dls_xy_data_by_key )
				self.__statstext.updateTextWidgetContents()

			#end if plot frame exists
		#end if tsv file manager exists

		return
	#end __update_stats_text

	def __make_buttons( self ):

		o_myc=PGNeEstimationRegressplotInterface

		self.__buttons={}

		self.__buttons[ 'save_plot_to_file' ]=Button( \
				self.__subframes[ 'plot' ],
				text="Save to file",
				command=self.__on_click_save_plot_button )

		self.__buttons[ 'save_plot_to_file' ].grid( \
									row =o_myc.ROW_NUM_SAVE_PLOT_BUTTON,
									column=o_myc.COLNUM_SAVE_PLOT_BUTTON )
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

		
		return
	#end __on_group_by_selection_change	

	def __on_y_variable_selection_change( self, s_column_name, s_value, o_tsv_file_manager ):

		o_myc=PGNeEstimationRegressplotInterface

		'''
		When the variable for the y value changes,
		we need to clear any filters imposed by the
		Scale object setting a limit on the value for
		any formerly selected y values, but still filter
		non-float-convertible values:
		'''

		ls_non_numeric_values=[ "NA" ]

		for s_name in o_myc.Y_AXIS_VALUE_COLUMNS:
			self.__tsv_file_manager.setFilter( s_name, 
							lambda x : x not in ls_non_numeric_values )
		#end for each y-val column variable, reset filter.

		self.__update_y_scales()

		if self.__plotframe is not None:
			s_y_label=self.__get_y_label( \
					self.__comboboxes[ 'select_y_variable' ].current_value )
			self.__plotframe.setYValueColumnName( \
					self.__comboboxes[ 'select_y_variable' ].current_value )
			self.__plotframe.setYLabel( s_y_label )

			self.__update_plot_and_stats_text()
		#end if plot frame exists

		return
	#end __on_y_variable_selection_change

	def __on_x_value_selection_change( self, s_column_name, s_value, o_tsv_file_manager ):

		self.__x_value_field_name=s_value

		if self.__plotframe is not None:
			self.__plotframe.setXValueColumnName( s_value )

			if s_value == 'original_file':
				self.__make_file_name_numeric_value_table()
				self.__statstext.useFileNameOnlyInStatsTableCol1( False )
			else:
				self.__statstext.useFileNameOnlyInStatsTableCol1( True )
			#end if the user wants to regress over file names
			
			self.__update_plot_and_stats_text()
		#end if we have a plot frame

		return
	#end __on_x_value_selection_change

	def __on_filter_value_combo_change( self, s_column_name, s_val, o_tsv_file  ):

		if s_val == "All":
			self.__tsv_file_manager.setFilter( s_column_name, lambda x:True )
		else:
			self.__tsv_file_manager.setFilter( s_column_name, lambda x:x==s_val )
		#end if All values accepted, else filter
		
		if self.__plotframe is not None:
			self.__update_plot_and_stats_text()
		#end if we have a plot frame, replot

		return
	#end __on_filter_value_combo_change

	def __on_y_scale_change(self, o_event=None ):

		def is_valid_y( s_value ):
			b_valid=False
			if s_value == "NA":
				b_valid=False
			else:
				f_value=float( s_value )
				if f_value <= float( self.__scales[ 'y_value_upper' ].scale.get() ) \
						and f_value >= float( self.__scales[ 'y_value_lower' ].scale.get() ):
					b_valid= True
				#end if float in range
			#end if
			return b_valid
		#end local def is_valid_y
	
		self.__tsv_file_manager.setFilter( self.__comboboxes[ 'select_y_variable' ].current_value, 
											 is_valid_y )

		if self.__plotframe is not None:
			self.__update_plot_and_stats_text()
		#end if we have a plotframe, replot the data
		return		
	#end __on_y_scale_change

	def __convert_labels( self, ls_labels, ls_field_list ):

		MAX_LABEL_LEN=25
		MIN_FILE_NAME_LABEL_LEN=5
		TRUNCATED_FILE_PREFIX="..."

		o_myc=PGNeEstimationRegressplotInterface
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

	def __make_file_name_numeric_value_table( self ):
		self.__file_name_numeric_value_table=None
		if self.__x_value_field_name == 'original_file':
			if self.__tsv_file_manager is not None:
				b_all_files_are_float_castable=True
				ls_uniq_file_names=self.__tsv_file_manager\
									.getUniqueStringValuesForColumn( 'original_file' )
				
				for s_file_name in ls_uniq_file_names:
					s_base_name=os.path.basename( s_file_name )
					try:
						f_file_name_as_float=float( s_base_name )
						self.__file_name_numeric_value_table[ s_file_name ]=f_file_name_as_float
					except ValueError as ove:
						b_all_files_are_float_castable=False
						break
					#end try to cast as a float
				#end for each file name
				if not b_all_files_are_float_castable:
					ds_full_name_by_base_name={ os.path.basename( s_name ):s_name \
									for s_name in ls_uniq_file_names }
					if len( ds_full_name_by_base_name) != len( ls_uniq_file_names ):
						s_msg="In PGNeEstimationRegressplotInterface instance " \
								+ "def __make_file_name_numeric_value_table, " \
								+ "the program found non-uniq file names, and so " \
								+ "can't convert each file name to a unique number " \
								+ "for regression."
						raise Exception( s_msg )
					#end if we don't have a unique base name for each full name
					ls_basenames=list( ds_full_name_by_base_name.keys() )
					ls_natsorted_basenames=realsorted( ls_basenames )
					i_file_count=0
					self.__file_name_numeric_value_table={}
					for s_sorted_basename in ls_natsorted_basenames:
						i_file_count+=1
						s_full_name_this_base=ds_full_name_by_base_name[ s_sorted_basename ]
						self.__file_name_numeric_value_table[ s_full_name_this_base ] = i_file_count
					#end for each file, give it an integer value according to its sort position		
				#end if we can't cast each file name as a float
			#end if we have a file manager
		else:
			self.__file_name_numeric_value_table=None
		#end if the user has selected to regress over file name,
		#else not
		return
	#end __make_file_name_numeric_value_table

	def __convert_file_name_x_values_to_numeric_values( self, dict_data ):
		'''
		If our user selects file as the x value, over which to regress,
		we sort the names by natural sort (and, so, assume the user
		has named files such that the sort will represent, for example,
		populations over time, progressing in one temporal direction,
		such as earliest->latest.

		We assume that ths is called by a 
		PGPlottingFrameRegressionLinesFromFileManager
		instance, and which has passed a dict with
		keys being concattenated Ne estimation input values other than
		that used for the x value, and each of these keys 
		pointing to a list of strings, each of a tab-delimited  2-item list, 
		the first item of which is an x 
		value.  If our current x-value-field selected in the interface
		is the file name, we then use our current filename/value table
		to select labels, truncated if very long.
		'''

		if self.__x_value_field_name=='original_file':

			if self.__file_name_numeric_value_table is None:
				self.__make_file_name_numeric_value_table()
			#end if table does not exist, make it
			s_xy_delim=NeEstimationTableFileManager.DELIM_TABLE
			for s_line_name in dict_data:

				for idx in range(  len( dict_data[ s_line_name ] ) ):
					s_xy_vals=dict_data[ s_line_name ][ idx ]
					ls_xy_vals=s_xy_vals.split( s_xy_delim )
					s_this_x_val=ls_xy_vals[ 0 ]

					try:
						v_numeric_val=self.__file_name_numeric_value_table[ s_this_x_val ]
						#reassign the x value with its numeric replacement value,
						#and use the original y value part of the original string.
						s_converted_entry=s_xy_delim.join( [ str( v_numeric_val ), 
																	ls_xy_vals[ 1 ] ] )
						dict_data[ s_line_name ][ idx ] = s_converted_entry
					except KeyError as oke:
						s_msg="In PGNeEstimationRegressplotInterface instance, " \
									+ "def __convert_file_name_x_values_to_numeric_values, " \
									+ "the program had no numeric value entry for the file name, " \
									+ s_this_x_val + "."
						raise Exception( s_msg )
					#end try...except
				#end for each x value
			#end for each line name
		#end if the user has selected file name as x value
		return
	# end __convert_file_name_x_values_to_numeric_values

	def __get_file_name_from_number( self, v_number ):
		'''
		This def assumes calling keys() and values() on a dictionary
		(that is not altered between the calls) gets lists such that
		the ith value is the value assoc the ith key. (see
		https://stackoverflow.com/questions/835092/
		python-dictionary-are-keys-and-values-always-the-same-order)
		'''
		lv_numbers=list( self.__file_name_numeric_value_table.values() )
		idx_number=lv_numbers.index( v_number )
		ls_file_names=list( self.__file_name_numeric_value_table.keys() )
		s_file_name=ls_file_names[ idx_number ]
		return s_file_name
	#end __get_file_name_from_number


	def __get_x_labels_for_numeric_values_representing_file_names( self, dict_data ):
		'''
		This def should be called by an instance of 
		PGPlottingFrameRegressionLinesFromFileManager
		after it has regressed and has a resulting
		data dictionary ready for plotting, so that each
		outer key (concatted input fields)  has a dict 
		with an "x", and a "y" key, each of this with
		a list of a series of values.  If this interface
		is currently selected to use file name for the x value,
		This def will create another key, "x_labels", for 
		this inner dict, and will make a for each numeric x value,
		which is assumed to be a number associated with a file name
		as given in the self.__file_name_numeric_value_table. 

		'''
		if self.__x_value_field_name == 'original_file':
			
			MAX_LABEL_LEN=15
			MIN_FILE_NAME_LABEL_LEN=5
			TRUNCATED_FILE_PREFIX="..."
			'''
			For each line data set,
			we create a label for each xy entry,
			and append it to the dict_data.  We
			know that the PGPlottingFrame2DLines
			parent of our PGPlottingFrameRegressionLinesFromFileManager
			plotframe object will check for an "x_labels" entry
			and use the labels if found.
			'''
			for s_line_name in dict_data:
				ls_these_labels=[]
				for v_xval in dict_data[ s_line_name ]['x']:
					s_file_name=self.__get_file_name_from_number( v_xval )
					i_file_name_len=len( s_file_name )
					i_tot_to_trim=max( 0, i_file_name_len - MAX_LABEL_LEN )
					s_trimmed_file_name=s_file_name[ i_tot_to_trim : i_file_name_len ]
					i_len_trimmed=len(s_trimmed_file_name )

					if i_len_trimmed < i_file_name_len:
						s_trimmed_file_name=TRUNCATED_FILE_PREFIX + s_trimmed_file_name
					#end if any trimming was done, prefix with ellipses

					ls_these_labels.append( s_trimmed_file_name )					
				#end for each xvalue for this line
			#end for each line

			dict_data[ s_line_name ][ "x_labels" ] = ls_these_labels
			#end if user has selected file name for x value
		return
	#end __get_x_labels_for_numeric_values_representing_file_names

	def __do_results_update( self ):
		self.__update_in_progress=True
		try:
			self.__plotframe.animate()
			self.__update_stats_text()
		except Exception as oex:
			self.__update_in_progress=False
			PGGUIErrorMessage( o_parent=self.__master_frame, s_message= \
					oex.__class__.__name__ + ", " + str( oex ) )
			raise oex 
		#end try . . . except

		self.__update_in_progress=False
		return 
	#end __do_results_update

	def __update_plot_and_stats_text( self ):
		'''
		This def is meant to call __do_results_update
		as an asyn process and arrange for a GUI message
		to the user that it is in progress.  It is not
		yet implemented.
		'''
		self.__do_results_update()
		return
	#end __update_plot_and_stats_text

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

			except tki._tkinter.TclError as tkerr:
				if SHOW_WIDGET_DESTROY_ERRORS:
					s_tkmsg=str( tkerr )
					s_msg="Warning:  in PGNeEstimationBoxplotInterface instance, " \
								+ "def __destroy_widgets, " \
								+ "Failed to forget and destroy widgets keyed to " \
								+ s_widget_name + ".  Tkinter Error message is: " \
								+ s_tkmsg + "\n"

					sys.stderr.write( s_msg )
				#end if SHOW_WIDGET_DESTROY_ERRORS
			#end try...except	
		#end for each widget

		return

	#end __destroy_widgets

	def cleanup( self ):
		'''
		This def is called by the pghostnotebook.py instance
		when user wants to exit.
		'''
		self.__destroy_all_widgets()
		return
	#end def cleanup
#end PGNeEstTableValueSelectionCombo

if __name__ == "__main__":
	s_tsv_file="/home/ted/documents/source_code/python/negui/temp_data/frogs.estimates.ldne.tsv"
	omaster=Tk()

	o_myinterface=PGNeEstimationRegressplotInterface( o_master_frame=omaster,
													s_tsv_file_name=s_tsv_file )
	omaster.mainloop()

#end if name is main

