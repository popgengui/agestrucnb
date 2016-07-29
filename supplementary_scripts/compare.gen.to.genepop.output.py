#!/usr/bin/env python

import pgutilities as pgut
import sys

GENCOLINDIV=0
GENCOLGEN=1
GENCOLLOCI=2

def  getgeninfo( s_genfile ):

	dli_indivbygen={}
	ds_locibyindiv={}
	ogenfile=open( s_genfile, 'r' )
	li_loci_totals=[]

	i_entrycount=0
	for s_line in ogenfile:	
		
		i_entrycount+=1

		ls_vals=s_line.strip().split( " " )
		gennum=ls_vals[GENCOLGEN]
		indivnum=ls_vals[ GENCOLINDIV ]		
		li_loci_totals.append( len( ls_vals[ GENCOLLOCI : ] ) )

		s_loci=" ".join( ls_vals[ GENCOLLOCI : ]  )

		if gennum in dli_indivbygen:
			dli_indivbygen[gennum].append( indivnum )
		else:
			dli_indivbygen[gennum]=[ indivnum ]
		#end if old gennum else new

		#add loci for this indiv (we assume, if indiv in more than one gen, then
		#we are simply overwriting identical loci info):
		ds_locibyindiv[ indivnum ] = s_loci
	#end for each line

	ogenfile.close()

	i_num_loci_totals=len( set( li_loci_totals ) )

	if i_num_loci_totals != 1:
		raise Exception ("In compare.gen.to.genepop.output.py, gen file loci totals not uniform" )
	#end if i_num_loci_totals nonuniform

	i_gen_loci_count=li_loci_totals[ 0 ]

	return ( i_entrycount, i_gen_loci_count, dli_indivbygen, ds_locibyindiv )

#end getgeninfo


def compare_genepop_file( s_genfile, s_popfile ):

	i_entrycount, i_gen_loci_count, dli_indivbygen, ds_locibyindiv=getgeninfo( s_genfile )

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
			loci=ls_vals[1]	
			b_indivisin=( indiv in dli_indivbygen[ str( currgen ) ] )

			b_locicorrect=( loci == ds_locibyindiv[ indiv ] )
			if b_indivisin:
				countindivcorrect+=1
			else:
				countindivwrong+=1	
			#end if indiv in else not

			if b_locicorrect:
				countlocicorrect+=1
			else:
				countlociwrong+=1
			#end if loci correct else not
		#end if in pop sections and not pop line
	#end for each line in file

	opopfile.close()

	print ( "total gen file entries: " + str( i_entrycount  ) )
	print ( "correct indiv-gen associations: " + str( countindivcorrect ) )
	print ( "wrong indiv-gen associations: " + str( countindivwrong ) )
	print ( "correct loci-indiv associations: " + str( countlocicorrect ) )
	print ( "wrong loci-indiv associations: " + str( countlociwrong) )

	print ( "total loci per gen entry: " + str( i_gen_loci_count ) )
	print ( "total loci count in pop header: " + str( i_pop_loci_count ) )

#end compare_genepop_file



if __name__=="__main__":

	numargs="3"

	lsargs=[ "gen file", "genepop file" ]

	s_usage=pgut.do_usage_check
	s_genfile=sys.argv[1]
	s_popfile=sys.argv[2]

	compare_genepop_file( s_genfile, s_popfile )
#end if name is "main"

