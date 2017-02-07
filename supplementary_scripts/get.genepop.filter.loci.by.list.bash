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
#	 4. comma-delimited list of loci positions (1-based), 
#Output: Genepop file excluding loci listings outside the list
#Assumptions: loci names are listed one to a line after
#		the header line and before the first pop.
#	      loci names are of form "lxx" where xx=0,1,2..n
#             for n-1 loci, these names entered in numerical
#	      order in the gene pop file

numargs="4"

mys=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mys <genepop file> <start pop index> <end pop index> <start loci index> <end loci index>"
	exit 0
fi

myfile="$1"
idxpopstart="$2"
idxpopend="$3"
idxlocilist="$4"

popnum="0"
linenum="0"

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

		else
			#Loci list is one-based, but
			#loci names use zero-based numbers,
			#so we convert the loci name.  Also,
			#we surround loci numbers in commas,
		        #and the list in commas so that all
			#indices are surrounded by commas,
			#for the awk pattern match:	
			listformatch=",${idxlocilist},"
			locinumzeroindexed="${myline/l}"
			lociordinal="$( expr $locinumzeroindexed + 1 )"
			locinumformatch=",${lociordinal},"
			loci_is_in_list=$( echo "$locinumformatch" \
				| awk -v myl="${listformatch}" \
					'{ print ( myl ~ $0 ); }' )

			if [ "$loci_is_in_list" -eq "1" ]
			then
				echo "$myline"
			fi
		fi

	elif [ "$popnum" -ge "$idxpopstart" ] \
			&& [ "$popnum" -le "$idxpopend" ]
	then
		
		myid=$( echo "$myline" | cut -d "," -f 1 )
		myloci=$( echo "$myline" | cut -d "," -f 2 )

		lociinrange=$( echo "$myloci" \
				| cut -d " " -f ${idxlocilist} )
		echo "${myid},${lociinrange}"

	fi	
		
done < "$myfile"

