'''
Description
A class to use  Brian T's Viz code to get regression 
quantities in order to use the data in a new embedded 
plot class.  The x value is resettable, but as in his 
code we default to the pop number as the x value.
'''

__filename__ = "pgregresser.py"
__date__ = "20171011"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import agestrucne.asnviz.LineRegress as vizlr

class PGRegresser( object ):
	'''
	A class to use  Brian T's Viz code to get regression 
	quantities in order to use the data in a new embedded 
	plot class.  The x value is resettable, but as in his 
	code we default to the pop number as the x value.
	'''
	def __init__( self,
					dltup_ne_x_and_y_values_by_group_name=None,
					s_expected_slope="auto", 
					dtup_individ_count_table=None ):
		'''
		arg dltup_ne_x_and_y_values_by_group_name, a dictionary
			of lists of duples, each duple the x value and y value,
			keyed to grouped tsv fields.
		arg s_expected_slope, the value passed to the 
			Viz._NeRegressionGraphCalc, arg "expectedSlope, used to 
			plot an "expected line" on the final plot.  if set to 
			"pop", then the individual count table is used to to 
			calculate an expected slope.  The slope is then passed
			to def _getExpectedLineStats.  If the expected slope 
			value is "auto", our default, then it is calc'd as the
			avg of the slopes of the regression lines.		
		arg dtup_individ_count_table, a dict keyed to grouped fields,
			giving a list of individual counts.  Note that in the 
			current state of the GUI interface, this dict always
			has lists with no items.  See Vis.FileIO.py, def
			scrapeNE.
		'''

		self.__expected_slope=s_expected_slope
		self.__individ_count_table=dtup_individ_count_table
		self.__ne_x_and_y_values_by_group_name=\
						dltup_ne_x_and_y_values_by_group_name
	
		'''
		This is the "lineVctrs" structure returned
		from the Viz.LineRegress def "_NeRegressionGraphCalc"
		See below, def __get_plotting_data
		'''
		self.__list_of_lists_of_regressed_x_and_y_values=None

		return
 	#end __init__

	def __get_plotting_data( self ):

		v_line_colors=None
		v_line_styles=None

		if self.__x_and_y_values_by_group_name is not None:
			idx_data=0
			idx_colors=1
			idx_styles=2

			tup_returnvals=\
						vizlr._NeRegressionGraphCalc( \
								self.__x_and_y_values_by_group_name,
												self.__expected_slope,
												self.__individ_count_table )

			self.__list_of_lists_of_regressed_x_and_y_values=tup_returnvals[ idx_data ]
			'''
			Note: currently we're ignoring the colors and styles values, preferring 
			for now to create these plotting params in a plotting class, such as
			PGPlottingFrameRegressionLinesFromFileManager.
			'''
		return
	#end __get_plotting_data

	def doRegression( self ):
		self.__get_plotting_data()
		return
	#end doRegression

	@property
	def x_and_y_values_by_group_name( self ):
		return self.__x_and_y_values_by_group_name
	#end property x_and_y_values_by_group_name

	@x_and_y_values_by_group_name.setter
	def x_and_y_values_by_group_name( self, dtup_vals ):
		self.__x_and_y_values_by_group_name=dtup_vals
		return
	#end x_and_y_values_by_group_name

	@property
	def regressed_x_and_y_values( self ):
		return self.__list_of_lists_of_regressed_x_and_y_values
	#end property regressed_x_and_y_values

#end class Regresser

if __name__ == "__main__":
	pass
#end if main

