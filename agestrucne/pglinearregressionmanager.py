'''
Description

'''

__filename__ = "pgexpectedlinemanager.py"
__date__ = "20181105"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import numpy as np
import scipy.stats as stats

FLOAT_PRECISION=1e-64

'''
When the expected line data has uniform y values, 
from a zero slope and non-zero initial y value,
we get zero for residual standard error, and 
do not wasnt to do an F-test, nor do we want
to generate a slope comparison in such a case.
This Exception child class allows caller to
detect such a case and ignore its own call
to get a slope comparison (i.e. see class
PGRegressionStats).
'''
class FTestInputError( Exception ):
	pass
#end class FTestInputError

class PGLinearRegressionManager( object ):
	'''
	Description
	Wraps functions of linear regression on x,y pairs.  This
	class was abstracted out from the PGExpectedLineManager, to
	allow other clients to use the regression functions, leaving
	the calculated y's of the PGExpectedLineManager using rate
	and initial value to that class, which is now a child of this class.
	'''

	'''
	2018_11_23.  We are now also plotting the pre-regressed x,y pairs,
	and so need a  way to id this curve instead of the regression line:
	'''
	PREREGRESSION_LINE_NAME_TAG="_before_regress"

	def __init__( self, 
					s_line_name="pglinearregression",
					lv_x_values=None,
					lv_y_values=None,
					s_line_style="solid", 
					s_line_color="black",
					f_line_width_adjust=1.0,
					s_orig_values_line_style="dashed" ):

		'''
		Args
		s_line_name:  the key used by the plotting frame when it adds this line to
		              its data dictionary.
		lv_x_values: values of x (see below), typically, cycle numbers which give the 
		y value as a product of its last value and the number of cycles since
		the last plotted cycle number (these values are usually just a set of contiguous, 
		increasing ints, 1,2,3...  We expect that this list will most often be updated
		via the x_values property, as users change the range of x values in the plotting
		interface.

		lv_y_values: in our motivating case, these will be calculated in the child class
		PGExpectedLineManager using the rate and intitial values (see child class below).
		In other cases, the client will supply them either here in the init or using 
		the property y_values.

		s_line_style: matplotlib line style
		s_line_color: matplotlib color
		s_line_width: float, auqment or shrink relative to another line width
		'''
		self.__line_name=s_line_name
		self.__line_style=s_line_style
		self.__line_color=s_line_color
		self.__line_width_adjust=f_line_width_adjust
		self.__orig_values_line_style=s_orig_values_line_style

		self.__x_values=[ v_val for v_val in lv_x_values ] if lv_x_values is not None else None
		self.__y_values=[ v_val for v_val in lv_y_values ] if lv_y_values is not None else None

		self.__fit_y_values=None
		self.__slope=None
		self.__intercept=None
		self.__r_value=None
		self.__p_value=None
		self.__slope_std_error=None
		self.__residual_std_error=None

		return
	#end __init__

	def __copy_values( self, lv_values ):
		lv_copy=None
		return [ v_val for v_val in lv_values ]
	#end __copy_values

	def __do_regress_on_xy( self ):
		( self.__slope, 
					self.__intercept, 
					self.__r_value, 
					self.__p_value, 
					self.__slope_std_error ) = stats.linregress( self.__x_values, self.__y_values )

		self.__fit_y_values=[ v_x * self.__slope + self.__intercept for v_x in self.__x_values ]

		self.__residual_std_error=self.__get_residual_standard_error( \
												lf_x_values=self.__x_values,
												lf_y_values= self.__y_values, 
												f_slope=self.__slope, 
												f_intercept=self.__intercept )
		return
	#end __do_regress_on_xy

	def getDictRegressedXYValues( self ):
		'''
		The PGPlottingFrameRegressionLinesFromFileManager
		instance can call this after updating its regression
		set, to add an "expected" line to its collection, since
		its structure matches that of the regression lines it 
		has in its "current_data" member.
		'''
		dsl_line={ self.__line_name : { "x":self.__x_values, "y":self.__fit_y_values }}
		return dsl_line
	#end getDictRegressedXYValues

	def getDictOriginalXYValues( self ):
		'''
		2018_11_23.  We now also want to plot the original
		x,y series used for regression:
		'''
		myc=PGLinearRegressionManager
		s_orig_line_name=self.orig_values_line_name
		dsl_line={ s_orig_line_name : { "x":self.__x_values, "y":self.__y_values } }
		return dsl_line
	#end getDictOriginalXYValues


	def __do_f_test( self, 
						f_squared_se_numerator, 
						f_squared_se_denominator, 
						f_sample_size_numerator,
						f_sample_size_denominator,
						b_always_use_largest_in_numerator=False,
						i_num_params=2 ):
		f_f_value=None
		f_df_numerator=None
		f_df_denominator=None
		f_cdf_f_value=None
		f_p_value=None

		if f_squared_se_numerator <= FLOAT_PRECISION  \
								or f_squared_se_denominator  <= FLOAT_PRECISION:
				f_f_value=0.0
				'''
				If the se designated as numerator is zero,
				then it's sample size should be the first df listed,
				otherwise the opposite.
				'''
				if f_squared_se_numerator <= FLOAT_PRECISION:
					f_df_numerator=f_sample_size_numerator - i_num_params
					f_df_denominator=f_sample_size_denominator - i_num_params
				else:
					f_df_numerator=f_sample_size_denominator - i_num_params
					f_df_denominator=f_sample_size_numerator - i_num_params
				#end if numerator se zero, else denominator se is zero

		#end if either se is zero

		if f_squared_se_denominator > f_squared_se_numerator \
								and b_always_use_largest_in_numerator:
			'''
			Reverse the ratio if the denom value is bigger and we want
			the largest in the numerator
			'''
			f_f_value=f_squared_se_denominator/f_squared_se_numerator		
			f_df_numerator=f_sample_size_denominator - 2
			f_df_denominator=f_sample_size_numerator - 2
		else:
			'''
			Default case: both values non-zero and no flag to ensure
			largest is in numerator:
			'''
			f_f_value=f_squared_se_numerator/f_squared_se_denominator
			f_df_numerator=f_sample_size_numerator - 2
			f_df_denominator=f_sample_size_denominator - 2
		#end if denom value > numerator and we should rearrange

		f_cdf_f_value = stats.f.cdf( f_f_value, f_df_numerator, f_df_denominator )
		
		f_min_extreme_value=f_cdf_value if f_cdf_f_value < 0.5 \
												else 1-f_cdf_f_value

		f_p_value=2*f_min_extreme_value

		return f_p_value

	#end do_f_test

	def __do_welchs_t_test( self, f_other_slope, 
								f_other_slope_se, 
								f_other_sample_size ):
		f_t_estimate=None

		f_my_sample_size=float( len( self.__x_values ) )
		f_my_squared_slope_se=self.__slope_std_error**2
		f_other_squared_slope_se=f_other_slope_se**2

		f_dof_numerator = ( f_my_squared_slope_se + f_other_squared_slope_se )**2  
		f_dof_denominator = f_my_squared_slope_se/f_my_sample_size \
									+ f_other_squared_slope_se/f_other_sample_size

		f_dof=f_dof_numerator / f_dof_denominator

		f_t_estimate_numerator=self.__slope - f_other_slope
		f_t_estimate_denomiator=np.sqrt( f_my_squared_slope_se + f_other_squared_slope_se )

		f_t_estimate=f_t_estimate_numerator / f_t_estimate_denomiator
		
		return f_t_estimate, f_dof

	#end do_welchs_t_test

	def __get_squared_deviation_from_mean( self, lf_values ):

		f_sum_squared_deviation=None
		f_mean=np.mean( lf_values )
		lf_squared_deviations=\
				[ ( f_this_val-f_mean )**2 for f_this_val in lf_values ]
		f_sum_squared_deviation=sum( lf_squared_deviations )
		return f_sum_squared_deviation
	#end __get_square_deviation_from_mean

	def __get_residual_standard_error( self, lf_x_values, 
												lf_y_values,
												f_slope, 
												f_intercept,
												i_num_params=2 ): 

		f_resid_std_err=None

		i_num_values=len( lf_y_values )

		lf_fit=[ f_val*f_slope + f_intercept for f_val in lf_x_values ]
		lf_squared_residuals=[ ( lf_y_values[ idx ] - lf_fit [ idx ] ) ** 2 \
													for idx in range( i_num_values ) ]		

		f_squared_resid_std_err = sum( lf_squared_residuals ) / (i_num_values-i_num_params ) 

		f_resid_std_err=np.sqrt( f_squared_resid_std_err )

		return f_resid_std_err

	#end __get_residual_standard_error
	
	def __compute_t_value_on_null_hypo( self, f_null_hypo_value ):
		
		if self.__slope is None or self.__slope_std_error is None:
			raise Exception( "In PGLinearRegressionManager instance, " \
						+ "def __compute_t_value_on_null_hypo, " \
						+ "the program cannot compute a t value " \
						+ "because this instance  has no slope " \
						+ "or no slope standard error." )
		f_t_value=None
		'''
		2019_01_15.  This computation is from answer 15 at:
		https://stats.stackexchange.com/questions
		/111559/test-model-coefficient-regression-slope
		-against-some-value
		
		'''
		f_diff_from_hypo=self.__slope - f_null_hypo_value 
		
		f_t_value=f_diff_from_hypo/self.__slope_std_error
		
		return f_t_value
	#end def __compute_t_value_on_null_hypo

	def __do_standard_t_test( self, 
						f_other_slope,
						f_other_intercept,
						lf_other_x_values,
						f_other_residual_se_regress ):

		f_t_estimate=None

		f_my_sample_size=float( len( self.__x_values ) )

		f_other_sample_size=float( len( lf_other_x_values ) )

		f_dof = f_my_sample_size + f_other_sample_size - 4

		f_my_residual_se_regress=\
				self.residual_standard_error

		f_squared_deviation_my_x_values=\
				self.__get_squared_deviation_from_mean( self.__x_values )

		f_squared_deviation_other_x_values=\
				self.__get_squared_deviation_from_mean( lf_other_x_values )

		f_pooled_error_numerator=( f_my_sample_size - 2 ) * f_my_residual_se_regress**2 \
									+ ( f_other_sample_size -1 ) * f_other_residual_se_regress **2

		f_pooled_error_denominator=f_my_sample_size + f_other_sample_size - 4

		f_pooled_error=f_pooled_error_numerator/f_pooled_error_denominator
	
		f_t_estimate_numerator=self.__slope - f_other_slope
		f_t_estimate_denominator_multiple1=f_pooled_error
		f_t_estimate_denominator_multiple2 = 1/f_squared_deviation_my_x_values \
													+ 1/f_squared_deviation_other_x_values 

		f_t_estimate_denominator=np.sqrt( f_t_estimate_denominator_multiple1 \
													* f_t_estimate_denominator_multiple2)

		f_t_estimate=f_t_estimate_numerator/f_t_estimate_denominator

		return f_t_estimate, f_dof
	#end __do_standard_t_test

	def getPValueComarisonOfSlopes( self, f_other_slope, 
											f_other_intercept,
											f_other_slope_standard_error, 
											lf_other_x_values,
											f_other_residual_se ):

		'''
		Compare this regression to the one passed in the args
		to see how likely it is that they both represent the
		same underlying population.

		from 1.Andrade, J. M. & Estévez-Pérez, M. G. Statistical 
		comparison of the slopes of two regression lines: A tutorial. 
		Analytica Chimica Acta 838, 1–12 (2014), using their test
		that is robust to non-equal variances in the two linear models,
		which thay label t*exp (pg 5 of the article pdf).

		'''

		'''
		Fisher-Snedecor's F test to see if we should see
		the two slopes as from pops with the same variance.
		'''

		MAX_SIGNIFICANT_P_VALUE=0.05

		f_prob_f_value=None
		f_t_value=None
		f_dof=None
		f_prob_t_value=None

		f_my_residual_se=self.residual_standard_error

		f_my_squared_se=f_my_residual_se**2
		f_other_squared_se=f_other_residual_se**2
		f_my_sample_size=float( len( self.__x_values ) )
		f_other_sample_size=float( len( lf_other_x_values ) )

		f_squared_se_numerator=None
		f_squared_se_denominator=None
		f_sample_size_numerator=None
		f_sample_size_denominator=None

		if f_my_squared_se > f_other_squared_se:
			f_squared_se_numerator=f_my_squared_se
			f_squared_se_denominator=f_other_squared_se
			f_sample_size_numerator=f_my_sample_size
			f_sample_size_denominator=f_other_sample_size
		else:
			f_squared_se_numerator=f_other_squared_se
			f_squared_se_denominator=f_my_squared_se
			f_sample_size_numerator=f_other_sample_size
			f_sample_size_denominator=f_my_sample_size 
		#end if my squared residuals larger than other, else not

		if f_squared_se_numerator <= FLOAT_PRECISION \
					or f_squared_se_denominator <= FLOAT_PRECISION:

			raise FTestInputError( "F test (and its following slope comparison) " \
										+ "will not be performed, " \
										+ "because one of the two " \
										+ "regressions has zero " \
										+ "value for residual standard " \
										+ "error, indicating an essentially perfect fit." )
		#end if zero residual se in either term

		f_pval_f_test=self.__do_f_test( f_squared_se_numerator, 
											f_squared_se_denominator,
											f_sample_size_numerator,
											f_sample_size_denominator ) 

		if abs( f_pval_f_test ) <= MAX_SIGNIFICANT_P_VALUE:
			'''
			F test shows variances not equal, so we do the
			welch's t-test
			'''
			f_other_sample_size=float( len(lf_other_x_values ) )
			f_t_value, f_dof = self.__do_welchs_t_test( f_other_slope=f_other_slope, 
														f_other_slope_se=f_other_slope_standard_error, 
														f_other_sample_size=f_other_sample_size )
		
		else:
			'''
			F test suggests equal variances, so we use standart t test
			'''
			
			f_t_value, f_dof= self.__do_standard_t_test( f_other_slope=f_other_slope,
															f_other_intercept=f_other_intercept,
															lf_other_x_values=lf_other_x_values,
															f_other_residual_se_regress=f_other_residual_se )

		#end if we have needed data, else warning
		
		f_cdf_t_value=stats.t.cdf( f_t_value, f_dof )

		f_prob_values_larger_mag=f_cdf_t_value if f_cdf_t_value < 0.5 \
													else  1 - f_cdf_t_value 
			
		f_2tail_pval=2*f_prob_values_larger_mag

		return f_2tail_pval

	#end getPValueComarisonOfSlopes
	
	def getPValueNullHypoExpectedSlope( self, f_slope_null_hypo ):
		
		f_2tail_pval=None
		
		f_t_value=self.__compute_t_value_on_null_hypo( f_slope_null_hypo )
		
		f_dof=len( self.x_values ) - 2
		
		f_cdf_t_value=stats.t.cdf( f_t_value, f_dof )

		f_prob_values_larger_mag=f_cdf_t_value if f_cdf_t_value < 0.5 \
													else  1 - f_cdf_t_value 
			
		f_2tail_pval=2*f_prob_values_larger_mag

		return f_2tail_pval
	
	#end getPValueNullHypoExpectedSlope

	def hasRegressionInfo( self ):
		b_info_complete=True
		for v_value in [ self.x_values, 
								self.fit_y_values, 
								self.slope, 
								self.intercept, 
								self.slope_std_error, 
								self.residual_standard_error ]:

			if v_value is None:
				b_info_complete = False
				break;
			#end if no valud for this param
		#end for each value
		return b_info_complete
	#end hasRegressionInfo

	def doRegression( self ):
		self.__do_regress_on_xy()
		return
	#end def 
	@property
	def x_values( self ):
		return self.__x_values
	#end property x_values

	@x_values.setter
	def x_values( self, lv_values ):
		self.__x_values=self.__copy_values( lv_values )	
		return
	#end setter x_values

	@property
	def y_values( self ):
		return self.__y_values
	#end property y_values

	@y_values.setter
	def y_values( self, lv_values ):
		self.__y_values=self.__copy_values( lv_values )	
		return
	#end setter y_values

	@property
	def fit_y_values( self ):
		return self.__fit_y_values
	#end property fit_y_values
	
	@property
	def slope( self ):
		return self.__slope
	#end getter slope

	@property
	def intercept( self ):
		return self.__intercept
	#end getter intercept
	
	@property
	def r_value( self ):
		return self.__r_value
	#end getter r_value

	@property
	def p_value( self ):
		return self.__p_value
	#end getter p_value
	
	@property
	def slope_std_error( self ):
		return self.__slope_std_error
	#end getter slope_std_error

	@property
	def residual_standard_error( self ):
		return self.__residual_std_error
	#end getter residual_standard_error

	@property
	def line_name( self ):
		return self.__line_name
	#end getter line_name

	@line_name.setter
	def line_name( self, s_val ):
		self.__line_name=s_val
		return
	#end setter line_name
	
	@property
	def orig_values_line_name( self ):
		s_tag=PGLinearRegressionManager\
					.PREREGRESSION_LINE_NAME_TAG
		return self.__line_name + s_tag
	#end getter line_name

	@property
	def orig_values_line_style( self ):
		return self.__orig_values_line_style
	#end property orig_values_line_style

	@orig_values_line_style.setter
	def line_style( self, v_val ):
		self.__orig_values_line_style = v_val
	#end setter.line_style

	@property
	def line_style( self ):
		return self.__line_style
	#end property line_style

	@line_style.setter
	def line_style( self, v_val ):
		self.__line_style = v_val
	#end setter.line_style

	@property
	def line_color( self ):
		return self.__line_color
	#end property line_color

	@line_color.setter
	def line_color( self, v_val ):
		self.__line_color = v_val
	#end setter.line_color

	@property
	def line_width_adjust( self ):
		return self.__line_width_adjust
	#end property line_width_adjust

	@line_width_adjust.setter
	def line_width_adjust( self, v_val ):
		self.__line_width_adjust = v_val
	#end setter.line_width_adjust

#end class PGLineManager

class PGExpectedLineManager( PGLinearRegressionManager ):
	'''
	2018_11_05
	This class offers a PGPlottingFrameRegressionLinesFromFileManager
	instance the ability to perform a linear regression on x,y values 
	computed via a rate of decline or incline and an initial Nb/Ne

	It also serves the PGNeEstimationRegressplotInterface instabnce
	via the PGPlottingFrameRegressionLinesFromFileManager, by 
	allowing The user to set the rate and initial Nb/Ne.

	The PGPlottingFrameRegressionLinesFromFileManager client then
	calls this class with the current number of x-values being
	plotted (i.e. cycle numbers), so that this object can then
	compute y values and do a scipy.stats.lineregress on the
	x and y values, and then compute the regression based
	y value.  It also stores the slope, intercept, correlation,
	standard_error quantities from the regression.

	Finally, it allows a PGRegressionStats instance to call it
	with the slope, std err, and sample size of another line,
	and compute a p-value on the H0 that the slope is that
	given by this instances regression coefficient as slope.

	This class assumes that y values are cycle numbers,
	strictly increasing, the typical case being n cycles with x values
	of 1,2,3...n.  But it applies the rate on a per cycle
	basis, sto that if x_1=3 and x_2=5, then y_2 will be
	y_1*rate*2.
		
	2019_01_15.  We've changed the expected line plot, such that the above
	rate computation is not used, although we keep the method that computes
	it (as called from doRegression), to retain the functionality.  
	We now have a new member method makeLinearYValuesUsingRateAndInitY, 
	in which the "rate" is now the slope "m" in a line y=mx+b. 
	'''

	def __init__(self,
					f_rate=0.0,
					f_initial_y_value=0.0,
					s_line_name="expected_incline_and_initial_y_value",
					lv_x_values=None,
					lv_y_values=None,
					s_line_style="solid", 
					s_line_color="black",
					f_line_width_adjust=1.0,
					s_orig_values_line_style="dashed" ):
		'''
		Args:
		f_rate: rate of decline (neg rate) or increase (pos rate) per x unit 
		the x_values (cycles ) proportion of an initial Nb value.  2019_01_15, the 
		rate is now also used as slope to compute a line with init-y as the first y-value .
		f_initial_y_value:  the initial y-value that will be adjusted up or down by rate
		See parent class PGLinearRegressionManager for details about other args.
		'''

		PGLinearRegressionManager.__init__( self,
									s_line_name=s_line_name,
									lv_x_values=lv_x_values,
									lv_y_values=lv_y_values,
									s_line_style=s_line_style,
									s_line_color=s_line_color,
									f_line_width_adjust=f_line_width_adjust,
									s_orig_values_line_style=s_orig_values_line_style )

		self.__rate=f_rate
		self.__initial_y_value=f_initial_y_value
		return
	#end def __init__
	
	def __make_y_values_using_rate_and_init_y( self ):
		'''
		Use the rate and initiabl nb value to
		compute a (non-linear for nonzero rate)
		series of y values.  These will be used for the
		linear regression.
		'''
		lv_y_values=[]
		
		i_num_x_values=len( self.x_values )

		for idx in range( i_num_x_values ):
			if idx==0:
				lv_y_values.append( self.__initial_y_value )
			else:
				i_x_interval=self.x_values[ idx ] - self.x_values[ idx - 1 ]
				f_delta=lv_y_values[ idx - 1 ] * self.__rate
				lv_y_values.append( lv_y_values[ idx - 1 ] + f_delta )
			#end if first y value else not
		#end for each x value			
		return lv_y_values
	#end __make_y_values_using_rate_and_init_y

	def doRegression( self ):
		'''
		This overrides the parent class version,
		because it needs to create y values before
		a regression is possible.  We call the parent
		version of this method after we get y values
		'''
		lv_y_values=self.__make_y_values_using_rate_and_init_y()
		self.y_values=lv_y_values
		PGLinearRegressionManager.doRegression( self )
	#end def do_regression
	
	def makeLinearYValuesUsingRateAndInitY( self ):
		'''
		2019_01_15.  This method is added because we decided
		to skip regressing on the y values derived from init-y
		and a non-linear rate (given a set of x values).  
		Instead we are now calculating a p-value for 
		each ldne-based regressed line using the "rate" of 
		our expected line as the (null) hypothesized
		slope.
		'''
		
		if self.x_values is None:
			raise Exception( "In PGExpectedLineManager instance, " \
								+ "method makeLinearYValuesUsingRateAndInitY, " \
								+ "there are no x_values (x_values are None)." )
		#end if no x_values
		
		lv_y_values=[]
		
		#We shift the x values so that x_1=0 (which makes our initial y value
		#the first:
		v_x0=self.x_values[0]
		
		lv_shifted_x_values=[ v_this_x - v_x0 for v_this_x in self.x_values ]
		
		for f_x in lv_shifted_x_values:
			lv_y_values.append( ( f_x * self.__rate ) \
										+ self.__initial_y_value )
		#end for each shifted x value
		
		self.y_values=lv_y_values
		
		return 
	#end makeLinearYValuesUsingRateAndInitY

	@property
	def rate( self ):
		return self.__rate
	#end getter slope

	@rate.setter
	def rate( self, f_val ):
		self.__rate=f_val
		return
	#end setter slope
	
	@property
	def initial_y_value( self ):
		return self.__initial_y_value
	#end getter initial_y_value

	@initial_y_value.setter
	def initial_y_value( self, f_val ):
		self.__initial_y_value=f_val
		return
	#end setter initial_y_value
	
#end class PGExpectedLineManager

if __name__ == "__main__":
	pass
#end if main

