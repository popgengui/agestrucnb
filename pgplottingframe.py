'''
Description
These classes provide tkinter frames that embed 
matplotlib plotting figures, with def do_animate
to update the figure.  The do_animate def is 
a wrapper for a client-supplied def.  Code to create
and animate was adapted from tutorial at
https://pythonprogramming.net/
plotting-live-bitcoin-price-data-tkinter-matplotlib/
?completed=/organizing-gui/
'''

#These are boilerplate for py2/py3 compatibility:
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import range

from tkinter import *
from tkinter.ttk import *

from natsort import realsorted

#These imports are from the
#URL tutorial (see Description above).
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import numpy as np
#For message to stderr in def, update_data_from_file:
import sys
#So that we can wait for a file to exist before 
#trying to open it in def, update_data_from_file.
import os

from pgguiutilities import FredLundhsAutoScrollbar
from pgneestimationtablefilemanager import NeEstimationTableFileManager
from pgregresser import PGRegresser

#For initializing boxplots when no data is available.
NO_BOXPLOT_DATA={ 'labels':["no_data"], 'value_lists':[[0]] }


#For using more readable aliases in place of tsv file col names:
COLNAME_ALIASES=\
		NeEstimationTableFileManager.COLUMN_NAME_ALIASES_BY_COLUMN_NAME
COLNAMES_BY_ALIASE=\
		NeEstimationTableFileManager.COLUMN_NAMES_BY_ALIAS

__filename__ = "pgplottingframe.py"
__date__ = "20170825"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

'''
Supporting class:
'''

class PGPlottingFrame( Frame ):
	def __init__( self, 
				o_master_frame=None,
				b_do_animate=True,
				tuple_args_for_animation_call=None,
				v_init_data=None,
				f_figure_width=5.0,
				f_figure_height=3.4,
				i_figure_dpi=100,
				i_ticklabelsize=8,
				i_labelfontsize=8,
				i_animate_interval=1000,
				s_xlabel="",
				s_ylabel="",
				s_zlabel=""):

		Frame.__init__( self, o_master_frame )

		self.__figure_width=f_figure_width
		self.__figure_height=f_figure_height
		self.__figure_dpi=i_figure_dpi
		self.__ticklabelsize=i_ticklabelsize
		self.label_fontsize=i_labelfontsize
		self.current_data=v_init_data
		self.__animate_interval=1000
		self.xlabel=s_xlabel
		self.ylabel=s_ylabel
		self.zlabel=s_zlabel
		self.__tuple_of_args_for_animation_call=tuple_args_for_animation_call
		self.__do_animate=b_do_animate
		#Assigned in make_figure def below.
		self.subplot=None
		self.__host_canvas=None
		self.__subframe=None

		self.__make_figure()
		self.__add_plotting_canvas()

		return
	#end __init__

	def __make_figure( self ):
		self.__figure=Figure( figsize=( self.__figure_width, self.__figure_height ), dpi=self.__figure_dpi )
		self.subplot=self.__figure.add_subplot(111)
		self.subplot.tick_params( axis='both', which='major', labelsize=self.__ticklabelsize )
		return
	#end __make_figure

	def __add_plotting_canvas( self ):

		o_scrolling_canvas=Canvas( self )
	
		self.__plotting_canvas=FigureCanvasTkAgg( self.__figure, o_scrolling_canvas )
		self.__plotting_canvas.get_tk_widget().pack( side = BOTTOM, fill=BOTH, expand=True )

		if self.__do_animate == True:

				self.__plot_animation=animation.FuncAnimation( self.__figure, 
														self.animate, 
														fargs=self.__tuple_of_args_for_animation_call, 
														interval=self.__animate_interval )
		#end if do animate

		o_scrolling_canvas.create_window( self.__figure_width, self.__figure_height, 
											window=self )
		o_scrolling_canvas.config( scrollregion=o_scrolling_canvas.bbox( ALL ) )
		self.__host_canvas=o_scrolling_canvas

		self.__host_canvas.grid( row=0, column=0 )
		
		self.grid_rowconfigure( 0, weight=1 )
		self.grid_columnconfigure( 0, weight=1 )

		self.__host_canvas.grid_rowconfigure( 0, weight=1 )
		self.__host_canvas.grid_columnconfigure( 0, weight=1 )

		#self.bind( '<Configure>', self.__on_configure_frame )

		return
	#end __add_plotting_canvas 

	def __on_configure_frame( self, event ):

		#we need the scroll region and the canvas dims to 
		#always match the subframe dims.
		q_size=( self.winfo_reqwidth(), self.winfo_reqheight() )
		self.__host_canvas.config( scrollregion="0 0 %s %s" % q_size )
		self.__host_canvas.config( width=q_size[ 0 ] )
		self.__host_canvas.config( height=q_size[ 1 ] )
		return
	#end __configure_subframe

	def animate( self, i_interval=None ):
		return
	#end do_animate

	def __save_plot_to_file( self, s_filename, s_type="png" ):
		if not( s_filename.endswith( ".png" ) or s_filename.endswith( ".pdf" ) ):
			s_filename=s_filename + ".png"
		#end if unknown image file type

		self.__figure.savefig( s_filename )
		return
	#end __save_plot_to_file

	def data( self ):
		return self.current_data
	#end current_data

	def updateData( self, v_data=None ):
		return
	#end updateData

	def savePlotToFile( self, s_filename ):
		self.__save_plot_to_file( s_filename )
		return
	#end savePlotToFile

	def setXLabel( self, s_label ):
		self.xlabel=s_label 
	#end x_label setter

	def setYLabel( self, s_label ):
		self.ylabel=s_label 
	#end y_label setter

	def resetFigureWidthAndHeight( self, f_width, f_height ):
		self.__figure_width=f_width
		self.__figure_width=f_height
		self.__make_figure()
		self.__add_plotting_canvas()
	#end setFigureWidthAndHeight
#end class PGPlottingFrame

class PGPlottingFrame2DLines( PGPlottingFrame ):

	MARKER_SIZE_PAD=3

	def __init__( self, 
					o_master_frame=None,
					tuple_args_for_animation_call=None,
					b_do_animate=True,
					v_init_data={ "x":None, "y":None },
					f_figure_width=5.0,
					f_figure_height=3.4,
					i_figure_dpi=100,
					i_ticklabelsize=8,
					i_labelfontsize=8,
					i_animate_interval=1000,
					s_xlabel="",
					s_ylabel="",
					f_plot_line_width=0.6,
					s_data_file=None,
					i_col_num_x_values=1,
					i_col_num_y_values=2,
					s_file_col_delimiter="\t" ):

		PGPlottingFrame.__init__ ( self, 
									o_master_frame=o_master_frame,
									b_do_animate=b_do_animate,
									tuple_args_for_animation_call=tuple_args_for_animation_call,
									v_init_data=v_init_data,
									f_figure_width=f_figure_width,
									f_figure_height=f_figure_height,
									i_figure_dpi=i_figure_dpi,
									i_ticklabelsize=i_ticklabelsize,
									i_labelfontsize=i_labelfontsize,
									i_animate_interval=i_animate_interval,
									s_xlabel=s_xlabel,
									s_ylabel=s_ylabel )
	
		
		self.__plot_line_width=f_plot_line_width
		self.__data_file=s_data_file
		self.__col_num_x_vals=i_col_num_x_values
		self.__col_num_y_vals=i_col_num_y_values
		self.__data_file_col_delimiter="\t"

	#end __init__

	def animate( self, i_interval=None ):

		MARGIN_ADJUST=0.2
		self.updateData()
		self.subplot.clear()
		self.subplot.set_xlabel(self.xlabel, fontsize=self.label_fontsize )
		self.subplot.set_ylabel( self.ylabel, fontsize=self.label_fontsize )
		self._PGPlottingFrame__figure.subplots_adjust(bottom=MARGIN_ADJUST)

		for s_line_name in self.current_data:

			lv_xvals=self.current_data[ s_line_name ][ "x" ]
			lv_yvals=self.current_data[ s_line_name ][ "y" ]

			self.subplot.plot( self.current_data[s_line_name ][ "x" ],
										self.current_data[ s_line_name ][ "y" ], 
										linewidth=self.__plot_line_width,
										markersize=self.__plot_line_width \
												+ PGPlottingFrame2DLines.MARKER_SIZE_PAD,
										linestyle='dashed', 
										marker='o'	)



		#end for each line, plot the line									

		if self._PGPlottingFrame__do_animate==False:
				self._PGPlottingFrame__figure.canvas.draw() 
		#end if no animation 
		return
	#end __animate

	def updateData( self ):
		if self.__data_file is not None:
			self.__update_data_from_file()
		return
	#end updateData

	def clearPlot( self ):
		if self.subplot is not None \
				and hasattr( self.subplot, "clear" ):
			self.subplot.clear()
		#end if subplot exists, has "clear" def
		return
	#end clearPlot

	def __update_data_from_file( self ):
		
		self.clearPlot()

		o_file=None	

		NO_DATA={ "line1": { "x":[], "y":[] } }

		
		self.current_data=NO_DATA

		'''
		We want this object to be able to wait
		for a file of data to be created and written to.
		'''
		if os.path.exists( self.__data_file ):
			o_file=open( self.__data_file )
			i_line_count=0

			for s_line in o_file:
				i_line_count+=1

				ls_values=s_line.strip().split( self.__data_file_col_delimiter )

				try:
					f_x = float( ls_values[ self.__col_num_x_vals - 1 ] ) 
					f_y = float( ls_values[ self.__col_num_y_vals - 1 ] )  

					self.current_data[ "line1" ][ "x" ].append( f_x )
					self.current_data[ "line1" ][ "y" ].append( f_y )
				except ValueError as ve:
					s_msg="In PGPlottingFrame2DLines instance, " \
							+ "def update_data_from_file, " \
							+ "reading file line: \"" \
							+ s_line.strip() + "\", columns " + str(self.__col_num_x_vals ) \
							+ " and " + str( self.__col_num_y_vals ) + ", " \
							+ "the program could not cast the values as numbers."

					sys.stderr.write( "Warning:  " + s_msg  + "\n" )
				#end if can't cast send message, try next
			#end for each line

			o_file.close()

		#end if the file exists, open it

		'''
		We need strictly increasing xvalues or the 
		plotted line can zigzag and cross itself.
		'''

		l_idx_sorted_on_xval=list( np.argsort( self.current_data[ "x" ] ) )

		lf_sorted_x=[ self.current_data["x"][idx] for idx in l_idx_sorted_on_xval ]
		lf_sorted_y=[ self.current_data["y"][idx] for idx in l_idx_sorted_on_xval ]

		dlv_sorted_data_in_file={ "x":lf_sorted_x , "y":lf_sorted_y } 

		self.current_data=dlv_sorted_data_in_file

		return	

	#end update_data_from_file
#end class PGPlottingFrame2DLines

class PGPlottingFrame2DLinesFromFileManager( PGPlottingFrame2DLines ):
	'''
	This class inherits most of its code from class PGPlottingFrame2DLines,
	but substitutes the file name with an object of type NeEstimationTableFileManager,
	and uses this object to get lists of data for plotting.  It is created to use along
	with classes like PGNeEstTableSelectionCombo to give users an interface in which
	they can see plots as they change the values used to filter the data.
	'''

	MARKER_SIZE_PAD=3

	def __init__( self, 
					o_master_frame=None,
					b_do_animate=True,
					o_tsv_file_manager=None,
					s_x_value_colname=None,
					s_y_value_colname=None,
					ls_group_by_column_names=None,
					def_to_convert_x_vals_to_numeric=None,
					def_to_convert_y_vals_to_numeric=None,
					tuple_args_for_animation_call=None,
					v_init_data={ "line1:":{ "x":None, "y":None } },
					f_figure_width=5.0,
					f_figure_height=3.4,
					i_figure_dpi=100,
					i_ticklabelsize=8,
					i_labelfontsize=8,
					i_animate_interval=1000,
					s_xlabel="",
					s_ylabel="",
					f_plot_line_width=0.6,
					s_data_file=None,
					i_col_num_x_values=1,
					i_col_num_y_values=2,
					s_file_col_delimiter="\t" ):

		'''
		Note that we don't use the s_data_file string,
		as the code that uses it in the parent class is
		overridden in this class.
		'''
		PGPlottingFrame2DLines.__init__( self,   
									o_master_frame=o_master_frame,
									b_do_animate=b_do_animate,
									tuple_args_for_animation_call=tuple_args_for_animation_call,
									v_init_data=v_init_data,
									f_figure_width=f_figure_width,
									f_figure_height=f_figure_height,
									i_figure_dpi=i_figure_dpi,
									i_ticklabelsize=i_ticklabelsize,
									i_labelfontsize=i_labelfontsize,
									i_animate_interval=i_animate_interval,
									s_xlabel=s_xlabel,
									s_ylabel=s_ylabel,
									f_plot_line_width=f_plot_line_width,
									s_data_file=None,
									i_col_num_x_values=i_col_num_x_values,
									i_col_num_y_values=i_col_num_y_values,
									s_file_col_delimiter=s_file_col_delimiter )

		self.__tsv_file_manager=o_tsv_file_manager	
		self.__x_val_column_name=s_x_value_colname
		self.__y_val_column_name=s_y_value_colname
		self.__group_by_column_names=ls_group_by_column_names
		self.__def_to_convert_x_values_to_numeric=def_to_convert_x_vals_to_numeric
		self.__def_to_convert_y_values_to_numeric=def_to_convert_y_vals_to_numeric

		return
	#end __init__

	def __update_data_from_file( self  ):

		dls_data_lines={}

		if self.__group_by_column_names is not None:
			dls_data_lines=\
				self.__tsv_file_manager.getGroupedDataLines( self.__group_by_column_names,
																[ self.__x_val_column_name,
																	self.__y_val_column_name ] )
		else:
			ls_data_lines=self.__tsv_file_manager.getFilteredTableAsList( \
													[ self.__x_val_column_name,
														self.__y_val_column_name ],
														b_skip_header=True )

			dls_data_lines=self.current_data={ "line1":ls_data_lines }
		#end if group-by columns else not

		s_delimiter=self._PGPlottingFrame2DLines__data_file_col_delimiter

		self.current_data= { s_line_name:{ "x":[], "y":[] } for s_line_name in dls_data_lines }
		
		for s_line_name in dls_data_lines:
			lf_these_x_vals=[]
			lf_these_y_vals=[]

			for s_line in dls_data_lines[ s_line_name ]:
				ls_values=s_line.strip().split( s_delimiter )

				try:
					if self.__def_to_convert_x_values_to_numeric is None:
						f_x = float( ls_values[ 0 ] ) 
					else:
						f_x = self.__def_to_convert_x_values_to_numeric( ls_values[0] ) 
					#end if no def to convert value, cast as float, else call def

					if self.__def_to_convert_y_values_to_numeric is None:
						f_y = float( ls_values[ 1 ] )  
					else:
						f_y = self.__def_to_convert_y_values_to_numeric( ls_values[ 1 ] )
					#end if no def to convert, then cast at float, else call def

					lf_these_x_vals.append( f_x )
					lf_these_y_vals.append( f_y )

				except ValueError as ve:
					s_msg="In PGPlottingFrame2DLinesFromFileManager instance, " \
							+ "def update_data_from_file, " \
							+ "reading file line: \"" \
							+ s_line.strip() \
							+ ", the program could not cast the values as numbers."

					sys.stderr.write( "Warning:  " + s_msg  + "\n" )
				#end if can't cast send message, try next
			#end foreach line of data for this line

			'''
			We need strictly increasing xvalues or the 
			plotted line can zigzag and cross itself.
			'''

			l_idx_sorted_on_xval=list( np.argsort( lf_these_x_vals ) )

			lf_sorted_x=[ lf_these_x_vals[idx] for idx in l_idx_sorted_on_xval ]
			lf_sorted_y=[ lf_these_y_vals[idx] for idx in l_idx_sorted_on_xval ]

			self.current_data[ s_line_name ][ "x" ]=lf_sorted_x 
			self.current_data[ s_line_name ][ "y" ] = lf_sorted_y

		#end for each line name

		return	
	#end update_data_from_file

	def updateData( self ):
		if self.__tsv_file_manager is not None:
			self.__update_data_from_file()
		#end if file manager is not none
		return
	#end updateData

	def setXValueColumnName( self, s_name ):
		self.__x_val_column_name=s_name
		return
	#end setXValueColumnName

	def setYValueColumnName( self, s_name ):
		self.__y_val_column_name=s_name
		return
	#end setXValueColumnNam

	def getXValueColumnName( self ):
		return self.__x_val_column_name
	#end setXValueColumnName

	def getYValueColumnName( self ):
		return self.__y_val_column_name
	#end setXValueColumnNam

#end class PGPlottingFrame2DLinesFromFileManager	

class PGPlottingFrameRegressionLinesFromFileManager( PGPlottingFrame2DLinesFromFileManager ):
	'''
	A child of class PGPlottingFrame2DLinesFromFileManager, this class plots data using 
	the data from a NeEstimationTableFileManager object, but processed through
	class PGRegresser to plot regression lines instead of a simple plotting of
	the x and y data points.  It further multiplexes the parent class data updates so
	that the date is grouped for each possible x-value. Thus essential difference 
	from the parent class is the both multiplexing processing of the x,y line data  
	delivered by the parent's "__update_data_from_file"  and then regressing on 
	the multi lines in def," __convert_tsv_line_data_to_regression_data."
	'''

	INPUT_FIELDS_ASSOC_WITH_ONE_ESTIMATE=\
			NeEstimationTableFileManager\
					.INPUT_FIELDS_ASSOC_WITH_ONE_ESTIMATE

	MARKER_SIZE_PAD=3

	def __init__( self, 
					o_master_frame=None,
					o_tsv_file_manager=None,
					b_do_animate=True,
					s_x_value_colname=None,
					s_y_value_colname=None,
					ls_group_by_column_names=None,
					def_to_convert_x_vals_to_numeric=None,
					def_to_convert_y_vals_to_numeric=None,
					tuple_args_for_animation_call=None,
					v_init_data={ "line1:":{ "x":None, "y":None } },
					f_figure_width=5.0,
					f_figure_height=3.4,
					i_figure_dpi=100,
					i_ticklabelsize=8,
					i_labelfontsize=8,
					i_animate_interval=1000,
					s_xlabel="",
					s_ylabel="",
					f_plot_line_width=0.6,
					s_data_file=None,
					i_col_num_x_values=1,
					i_col_num_y_values=2,
					s_file_col_delimiter="\t" ):

		'''
		Note that we don't use the s_data_file string,
		as the code that uses it in the parent class is
		overridden in this class.
		'''
		PGPlottingFrame2DLinesFromFileManager.__init__( self,   
									o_master_frame=o_master_frame,
									o_tsv_file_manager=o_tsv_file_manager,
									s_x_value_colname=s_x_value_colname,
									s_y_value_colname=s_y_value_colname,
									ls_group_by_column_names=ls_group_by_column_names,
									def_to_convert_x_vals_to_numeric=def_to_convert_x_vals_to_numeric,
									def_to_convert_y_vals_to_numeric=def_to_convert_y_vals_to_numeric,
									tuple_args_for_animation_call=tuple_args_for_animation_call,
									b_do_animate=b_do_animate,
									v_init_data=v_init_data,
									f_figure_width=f_figure_width,
									f_figure_height=f_figure_height,
									i_figure_dpi=i_figure_dpi,
									i_ticklabelsize=i_ticklabelsize,
									i_labelfontsize=i_labelfontsize,
									i_animate_interval=i_animate_interval,
									s_xlabel=s_xlabel,
									s_ylabel=s_ylabel,
									f_plot_line_width=f_plot_line_width,
									s_data_file=None,
									i_col_num_x_values=i_col_num_x_values,
									i_col_num_y_values=i_col_num_y_values,
									s_file_col_delimiter=s_file_col_delimiter )

		self.__mangledname="_PGPlottingFrame2DLinesFromFileManager__"
		return
	#end __init__

	def __do_have_tsv_file_and_field_names( self ):
		b_return_value=False
		ls_all_tsv_fields=list( NeEstimationTableFileManager\
				.COLUMN_NAME_ALIASES_BY_COLUMN_NAME.keys() )
		s_x_value_field_name=getattr( self, self.__mangledname + "x_val_column_name" )
		s_y_value_field_name=getattr( self, self.__mangledname + "y_val_column_name" )
		o_tsv_file_manager=getattr( self, self.__mangledname + "tsv_file_manager" )

		b_have_x_field=s_x_value_field_name in ls_all_tsv_fields
		b_have_y_field=s_y_value_field_name in ls_all_tsv_fields
		b_have_file_manager=o_tsv_file_manager is not None

		if b_have_x_field and b_have_y_field and b_have_file_manager:
			b_return_value=True
		#end if have all info

		return b_return_value
	#end __do_have_tsv_file_and_field_names

	def __update_data_from_file( self  ):

		NODATA={ "no_data":{ "x":[0], "y":[0] } }
		INSUFFDATA={ "insufficient_data":{ "x":[0], "y": [ 0 ] } }

		b_have_tsv_file_info=self.__do_have_tsv_file_and_field_names()
		
		if not b_have_tsv_file_info:
			self.current_data=NODATA
			return
		#end if we're missing required tsv info

		o_myc=PGPlottingFrameRegressionLinesFromFileManager

		o_tsv_file_manager=getattr( self, self.__mangledname + "tsv_file_manager" )

		ls_key_fields=[ s_field for s_field in 
				o_myc.INPUT_FIELDS_ASSOC_WITH_ONE_ESTIMATE ] 
		
		s_x_value_field_name=getattr( self, self.__mangledname + "x_val_column_name" )
		s_y_value_field_name=getattr( self, self.__mangledname + "y_val_column_name" )

		if s_x_value_field_name in ls_key_fields:
			ls_key_fields.remove( s_x_value_field_name )
		#end if our x value variable is in the key fields

		if s_y_value_field_name in ls_key_fields:
			ls_key_fields.remove( s_y_value_field_name )
		#end if our y value variable is in the key fields

		self.current_data=o_tsv_file_manager\
					.getDictDataLinesKeyedToColnames(\
											ls_key_column_names=ls_key_fields,
											ls_value_column_names=\
													[ s_x_value_field_name, s_y_value_field_name ],
											b_skip_header=True )


		##### temp
		s_msg=None
		if self.current_data is not None and len( self.current_data ) > 0:
			s_msg=str( list( self.current_data.values() )[0] ) 
		else:
			s_msg=str( self.current_data )

		print( "calling current_data_has... with first line data: " + s_msg )
		#####

		b_do_regression=self.__current_data_has_two_or_more_points_per_line_name() 
		
		if b_do_regression==True:
			self.__convert_tsv_line_data_to_regression_data()	
			self.__sort_current_data()
		else:
			self.current_data=INSUFFDATA
		#end if we have enough data to regress, else not
			
		return	
	#end update_data_from_file

	def __current_data_has_two_or_more_points_per_line_name( self ):

		b_all_data_has_at_least_two_points=False
		b_found_one_line_with_one_or_fewer_points=False
		b_data_present=self.current_data is not None \
							and len( self.current_data ) > 0 
		if b_data_present:
			for s_line_name in self.current_data:
				i_num_data_points=len( self.current_data[ s_line_name ] )
				if i_num_data_points < 2:
					b_found_one_line_with_one_or_fewer_points=True
					break;
				#end if number of points lt 2
			#end for each line
		#end if data is present

		if b_data_present == True \
				and b_found_one_line_with_one_or_fewer_points==False:
			b_all_data_has_at_least_two_points=True
		#end if no single point lines

		return b_all_data_has_at_least_two_points
	#end __current_data_has_at_least_two_data_points

	def __sort_current_data( self ):

		for s_line_name in self.current_data:

			lf_these_x_vals=self.current_data[ s_line_name ][ "x" ]
			lf_these_y_vals=self.current_data[ s_line_name ][ "y" ]

			l_idx_sorted_on_xval=list( np.argsort( lf_these_x_vals ) )

			lf_sorted_x=[ lf_these_x_vals[idx] for idx in l_idx_sorted_on_xval ]
			lf_sorted_y=[ lf_these_y_vals[idx] for idx in l_idx_sorted_on_xval ]

			self.current_data[ s_line_name ][ "x" ]=lf_sorted_x 
			self.current_data[ s_line_name ][ "y" ]=lf_sorted_y
		
		#end for each line name
	#end __sort_current_data

	def __get_regressed_data( self ):

		def_to_conv_x=getattr( self, self.__mangledname \
							+ "def_to_convert_x_values_to_numeric" )
		def_to_conv_y=getattr( self, self.__mangledname \
							+ "def_to_convert_y_values_to_numeric" )

		if def_to_conv_x is None:
			def_to_conv_x=lambda x : float(x)
		#end if def to convert x is none, cast as float

		if def_to_conv_y is None:
			def_to_conv_y=lambda x : float(x)
		#end if def to convert x is none, cast as float

		DELIMITER=NeEstimationTableFileManager.DELIM_TABLE
		o_regresser=PGRegresser()
		dltup_xy_by_group_name={}

		def convert_to_duple_numeric_pair( s_xy_val_string ):

			ls_vals=s_xy_val_string.split( DELIMITER )
			v_x=def_to_conv_x( ls_vals[0] )
			v_y=def_to_conv_y( ls_vals[1] )

			return ( v_x, v_y ) 

		#end convert_to_duple_numeric_pair

		dltup_data_converted_for_regression={}	
		for s_line_name in self.current_data:
			ls_xy_strings=self.current_data[ s_line_name ]
			ls_xy_tuples=[ convert_to_duple_numeric_pair( s_xy ) \
											for s_xy in ls_xy_strings ]
			dltup_xy_by_group_name[ s_line_name ]=ls_xy_tuples
		#end for each line name
		o_regresser.x_and_y_values_by_group_name=dltup_xy_by_group_name

		o_regresser.doRegression()
	
		lltup_regressed_data=o_regresser.regressed_x_and_y_values

		return lltup_regressed_data
	#end __get_regressed_data	

	def __convert_regression_data_back_to_plotting_format( self,
													lltup_regressed_data ):
		ddf_regressed_data={}

		ls_linenames=list( self.current_data.keys() )

		idx_this_line=0

		##### temp
#		i_num_lines=len( ls_linenames )
#		print( "current data keys: " + str( ls_linenames ) )
#		#print( "i_num_lines: " + str( i_num_lines ) )
#		print( "num xysets: " + str( len( lltup_regressed_data ) ) )
		#####
		
		i_regress_data_count=0
		
		for ltup_xyvals in lltup_regressed_data:

			i_regress_data_count+=1

			##### temp
#			print( "line number idx: " + str( idx_this_line ) )
			#####

			ltup_unzipped=zip( *ltup_xyvals )

			'''
			Note that py3 and py2 treat zip objects differently.
			Py3 zipped objects loose their data after an operation
			that converts it.  Hence, at earliest convenience we 
			convert it to a list of tuples, which will persist.
			'''
			ltup_vals=list( ltup_unzipped )

			dl_xyvals={ "x":list( ltup_vals[ 0 ] ),
									"y":list( ltup_vals[ 1 ] ) }

			'''
			Note that I need to recheck but I think the first 
			line of regressed data comes from the expected slope 
			(Need to recheck Viz.Linegregress._NeRegressionGraphCalc). 
			I have seen in any case that the regression returns 
			one more set of line data than is delivered to the 
			_NeRegressionGraphCalc.
			'''
			if i_regress_data_count == 1:
				
				ddf_regressed_data[ "expected" ]=dl_xyvals
			else:
				s_this_line_name=ls_linenames[ idx_this_line ]

				ddf_regressed_data[ s_this_line_name ] = dl_xyvals
								
				idx_this_line+=1
			#end if first set of regress data else noe
		#end for each list of regression xy tuples	

		return ddf_regressed_data
	#end __convert_regression_data_back_to_plotting_format

	def __convert_tsv_line_data_to_regression_data( self ):

		if self.current_data is not None:

			lltup_regressed_data=self.__get_regressed_data()

			self.current_data=\
					self.__convert_regression_data_back_to_plotting_format( \
															lltup_regressed_data )
			
		#end if we have current data
		return
	#end __convert_tsv_line_data_to_regression_data

	def updateData( self ):
		o_tsv_file_manager=getattr( self, self.__mangledname + "tsv_file_manager" )
		if o_tsv_file_manager is not None:
			self.__update_data_from_file()
		#end if file manager is not none
		return
	#end updateData
#end class PGPlottingFrameRegressionLinesFromFileManager

class PGPlottingFrameBoxplot( PGPlottingFrame ):

	def __init__( self, 
					o_master_frame=None,
					tuple_args_for_animation_call=None,
					v_init_data={ 'labels':["no_data"], 'value_lists':[[0]] },
					f_figure_width=5.0,
					f_figure_height=3.4,
					i_figure_dpi=100,
					i_ticklabelsize=8,
					i_labelfontsize=8,
					i_animate_interval=1000,
					s_xlabel="",
					s_ylabel="",
					f_plot_line_width=0.6,
					s_data_file=None,
					i_col_num_x_values=1,
					i_col_num_y_values=2,
					s_file_col_delimiter="\t" ):

		PGPlottingFrame.__init__ ( self, 
							o_master_frame=o_master_frame,
							tuple_args_for_animation_call=tuple_args_for_animation_call,
							v_init_data=v_init_data,
							f_figure_width=f_figure_width,
							f_figure_height=f_figure_height,
							i_figure_dpi=i_figure_dpi,
							i_ticklabelsize=i_ticklabelsize,
							i_labelfontsize=i_labelfontsize,
							i_animate_interval=i_animate_interval,
							s_xlabel=s_xlabel,
							s_ylabel=s_ylabel )
		
		self.__plot_line_width=f_plot_line_width
		self.__data_file=s_data_file
		self.__col_num_x_vals=i_col_num_x_values
		self.__col_num_y_vals=i_col_num_y_values
		self.__data_file_col_delimiter="\t"

		'''
		This value is used to make space for the xlabel.
		It is referenced in def "animate" and adjusted
		in def __adjust_bottom_margin.
		'''

		self.__subplot_bottom_margin_adjust=0.2

	#end __init__

	def animate( self, i_interval=None ):
		'''
		After reading https://stackoverflow.com/
		questions/18795172/ using-matplotlib-and-ipython-how-to-reset-x-and-y-axis-limits-to-autoscale,
		found that clf allows the autoscaling to be reinitialized for each
		animation.
		'''
		self.__figure.clf()
		self.updateData()

		self.subplot.clear()

		self.subplot.set_xlabel(self.xlabel, fontsize=self.label_fontsize )
		self.subplot.set_ylabel( self.ylabel, fontsize=self.label_fontsize )
		self.subplot.boxplot( x=self.current_data[ 'value_lists' ],
									labels=self.current_data[ 'labels' ] )
		return
	#end animate

	def updateData( self, v_data=None ):
		if v_data is not None:
			self.current_data=v_data
		else:
			pass
		#end if data passed as arg
		return
	#end updateData

#end class PGPlottingFrameBoxplot

class PGPlottingFrameBoxplotFromFileManager( PGPlottingFrame ):

	def __init__( self, 
					o_master_frame=None,
					tuple_args_for_animation_call=None,
					b_do_animate=True,
					o_tsv_file_manager=None,
					ls_group_by_column_names=None,
					s_y_value_colname=None,
					def_to_convert_labels=None,
					v_init_data=NO_BOXPLOT_DATA,
					f_figure_width=5.0,
					f_figure_height=3.4,
					i_figure_dpi=100,
					i_ticklabelsize=8,
					i_labelfontsize=8,
					i_animate_interval=1000,
					s_xlabel="",
					s_ylabel="",
					f_plot_line_width=0.6,
					s_data_file=None,
					i_col_num_x_values=1,
					i_col_num_y_values=2,
					s_file_col_delimiter="\t"):
		'''
		Arg def_to_convert_labels expects a ref to a def
		that takes as the first arg the self.current_data[ 'labels' ]
		list, and as the second arg the sorted version of the sting list 
		given by self.__group_by_column_names.
		'''

		PGPlottingFrame.__init__ ( self, 
							o_master_frame=o_master_frame,
							tuple_args_for_animation_call=tuple_args_for_animation_call,
							b_do_animate=b_do_animate,
							v_init_data=v_init_data,
							f_figure_width=f_figure_width,
							f_figure_height=f_figure_height,
							i_figure_dpi=i_figure_dpi,
							i_ticklabelsize=i_ticklabelsize,
							i_labelfontsize=i_labelfontsize,
							i_animate_interval=i_animate_interval,
							s_xlabel=s_xlabel,
							s_ylabel=s_ylabel )
		
		self.__plot_line_width=f_plot_line_width
		self.__data_file=s_data_file
		self.__col_num_x_vals=i_col_num_x_values
		self.__col_num_y_vals=i_col_num_y_values
		self.__data_file_col_delimiter="\t"

		self.__tsv_file_manager=o_tsv_file_manager
		self.__group_by_column_names=ls_group_by_column_names
		self.__y_value_column_name=s_y_value_colname
		self.__def_to_convert_labels=def_to_convert_labels

	#end __init__

	def animate( self, i_interval=None ):

		self.updateData()
		self.subplot.clear()

		if len( self.current_data[ 'labels' ] ) > 0:
			self.__set_x_axis_margin_and_xtick_rotation()
			self.subplot.set_xlabel(self.xlabel, fontsize=self.label_fontsize )
			self.subplot.set_ylabel( self.ylabel, fontsize=self.label_fontsize )
			self.subplot.boxplot( x=self.current_data[ 'value_lists' ],
										labels=self.current_data[ 'labels' ] )
			if self._PGPlottingFrame__do_animate==False:
				#self.subplot.draw( renderer=self._PGPlottingFrame__figure.canvas.draw() )
				self._PGPlottingFrame__figure.canvas.draw() 
			#end if no animation 
		else:
			self.__set_x_axis_margin_and_xtick_rotation()
			self.subplot.set_xlabel(self.xlabel, fontsize=self.label_fontsize )
			self.subplot.set_ylabel( self.ylabel, fontsize=self.label_fontsize )

			self.subplot.boxplot( x=NO_BOXPLOT_DATA[ 'value_lists' ],
										labels=NO_BOXPLOT_DATA[ 'labels' ] )
			if self._PGPlottingFrame__do_animate==False:
				#self.subplot.draw( renderer=self._PGPlottingFrame__figure.canvas.draw() )
				self._PGPlottingFrame__figure.canvas.draw() 
			#end if no animation 

		#end if we have at least one data set
		return
	#end __animate

	def __set_x_axis_margin_and_xtick_rotation( self ):

		MAX_LABEL_LEN=10

		NO_ROTATION=0
		SLIGHT_ROTATION=10
		HALF_ROTATION=30

		NORMAL_X_MARGIN_ADJUST=0.2
		HIGH_X_MARGIN_ADJUST=0.3

		SHORT_LABEL=4

		HIGH_LABEL_COUNT=25
		HIGH_LABEL_COUNT_ANGLE=60
		HIGH_LABEL_COUNT_MARGIN_ADJ=0.2

		li_rotation_by_length=[ NO_ROTATION for i_length in range( SHORT_LABEL ) ]
		li_rotation_by_length += [ HALF_ROTATION for i_length in range( SHORT_LABEL + 1, MAX_LABEL_LEN + 1 ) ]

		'''
		Convenience local def:
		'''
		def mylengetter( s_label ):
			return 0 if s_label=='' else len( s_label )
		#end mylengetter

		if len( self.current_data[ 'labels' ] ) == 0:
			i_len_longest_label=0
		else:
			i_len_longest_label=max( [ mylengetter(s_label) \
					for s_label in self.current_data[ 'labels' ] ] )
		#end if we have no data sets, else at least 1

		if i_len_longest_label > MAX_LABEL_LEN:
			self.__bottom_margin_adjustment=HIGH_X_MARGIN_ADJUST
			self.__xtick_rotation_angle=SLIGHT_ROTATION
		else:
			self.__bottom_margin_adjustment=NORMAL_X_MARGIN_ADJUST
			self.__xtick_rotation_angle=li_rotation_by_length[ i_len_longest_label - 1 ]
		#end if length longer than max, else not

		if len( self.current_data[ 'labels' ] ) >= HIGH_LABEL_COUNT:
			##### temp
		#	print( "adjusting for high label count" )
			#####
			self.__xtick_rotation_angle = HIGH_LABEL_COUNT_ANGLE
			self.__bottom_margin_adjustment += HIGH_LABEL_COUNT_MARGIN_ADJ
		#end if lots of xtick labels, adjust the rotation angle

		self._PGPlottingFrame__figure.subplots_adjust(bottom=self.__bottom_margin_adjustment)

		o_xticklabels=self._PGPlottingFrame__figure.get_axes()[0].set_xticklabels( 
														self.current_data[ 'labels' ], 
														rotation = self.__xtick_rotation_angle, ha="right")
		return
	#end __set_x_axis_margin_and_xtick_rotation

	def __update_data_from_file_manager( self ):

		dls_data_lines=\
				self.__tsv_file_manager.getGroupedDataLines( \
											self.__group_by_column_names,
												[ self.__y_value_column_name ] )

		self.current_data[ 'labels'] = []

		self.current_data[ 'value_lists' ]=[ [] for idx in dls_data_lines ] 
		
		i_idx_grouping=-1

		for s_group_label in dls_data_lines:

			i_idx_grouping += 1

			self.current_data[ 'labels' ].append( s_group_label )

			for s_value in dls_data_lines[ s_group_label ]:
				try:
					f_yvalue=float( s_value ) 
				except ValueError as ove:
					s_msg="In PGPlottingFrameBoxplotFromFileManager instance, " \
								+ "def __update_data_from_file_manager, " \
								+ "the program could not convert a y value to a float: " \
								+ s_value  + "."
					raise Exception( s_msg )
				#end try...except...

				self.current_data[ 'value_lists' ][ i_idx_grouping ].append( f_yvalue )

			#end for each value for this grouping
		#end for each grouping

		ls_sorted_groupby_column_names=None if self.__group_by_column_names is None \
							else sorted( self.__group_by_column_names ) 

		self.__remove_empty_data_lists()

		self.__sort_data_by_label_order()

		if self.__def_to_convert_labels is not None:
			self.__def_to_convert_labels( self.current_data[ 'labels' ], 
										ls_sorted_groupby_column_names )
		#end if client wants some label processing

		return
	#end __update_data_from_file_manager

	def __remove_empty_data_lists( self ):

		ls_labels_with_data=[]
		llv_data_lists_with_values=[]
		for idx in range( len( self.current_data[ 'labels' ] ) ):
			if len( self.current_data[ 'value_lists' ][idx] ) > 0:
				ls_labels_with_data.append( self.current_data[ 'labels' ][ idx ] )
				llv_data_lists_with_values.append( self.current_data[ 'value_lists' ][ idx ] )
			#end if length of this list gt 0
		#end for each index

		self.current_data[ 'labels' ] = ls_labels_with_data
		self.current_data[ 'value_lists' ] = llv_data_lists_with_values

		return
	#end __remove_empty_data_lists

	def __sort_data_by_label_order( self ):
		'''
		Uses the natsort package's realsorted
		to sort strings such that substrings that are 
		numeric values are sorted in numeric order, 
		and non-numeric substrings sorted lexigraphically.
		'''

		ls_natsorted_labels=realsorted( self.current_data[ 'labels' ] )

		l_idx_labels_sorted=[ self.current_data[ 'labels' ].index( s_label ) \
						for s_label in ls_natsorted_labels ]

		
		ls_sorted_labels=[ self.current_data[ 'labels' ][idx] for idx in l_idx_labels_sorted ]
		ls_sorted_value_lists=[ self.current_data[ 'value_lists' ][idx] for idx in l_idx_labels_sorted ] 
		
		self.current_data[ 'labels' ] = ls_sorted_labels
		self.current_data[ 'value_lists' ] = ls_sorted_value_lists
		return
	#end __sort_data_by_label_order

	def __adjust_bottom_margin( self ):
		self.__get_longest_label()
		
		return
	#end __adjust_bottom_margin

	def __get_longest_label( self ):
		return
	#end __get_longest_label

	def updateData( self, v_data=None ):

		if self.__tsv_file_manager is not None:
			self.__update_data_from_file_manager()
		else:
			pass
		#end if data passed as arg
		return
	#end updateData

	def setGroupByColumnNames( self, ls_group_by_column_names ):
		self.__group_by_column_names=ls_group_by_column_names 
		return
	#end setGroupByColumnNames

	def setYValueColumnName( self, s_column_name ):

		self.__y_value_column_name=s_column_name

		return
	#end y_value_column_name setter

#end class PGPlottingFrameBoxplotFromFileManager

if __name__ == "__main__":

	import time
	import pgneestimationtablefilemanager as pgnfm

#	s_tsv_file="/home/ted/documents/source_code/python/negui/temp_data/fig_1_for_luikart_draft/mosquito/nb50.chubachi/1k_genepops_randomly_selected/ldne.tsv"
	s_tsv_file="/home/ted/documents/source_code/python/negui/temp_data/t2.nb.ldne.tsv"
	o_tsv=pgnfm.NeEstimationTableFileManager( s_tsv_file )

	o_tsv.setFilter( 'ne_est_adj', lambda x:abs(float(x))<100 )

	mym=Tk()
#	op=PGPlottingFrame2DLines( o_master_frame=mym, 
#						s_data_file="/home/ted/temp/mydat",
#						s_xlabel="xvalues",
#						s_ylabel="yvalues" )

	op=PGPlottingFrameBoxplotFromFileManager( o_master_frame=mym,
									tuple_args_for_animation_call=None,
									o_tsv_file_manager=o_tsv,
									ls_group_by_column_names=[ 'original_file', 'pop' ],
									s_y_value_colname='ne_est_adj' )
		
	
	op.grid()

	mym.mainloop()

	pass
#end if main

