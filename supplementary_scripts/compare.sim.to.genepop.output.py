'''
Description
Check for each generation n, compare the list of individual IDs in the sim file,
to the list of individual IDs in the nth pop in the genepop file
'''
from __future__ import print_function
__filename__ =""
__date__ = "20160825"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import supp_utils as supu
try:
	import pgutilities as pgut
except ImportError as oie:
	supu.add_main_pg_dir_to_path()
	import pgutilities as pgut
#end try...except	

SIMCOLINDIV=2
SIMCOLGEN=0

def  getsiminfo( s_simfile ):

	dli_indivbygen={}
	osimfile=open( s_simfile, 'r' )

	i_entrycount=0

	for s_line in osimfile:	
		
		i_entrycount+=1

		ls_vals=s_line.strip().split( " " )
		gennum=ls_vals[SIMCOLGEN]
		indivnum=ls_vals[ SIMCOLINDIV ]		

		if gennum in dli_indivbygen:
			dli_indivbygen[gennum].append( indivnum )
		else:
			dli_indivbygen[gennum]=[ indivnum ]
		#end if old gennum else new

	#end for each line

	osimfile.close()

	return ( i_entrycount,  dli_indivbygen  )

#end getgeninfo


def compare_genepop_file( s_genfile, s_popfile ):

	i_entrycount, dli_indivbygen=getsiminfo( s_genfile )

	i_genepop_indiv_entries=0
	currgen=-1
	countindivcorrect=0
	countindivwrong=0
	countlocicorrect=0
	countlociwrong=0

	opopfile=open( s_popfile, 'r' )

	i_poplinecount=0
	i_pop_loci_count=0

	for s_line in opopfile:
		i_poplinecount+=1

		ls_vals=s_line.strip().split( "," )

		ispopline=( ls_vals[0]=="pop" )

		if ispopline:
			currgen=currgen + 1
		elif currgen == -1 and i_poplinecount > 1:
			i_pop_loci_count+=1
		elif currgen >= 0 and not( ispopline ):
			indiv=ls_vals[0]			
			b_indivisin=( indiv in dli_indivbygen[ str( currgen ) ] )
			if b_indivisin:
				countindivcorrect+=1
			#end if indiv in else not
		#end if in pop sections and not pop line
	#end for each line in file

	opopfile.close()

	print ( "total sim file entries: " + str( i_entrycount  ) )
	print ( "correct indiv-gen associations: " + str( countindivcorrect ) )
	print ( "wrong indiv-gen associations: " + str( countindivwrong ) )

#end compare_genepop_file

if __name__=="__main__":

	lsargs=[ "sim file", "genepop file" ]

	s_usage=pgut.do_usage_check ( sys.argv, lsargs )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	s_simfile=sys.argv[1]
	s_popfile=sys.argv[2]

	compare_genepop_file( s_simfile, s_popfile )
#end if name is "main"




