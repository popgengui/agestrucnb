
'''
Description
We needed a suite of tests to validate the simulation and nb output.  
The first of these requested by Gordon is a comparison of expected
hegerozygosity, calculated from the Ne value, for the tth generation
as ( 1-2/Ne )**t, vs  the "observed" 
loss of heterozygosity, calculated for each gen as the mean ( 1-He ), with
He_l = sum_i_l=1 to n_l (i_l**2), with i_l=allele freq of the ith of n alleles 
for the lth loci.
'''

__filename__ = "pgvalidationtests.py"
__date__ = "20170130"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import numpy as np

import genepopfilemanager as gpm
import genepopfilelociinfo as gpl
import pgutilityclasses as pguc

b_can_plot=True
try:
	import matplotlib.pyplot as pt
except ImportError as oie:
	print( "The matplotlib module was not found.  Results cannot be plotted." )
	b_can_plot=False
#end


def get_mean_het_per_generation( o_gp_file, 
								i_initial_generation, 
								i_final_generation,
								i_min_loci_number=None, 
								i_max_loci_number=None ):

	MAX_POSSIBLE_LOCI=int( 1e32 )

	li_pop_subsample=list( \
				range( i_initial_generation, i_final_generation + 1  ) )

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
	##### temp
	print( "--------------" )
	print( "df_mean_het_by_pop: " + str( df_mean_het_by_pop ) )
	#####

	return df_mean_het_by_pop
#end get_mean_het_per_generation

def get_expected_het_loss_per_generation( o_tsv_file, s_genepop_file, 
														i_initial_generation_number,
														i_final_generation_number ):
	'''

	The calculation for expected loss of heterozygosity is from
	From http://labs.russell.wisc.edu/peery/files/2011/12/Primer-in-Population-Genetics.pdf

	This def also returns the Ne value for the initial generation.
	'''

	df_expected_het_loss_by_generation={}

	o_tsv_file.setFilter( "original_file", lambda x:x==s_genepop_file )

	'''
	This local def will be passed to test gen ranges.
	The arg as string required by the o_tsv_file 
	(class NeEstimationTableFileManager) object's setFilter.  
	All filers must take one string arg and return a boolean
	'''
	def gen_range_check( s_gen_number_as_string ):
		i_this_gen=int( s_gen_number_as_string )
		b_return_val= i_this_gen >= i_initial_generation_number \
							and i_this_gen <= i_final_generation_number
		return b_return_val
	#end def gen_range_check

	o_tsv_file.setFilter( "pop" , gen_range_check )

	ls_pop_and_ne=o_tsv_file.getFilteredTableAsList( [ "pop", "est_ne" ] )

	#The zeroth item in the ls_pop_and_ne list is the header, so we
	#process the entries with indices 1 through the last.
	ddf_ne_by_pop_number={ int( s_vals.split()[0] ):float( s_vals.split()[1] ) \
												for s_vals in ls_pop_and_ne[ 1 : ] } 

	f_ne_for_initial_pop=ddf_ne_by_pop_number[ i_initial_generation_number ]

	f_one_over_2Ne=1.0/( 2.0*f_ne_for_initial_pop )

	f_one_minus_one_over_2Ne=1 - f_one_over_2Ne

	'''
	We want zero loss of het in the
	first generation, so the counter,
	which gives the exponent in the 
	loss calculation, will be at zero
	for the first (initial) generation. 
	'''
	i_gen_count = -1

	li_sorted_gen_numbers=ddf_ne_by_pop_number.keys()
	li_sorted_gen_numbers.sort()

	for i_gen in li_sorted_gen_numbers:
		i_gen_count += 1

		'''
		We raise ( 1 - 1/2Ne ) to  t = gen_counter, subtract
		that value from 1:
		'''
		f_loss_this_gen=1 - (  ( f_one_minus_one_over_2Ne )**i_gen_count  )

		df_expected_het_loss_by_generation[ i_gen ] = f_loss_this_gen
	#end for each generation
	
	return f_ne_for_initial_pop, df_expected_het_loss_by_generation

#end get_expected_het_loss_per_generation

def convert_mean_hets_to_het_loss( df_mean_het_by_gen ):

	df_mean_het_loss_by_gen={}

	i_min_het_number=min( df_mean_het_by_gen.keys() )

	f_h0=df_mean_het_by_gen[ i_min_het_number ]

	li_sorted_gen_numbers=df_mean_het_by_gen.keys()
	li_sorted_gen_numbers.sort()

	for i_gen_number in li_sorted_gen_numbers:
		f_diff=f_h0 - df_mean_het_by_gen[ i_gen_number ]
		df_mean_het_loss_by_gen[ i_gen_number ] = f_diff
	#end for each gen number

	return df_mean_het_loss_by_gen

#end convert_mean_hets_to_het_loss

def get_expected_vs_observed_loss_heterozygosity( s_ne_tsv_file, 
															i_initial_generation_number, 
															i_final_generation_number,
															i_min_loci_number=None,
															i_max_loci_number=None,
															b_plot=True, 
															s_plot_file=None,
															s_plot_type="png" ):
	'''
	This def is designed to test Ne estimations done on simuPOP generated
	genepop files, with the ith pop section in the genepop file corresponding
	the ith simulated generation.

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
	param i_initial_generation_number, integer giving the ith pop section,
		where i is the poplulation (generation) that gives the initital Ne value on which
		to base the expected loss of het, that is the Ne value in ( 1-2/Ne )^t for
		each subsequent generation t.
	param i_final_generation_number, if not None, then an integer giving the highest pop section
		(generation) value to analyze.  If None, then analyze all pop sections with numbers 
		>= i_initial_generation_number
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

	o_tsv_file=pguc.NeEstimationTableFileManager( s_ne_tsv_file )

	'''
	The file_names property of the tsv file manager object
	yields the set (ie.unique values, but returned as a list) 
	of file names in column 1 of the tsv file:
	'''
	ls_genepop_files_used_to_produce_ne_table=o_tsv_file.file_names

	for s_genepop_file in ls_genepop_files_used_to_produce_ne_table:

		o_this_gp_file=gpm.GenepopFileManager( s_genepop_file )

		i_total_generations=o_this_gp_file.pop_total

		if i_final_generation_number > i_total_generations:
			s_msg="In pgvalidationtests, def "  \
					+ "get_table_expected_vs_observed_loss_heterozygosity, " \
					+ "arg value for final generation number, " \
					+ str( i_final_generation_number ) \
					+ ", it greater than the available number of generations, " \
					+ str( i_total_generations ) + "."
			raise Exception ( s_msg )
		#end if requested final gen is too large

		if i_initial_generation_number < 1 \
					or i_initial_generation_number > i_total_generations:
			s_msg="In pgvalidationtests, def "  \
					+ "get_table_expected_vs_observed_loss_heterozygosity, " \
					+ "arg value for initial generation number, " \
					+ str( i_final_generation_number ) \
					+ ", it outside the valid range, 1 - " \
					+ str( i_total_generations ) + "."
			raise Exception ( s_msg )
		#end if requested final gen is too large

		i_actual_final_gen=min( i_final_generation_number, i_total_generations )

		df_mean_het_by_gen=get_mean_het_per_generation( o_this_gp_file, 
															i_initial_generation, 
															i_actual_final_gen, 
															i_min_loci_number, 
															i_max_loci_number )

		df_mean_het_loss_by_gen=convert_mean_hets_to_het_loss( df_mean_het_by_gen )
		
		##### temp
		print( "-----------------" )
		print( "df_mean_het_loss_by_gen: " + str( df_mean_het_loss_by_gen ) )
		#####

		o_tsv_file.unsetAllFilters()

		f_ne_for_initial_pop, df_expected_het_loss_by_gen= \
					get_expected_het_loss_per_generation( o_tsv_file, 
														s_genepop_file, 
														i_initial_generation, 
														i_actual_final_gen )

		if b_plot == True:

			FONTSIZE=12
			PLOTFONTSIZE=10
			s_title="Expected het loss compared with" \
						+ "\nper-generation calculated Het loss, " \
						+ "\nNe of initial generation: " + str( f_ne_for_initial_pop ) \
						+ "."

			li_xlimits=[ i_initial_generation - 1, i_actual_final_gen + 1 ]
			
			f_y_limits_units=(1/10.0)

			f_label_y_space_unit=(1/30.0)
			f_label_x_space_unit=(1/5.0)

			f_label_x_coord_offset=( li_xlimits[ 1 ] - li_xlimits[ 0 ] ) * f_label_x_space_unit

			s_het_label="mean het"
			s_expected_label="expected"

			s_xaxis_label="generation"
			s_yaxis_label="percent heterozygosity loss"

			f_ne0=df_expected_het_loss_by_gen[ i_initial_generation ]


			df_expected_as_perc={ i_gen: 100 * ( 1.0 - df_expected_het_loss_by_gen[ i_gen ] ) for i_gen in df_expected_het_loss_by_gen } 
			df_het_loss_as_perc={ i_gen: 100 * ( 1.0 - df_mean_het_loss_by_gen[ i_gen ] ) for i_gen in df_mean_het_loss_by_gen }	

			f_min_y_value=min( list( df_expected_as_perc.values() ) + list( df_het_loss_as_perc.values() ) )
			f_max_y_value=max( list( df_expected_as_perc.values() ) + list( df_het_loss_as_perc.values() ) )
			f_y_range=f_max_y_value-f_min_y_value
			lf_ylimits=[ f_min_y_value - f_y_range*f_y_limits_units, 100 ]

			f_label_y_coord_offset=( lf_ylimits[ 1 ] - lf_ylimits[ 0 ] ) * f_label_y_space_unit
			

						
			i_max_gen_number=max( df_mean_het_loss_by_gen.keys() )
			f_last_het_value=df_het_loss_as_perc[ i_max_gen_number ]
			f_last_expected_value=df_expected_as_perc[ i_max_gen_number ]
			

			o_fig=pt.figure()
			o_subplt=o_fig.add_subplot(111)
			o_subplt.plot( df_het_loss_as_perc.keys(), list( df_het_loss_as_perc.values() ) )
			o_subplt.text( i_max_gen_number -  f_label_x_coord_offset , f_last_het_value + f_label_y_coord_offset, 
																							s_het_label, fontsize=PLOTFONTSIZE )

			o_subplt.plot( df_expected_as_perc.keys(), list( df_expected_as_perc.values() ) )
			o_subplt.text( i_max_gen_number - f_label_x_coord_offset, 
									f_last_expected_value + f_label_y_coord_offset, 
																		s_expected_label, fontsize=PLOTFONTSIZE )

			o_subplt.set_ybound( lower=lf_ylimits[0], upper=lf_ylimits[ 1 ] )
			o_subplt.set_xlabel( s_xaxis_label, fontsize=FONTSIZE )
			o_subplt.set_ylabel( s_yaxis_label, fontsize=FONTSIZE )
			o_subplt.set_title( s_title, fontsize=FONTSIZE )
			pt.show()

			if s_plot_file is not None:
				pass
			#end if no plot file
	#end for each genepop file named in the tsv file

	return { "mean_het_by_gen" : df_mean_het_by_gen, "expected_het_loss_by_gen" : df_expected_het_loss_by_gen }
#end get_expected_vs_observed_loss_heterozygosity

if __name__ == "__main__":

	import argparse	as ap

	LS_ARGS_SHORT=[ "-t", "-i" , "-f"  , "-n", "-m"  ]
	LS_ARGS_LONG=[ "--tsvfile" , "--initialgen", "--finalgen", "--minloci", "--maxloci" ]
	LS_ARGS_HELP=[ "names tsv file of ne estimations as generated " \
						+ "from negui interface or console command using pgdriveneestimator.py",
						"Integer The ith generation (pop section in the source genepop file.  This " \
						+	"number will be the initial pop used to get Ne for " \
						+"the expected het loss calculation).",
						"Integer, the jth generation, to be the last generation analyzed.", 
						"Integer i giving the min value for a range of loci (as ordered in " \
						+ "the genepop file), the ith to the jth",
						"Integer j giving the max value for a range of loci, the ith to the jth" ]

	o_parser=ap.ArgumentParser()

	o_arglist=o_parser.add_argument_group( "args" )

	i_total_nonopt=len( LS_ARGS_SHORT )

	for idx in range( i_total_nonopt ):
		o_arglist.add_argument( \
				LS_ARGS_SHORT[ idx ],
				LS_ARGS_LONG[ idx ],
				help=LS_ARGS_HELP[ idx ],
				required=True )
	#end for each required argument

	o_args=o_parser.parse_args()

	s_tsv_file=o_args.tsvfile
	i_initial_generation=int( o_args.initialgen )
	i_final_generation=int( o_args.finalgen )
	i_min_loci=int( o_args.minloci )
	i_max_loci=int( o_args.maxloci )
	
	get_expected_vs_observed_loss_heterozygosity( s_tsv_file, i_initial_generation, i_final_generation, i_min_loci, i_max_loci )

#end if main

