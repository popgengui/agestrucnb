#!/usr/bin/env python

#Adapted for python from script gnuplot_compare_sim_nb_to_neest.bash.  

#input table file should have cols generation<tab>Nb value
#input tsv file from NeEstimator should have generation (1-based)
#in col 2 and Nb estimation in col 11

#requires matplotlib.


from __future__ import division
from __future__ import print_function
from past.utils import old_div
import matplotlib.pyplot as pt
import sys
import os

def get_pwop_and_tsv_values( mytable, mytsv ):

	o_pwop_table=open( mytable )
	o_tsv_table=open( mytsv )

	if b_pwop_has_header:
		o_pwop_table.readline()
	#end if header pwop

	if b_tsv_has_header:
		o_tsv_table.readline()
	#end if

	def splitforcol( s_entry, idx):
		return s_entry.strip().split( "\t" )[ idx ]
	#end splitforcol

	df_pwop_entries_by_cycle = { int( splitforcol( s_line, 0 ) ) + 1 : float( splitforcol( s_line, 1 ) ) \
																	for s_line in o_pwop_table.readlines() }

	df_ldne_by_cycle = { int( splitforcol( s_line, const_tsv_gen_col ) ) : float( splitforcol( s_line, const_tsv_nb_col ) )  \
																							for s_line in o_tsv_table.readlines() }

	
	##### temp
	print( "pwops: " + str( df_pwop_entries_by_cycle ) )
	print( "ldnes: " + str( df_ldne_by_cycle ) )
	#####

	return df_pwop_entries_by_cycle, df_ldne_by_cycle
#end get_pwop_and_tsv_values


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

	f_y_limits_units=(old_div(1,10.0))
	f_x_limits_units=(old_div(1,60.0) )

	f_label_y_space_unit=(old_div(1,30.0))
	f_label_x_space_unit=(old_div(1,5.0))

	v_min_x_value_dict1=max( minxval, min( list( d_dict1.keys() ) ) )
	v_max_x_value_dict1=min( maxxval,  max( list( d_dict1.keys() ) ) )

	v_min_y_value_dict1=max( minyval,  min( list( d_dict1.values() ) ) )
	v_max_y_value_dict1=min( maxyval, max( list( d_dict1.values() ) ) )

	v_min_x_value_dict2=max( minxval, min( list( d_dict2.keys() ) ) )
	v_max_x_value_dict2=min( maxxval,  max( list( d_dict2.keys() ) ) )

	v_min_y_value_dict2=max( minyval,  min( list( d_dict2.values() ) ) )
	v_max_y_value_dict2=min( maxyval, max( list( d_dict2.values() ) ) )


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
	o_subplt.plot( list(d_dict1.keys()), list( d_dict1.values() ), linewidth=PLOTLINEWIDTH )
	o_subplt.plot( list(d_dict2.keys()), list( d_dict2.values() ), linewidth=PLOTLINEWIDTH )
	o_subplt.plot( [ v_min_x_value, v_max_x_value ], [ target_nb, target_nb ], linewidth=PLOTLINEWIDTH )

	o_subplt.set_ybound( lower=lf_ylimits[0], upper=lf_ylimits[ 1 ] )
	o_subplt.set_xlabel( s_xaxis_label, fontsize=FONTSIZE )
	o_subplt.set_ylabel( s_yaxis_label, fontsize=FONTSIZE )
	o_subplt.set_title( s_title, fontsize=FONTSIZE )
	o_subplt.legend( [ s_data1_label , s_data2_label, "target Nb" ], frameon=False, fontsize=PLOTFONTSIZE )

	pt.show()

	o_fig=None

	if s_plot_file_name is not None:
		pt.savefigure( s_file_name )
	#end if no plot file
	return
#end plot_two_dicts_similarly_scaled


def mymain ( mytable, mytsv ):
	df_pwop_entries_by_cycle, df_ldne_by_cycle = \
			get_pwop_and_tsv_values( mytable, mytsv )

	plot_two_dicts_similarly_scaled( df_pwop_entries_by_cycle, 
										df_ldne_by_cycle,
										"PWOP sim Nb",
										"LDNE estimate",
										"cycle number",
										"Nb or Ne",
										mytitle )
#end def mymain


if __name__=="__main__":

	numrequiredargs=10

	mys=os.path.basename( __file__ )

	numargspassed=len( sys.argv ) - 1

	if numargspassed != numrequiredargs:

		print( "usage: " +  mys  )
		print( "args: " )
		print( "       <file with nb values table> " )
		print( "       <file, *.tsv,  with NeEstimator Nb values> " )
		print( "       <int, number of generations> " )
		print( "       <int, min value for cycle axis (x-axis)" )
		print( "       <int, max value for cycle axis (x-axis)" )
		print( "       <int, min value for Nb axis (y-axis)" )
		print( "       <int, max value for Nb axis (y-axis)" )
		print( "       <True|False, use bias adjusted estimate" )
		print( "       <int, target Nb>" )
		print( "       <title> (use \"newline\" to break the title into multiple lines)" )

		sys.exit()

	#end if num args invalid

	mytable=sys.argv[ 1 ]
	mytsv=sys.argv[ 2 ]
	total_gens=int( sys.argv[ 3 ] )
	minxval=float( sys.argv[ 4 ] )
	maxxval=float( sys.argv[ 5 ] )
	minyval=float( sys.argv[ 6 ] )
	maxyval=float( sys.argv[ 7 ] )
	use_bias_adjusted_ldne=bool( sys.argv[ 8 ] )
	target_nb=float( sys.argv[ 9 ] )
	mytitle=sys.argv[ 10 ]

	const_tsv_gen_col=1
	const_tsv_nb_col=10
	cont_tsv_nb_adjusted_col=18

	#global replacement of newline with 
	#literal newline (i.e. 2-line substitution
	#breaks title into multi lines:
	mynewtitle=mytitle.replace( "newline", "\n" ) 

	b_pwop_has_header=False
	b_tsv_has_header=True

	mymain( mytable, mytsv )	
