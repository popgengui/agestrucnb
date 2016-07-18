'''
Description
from stderr output table from pgdriveneestimator.py, using "testmulti" or "testserial"
thatlists indices of individuals for each replicate, find for each indiv, the frequency
with which it is in the same replicate as the indiv whose index is provided as arg 2
'''
__filename__ = "get_freq_idx_paired_with_other_idx.py"
__date__ = "20160709"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"
import sys

import MyUtilities.misc_utilities as modut

import numpy as np

if __name__ == "__main__":

	ls_args=[ "table with indiv indices list in col5", "index of indiv for test", "total individuals in orig genepop file" ]

	s_usage=modut.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage
	
	s_table=sys.argv[1]
	idx_indiv_of_interest=int( sys.argv[2] )
	itotindiv=int( sys.argv[3] )

	ofile=open( sys.argv[1], 'r' )

	li_freqs_of_indiv_paired_with_our_indiv=[ 0 for i in range( itotindiv ) ]

	for sline in ofile:
		ls_vals=sline.strip().split( "\t" )
		s_list=ls_vals[4]
		di_indivs_this_replicate={ int( i ):1 for i in s_list.split( "," ) }

		if idx_indiv_of_interest in di_indivs_this_replicate:
			for thisi in di_indivs_this_replicate:
				#zero as index in these lists does
				#not designate an indiv (only the "pop" entry
				#in the genepop file)
				if thisi != idx_indiv_of_interest and thisi != 0:
					#subtract 1 to accomodate python zero-indexing:
					li_freqs_of_indiv_paired_with_our_indiv[ thisi - 1 ]+=1 
				#end if not equal to index arg
			#end for each index in the list
		#end if this list contains our idx of interest
	#end for each line in file

	ofile.close()

	for indiv in range( len( li_freqs_of_indiv_paired_with_our_indiv ) ):
		print ( str( indiv + 1 ) +  "\t" + str( li_freqs_of_indiv_paired_with_our_indiv[ indiv ] ) )
	#end for each indiv

	mymean=str( round( np.mean( li_freqs_of_indiv_paired_with_our_indiv ), 2 ) )
	mymedian=str( round(  np.median( li_freqs_of_indiv_paired_with_our_indiv ), 2 ) )
	mystd=str( round( np.std( li_freqs_of_indiv_paired_with_our_indiv ), 2 )  )
	mymax=str( max( li_freqs_of_indiv_paired_with_our_indiv ) )
	mymin=str( min( li_freqs_of_indiv_paired_with_our_indiv ) )

#	sys.stderr.write( "\t".join( [ "mean", "median", "stddev", "max", "min" ] ) + "\n" )
	sys.stderr.write( "\t".join( [mymean, mymedian, mystd, mymax, mymin ] ) + "\n" )




		

#end if main

