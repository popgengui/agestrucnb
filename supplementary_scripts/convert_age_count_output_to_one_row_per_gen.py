#!/usr/bin/env python
'''
Description
Script get_cohort_breakdown_genepop_file.bash produces a table of for gen <tab> age <tab> total,
and we want table gen <tab> total_age1 <total_age2>...<total_age_max>

Input to be from stdin.
'''
__filename__ =""
__date__ = "20170212"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"


import sys

IDX_GEN=0
IDX_AGE=1
IDX_TOT=2

DELIMIT="\t"

ddi_counts_by_age_by_gen={}

i_max_age=0

for s_line in sys.stdin:

	ls_vals=s_line.strip().split( DELIMIT )	
	
	i_gen=int( ls_vals[IDX_GEN] )
	i_age=int( float( ls_vals[IDX_AGE] ) )
	i_tot=int( ls_vals[IDX_TOT] )
	
	if i_age > i_max_age:
		i_max_age=i_age
	#end if new max age

	if i_gen in ddi_counts_by_age_by_gen:
		ddi_counts_by_age_by_gen[ i_gen ][ i_age ]=i_tot
	else:
		ddi_counts_by_age_by_gen[ i_gen ]={ i_age:i_tot }
	#end if already-seen gen else not

#end foreach line

li_sorted_gens= sorted( ddi_counts_by_age_by_gen.keys() )

s_header="\t".join( [ "gen" ] + [ "age" + str( idx ) for idx in range( 1, i_max_age + 1 ) ] )

print( s_header )
for i_gen in li_sorted_gens:

	ls_entry_vals=[ str( i_gen ) ]

	for idx in range( 1, i_max_age + 1 ):

		if idx not in ddi_counts_by_age_by_gen[ i_gen ]:

			ls_entry_vals.append( str( 0 ) )
		else:
			ls_entry_vals.append( str( ddi_counts_by_age_by_gen[ i_gen ][ idx ] ) )
		#end if age not present

	#end for each age

	print( "\t".join( ls_entry_vals ) )

#end for each gen

if __name__ == "__main__":
	pass
#end if main
