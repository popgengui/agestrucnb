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

PLOTLABELFONTSIZE=18
TICKLABELFONTSIZE=14

'''
2018_05_04. To define range for the new
scales added to allow user to set font
sizes for axis and tic labels.
'''
MINFONTSIZE=8
MAXFONTSIZE=40


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
2018_04_13. We use this class to validate user entries for the
new text boxes for user-setting of min and max cycle number, 
and alpha value.
'''
from agestrucne.pgutilityclasses import ValueValidator

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

	Y_AXIS_VALUE_COLUMNS=[ 'ne_est_adj', '95ci_low_adj', '95ci_high_adj', 'est_ne', '95ci_low', '95ci_high'  ]

	VALUE_FILTERABLE_COLUMNS=[ 'original_file','replicate_number',
								'loci_replicate_number','sample_value', 
														'loci_sample_value' ]

	VALUE_FILTERABLE_COLUMNS_SORT_VALUES_NUMERICALLY = [ False, True, True, False, False ]

	ROW_NUM_SUBFRAME_TSV_FILE_LOADER=0
	ROW_NUM_SUBFRAME_GROUPBY=1
	ROW_NUM_SUBFRAME_FILTER=2
	ROW_NUM_SUBFRAME_Y_VALUE=0
	ROW_NUM_SUBFRAME_X_VALUE=0
	ROW_NUM_SUBFRAME_PLOT=4 
	ROW_NUM_SUBFRAME_STATS_TEXT=4
	'''
	2018_05_04. New subframe for setting font sizes
	via scales:
	'''
	ROW_NUM_SUBFRAME_PLOT_APPEARANCE=0
	'''
	2018_05_05. New subframe to contain the
	3 subframes y_value, x_value, and plot_appearance.
	'''
	ROW_NUM_SUBFRAME_ROW_3_SUBFRAME=3

	ROW_NUM_GROUPBY_LABELS=0
	ROW_NUM_GROUPBY_COMBOS=1
	ROW_NUM_FILTER_LABELS=0
	ROW_NUM_FILTER_COMBOS=1
	ROW_NUM_X_VALUE_LABEL=0
	ROW_NUM_MIN_CYCLE_TEXT_BOX=0
	ROW_NUM_MAX_CYCLE_TEXT_BOX=1
	ROW_NUM_ALPHA_TEXT_BOX=2
	ROW_NUM_YVAL_LABEL=0
	ROW_NUM_YVAL_LOWER_SCALE_LABEL=0
	ROW_NUM_YVAL_UPPER_SCALE_LABEL=0
	ROW_NUM_YVAL_COMBO=1
	ROW_NUM_YVAL_UPPER_SCALE=1
	ROW_NUM_YVAL_LOWER_SCALE=1
	ROW_NUM_SAVE_PLOT_BUTTON=1
	ROW_NUM_PLOT=0
	ROW_NUM_STATS_TEXT=0
	'''
	2018_05_04. New scales to change font size
	of labels:
	'''
	ROW_NUM_SET_FONT_SIZE_AXIS_LABEL_SCALE=1
	ROW_NUM_SET_FONT_SIZE_TIC_LABEL_SCALE=1

	#NUM_VALS_IN_SCALE=3000
	NUM_VALS_IN_SCALE=int( 1e10 )

	COLNUM_SUBFRAME_TSV_LOADER=0
	COLNUM_SUBFRAME_Y_VALUE=0
	COLNUM_SUBFRAME_X_VALUE=2
	COLNUM_SUBFRAME_FILTER=0
	COLNUM_SUBFRAME_GROUPBY=0
	COLNUM_SUBFRAME_PLOT=0
	COLNUM_SUBFRAME_STATS_TEXT=4
	'''
	2018_05_04. New subframe for setting font sizes:
	'''
	COLNUM_SUBFRAME_PLOT_APPEARANCE=3

	'''
	2018_05_05. New subframe to contain the
	3 subframes y_value, x_value, and plot_appearance.
	'''
	COLNUM_SUBFRAME_ROW_3_SUBFRAME=0


	COLNUM_YVAL_LOWER_SCALE_LABEL=1
	COLNUM_YVAL_UPPER_SCALE_LABEL=2
	COLNUM_YVAL_LOWER_SCALE=1
	COLNUM_YVAL_UPPER_SCALE=2
	COLNUM_SAVE_PLOT_BUTTON=0
	COLNUM_PLOT=0
	COLNUM_STATS_TEXT=0
	COLNUM_MIN_CYCLE_TEXT_BOX=1
	COLNUM_MAX_CYCLE_TEXT_BOX=1
	COLNUM_ALPHA_TEXT_BOX=1
	'''
	2018_05_04. New scalsed for setting font sizes:
	'''
	COLNUM_SET_FONT_SIZE_AXIS_LABEL_SCALE=1
	COLNUM_SET_FONT_SIZE_TIC_LABEL_SCALE=2

	COLSPAN_SUBFRAME_TSV_LOADER=30
	COLSPAN_SUBFRAME_FILTER=30
	COLSPAN_SUBFRAME_Y_VALUE=2
	COLSPAN_SUBFRAME_X_VALUE=1
	COLSPAN_SUBFRAME_PLOT=4
	COLSPAN_SUBFRAME_STATS_TEXT=30
	COLSPAN_SUBFRAME_PLOT_APPEARANCE=30
	'''
	2018_05_05. New subframe to contain the
	3 subframes y_value, x_value, and plot_appearance.
	'''
	COLSPAN_SUBFRAME_ROW_3_SUBFRAME=30



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

		'''
		2018_04_13. We add these for new 
		text boxes that allow the user to change
		the cycle range over which to regress.
		They are initially set in def __make_text_boxes.
		'''
		self.__min_tsv_cycle_number=None
		self.__max_tsv_cycle_number=None
		self.__min_cycle_number=None
		self.__max_cycle_number=None

		self.__labels=None
		self.__comboboxes=None
		self.__buttons=None
		self.__scales=None
		self.__entries=None
		self.__subframes=None
		'''
		2018_04_13. Adding text boxes
		to allow user entry of cycle ranges
		and and alpha value.
		'''
		self.__text_boxes=None

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
						+ "does not appear to be an LDNe tsv file with correct " \
						+ "data lines in it. " \
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

		return
	#end __destroy_all_widgets

	def __setup_plotting_interface( self ):

		self.__make_subframes()
		self.__make_labels()
		self.__make_combos()
		self.__make_entries()
		'''
		2018_04_13. New text boxes to allow
		user-entry of min and max cycles,
		and an alpha value.
		'''
		self.__make_text_boxes()
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
		PLOT_APPEARANCE_FRAME_LABEL="Other settings"

		FRAME_PADDING=PGNeEstimationRegressplotInterface.SUBFRAME_PADDING


		'''
		2018_05_05.  This new frame is added to simplify the spacing
		of the 3 subframes that constitute row 3 of the GUI's main grid.
		Note that these 3 subframs (y_value, x_value, and plot_appearance),
		are still added to the self.__subrames dict, so they are accessible
		from it, even though their master frame has been changed to the row_3_subframe.
		Note, too, that this new subrame is of type Frame instead of LabelFrame,
		and so will lack any relief or label.
		'''
		o_row_3_subframe=Frame( self.__master_frame )

		self.__subframes[ 'row_3_subframe' ] = o_row_3_subframe 

		self.__subframes[ 'filter' ]=LabelFrame( self.__master_frame,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=GROUPBY_FILTER_FRAME_LABEL )

		self.__subframes[ 'y_value' ]=LabelFrame( o_row_3_subframe,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=Y_VALUE_FRAME_LABEL )

		self.__subframes[ 'x_value' ]=LabelFrame( o_row_3_subframe,
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

		'''
		2018_05_04. New subframe on which we place scales to set font sizes:
		'''
		self.__subframes[ 'plot_appearance' ]=LabelFrame( o_row_3_subframe,
				padding=FRAME_PADDING,
				relief=FRAME_STYLE,
				text=PLOT_APPEARANCE_FRAME_LABEL )


		'''
		2018_05_05. New subframe contains the y_value, x_value, and plot_appearance subframes
		'''
		self.__subframes[ 'row_3_subframe' ].grid( row=o_myc.ROW_NUM_SUBFRAME_ROW_3_SUBFRAME,
														column=o_myc.COLNUM_SUBFRAME_ROW_3_SUBFRAME,
														columnspan=o_myc.COLSPAN_SUBFRAME_ROW_3_SUBFRAME,
														sticky=(N,W) )

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
													columnspan=o_myc.COLSPAN_SUBFRAME_STATS_TEXT, 
													sticky=(N,W) )
		'''
		2018_05_04. New subframe for setting the plot's label font sizes.
		'''

		self.__subframes[ 'plot_appearance' ].grid( row=o_myc.ROW_NUM_SUBFRAME_PLOT_APPEARANCE, 
													column=o_myc.COLNUM_SUBFRAME_PLOT_APPEARANCE, 
													columnspan=o_myc.COLSPAN_SUBFRAME_PLOT_APPEARANCE,
													sticky=(N,W) )
		return
	#end __make_subframes

	def __make_labels( self ):

		self.__labels={}

		o_myc=PGNeEstimationRegressplotInterface

		self.__labels[ 'x_value' ]= Label( self.__subframes[ 'x_value' ], 
									text="X axis variable", padding=o_myc.LABEL_PADDING )

		self.__labels[ 'x_value' ].grid( row = o_myc.ROW_NUM_X_VALUE_LABEL, column = 0, sticky=( N,W ) )

#		self.__labels[ 'min_cycle' ]=Label( self.__subframes[ 'x_value' ],
#									text="Min cycle number", padding=o_myc.LABEL_PADDING )
#
#		self.__labels[ 'x_value' ].grid( row = o_myc.ROW_NUM_MIN_CYCLE_LABEL, column = 0, sticky=( N,W ) )
#
#		self.__labels[ 'max_cycle' ]=Label( self.__subframes[ 'x_value' ],
#									text="Max cycle number", padding=o_myc.LABEL_PADDING )
#
#		self.__labels[ 'x_value' ].grid( row = o_myc.ROW_NUM_MAX_CYCLE_LABEL, column = 0, sticky=( N,W ) )

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

	def __make_text_boxes( self ):
		'''
		Added 20180413 to allow user
		setting a range of cycles over which
		to regress, and to set the alpha value.
		'''

		MIN_ALPHA=0.0
		MAX_ALPHA=1.0

		CYCLE_BOX_LABEL_WIDTH=8
		ALPHA_BOX_LABEL_WIDTH=8

		KEYVAL_SUBFRAME_PADDING=10

		self.__text_boxes={}

		o_myc=PGNeEstimationRegressplotInterface

		s_demangler="_PGNeEstimationRegressplotInterface__"

		ls_cycle_numbers=self.__tsv_file_manager.pop_numbers
		li_cycle_numbers=[ int( i_num ) for i_num in ls_cycle_numbers ]

		#We keep a copy of the entire range, in case we want
		#to reset to these (e.g. in def __reset_cycle_number_filter )
		self.__min_tsv_cycle_number=min( li_cycle_numbers )
		self.__max_tsv_cycle_number=max( li_cycle_numbers )
		
		#These are the attribute variables
		#we associate with the text boxes:
		self.__min_cycle_number=min( li_cycle_numbers )
		self.__max_cycle_number=max( li_cycle_numbers )

		
		s_cycle_range_lambda="x >= " + str( self.__min_cycle_number ) \
									+	" and x<= " + str( self.__max_cycle_number ) 

		s_valid_alpha="x >= " + str( MIN_ALPHA ) + " and x <= " + str( MAX_ALPHA )
			
		o_validity_test_for_cycle_range=ValueValidator( s_cycle_range_lambda )
		o_validity_test_for_alpha=ValueValidator( s_valid_alpha ) 

		self.__text_boxes[ 'min_cycle' ]=KeyValFrame( s_name="min_cycle", 
						v_value=self.__min_cycle_number,
						o_type=int,
						v_default_value="1",
						o_master=self.__subframes[ 'x_value' ],
						o_associated_attribute_object=self,
						s_associated_attribute=s_demangler+"min_cycle_number",
						b_is_enabled=True,
						b_force_disable=False,
						def_entry_change_command=self.__on_min_cycle_change,
						o_validity_tester=o_validity_test_for_cycle_range,
						s_tooltip = "Use this as the minimum cycle number for the x values",
						i_labelwidth=CYCLE_BOX_LABEL_WIDTH,
						i_subframe_padding=KEYVAL_SUBFRAME_PADDING )

		self.__text_boxes[ 'min_cycle' ].grid( row = o_myc.ROW_NUM_MIN_CYCLE_TEXT_BOX, 
								column = o_myc.COLNUM_MIN_CYCLE_TEXT_BOX, sticky=( N,W ) )

		self.__text_boxes[ 'max_cycle' ]=KeyValFrame( s_name="max_cycle", 
						v_value=self.__max_cycle_number,
						o_type=int,
						v_default_value="1",
						o_master=self.__subframes[ 'x_value' ],
						o_associated_attribute_object=self,
						s_associated_attribute=s_demangler+"max_cycle_number",
						b_is_enabled=True,
						b_force_disable=False,
						def_entry_change_command=self.__on_max_cycle_change,
						o_validity_tester=o_validity_test_for_cycle_range,
						s_tooltip = "Use this as the maximum cycle number for the x values",
						i_labelwidth=CYCLE_BOX_LABEL_WIDTH,
						i_subframe_padding=KEYVAL_SUBFRAME_PADDING )

		self.__text_boxes[ 'max_cycle' ].grid( row = o_myc.ROW_NUM_MAX_CYCLE_TEXT_BOX, 
								column = o_myc.COLNUM_MAX_CYCLE_TEXT_BOX, sticky=( N,W ) )

		self.__text_boxes[ 'alpha' ] =KeyValFrame( s_name="alpha", 
								v_value=self.__alpha,
								o_type=float,
								v_default_value=self.__alpha,
								o_master=self.__subframes[ 'x_value' ],
								o_associated_attribute_object=self,
								s_associated_attribute=s_demangler+"alpha",
								b_is_enabled=True,
								b_force_disable=False,
								def_entry_change_command=self.__on_alpha_change,
								o_validity_tester=o_validity_test_for_alpha,
								s_tooltip = "Use this as the alpha value for the regression.",
								i_labelwidth=ALPHA_BOX_LABEL_WIDTH,
								i_subframe_padding=KEYVAL_SUBFRAME_PADDING )

		
		self.__text_boxes[ 'alpha' ].grid( row = o_myc.ROW_NUM_ALPHA_TEXT_BOX, 
								column = o_myc.COLNUM_ALPHA_TEXT_BOX, sticky=( N,W ) )
		return
	#end __make_text_boxes
	
	def __reset_cycle_number_filter( self ):

		if self.__min_cycle_number<=self.__max_cycle_number:

			def_range=lambda x: int( x ) >= self.__min_cycle_number \
										and int( x ) <= self.__max_cycle_number
			self.__tsv_file_manager.setFilter( 'pop', def_range )

		else:
			s_msg="In PGNeEstimationRegressplotInterface instance, "  \
							+ "def __reset_cycle_number_filter, " \
							+ "the program can't reset the cycle filter " \
							+ "because the minimum is not less than or equal " \
							+ "to the maximum.  The minimum range is being reset to " \
							+ "cycle the smallest cycle number in the tsv file."

			PGGUIInfoMessage( self.__master_frame, s_msg )

			self.__min_cycle_number=self.__min_tsv_cycle_number

			self.__text_boxes[ 'min_cycle' ].manuallyUpdateValue( self.__min_tsv_cycle_number )

		#end if valid min, max else info message

		return
	#end __reset_cycle_number_filter	
		
	def __on_min_cycle_change( self ):
		self.__reset_cycle_number_filter()
		self.__update_plot_and_stats_text()
		return
	#end __on_min_cycle_change

	def __on_max_cycle_change( self ):
		self.__reset_cycle_number_filter()
		self.__update_plot_and_stats_text()
		return
	#end __on_max_cycle_change

	def __on_alpha_change( self ):
		self.__regress_stats_maker.confidence_alpha=self.__alpha
		self.__update_plot_and_stats_text()
		return
	#end __on_alpha_change

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

		2018_05_07.  We are removing the y-values scale from the gui -- users
		will only be able to regress on the whole data set:
		'''

#		o_y_lower_value_scale=PGScaleWithEntry( 
#							o_master_frame= self.__subframes[ 'y_value' ], 
#							f_scale_from=df_min_max[ "min" ], 
#							f_scale_to = df_min_max["max"],
#							def_scale_command=self.__on_y_scale_change,
#							v_orient=HORIZONTAL,
#							f_resolution=f_resolution,
#							f_bigincrement=f_bigincrement,
#							i_scale_length=SCALE_LENGTH,
#							s_scale_label="lower limit y axis values")
#
#		o_y_lower_value_scale.scale.set( df_min_max[ "min" ] )
#		o_y_lower_value_scale.grid( row=o_myclass.ROW_NUM_YVAL_LOWER_SCALE, 
#											column=o_myclass.COLNUM_YVAL_LOWER_SCALE, 
#																		sticky=( N,W ) )
#
#		o_y_upper_value_scale=PGScaleWithEntry( 
#							o_master_frame= self.__subframes[ 'y_value' ], 
#							f_scale_from=df_min_max[ "min" ], 
#							f_scale_to = df_min_max["max"],
#							def_scale_command=self.__on_y_scale_change,
#							v_orient=HORIZONTAL,
#							f_resolution=f_resolution,
#							f_bigincrement=f_bigincrement,
#							i_scale_length=SCALE_LENGTH,
#							s_scale_label="upper limit y axis values")
#
#		o_y_upper_value_scale.scale.set( df_min_max[ "max" ] )
#		o_y_upper_value_scale.grid( row=o_myclass.ROW_NUM_YVAL_UPPER_SCALE, 
#											column=o_myclass.COLNUM_YVAL_UPPER_SCALE, 
#																			sticky=( N,W ) )
#		
#		self.__scales={ 'y_value_lower':o_y_lower_value_scale, 'y_value_upper':o_y_upper_value_scale }
#
		'''
		Required now that we've removed the y_value scales::
		'''
		self.__scales={}
		'''
		2018_05_04.  New scales allow user to set the font size for axis and tic labels:
		'''
		o_axis_label_font_size_scale=PGScaleWithEntry( 
							o_master_frame= self.__subframes[ 'plot_appearance' ], 
							f_scale_from=MINFONTSIZE, 
							f_scale_to = MAXFONTSIZE,
							def_scale_command=self.__on_font_size_axis_label_change,
							v_orient=HORIZONTAL,
							f_resolution=1,
							i_scale_length=SCALE_LENGTH,
							s_scale_label="axis label font size" )

		o_axis_label_font_size_scale.scale.set( PLOTLABELFONTSIZE )

		o_axis_label_font_size_scale.grid( row=o_myclass.ROW_NUM_SET_FONT_SIZE_AXIS_LABEL_SCALE, 
											column=o_myclass.COLNUM_SET_FONT_SIZE_AXIS_LABEL_SCALE, 
																			sticky=( N,W ) )
		self.__scales[ 'font_size_labels_axis' ] = o_axis_label_font_size_scale

		'''
		New scales allow user to set the font size for axis and tic labels:
		'''
		o_tic_label_font_size_scale=PGScaleWithEntry( 
							o_master_frame= self.__subframes[ 'plot_appearance' ], 
							f_scale_from=MINFONTSIZE, 
							f_scale_to = MAXFONTSIZE,
							def_scale_command=self.__on_font_size_tic_label_change,
							v_orient=HORIZONTAL,
							f_resolution=1,
							i_scale_length=SCALE_LENGTH,
							s_scale_label="tic label font size" )

		o_tic_label_font_size_scale.scale.set( TICKLABELFONTSIZE )

		o_tic_label_font_size_scale.grid( row=o_myclass.ROW_NUM_SET_FONT_SIZE_TIC_LABEL_SCALE, 
											column=o_myclass.COLNUM_SET_FONT_SIZE_TIC_LABEL_SCALE, 
																			sticky=( N,W ) )
		self.__scales[ 'font_size_labels_tic' ] = o_tic_label_font_size_scale



		return

	#end __make_scales


	def __on_font_size_axis_label_change( self, o_event=None ):
		if self.__plotframe is not None:
			i_font_size=int( self.__scales[ 'font_size_labels_axis'].scale.get()  )
			self.__plotframe.setFontSizeAxisLabels( i_font_size )
			self.__update_plot_and_stats_text()
		#end if we have a plot frame
		return
	#end __on_font_size_axis_lable_change

	def __on_font_size_tic_label_change( self, o_event=None ):
		if self.__plotframe is not None:
			i_font_size=int( self.__scales[ 'font_size_labels_tic'].scale.get()  )
			self.__plotframe.setFontSizeTicLabels( i_font_size )
			self.__update_plot_and_stats_text()
		#end if we have a plot frame
		return
	#end __on_font_size_axis_lable_change

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

		'''
		2018_04_13. This is commented out in order to
		keep the resolution fine enough that no 
		values get trimmed in the ranges specified.
		'''
#		if f_resolution < 1:
#			f_resolution = 1
#		#end if res less than unity

		return f_resolution
	#end __get_scale_resolution

	def __get_scale_bigincrement( self, f_min, f_max ):
		f_bigincrement=0
		return f_bigincrement
	#end __get_scale_bigincrement

	def __update_y_scales( self ):
		'''
		2018_05_07. we are removing the y-value scales:
		'''
#		if self.__comboboxes is not None and 'select_y_variable' in self.__comboboxes:
#			
#			df_min_max=self.__get_range_unfiltered_y_data()
#
#			f_resolution=self.__get_scale_resolution( df_min_max[ 'min' ], df_min_max[ 'max' ]  )
#			f_bigincrement=self.__get_scale_bigincrement( df_min_max[ 'min' ], df_min_max[ 'max' ] )
#
#			'''
#			Note that the order of these re-settings matters, because,
#			if the current resolution (in cases where this reset is called
#			after a change in y variable) is larger than the range
#			we got from __get_range_unfiltered_y_data, then
#			the min (from)  and max (to) will be both set to 0.0. Hence,
#			we must reset the resolution before resetting the from and to.
#			'''
#			self.__scales[ 'y_value_lower' ].scale[ 'resolution' ] = f_resolution
#			self.__scales[ 'y_value_lower' ].scale[ 'bigincrement' ] = f_bigincrement	
#			self.__scales[ 'y_value_lower' ].scale[ 'from' ] = df_min_max[ "min" ] 	
#			self.__scales[ 'y_value_lower' ].scale[ 'to' ]=df_min_max[ "max" ] 
#			self.__scales[ 'y_value_lower' ].scale.set( df_min_max[ "min" ] )
#
#			self.__scales[ 'y_value_upper' ].scale[ 'resolution' ] = f_resolution
#			self.__scales[ 'y_value_upper' ].scale[ 'bigincrement' ] = f_bigincrement
#			self.__scales[ 'y_value_upper' ].scale[ 'from' ] = df_min_max[ "min" ] 	
#			self.__scales[ 'y_value_upper' ].scale[ 'to' ]=df_min_max[ "max" ] 
#			self.__scales[ 'y_value_upper' ].scale.set( df_min_max[ "max" ] )
#
#		#end if the y var combo has been created

		return
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
											f_figure_height=self.__plot_height,
											i_labelfontsize=PLOTLABELFONTSIZE,
											i_ticklabelsize=TICKLABELFONTSIZE )
		
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
		'''
		From this module's inception up to 2018_04_11, there are no group by selectors.
		'''
		pass
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
				'''
				2018_04_13. We add code to disable the new controls
				that users can use to set cycle ranges, and remove 
				the cycle range.
				'''
				self.__text_boxes[ 'min_cycle' ].setStateControls( 'disabled' )
				self.__text_boxes[ 'max_cycle' ].setStateControls( 'disabled' )
				self.__tsv_file_manager.setFilter( 'pop', None )
			else:
				self.__statstext.useFileNameOnlyInStatsTableCol1( True )
				self.__text_boxes[ 'min_cycle' ].setStateControls( 'enabled' )
				self.__text_boxes[ 'max_cycle' ].setStateControls( 'enabled' )
				self.__reset_cycle_number_filter()
				 
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
		'''
		2018_05_07. we are removing the y value scales:
		'''
#		def is_valid_y( s_value ):
#			b_valid=False
#			if s_value == "NA":
#				b_valid=False
#			else:
#				f_value=float( s_value )
#				if f_value <= float( self.__scales[ 'y_value_upper' ].scale.get() ) \
#						and f_value >= float( self.__scales[ 'y_value_lower' ].scale.get() ):
#					b_valid= True
#				#end if float in range
#			#end if
#			return b_valid
#		#end local def is_valid_y
#	
#		self.__tsv_file_manager.setFilter( self.__comboboxes[ 'select_y_variable' ].current_value, 
#											 is_valid_y )
#
#		if self.__plotframe is not None:
#			self.__update_plot_and_stats_text()
#		#end if we have a plotframe, replot the data
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
		most likely as earliest->latest.

		We assume that this is called by a 
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
		#end if original file column
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

