
'''
Description
We needed a suite of tests to validate the simulation and nb output.  
The first of these requested by Gordon is a comparison of expected
hegerozygosity, calculated from the Ne value, for the tth generation
as ( 1-2/Ne )**t, vs  the "observed" 
loss of heterozygosity, calculated for each generation as the mean ( 1-He ), with
He_l = sum_i_l=1 to n_l (i_l**2), with i_l=allele freq of the ith of n alleles 
for the lth loci.


2017_02_22
We've clarified that we will add a cycles/generation ratio to our input values
in order to correctly implement the theoretical vs expected values. Note that
plotting for most of our model species by sim breeding cycles, implying a 1/1
breeding cycle per generation ratio for measuring heterozygosity, shows 
inaccurate declines, expected vs theoretical.
'''
from __future__ import division
from __future__ import print_function

from builtins import range
from past.utils import old_div
__filename__ = "pgvalidationtests.py"
__date__ = "20170130"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import numpy as np

import agestrucne.genepopfilemanager as gpm
import agestrucne.genepopfilelociinfo as gpl
import agestrucne.pgutilityclasses as pguc

b_can_plot=True
try:
	import matplotlib.pyplot as pt
except ImportError as oie:
	print( "The matplotlib module was not found.  Results cannot be plotted." )
	b_can_plot=False
#end


def get_mean_het_per_cycle( o_gp_file, 
								i_initial_cycle, 
								i_final_cycle,
								i_min_loci_number=None, 
								i_max_loci_number=None ):

	MAX_POSSIBLE_LOCI=int( 1e32 )

	li_pop_subsample=list( \
				range( i_initial_cycle, i_final_cycle + 1  ) )

	o_gp_file.subsamplePopulationsByList( li_pop_subsample, "pop_sub" )

	v_loci_subsample_tag=None

	if [ i_min_loci_number, i_max_loci_number ] != [ None, None ]:
		if i_min_loci_number is None:
			i_min_loci_number = 1
		#end if our range has only an upper limit

		if i_max_loci_number is None:
			'''
			This should be truncated to the max
			possible loci range number (i.e.
			N for N total loci in the genepop file
			'''
			i_max_loci_number = MAX_POSSIBLE_LOCI
		#end if only limit is on min loci number
		v_loci_subsample_tag="loci_sub"


		o_gp_file.subsampleLociByRangeAndMax( i_min_loci_number,
												i_max_loci_number, 
													v_loci_subsample_tag )
	#end if we have limits on loci number

	o_loci_info=gpl.GenepopFileLociInfo( o_gp_file, 
								s_population_subsample_tag="pop_sub",
								s_loci_subsample_tag= v_loci_subsample_tag )

	ddf_het_by_pop_by_loci=o_loci_info.getHeterozygosity()

	'''
	A dictionary whose keys are pop numbers and whose
	values are the mean heterozygosity he_l, where
	he_l is one minus the sum of squared allele frequencies
	for locus l.
	'''
	df_mean_het_by_pop={ i_pop : np.mean( list(  \
							ddf_het_by_pop_by_loci[ i_pop ].values() ) ) \
							for i_pop in ddf_het_by_pop_by_loci }

	return df_mean_het_by_pop

#end get_mean_het_per_cycle

def get_ne_per_cycle( s_genepop_file, 
									o_tsv_file,
									i_initial_cycle_number,
									i_final_cycle_number ):

	TSV_COL_WITH_NE_VALS="ne_est_adj"
	df_ne_by_cycle=None

	o_tsv_file.unsetAllFilters()

	#This allows us to select only tsv table entries
	#whose col 1 file name matches our desired file:
	o_tsv_file.setFilter( "original_file", lambda x:x==s_genepop_file )

	'''
	This local def will be passed to test gen ranges.
	The arg as string required by the o_tsv_file 
	(class NeEstimationTableFileManager) object's setFilter.  
	All filers must take one string arg and return a boolean
	'''
	def cycle_range_check( s_cycle_number_as_string ):
		i_this_cycle=int( s_cycle_number_as_string )
		b_return_val= i_this_cycle >= i_initial_cycle_number \
							and i_this_cycle <= i_final_cycle_number

		return b_return_val
	#end def gen_range_check

	o_tsv_file.setFilter( "pop" , cycle_range_check )

	ls_pop_and_ne=o_tsv_file.getFilteredTableAsList( [ "pop", TSV_COL_WITH_NE_VALS ] )


	#The zeroth item in the ls_pop_and_ne list is the header, so we
	#process the entries with indices 1 through the last.
	df_ne_by_cycle={ int( s_vals.split()[0] ):float( s_vals.split()[1] ) \
												for s_vals in ls_pop_and_ne[ 1 : ] } 
	
	return df_ne_by_cycle
#end get_ne_per_cycle

def get_theoretical_heterozygosity_per_generation( df_mean_het_by_cycle, 
														df_ne_by_cycle,
														f_cycles_per_generation,
														f_theoretical_ne=None ):
	f_reltol=1e-80

	'''
	From Brian H, the iterative caluclation:
	H_t = H_[t-1](1 - 1/(2Ne_0)), where Ne_0 is the Ne value for the 
	initial population.
	'''

	df_theoretical_het_per_generation={}

	li_cycle_numbers_for_ne=list(df_ne_by_cycle.keys())
	li_cycle_numbers_for_het=list(df_mean_het_by_cycle.keys())

	li_cycle_numbers_for_ne.sort()
	li_cycle_numbers_for_het.sort()

	i_cycles_per_generation=int( round( f_cycles_per_generation ) )

	if li_cycle_numbers_for_ne != li_cycle_numbers_for_het:

		s_msg="In pgvalidationtests.py, " \
						+ "def get_theoretical_heterozygosity_per_generation, " \
						+ "Ne values dict has keys (cycle numbers) " \
						+ "that do not equal those in the Het values dict. " \
					 	+ "Ne dict keys: " + str( list( df_ne_by_cycle.keys() ) ) \
						+ ", Het dict keys: " + str( list( df_mean_het_by_cycle ) ) \
						+ "."
		raise Exception( s_msg )
	#end if non-equal key sets

	i_total_cycle_numbers=len( list(df_ne_by_cycle.keys()) )
	i_lowest_cycle_number=min( df_ne_by_cycle.keys() )

	f_ne0=f_theoretical_ne if f_theoretical_ne is not None  \
					else np.mean( list( df_ne_by_cycle.values() ) )

	f_ht0=df_mean_het_by_cycle[ i_lowest_cycle_number ]
	
	'''
	The initial generation has the het
	value caluclated by mean sum of squared
	allele frequencies over all loci, so 
	that for gen 1, the theoretical and the
	expected match:
	'''
	i_generation_number= 1

	df_theoretical_het_per_generation[ 1 ] =  f_ht0	

	f_calc_coefficient = 1 if f_ne0 <= f_reltol else 1 - old_div(1, ( 2*f_ne0 ))

	'''
	We use cycles per generation to
	itereate the correct number of times in the calculation
	'''

	
	for idx in range ( i_cycles_per_generation, i_total_cycle_numbers, i_cycles_per_generation ):

		
		i_generation_number+=1
		i_this_cycle_number=li_cycle_numbers_for_ne[ idx ]
	
		f_het_value_last_generation=df_theoretical_het_per_generation[ i_generation_number - 1 ]

		f_theoretical_het_for_this_generation = f_het_value_last_generation * f_calc_coefficient
			
		df_theoretical_het_per_generation[ i_generation_number ] = \
									f_theoretical_het_for_this_generation
	#end for each index into list cycle numbers

	return df_theoretical_het_per_generation
#end get_theoretical_heterozygosity_per_generation
														

def get_theoretical_het_loss_per_generation( df_ne_by_cycle_number, f_cycles_per_generation, f_theoretical_ne = None ):
	'''

	This calculation for theoretical loss of heterozygosity is from
	From http://labs.russell.wisc.edu/peery/files/2011/12/Primer-in-Population-Genetics.pdf

	This def also returns the Ne value for the initial cycle.
	'''

	df_theoretical_het_loss_by_generation={}

	i_cycles_per_generation=int( round( f_cycles_per_generation ) )

	li_sorted_cycle_numbers=list(df_ne_by_cycle_number.keys())
	li_sorted_cycle_numbers.sort()

	i_min_gen_number=min( li_sorted_cycle_numbers )

	f_ne_for_initial_pop=f_theoretical_ne if f_theoretical_ne is not None \
			else np.mean( list( df_ne_by_cycle_number.values() ) )	

	f_one_over_2Ne=old_div(1.0,( 2.0*f_ne_for_initial_pop ))

	f_one_minus_one_over_2Ne=1 - f_one_over_2Ne

	'''
	We want zero loss of het in the
	first cycle, so the counter,
	which gives the exponent in the 
	loss calculation, will be at zero
	for the first (initial) cycle. 
	'''
	i_generation_count = -1

	i_generation_number=0

	for i_gen in range( 0, len( li_sorted_cycle_numbers ), i_cycles_per_generation ):

		i_generation_count += 1
		i_generation_number+=1

		'''
		We raise ( 1 - 1/2Ne ) to  t = gen_counter, subtract
		that value from 1:
		'''
		f_loss_this_gen=1 - (  ( f_one_minus_one_over_2Ne )**i_generation_count  )

		df_theoretical_het_loss_by_generation[ i_generation_number ] = f_loss_this_gen
	#end for each cycle
	
	return  df_theoretical_het_loss_by_generation

#end get_theoretical_het_loss_per_generation

def convert_mean_hets_to_het_loss( df_mean_het_by_gen ):

	df_mean_het_loss_by_gen={}

	i_min_het_number=min( df_mean_het_by_gen.keys() )

	f_h0=df_mean_het_by_gen[ i_min_het_number ]

	li_sorted_gen_numbers=list(df_mean_het_by_gen.keys())
	li_sorted_gen_numbers.sort()

	for i_gen_number in li_sorted_gen_numbers:
		f_diff=f_h0 - df_mean_het_by_gen[ i_gen_number ]
		df_mean_het_loss_by_gen[ i_gen_number ] = f_diff
	#end for each gen number

	return df_mean_het_loss_by_gen

#end convert_mean_hets_to_het_loss


def plot_two_dicts_similarly_scaled( d_dict1, d_dict2, 
											s_data1_label="",
											s_data2_label="",
											s_xaxis_label="",
											s_yaxis_label="",
											s_title="", 
											s_plot_file_name=None ):

	'''
	This def assumes 
		--that the dict1 and dict2 keys have the x-axis values,
		and that they are numerical.
		--that the axis scales for dict1 and dict2 are similar for keys(),
		and similar for values().
	'''

	PLOTLINEWIDTH=2.0
	FONTSIZE=12
	PLOTFONTSIZE=12
	LINEPOINTTYPE1="o-"
	LINEPOINTTYPE2="^-"

	MAX_TOT_VALS_FOR_POINTS=65

	if len( d_dict1 ) > MAX_TOT_VALS_FOR_POINTS:
		LINEPOINTTYPE1="-"
		LINEPOINTTYPE2="-"
	#end if too many gens to show points, just show line

	f_y_limits_units=(old_div(1,10.0))
	f_x_limits_units=(old_div(1,60.0) )

	f_label_y_space_unit=(old_div(1,30.0))
	f_label_x_space_unit=(old_div(1,5.0))

	v_min_x_value_dict1=min( list( d_dict1.keys() ) )
	v_max_x_value_dict1=max( list( d_dict1.keys() ) )

	v_min_y_value_dict1=min( list( d_dict1.values() ) )
	v_max_y_value_dict1=max( list( d_dict1.values() ) )

	v_min_x_value_dict2=min( list( d_dict2.keys() ) )
	v_max_x_value_dict2=max( list( d_dict2.keys() ) )

	v_min_y_value_dict2=min( list( d_dict2.values() ) )
	v_max_y_value_dict2=max( list( d_dict2.values() ) )

	v_min_x_value=min( v_min_x_value_dict1, v_min_x_value_dict2 )
	v_max_x_value=max( v_max_x_value_dict1, v_max_x_value_dict2 )

	v_min_y_value=min( v_min_y_value_dict1, v_min_y_value_dict2 )
	v_max_y_value=max( v_max_y_value_dict1, v_max_y_value_dict2 )

	v_rightmnost_dict1_yval=d_dict1[ v_max_x_value_dict1 ] 
	v_rightmnost_dict2_yval=d_dict2[ v_max_x_value_dict2 ]

	v_y_range=v_max_y_value-v_min_y_value
	v_x_range=v_max_x_value-v_min_x_value

	lf_xlimits=[ v_min_x_value - v_x_range* f_x_limits_units, v_max_x_value + v_x_range*f_x_limits_units ]

	lf_ylimits=[ v_min_y_value - v_y_range*f_y_limits_units, v_max_y_value + v_y_range*f_y_limits_units ]

	f_label_x_coord_offset=( lf_xlimits[ 1 ] - lf_xlimits[ 0 ] ) * f_label_x_space_unit
	f_label_y_coord_offset=( lf_ylimits[ 1 ] - lf_ylimits[ 0 ] ) * f_label_y_space_unit
				
	o_fig=pt.figure()
	o_subplt=o_fig.add_subplot(111)
	o_subplt.plot( list(d_dict1.keys()), list( d_dict1.values() ), LINEPOINTTYPE1, linewidth=PLOTLINEWIDTH )
	o_subplt.plot( list(d_dict2.keys()), list( d_dict2.values() ), LINEPOINTTYPE2, linewidth=PLOTLINEWIDTH )

	o_subplt.set_ybound( lower=lf_ylimits[0], upper=lf_ylimits[ 1 ] )
	o_subplt.set_xlabel( s_xaxis_label, fontsize=FONTSIZE )
	o_subplt.set_ylabel( s_yaxis_label, fontsize=FONTSIZE )
	o_subplt.set_title( s_title, fontsize=FONTSIZE )
	o_subplt.legend( [ s_data1_label , s_data2_label ], frameon=False, fontsize=PLOTFONTSIZE )

	pt.show()

	o_fig=None

	if s_plot_file_name is not None:
		pt.savefigure( s_file_name )
	#end if no plot file
	return
#end plot_two_dicts_similarly_scaled

def has_requested_cycle_range( o_tsv_file, i_initial_cycle_number, i_final_cycle_number ):
	'''
	This is not yet implemented, so returns True in all cases.
	'''
	b_has_range=True
	return b_has_range
#end has_requested_cycle_range

def get_mean_hets_and_ne_for_cycles( s_ne_tsv_file, 
								i_initial_cycle_number,
								i_final_cycle_number, 
								i_min_loci_number, 
								i_max_loci_number ):

	ddf_mean_het_by_gp_file_by_gen={}
	ddf_ne_by_gp_file_by_gen={}

	o_tsv_file=pguc.NeEstimationTableFileManager( s_ne_tsv_file )

	#Test the tsv file for the requested cycle range:
	b_has_cycles=has_requested_cycle_range( o_tsv_file, 
										i_initial_cycle_number, 
											i_final_cycle_number )

	'''
	The file_names property of the tsv file manager object
	yields the set (ie.unique values, but returned as a list) 
	of file names in column 1 of the tsv file:
	'''
	ls_genepop_files_used_to_produce_ne_table=o_tsv_file.file_names

	for s_genepop_file in ls_genepop_files_used_to_produce_ne_table:

		o_this_gp_file=gpm.GenepopFileManager( s_genepop_file )

		i_total_cycles=o_this_gp_file.pop_total

		if i_final_cycle_number > i_total_cycles:
			s_msg="In pgvalidationtests, def "  \
					+ "get_mean_hets_and_ne_for_cycles, " \
					+ "arg value for final cycle number, " \
					+ str( i_final_cycle_number ) \
					+ ", it greater than the available number of cycles, " \
					+ str( i_total_cycles ) + "."
			raise Exception ( s_msg )
		#end if requested final gen is too large

		if i_initial_cycle_number < 1 \
					or i_initial_cycle_number > i_total_cycles:
			s_msg="In pgvalidationtests, def "  \
					+ "get_mean_hets_and_ne_for_cycles, " \
					+ "arg value for initial cycle number, " \
					+ str( i_final_cycle_number ) \
					+ ", it outside the valid range, 1 - " \
					+ str( i_total_cycles ) + "."
			raise Exception ( s_msg )
		#end if requested final gen is too large

		i_actual_final_gen=min( i_final_cycle_number, i_total_cycles )

		df_mean_het_by_gen=get_mean_het_per_cycle( o_this_gp_file, 
															i_initial_cycle_number, 
															i_actual_final_gen, 
															i_min_loci_number, 
															i_max_loci_number )

		ddf_mean_het_by_gp_file_by_gen[ s_genepop_file ]=df_mean_het_by_gen


		df_ne_by_gen=get_ne_per_cycle( s_genepop_file, 
													o_tsv_file,
													i_initial_cycle_number,
													i_actual_final_gen )

		ddf_ne_by_gp_file_by_gen[ s_genepop_file ] = df_ne_by_gen

	#end for each genepop file name

	return ddf_mean_het_by_gp_file_by_gen, ddf_ne_by_gp_file_by_gen

#end get_mean_hets_and_ne_for_cycles	

def get_per_generation_het_from_per_cycle_het( df_het_by_cycle, f_cycles_per_generation ):

	df_het_by_generation={}

	i_cycles_per_generation=int( round( f_cycles_per_generation ) )

	i_cycles_per_generation=int( round( f_cycles_per_generation ) )

	li_sorted_cycle_numbers=list( df_het_by_cycle.keys()  )

	li_sorted_cycle_numbers.sort()

	i_generation_number=0
	for idx in range( 0, len( li_sorted_cycle_numbers ), i_cycles_per_generation ):
		i_generation_number += 1
		
		df_het_by_generation[ i_generation_number ] = \
				df_het_by_cycle[ li_sorted_cycle_numbers[ idx ] ]
	#end for each index in the cycle numbers list

	return df_het_by_generation

#end get_per_generation_het_from_per_cycle_het

def get_expected_vs_observed_heterozygosity( s_ne_tsv_file, 
											i_initial_cycle_number, 
											i_final_cycle_number,
											f_cycles_per_generation,
											i_min_loci_number=None,
											i_max_loci_number=None,
											f_theoretical_ne=None,
											b_plot=True, 
											s_plot_file=None,
											s_plot_type="png" ):

	'''
	This def is designed to use either a user-supplied theoretical Ne, or to
	use the mean estimates in the tsv file for the theoretical Ne, and, for
	the initial heterozygosity the mean HW expected via allele frequencies
	for the first (initial) cycle.  The theoretical het for the ith generation
	is calculated as
		Hz_i=Hz_{i-1} X ( 1 - 1/(2Ne) )

	For the expected het for each cycle:
			sum_1_to_L(  1 - sum_1_to_A( allele-frequency_ij ** 2 ) )/L, in a cycle
			(pop section) with L loci, and each loci with some total alleles A, i=ith loci,
			j=jth allele.

	Assumption:  that the (genepop) file(s) named in column one of the s_ne_tsv_file 
			argument exist and have either absolute paths (the current
			default method used to write them to the tsv file), or relative
			paths that are accessible from the working directory of the
			current python environment.

	param s_ne_tsv_file, names the table file output from using module
		pgdriveneestimator.py to generate ne estimations, either
		via the negui interface or the command line use of pgdriveneestimator.py 
		itself, on genepop files generated by the negui implementation of
		the AgeStructureNe simulation driver.
	param i_initial_cycle_number, integer giving the ith pop section,
		where i is the poplulation (cycle) that gives the initital Ne value on which
		to base the expected loss of het, that is the Ne value in ( 1-2/Ne )^t for
		each subsequent cycle t.
	param i_final_cycle_number, if not None, then an integer giving the highest pop section
		(cycle) value to analyze.  If None, then analyze all pop sections with numbers 
		>= i_initial_cycle_number
	param f_cycles_per_generation.  gives the number of breeding cycles per generation, so
		that theoretical interations are done per generation (not per cycle, unless 
		cycles per generation is 1.0
	param i_min_loci_number, if not none than the He calculation will not use any of the loci
			in the range 1 to i, where i_min_loci_number is i + 1.
	param i_ma_loci_number, if not none than the He calculation will not use any of the N loci
			in the range j to N, where i_man_loci_number is j - 1.

	param b_plot, if true and maplotlib was importable, then a plot will be done.
	param s_plot_file, if not none and b_plot is true, then plot to file with this name.
			If s_plot_file is None, then call pyplot.show() after the plot command.
	param s_plot_type, if b_plot is true and s_plot_file is not None, the file type
			to be written is given by this extension, defaulting to png.

	'''
	

	ddf_mean_het_by_gp_file_by_cycle, ddf_ne_by_gp_file_by_cycle = \
			get_mean_hets_and_ne_for_cycles( s_ne_tsv_file, 
												i_initial_cycle_number,
												i_final_cycle_number, 
												i_min_loci_number, 
												i_max_loci_number )

	for s_gp_file_name in ddf_mean_het_by_gp_file_by_cycle:

		df_het_per_cycle=ddf_mean_het_by_gp_file_by_cycle[ s_gp_file_name ]

		df_expected_het_by_gen=get_per_generation_het_from_per_cycle_het( df_het_per_cycle, 
																			f_cycles_per_generation )

		df_theoretical_het_by_gen=\
			get_theoretical_heterozygosity_per_generation( df_het_per_cycle,
															ddf_ne_by_gp_file_by_cycle[ s_gp_file_name ],
															f_cycles_per_generation,
															f_theoretical_ne )
		if b_plot == True and b_can_plot == True:
			
			f_ne0=f_theoretical_ne if f_theoretical_ne is not None \
					else np.mean(  list( ddf_ne_by_gp_file_by_cycle[ s_gp_file_name ].values() ) )			

			f_he0=ddf_mean_het_by_gp_file_by_cycle[ s_gp_file_name ][ i_initial_cycle_number ]

			s_title="Expected vs. theoretical heterozygosity" \
				+ "\nSim cycles: " \
				+ str( i_initial_cycle_number ) \
				+ "-" + str( i_final_cycle_number ) + "." \
				+ ".  Ne for theoretical: " + str( f_ne0 ) \
				+ ".  Hz of initial gen: " \
				+ str( round( f_he0, 4) ) \
				+ "\nCycles per generation: " \
				+ str ( int ( round( f_cycles_per_generation ) ) ) + "."

			s_het_label="expected under HW, using allele freqs"
			s_theoretical_label="theoretical, Hz_i = Hz_{i-1} X ( 1 - 1/(2Ne) )"

			s_xaxis_label="generation"
			s_yaxis_label="heterozygosity"
			
			plot_two_dicts_similarly_scaled( df_expected_het_by_gen, 
										df_theoretical_het_by_gen, 
										s_data1_label=s_het_label,
										s_data2_label=s_theoretical_label,
										s_xaxis_label=s_xaxis_label,
										s_yaxis_label=s_yaxis_label,
										s_title=s_title )
		#end if plot is true

	#end for each genepop file named in the tsv file

	return { "mean_hets" : ddf_mean_het_by_gp_file_by_cycle, 
					"nes": ddf_ne_by_gp_file_by_cycle  }
#end get_expected_vs_observed_heterozygosity
		
def get_expected_vs_observed_loss_heterozygosity( s_ne_tsv_file, 
															i_initial_cycle_number, 
															i_final_cycle_number,
															f_cycles_per_generation,
															i_min_loci_number=None,
															i_max_loci_number=None,
															f_theoretical_ne= None,
															b_plot=True, 
															s_plot_file=None,
															s_plot_type="png" ):

	'''
	This def is designed to use a theoretical Ne value, either as passed by
	caller, or the mean of estimates in the tsv file for the cycles initaial to final.
	to use in the caluculation,
			1 - ( 1 - 1/(2Ne) )**t
	for the tth generation This is then compared to the loss as computed by
	Het=sum_i_to_L(  1 - sum_j_to_A( allele-frequency ** 2 ) )/L, in a generation
	(pop section, for a cycle that is the first in a generation series, as given
	by cycles per generation, starting with the initial, its individuals with
	L loci, and each loci having some L alleles.

	Assumption:  that the (genepop) file(s) named in column one of the s_ne_tsv_file 
			argument exist and have either absolute paths (the current
			default method used to write them to the tsv file), or relative
			paths that are accessible from the working directory of the
			current python environment.

	param s_ne_tsv_file, names the table file output from using module
		pgdriveneestimator.py to generate ne estimations, either
		via the negui interface or the command line use of pgdriveneestimator.py 
		itself, on genepop files generated by the negui implementation of
		the AgeStructureNe simulation driver.
	param i_initial_cycle_number, integer giving the ith pop section,
		where i is the poplulation (cycle) that gives the initital Ne value on which
		to base the expected loss of het, that is the Ne value in ( 1-2/Ne )^t for
		each subsequent cycle t.
	param i_final_cycle_number, if not None, then an integer giving the highest pop section
		(cycle) value to analyze.  If None, then analyze all pop sections with numbers 
		>= i_initial_cycle_number
	param f_cycles_per_generation, number of breeding cycles comprising a generation.
	param i_min_loci_number, if not none than the He calculation will not use any of the loci
			in the range 1 to i, where i_min_loci_number is i + 1.
	param i_ma_loci_number, if not none than the He calculation will not use any of the N loci
			in the range j to N, where i_man_loci_number is j - 1.

	param b_plot, if true and maplotlib was importable, then a plot will be done.
	param s_plot_file, if not none and b_plot is true, then plot to file with this name.
			If s_plot_file is None, then call pyplot.show() after the plot command.
	param s_plot_type, if b_plot is true and s_plot_file is not None, the file type
			to be written is given by this extension, defaulting to png.

	'''

	'''
	The file_names property of the tsv file manager object
	yields the set (ie.unique values, but returned as a list) 
	of file names in column 1 of the tsv file:
	'''

	ddf_mean_het_by_gp_file_by_cycle, ddf_ne_by_gp_file_by_cycle = \
			get_mean_hets_and_ne_for_cycles( s_ne_tsv_file, 
												i_initial_cycle_number,
												i_final_cycle_number, 
												i_min_loci_number, 
												i_max_loci_number )

	#Two dicts for the return value:
	ddf_expected_het_loss_by_file={}
	ddf_theoretical_het_loss_by_file={}

	for s_gp_file_name in ddf_mean_het_by_gp_file_by_cycle:

		df_mean_het_loss_by_cycle=convert_mean_hets_to_het_loss( ddf_mean_het_by_gp_file_by_cycle[ s_gp_file_name]  )
		df_mean_het_loss_by_generation=get_per_generation_het_from_per_cycle_het( df_mean_het_loss_by_cycle, 
																						f_cycles_per_generation )
		df_theoretical_het_loss_by_generation=get_theoretical_het_loss_per_generation( \
															ddf_ne_by_gp_file_by_cycle[ s_gp_file_name ], 
																						f_cycles_per_generation,
																						f_theoretical_ne )
	
		#Add to the dicts that get returned:
		ddf_expected_het_loss_by_file[ s_gp_file_name ] = df_mean_het_loss_by_generation

		ddf_theoretical_het_loss_by_file[ s_gp_file_name ] = df_theoretical_het_loss_by_generation

		f_ne0=f_theoretical_ne if f_theoretical_ne is not None \
				else np.mean( list(ddf_ne_by_gp_file_by_cycle[ s_gp_file_name ].values()) ) 

		df_theoretical_as_perc={ i_gen: 100 * ( 1.0 - df_theoretical_het_loss_by_generation[ i_gen ] ) \
																			for i_gen in df_theoretical_het_loss_by_generation } 
		df_expected_as_perc={ i_gen: 100 * ( 1.0 - df_mean_het_loss_by_generation[ i_gen ] )  \
															for i_gen in df_mean_het_loss_by_generation }	

		df_expected_as_perc_sorted= { i_key : df_expected_as_perc[ i_key ] for i_key in sorted( df_expected_as_perc ) }
		df_theoretical_as_perc_sorted = { i_key : df_theoretical_as_perc[ i_key ] for i_key in sorted( df_theoretical_as_perc ) }

		if b_plot == True and b_can_plot == True:
			
			s_title="Percent expected vs theoretical retained heterozygosity" \
				+ "\nSim cycles: " \
				+ str( i_initial_cycle_number ) \
				+ "-" + str( i_final_cycle_number ) + "." \
				+ ".  Ne for theoretical: " + str( f_ne0 ) \
				+ "\nCycles per generation: " \
				+ str( int( round( f_cycles_per_generation ) ) )

			s_expected_label="expected under HW, using allele frequencies"
			s_theoretical_label="theoretical: loss_gen_i =  1 - ( 1 - 1/2Ne )^i"

			s_xaxis_label="generation"
			s_yaxis_label="percent heterozygosity retained"
					
			plot_two_dicts_similarly_scaled( df_expected_as_perc_sorted, 
							df_theoretical_as_perc_sorted, 
							s_data1_label=s_expected_label,
							s_data2_label=s_theoretical_label,
							s_xaxis_label=s_xaxis_label,
							s_yaxis_label=s_yaxis_label,
							s_title=s_title )

	#end for each genepop file named in the tsv file

	return { "expected_het_loss" : ddf_expected_het_loss_by_file, 
					"theoretical_het_loss" : ddf_theoretical_het_loss_by_file }

#end get_expected_vs_observed_loss_heterozygosity

if __name__ == "__main__":

	import argparse	as ap

	LS_ARGS_SHORT=[ "-t", "-i" , "-f" , "-g", "-n", "-m", "-s"  ]
	LS_ARGS_LONG=[ "--tsvfile" , "--initialcycle", "--finalcycle", "--cyclespergen", "--minloci", "--maxloci", "--test" ]
	LS_ARGS_HELP=[ "names tsv file of ne estimations as generated " \
						+ "from negui interface or console command using pgdriveneestimator.py",
						"Integer The ith cycle (pop section in the source genepop file.  This " \
						+	"number will be the initial pop used to get Ne for " \
						+"the expected het loss calculation).",
						"Integer, the jth cycle, to be the last cycle analyzed.", 
						"Numeric (int or float) breeding cycles per cycle",
						"Integer i giving the min value for a range of loci (as ordered in " \
						+ "the genepop file), the ith to the jth", 
						"Integer j giving the max value for a range of loci, the ith to the jth",
						"String, [ 'hetloss' | 'het'  ], to compare expected vs observed loss of " \
						+ "heterozygosity, or expected vs observed heterozygosity" ]

	LS_OPTIONAL_ARGS_SHORT=[ "-e" ]
	LS_OPTIONAL_ARGS_LONG=[ "--expectedne" ]
	LS_OPTIONAL_ARGS_HELP=[ "float, Ne value to use for the calculation of the expected heterozygosity " \
								+ "( 1-( 1-1/(2Ne) )^{repro_cycle_number}), and loss of heterozygosity, " \
								+ "( Hz_repro_cycle_i=Hz_repro_cycle_i-1 * ( 1 - 1/( 2Ne ) ) ).  " \
								+ "Default is the mean of the LDNe estimations" ]
						


	ddefs_by_test_name={ "hetloss" : get_expected_vs_observed_loss_heterozygosity, 
									"het":get_expected_vs_observed_heterozygosity }

	o_parser=ap.ArgumentParser()

	o_arglist=o_parser.add_argument_group( "args" )

	i_total_nonopt=len( LS_ARGS_SHORT )
	i_total_opt=len( LS_OPTIONAL_ARGS_SHORT )

	for idx in range( i_total_nonopt ):
		o_arglist.add_argument( \
				LS_ARGS_SHORT[ idx ],
				LS_ARGS_LONG[ idx ],
				help=LS_ARGS_HELP[ idx ],
				required=True )
	#end for each required argument

	for idx in range( i_total_opt ):
		o_parser.add_argument( \
				LS_OPTIONAL_ARGS_SHORT[ idx ],
				LS_OPTIONAL_ARGS_LONG[ idx ],
				help=LS_OPTIONAL_ARGS_HELP[ idx ],
				required=False )
	#end for each required argument

	o_args=o_parser.parse_args()

	s_tsv_file=o_args.tsvfile

	i_initial_cycle=int( o_args.initialcycle )
	i_final_cycle=int( o_args.finalcycle )

	f_cycles_per_generation=float( o_args.cyclespergen )
	i_min_loci=int( o_args.minloci )
	i_max_loci=int( o_args.maxloci )
	s_test_name=o_args.test 

	r_def_to_call=None	

	if s_test_name not in ddefs_by_test_name:
		print( "\"test\" arg must be one of: " \
					+ ",".join( list(ddefs_by_test_name.keys()) )  \
					+ "." )

		sys.exit()
	else:
		r_def_to_call=ddefs_by_test_name[ s_test_name ]

	#end if non-valid test name

	if o_args.expectedne is not None:
		f_expected_ne=float( o_args.expectedne )
	else:
		f_expected_ne=None
	#end if caller passed an expected Ne value

	r_def_to_call( s_tsv_file, 
					i_initial_cycle, 
					i_final_cycle, 
					f_cycles_per_generation, 
					i_min_loci, i_max_loci, f_expected_ne )

#end if main

