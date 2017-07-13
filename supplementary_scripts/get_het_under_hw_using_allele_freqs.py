'''
Description

2017_06_26.  A script to call the def in pgvalidationtests.py that 
computes mean heterozygosity values per pop section of
gp file using allele frequences (see def get_mean_het_per_cycle 
in module pgvalidationtests.py).
'''

__filename__ = "get_het_under_hw_using_allele_freqs.py"
__date__ = "20170626"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys


try:
	import pgvalidationtests as pgval
	import genepopfilemanager as gpf

except ImportError as oie:

	try:
		import supp_utils as supu
		supu.add_main_pg_dir_to_path()		
		import pgvalidationtests as pgval
		import genepopfilemanager as gpf
	except:
		s_msg= "In plot_het_under_hw_using_allele_freqs.py, " \
					+ "the script could not import the pgvalidationtests.py and/or " \
					+ "the genepopfilemanager.py  module(s).  " \
					+ "Please make sure that this script's module is in the \"supplemental_scripts\"" \
					+ "subdirectory of your negui directory, so that it can acces the " \
					+ "supp_utils.py module, in order to get the path to your negui modules."
		raise Exception( s_msg )
	#end try, except
#end try...except


def get_pop_range( o_genepop_file_manager, i_init_cycle, i_final_cycle ):
		
		i_cycle_start=i_init_cycle
		i_cycle_end=i_final_cycle

		#We reassign to pop 1 if user passed a None value:
		if i_init_cycle is None:
			i_cycle_start=1
		#end if init cycle None

		#We reassign to last pop if user passed None
		if i_final_cycle is None:
			i_cycle_end=o_genepop_file_manager.pop_total
		#end if i_final_cycle is None
		
		return i_cycle_start, i_cycle_end
#end get_pop_range
	

def get_loci_range( o_genepop_file_manager, i_init_loci, i_final_loci ):
		
		i_loci_start=i_init_loci
		i_loci_end=i_final_loci

		#We reassign to pop 1 if user passed a None value:
		if i_init_loci is None:
			i_loci_start=1
		#end if init loci None

		#We reassign to last pop if user passed None
		if i_final_loci is None:
			i_loci_end=o_genepop_file_manager.loci_total
		#end if i_final_loci is None
		
		return i_loci_start, i_loci_end
#end get_loci_range

def mymain( s_genepop_file, 
				i_init_cycle,
				i_final_cycle,
				i_cycles_per_gen,
				i_min_loci,
				i_max_loci ):
	
	o_genepop_file_manager=gpf.GenepopFileManager( s_genepop_file )

	i_cycle_start, i_cycle_end=get_pop_range( o_genepop_file_manager, i_init_cycle, i_final_cycle )

	i_loci_start, i_loci_end = get_loci_range( o_genepop_file_manager, i_min_loci, i_max_loci )

	df_het_values_by_pop=pgval.get_mean_het_per_cycle( o_gp_file=o_genepop_file_manager, 
								i_initial_cycle=i_cycle_start, 
								i_final_cycle=i_cycle_end,
								i_min_loci_number=i_loci_start, 
								i_max_loci_number=i_loci_end  )
	
	l_popnums=list( df_het_values_by_pop.keys() )

	l_popnums.sort()

	i_numpops=len( l_popnums )

	for idx in range( 0, i_numpops, i_cycles_per_gen ):

		i_pop=l_popnums[ idx ]

		print( str( i_pop ) + "\t" + str( df_het_values_by_pop[ i_pop ] ) )

	#end for each pop	
	
	return
#end mymain



if __name__ == "__main__":
	import argparse	as ap

	LS_ARGS_SHORT=[ "-g"  ]
	LS_ARGS_LONG=[ "--genepopfile"  ]
	LS_ARGS_HELP=[ "genepop file" ]

	LS_OPTIONAL_ARGS_SHORT=[ "-i" , "-f" , "-c", "-n", "-m" ]
	LS_OPTIONAL_ARGS_LONG=[  "--initialcycle", "--finalcycle", "--cyclespergen", "--minloci", "--maxloci" ]
	LS_OPTIONAL_ARGS_HELP=[ "Integer The ith cycle (pop section in the source genepop file.  This " \
						+	"number will be the initial pop on which He is calculated. Default 1",
						"Integer, the jth cycle, to be the last cycle analyzed. Default is N for a file with N pops.", 
						"Numeric (int or float) breeding cycles per pop entry (ex, if 2, then for i to j, " \
								+ "output includes the He for pop i, i+2, i+4, ... f in {j, j-1}).  Default is 1.",
						"Integer i giving the min value for a range of loci (as ordered in " \
						+ "the genepop file), the ith to the jth.  Default is 1.",
						"Integer j giving the max value for a range of loci, the ith to the jth. Default is the Nth for a file with N loci." ]
						

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

	s_genepop_file=o_args.genepopfile


	i_init_cycle=None if o_args.initialcycle is None else int( o_args.initialcycle )
	i_final_cycle=None if o_args.finalcycle is None else int( o_args.finalcycle )
	i_cycles_per_gen=1 if o_args.cyclespergen is None else int( round( float( o_args.cyclespergen ) ) )
	i_min_loci=None if o_args.minloci is None else int( o_args.minloci )
	i_max_loci=None if o_args.maxloci is None else int( o_args.maxloci )

	mymain( s_genepop_file,
				i_init_cycle,
				i_final_cycle,
				i_cycles_per_gen,
				i_min_loci,
				i_max_loci )


#end if main

