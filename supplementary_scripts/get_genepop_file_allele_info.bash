#!/usr/bin/env python

def get_allele_info ( s_genepop_file ):






if __name__ == "__main__":

	import argparse	as ap

	LS_ARGS_SHORT=[ "-f"  ]
	LS_ARGS_LONG=[ "--genepopfile" ]
	LS_ARGS_HELP=[ "genepop file" ]

						

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

	s_genepop_file=o_args.genepopfile

	get_allele_info( s_genepop_file )
#end if main
