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

numargs="2"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <genepop file> <indices (comma-delim ints)>"
	exit 1
fi

gpfile="$1"
ilist="$2"

awk -v myl="$ilist" 'BEGIN { 
		popcount=0 
		indivcount=0
		split( myl,mya, "," )

		for( idx in mya )
		{
			myindices[ mya[idx] ]=1
		}#end for indices
	} #end BEGIN
	{
		if ( popcount == 0 )
		{
			print

			if ( match( $0, /^pop/ ) )
			{
				popcount++
			}

		}
		else if ( popcount == 1 )
		{
			indivcount++

#			##### temp
#			print "NR is " NR > "/dev/stderr"
#			print "indivcount is " indivcount > "/dev/stderr"
#			#####

			if(  myindices[ indivcount ] == 1 )
			{
#				#####
#				print "printing with indivcount = " indivcount " and myindices[ indivcount ] = " myindices[ indivcount ] > "/dev/stderr"
#				#####
				
				print
			}
		}
		else if ( popcount > 1 )
		{
			print "error: more than one population found in file"
			exit
		} #end if popcount == 0, else 1, else error
			
	} #end main' "$gpfile"


			
		 	
		





