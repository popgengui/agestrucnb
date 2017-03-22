'''
Description
'''
__filename__ = "plot.ages.panda.py"
__date__ = "20170309"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys

try:
	import pandas as pd
	import matplotlib.pyplot as pt
except ImportError as oie:
	s_msg="Requires package pandas."
	raise Exception( str(oie) + s_msg )
#end try, except

def mymain( s_ages_file ):
	df = pd.read_csv( s_ages_file, index_col='generation', sep="\t" )
	df.plot( kind='bar', stacked=True )	
	pt.show()
	return
#end mymain

if __name__ == "__main__":
	import argparse	as ap 
	LS_ARGS_SHORT=[ "-f" ] 
	LS_ARGS_LONG=[ "--agesfile" ] 
	LS_ARGS_HELP=[ "file output by simiulatuo run with extension, \"_age_counts_by_gen.csv\""]

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

	s_ages_file=o_args.agesfile

	mymain( s_ages_file )
#end if main

