'''
Description
To adapt Brian T's regressions stats code
to our new plotting interface, we revise
his _NeStatsHelper funcion to deliver a Table
string that we can write to a GUI object.
'''
from __future__ import division
from __future__ import print_function
#created by Brian Trethewey
#
#neGrapher is primary interface for graphing data
#neStats is primary interface for creating statistics output file for a dataset

from future import standard_library
standard_library.install_aliases()
from builtins import object
from past.utils import old_div

__filename__ = "pgregressionstats.py"
__date__ = "20171016"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os
import sys

from numpy import mean, median, isnan
from scipy import stats

'''
Now using revised versions of the viz files
from Brian T, so that slopeConfidence 
is now slope_confidence:
'''
#from agestrucne.asnviz.LineRegress import slopeConfidence
from agestrucne.asnviz.LineRegress import slope_confidence, alpha_test, calculate_s_score

from agestrucne.pgneestimationtablefilemanager import NeEstimationTableFileManager

'''
For an expected line regression comparison, 
we now use this class to get an object
with the needed values for a slope comparison
see def __get_stats_as_string:
'''
from agestrucne.pglinearregressionmanager import PGLinearRegressionManager
from agestrucne.pglinearregressionmanager import FTestInputError

class PGRegressionStats( object ):
	'''
	2018_11_04.  Revising the code to compute a sig. value for the
	slopes of the regression lines, given a non-zero expected slope.
	This is so that users can see whether the Nb estimates generated
	a regression, for example, whose slope is significantly different
	from a simulated Nb deline at some rate r.  Our null hypothesis,
	then for testing the slope of such a regression is the the slope=r.
	'''
	def __init__( self, 
					dltup_table=None,
					f_confidence_alpha=0.05,
					v_significant_value=0,
					f_expected_slope=0.0,
					o_expected_line_manager=None ):
		'''
		2018_11_11.  we add the o_expetced_line_manager
		parameter, so that we can add to the stats
		a new per-regression p-value based on comparing 
		the slope of a given regression line to the slope
		of a line computed by the expected_line_manager
		object. 
		'''
		self.__data_table=dltup_table
		self.__confidence_alpha=f_confidence_alpha
		self.__significant_value=v_significant_value
		self.__expected_line_manager=o_expected_line_manager
		return
	#end __init__

	def __get_printable_value_none_or_float( self, v_value, f_precision ):
		'''
		Allows rounding a float for printing, but
		returning None if the arg is not a roundable
		object.
		'''
		v_rounded=None
		try:
			v_rounded=round( v_value, f_precision )
		except ValueError as ove: 
			pass
		except TypeError as ote:
			pass
		#end try...except

		return v_rounded
	#end __get_printable_value_none_or_float

	def __get_y_values_for_a_zero_slope_null_hypo( self, ltup_x_and_y_values ):
		'''
		this will be an indirect way of essentially adjusting the
		regression to accomodate an H_0 of b=0 when we have a non-
		zero expected slope.  When the expected slope is zero we
		just return a copy of thej x and y values.  However,
		when non-zero we make an algebraic
		transformation to restate a non-zero hypo
		as a zero:
			let b=r, 
			r=any expected slope (non-zero for the non-trivial
			example):
				y=bx+c=>y-rx=(b-r)x+c
				so we can check for H0: b'= 0 using
				y'= b'x + c, with y'=y-rx
		See http://www.real-statistics.com/regression/
		hypothesis-testing-significance-regression-line-slope/
		'''

		IDX_X=0
		IDX_Y=1

		if len( x_values ) != len( y_values ):
			s_msg="In PGRegressionStats, def " \
					+ "__get_y_values_for_a_zero_slope_null_hypo "
		FLOAT_PRECISE=float( 1e-32 )

		ltup_x_and_recomputed_y_values=[]

		if abs( self.__expected_slope - 0.0 ) > FLOAT_PRECISE:
			ltup_x_and_recomputed_y_values=y_values
		else:
			
			for  tup_x_and_y in ltup_x_and_y_values:
				'''
				new y value, y'=y-rx, where r is our expected slope.
				'''
				f_new_y_value=\
						tup_x_and_y[IDX_Y] \
						- self.__expected_slope* tup_x_and_y[ IDX_X ]

				tup_new_xy=( tup_x_and_y[ IDX_X ], f_new_y_value )

				ltup_x_and_recomputed_y_values.append( tup_new_xy )
			#end for each x,y tuple

		#end if expected slope zero, no transformation needed, else transform
		
		return ltup_x_and_recomputed_y_values
	#end __get_y_values_for_a_zero_slope_null_hypo

	def __get_source_file_name_from_file_manager_key( self, s_field_values ):
		'''
		This def assumes that the first field,
		as delimited by the concatenated field 
		values delivered by the NeEstimationTableFileManager,
		def getDictDataLinesKeyedToColnames,
		(currently double underscore, __), will be 
		the source genepop file name, full path, which we
		reduce to file name only.
		'''
	
		IDX_FILE_NAME=0

		FIELDDELIM=NeEstimationTableFileManager.DELIM_GROUPED_FIELD_NAMES

		ls_values=s_field_values.split( FIELDDELIM )
		
		s_file_with_path=ls_values[ IDX_FILE_NAME ]	

		s_file_name=os.path.basename( s_file_with_path )

		return s_file_name
	#end __get_source_file_name_from_file_manager_key

	def __data_is_sufficient_for_regression(self):
		b_return_value=False
		if self.__data_table is not None:
			if len( self.__data_table ) > 0:
				b_all_lines_have_sufficient_data=True
				for s_key in self.__data_table:
					if len( self.__data_table[ s_key ] ) < 2:
						b_all_lines_have_sufficient_data=False
						break
					#end if length under two
				#end for each key
				if b_all_lines_have_sufficient_data==True:
					b_return_value=True
				#end if all lines had enough data
			#end there is at least one line
		#end if there is a data table

		return b_return_value
	#end __data_is_sufficient_for_regression

	def __get_expected_line_slope_comparison_info( self, ltup_xy ):

		lf_xvals=[ tup_record[0] for tup_record in ltup_xy ]
		lf_yvals=[ tup_record[1] for tup_record in ltup_xy ]

		o_my_regress=PGLinearRegressionManager( s_line_name="regression",
												lv_x_values=lf_xvals,
												lv_y_values=lf_yvals,
												s_line_style="solid", 
												s_line_color="black",
												f_line_width_adjust=1.0  )
		o_my_regress.doRegression()

		f_p_value=self.__expected_line_manager.getPValueComarisonOfSlopes( \
									f_other_slope=o_my_regress.slope,
									f_other_intercept=o_my_regress.intercept,
									f_other_slope_standard_error=o_my_regress.slope_std_error, 
									lf_other_x_values=o_my_regress.x_values,
									f_other_residual_se=o_my_regress.residual_standard_error )

		

		return f_p_value
	#end __get_expected_line_slope
		
	def __get_stats_as_string( self, b_use_file_name_only_for_column_1=True ):
		'''
		Most of this code is copied directly from Brian's
		def in Viz.LineRegress._neStatsHelper.
		'''
		PRECISION=3
		STATS_TABLE_DELIM="\t"

		'''
		2018_04_11.  Using the bullet character causes some OS 
		python installs to throw  the unicode-to-ascii error, 
		but not in others. Here I take the lazy way out by using 
		an asterisk instead.
		'''
#		BULLET=u'\u2022'
		BULLET="*"
		BULLET_INDENTED="    " + BULLET + " "

		s_return=None

		b_data_is_sufficient=self.__data_is_sufficient_for_regression()

		if b_data_is_sufficient:
			table=self.__data_table
			#tableFormat = "{:<30}{:<30}{:<50}{:<80}\n"
			confPercent = (1.0 - self.__confidence_alpha)*100.0
			tableString="-----Table of per-line values-----\n"

			'''
			2018_03_17.  Brian T has revised his def _neStatsHelper to
			include a p-value. We accordingly modify this def to include
			his revisions.
			'''
			tableString+=STATS_TABLE_DELIM.join( [ "Source",
													"Slope",
													"Intercept" ,
													"CI("+str(confPercent)+"%)", 
													"P-value",
													"P-value-expected-slope",
													"\n" ] )
			slopeVctr = []
			confidenceVctr = []
			alpha_vctr=[]
			s_score_vctr=[]

			Uncountable = 0
			'''
			2018_04_11.  Revisions as posted by Brian T to
			repository today or yesterday.
			'''
			negativeCount=0
			zeroCount=0
			positiveCount=0
			'''
			end revisions
			'''

			ls_keys_sorted=sorted( list(table.keys()) )

			i_sum_slope_comparison_reject_null=0
			i_sum_slope_comparisons=0

			for recordKey in ls_keys_sorted:
				#Reminder:  "record" is a list of (x,y) duples.

				record = table[recordKey]


				s_file_name=recordKey
				
				if b_use_file_name_only_for_column_1:
					s_file_name=self.__get_source_file_name_from_file_manager_key( recordKey )
				#end if not b_use_all_key_fields

				'''
				2018_11_18.  I added the flag for returning standard error to the
				def in asnviz/LineRegress.py:
				'''
				v_return_slope_conf=slope_confidence( self.__confidence_alpha,
															record, 
															b_return_slope_standared_error=True)

				'''
				2018_11_11. I add f_std_err, for expected line manager -- see also
				my addition of the std err value to the return tuple in the LineRegress.py mod,
				def slope_confidence.
				'''
				slope=None; intercept=None; confidence=None; f_std_err=None

				ls_vals_for_table=None

				if type( v_return_slope_conf ) == tuple:
					#We assume we got numbers if a tuple was returned.
					slope, intercept, confidence, f_std_err  = v_return_slope_conf 
					'''
					2018_03_17.  New code from Brian T's 
					latest _neStatsHelper
					'''
					# perform alpha test
					alpha_result = alpha_test(self.__significant_value, record)
					if alpha_result == 0:
						alpha_vctr.append(0)
					elif slope > 0:
						alpha_vctr.append(1)
					else:
						alpha_vctr.append(-1)

					#get std dev estimate
					s_val = calculate_s_score(record)
					s_score_vctr.append(s_val)
					t_star = old_div(slope,s_val)
					#calculate p value DF = num points-2
					p_score = stats.t.sf(t_star,len(record)-2)

					'''
					2018_04_11.  From Brian T's revisions as
					posted to master repository today or yesterday.
					'''
					#calculate significant from CDF(p-value)
					alpha_check = 1-(abs(p_score-0.5)*2)
					if self.__confidence_alpha > alpha_check:
						if slope > 0:
							positiveCount+=1
						else:
							negativeCount+=1
					else:
						zeroCount+=1

					#end if confidence alpha > alpha check
					'''
					End revisions 2018_04_11.
					'''
					 
					'''
					Note that the "float" cast was need (at least in py3 ), 
					else negative numbers don't get rounded.
					'''
					ls_rounded_confidence=[ str( round( float( v_val ) , PRECISION ) )  \
																for v_val in confidence  ]
					s_rounded_confidence=", ".join( ls_rounded_confidence  )

					s_rounded_confidence="(" +  s_rounded_confidence + ")"

					'''
					2018_11_11.  We add a p-value for the comparison
					of the slope of current line to an expected slope.
					'''
					f_p_value_slope_comparison=None

					if self.__expected_line_manager is not None:

						if self.__expected_line_manager.hasRegressionInfo():

							'''
							Default values loaded into interface give zero rate and zero
							initial y value, for which regression we will not do a slope comparison.
							'''
							lb_all_zeros=[ f_val<=PRECISION for f_val in self.__expected_line_manager.y_values ]

							if sum( lb_all_zeros ) != len ( lb_all_zeros ):

								try:
									f_p_value_slope_comparison=self.__get_expected_line_slope_comparison_info( record )
								except FTestInputError as fte:

									sys.stderr.write( "The program is skipping the regression slope comparison " \
														 + "due to a problem with the statistical tests: " \
														 + str( fte ) + "\n" )
								#end try ... except

								if f_p_value_slope_comparison is not None:
									i_sum_slope_comparisons+=1

									'''
									2018_11_24. We'll use the same threshold (user settable in the 
									PGNeEstimationRegressplotInterface instances) for CI intervals in
									Brian's CI calc, as the p-value threshold.
									'''
									if f_p_value_slope_comparison <= self.__confidence_alpha:
										i_sum_slope_comparison_reject_null += 1
									#end if sig value
								#end if we got a non-None return p-value

								
							else:
								##### temp
								#print( "Skipping slope comparison p-value:  all expected line y-values are zeros" )
								#####
								pass
							#end if we have fit regression info  for the expected line, else skip slope comapare
						else:
							##### tempo
							#print( "Skipping slope comparison p-value, with no expected line fit y values" )
							#####
							pass
						#end if the expected line values are not all zeros, else skip slope compare
					else:
						##### temp
						#print( "Skipping slope comparison p-value because expected line manager is None" )
						#####
						pass
					#end if we have an expected line manager, else skip slope compare

					f_printable_pval_expected_line_slope_comaparison=\
										self.__get_printable_value_none_or_float( \
															f_p_value_slope_comparison, PRECISION )

					ls_vals_for_table=[ s_file_name,
											str( round( slope, PRECISION ) ),  
											str( round( intercept, PRECISION ) ) ,  
											s_rounded_confidence, 
											str( round( p_score, PRECISION) ),
											str( f_printable_pval_expected_line_slope_comaparison ),
											"\n" ]
					if isnan(slope):
						Uncountable +=1
					else:
						slopeVctr.append(slope) 
						confidenceVctr.append(confidence)
					#end if isnan

				else:

					ls_vals_for_table=[ s_file_name, "NA", "NA", "NA", "NA","\n" ]

				#end if slopeConf returned a tuple or couldn't compute
				
				tableString+=STATS_TABLE_DELIM.join( ls_vals_for_table )
				
			#end for each recordKey

			if len( slopeVctr ) == 0:
				
				s_return= "Insufficient data."

			else:	

				maxSlope = max(slopeVctr)
				minSlope = min(slopeVctr)
				meanSlope = mean(slopeVctr)
				medSlope = median(slopeVctr)

				'''
				2018_03_17. New quantity from Brian T's new
				version:
				'''
				averageSscore=mean( s_score_vctr )

				'''
				2018_04_11.  These assignments form the 2018_03_17
				are now commented out, by Brian T's revisions
				from today or yesterday:
				'''
#				negativeCount=0
#				zeroCount=0
#				positiveCount=0

				'''
				2018_03_17 Remmed out and replaced by new code 
				by Brian T:
				'''
	#			for cI in confidenceVctr:
	#				if cI[0]>self.__significant_value:
	#					positiveCount+=1
	#				elif cI[1]<self.__significant_value:
	#					negativeCount+=1
	#				else:
	#					zeroCount+=1
	#			#end for each cI
				#change for alpha test
				'''
				2018_04_11. Change from 2018_03_17,
				this for loop is now commented out.
				'''
#				for value in alpha_vctr:
#					if value>0:
#						positiveCount+=1
#					elif value<0:
#						negativeCount+=1
#					else:
#						zeroCount+=1
					#end if val>0 else less else
				#end for alpha val

				f_slope_expected_slope=self.__get_printable_value_none_or_float( \
																self.__expected_line_manager.slope, PRECISION )
				f_confidence_alpha=self.__get_printable_value_none_or_float( self.__confidence_alpha, PRECISION )
				f_intercept_expected_slope=self.__get_printable_value_none_or_float( \
																self.__expected_line_manager.intercept, PRECISION )
				
				
				s_stats_string = "Max Regression Slope: "+str( round( maxSlope, PRECISION ) )+"\n"
				s_stats_string +="Min Regression Slope: "+str( round( minSlope, PRECISION ) )+"\n"
				s_stats_string +="Mean Regression Slope: " +str( round( meanSlope, PRECISION ) )+"\n"
				s_stats_string +="Median Regression Slope: "+str( round( medSlope, PRECISION ) )+"\n"
				s_stats_string += "Mean Variance Estimate:"+str( round( averageSscore) ) +"\n" 

				s_stats_string +="\n"
				s_stats_string +="Comparison to a slope of "+str( round( self.__significant_value, PRECISION ) ) \
						+ " at alpha =  " \
						+ str( round( self.__confidence_alpha, PRECISION ) )+"\n"
				s_stats_string +=BULLET_INDENTED \
								+ "Positive Slopes: "+str( round( positiveCount, PRECISION ) )\
								+ "\n" +  BULLET_INDENTED \
								+ "Neutral Slopes: "+str( round( zeroCount, PRECISION ) ) \
								+ "\n" + BULLET_INDENTED \
								+ "Negative Slopes: "+str( round( negativeCount, PRECISION ) ) \
								+ "\n" + BULLET_INDENTED \
								+ "Non-Number Slopes: "+str( round( Uncountable, PRECISION ) )
				s_stats_string+="\n\n"
				s_stats_string+="Test equality of slopes with regression on expected line " \
						+ "\nwith a slope " \
						+ str( f_slope_expected_slope ) \
						+ ", and intercept, " \
						+ str( f_intercept_expected_slope ) \
						+ "\nand significance threshold at " \
						+ str( f_confidence_alpha ) + "\n" 
				s_stats_string += BULLET_INDENTED \
								+ "Total lines rejecting: " + str( i_sum_slope_comparison_reject_null ) \
								+ "\n" + BULLET_INDENTED \
								+ "Total lines accepting: " + str( i_sum_slope_comparisons - i_sum_slope_comparison_reject_null ) 
				s_stats_string +="\n\n"
				s_stats_string +=tableString

				s_return=s_stats_string
			#end if no slopes were calc'd, else if slopes calcd
		else:
			s_return= "Insufficient data."
		#end if our table has sufficient data else not 

		return s_return
	#end __get_stats_as_string

	def setTsvFileManagerDictAsTable( self, 
						dls_dict_of_xy_lists_by_line_name ):
		'''
		This def was added in order for clients to
		pass in the dictionary associated
		with the NeEstimationTableFileManager objects
		getDictDataLinesKeyedToColnames, to convert
		it to the correct format and then set the 
		table attribute, self.__data_table.
		'''

		'''
		Helper inner-def:
		'''
		DELIMITER=NeEstimationTableFileManager.DELIM_TABLE
		def convert_to_duple_numeric_pair( s_xy_val_string ):

			ls_vals=s_xy_val_string.split( DELIMITER )
			v_x=float( ls_vals[0] )
			v_y=float( ls_vals[1] )

			return ( v_x, v_y ) 

		#end convert_to_duple_numeric_pair

		dltup_data_converted_for_regression={}	

		for s_line_name in dls_dict_of_xy_lists_by_line_name:
			ls_xy_strings=dls_dict_of_xy_lists_by_line_name[ s_line_name ]
			ls_xy_tuples=[ convert_to_duple_numeric_pair( s_xy ) \
											for s_xy in ls_xy_strings ]
			dltup_data_converted_for_regression[ s_line_name ]=ls_xy_tuples
		#end for each line name
		
		self.__data_table=dltup_data_converted_for_regression
		return
	#end convertDataFromTsvDictAndRegress

	def getStatsTableAsString( self, b_use_file_name_only_for_column_1=True ):
		s_table="No data available"
		if self.__data_table is not None:
			s_table=self.__get_stats_as_string( b_use_file_name_only_for_column_1 )
		#end if we have table data
		return s_table
	#end getStatsTableAsString

	'''
	2018_04_13. We've added an alpha text box to the 
	PGNeEstimationRegressplotInterface class, and we
	want to be able to update this class attribute when the user
	changes the alpha value.
	'''
	@property 
	def confidence_alpha( self ):
		return self.__confidence_alpha
	#end property confidence_alpha

	@confidence_alpha.setter
	def confidence_alpha( self, f_value ):
		self.__confidence_alpha=f_value 
		return
	#end def confidence_alpha

#end class PGRegressionStats

if __name__ == "__main__":
	pass
#end if main

