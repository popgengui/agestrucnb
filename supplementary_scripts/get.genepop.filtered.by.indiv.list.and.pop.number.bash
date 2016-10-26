#!/bin/bash
#uses output from the "testmulti" or "testserial" mode
#of pgdriveneestimator.py -- which yeilds both a genepop file
#name and a list (comma-delim) ofindices into the invidual lines
#in a genepop file -- note that the first index in the output
#is always zero -- which in the GenepopFileManager object 
#refers to the line with "pop", and so is properly skipped
#in the awk code below, by increm the indivcount var past zero
#when popcount first reaches "1"
#
#also note that this version expects and works properly on in
#the case of a single pop in the orig genepop file
# 2016_10_21
#revised to take a pop number, so that the list of ints i,j,k
#will be the ith,jth,kth indivs in the mth pop of 1,2,3...N pops
#listed in the genepop file.


numargs="3"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <genepop file> <indices (comma-delim ints)> <pop number>"
	exit 1
fi

gpfile="$1"
ilist="$2"
popnum="$3"

awk -v myl="$ilist" -v mypop="$popnum" \
	'BEGIN { 
		popcount=0 
		indivcount=0
		split( myl,mya, "," )

		for( idx in mya )
		{
			##### temp
#			print "entering indiv num " mya[idx]
			#####

			myindices[ mya[idx] ]=1
		}#end for indices
	} #end BEGIN
	{
		if ( tolower($0) ~ /^pop/ )
		{
			popcount++
				
			if( popcount==mypop )
			{
				print
			}
		}
		else if ( popcount == 0 )
		{
			print

		}
		else if ( popcount == mypop )
		{
			indivcount++

			##### temp
#			print "NR is " NR 
#			print "indivcount is " indivcount 
			#####
			
			if(  myindices[ indivcount ] == 1 )
			{
#				#####
#				print "printing with indivcount = " indivcount " and myindices[ indivcount ] = " myindices[ indivcount ]
#				#####
				
				print
			}
		}
		else if ( popcount > mypop )
		{
			exit
		} #end if popcount == 0, else 1, else error
			
	} #end main' "$gpfile"

