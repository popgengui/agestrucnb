#!/bin/bash
#2016_10_09
#Rewrite a genepop file to include the 
#ith - jth loci as ordered in the 
#individual entries.
#This script meant to check output
#of PGGuiNeEstimator-generated genepop files
#(intermediate files used in NeEstimator runs).
#Input:  1. Genepop file, 
#	 2. int, start index pop number
#	 3. int, end index pop number
#	 4. int, start index loci position (1-based), 
#	 5. int, end index loci position
#Output: Genepop file excluding loci listings outside
#Assumptions: loci names are listed one to a line after
#		the header line and before the first pop.

numargs="5"

mys=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mys <genepop file> <start pop index> <end pop index> <start loci index> <end loci index>"
	exit 0
fi

myfile="$1"
idxpopstart="$2"
idxpopend="$3"
idxlocistart="$4"
idxlociend="$5"

popnum="0"
linenum="0"

#header line correction:
idxstartline=$( expr $idxlocistart + 1 )
idxendline=$( expr $idxlociend + 1 )

idxfirstpopnumover=$( expr $idxpopend + 1 )

while read myline
do

	linenum=$( expr $linenum + 1 ) 

	lcaseline=${myline,,}

	if [ "$lcaseline" == "pop" ]
	then

		popnum=$( expr $popnum + 1 )

		if [ "$popnum" -ge "$idxpopstart" ] && [ "$popnum" -le "$idxpopend" ]
		then
			echo "$myline"
		elif [ "$popnum" -gt "$idxpopend" ]
		then
			break
		fi
	elif [ "$popnum" -eq "0" ]
	then
		if [ "$linenum" -eq "1" ]
		then
			echo "$myline"

		elif [ "$linenum" -ge "$idxstartline" ] \
				&& [ "$linenum" -le "$idxendline" ]
		then
			echo "$myline"
		fi

	elif [ "$popnum" -ge "$idxpopstart" ] && [ "$popnum" -le "$idxpopend" ]
	then
		
		myid=$( echo "$myline" | cut -d "," -f 1 )
		myloci=$( echo "$myline" | cut -d "," -f 2 )

		#Have revised my own genepop format to put a leading space after
		#comma to delimit id from loci 1.  This means we need to trim it
		#so cut won't consider a leading space (else you get 1 less loci than
		#desired, and loci 1 becomes loci 2:
		myloci=$( echo "${myloci}" | awk '{ sub( /^\s/, "" ); print }' )

		lociinrange=$( echo "$myloci" \
				| cut -d " " -f ${idxlocistart}-${idxlociend} )

		#add the space that should lead the loci:
		echo "${myid}, ${lociinrange}"

	fi	
		
done < "$myfile"

