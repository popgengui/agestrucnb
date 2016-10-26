#!/bin/bash

#Need to count individuals by age in each pop section of a
#genepop file, in order to test for correctness in the 
#negui genepop file sampling code. Input genepop file's
#individual ids are assumed to be semi-colon delimited fields,
#id;sex;father_id;mother_id;age, for example:
#
#	87.0;1;0.0;0.0;5.0
#
#Input:
#  1. genepop file with ids as described
#  2. a maximum age, for testing against the cohorts
#     sampling, to get the min per-age indiv total for 
#     ages <= the max.
#  3. min pop section number to print
#  4. max pop section number to print
#
#Output to be:
#  1. to stdout a table with columns giving
#	pop section number, age, and indiv_count.
#  2. to stderr a table giving pop section number, and min

colnumid=1
colnumage=5

numargs="4"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo -e "usage: $mysc <genepopfile with indiv ids with semicolon-delimited fields id;sex;father_id;mother_id;age> <max age> <min pop num> <max pop num>"
	exit 0
fi

gpfile="$1"
maxage="$2"
minpop="$3"
maxpop="$4"

function printtotals
{
	outcolage="2"
	outcolpop="1"
	outcoltot="3"

	popnum=$1

	myoutput=""	

	for mykey in "${!myagetotals[@]}"
	do
		thisline="$popnum\t${mykey}\t${myagetotals[$mykey]}"

		if [ -z "$myoutput"  ]
		then

			myoutput="$thisline"
		else
			myoutput="${myoutput}\n${thisline}"
		fi
	done
	
	#each pop section lines sorted by age:
	outsorted=$( echo -e "$myoutput" | sort -nk '2,2' )

	minagegroup=$( echo "$outsorted" | awk -v mymax="$maxage" '$2<=mymax' | sort -nk '3,3' | awk 'NR==1' )

	ageofmin=$( echo -e "$minagegroup" | cut -f "$outcolage" )
	totofmin=$( echo -e "$minagegroup" | cut -f "$outcoltot" )

	if [ -z "$ageofmin" ] 
	then
		ageofmin="No age"
	fi
	if [ -z "$totofmin" ]
	then
		totofmin="None"
	fi

	echo "For pop ${popnum}, smallest cohort has age: ${ageofmin}, with total indiv: ${totofmin}" 1>&2
	echo -e "${outsorted}"


	
}

popcount="0"

declare -A myagetotals

while read myline
do

	if [ "$myline" == "pop" ]
	then
		if [ "$popcount" -ge "$minpop" ] && [ "$popcount" -le "$maxpop" ]
		then
			printtotals $popcount $myagetotals
		fi

		popcount=$( expr $popcount + 1 )
		unset myagetotals
		declare -A myagetotals

	elif [ "$popcount" -gt "$maxpop" ]
	then
		break
	elif [ "$popcount" -ge "$minpop" ] && [ "$popcount" -le "$maxpop" ]
	then
		myid=$( echo "$myline" |  cut -d "," -f $colnumid )
		
		myage=$( echo "$myid" | cut -d ";" -f "$colnumage"  )
		
		#age is a float value -- assume it's usually really a whole number
		#but there may be alt cases.  Can't do arithmetic with non-ints
		#in bash, so
		ageltmax=$( echo "$myage" | awk -v mymax="$maxage" '{ print ( $0 <= mymax) }' )
	
		if [ "$ageltmax" -eq 1 ]
		then
			myagetotals["$myage"]=$( expr ${myagetotals["$myage"]} + 1 )
		fi
	fi

done < "$gpfile"

#last pop may have not yet printed
#if it was the final pop in the file
if [ "$popcount" -ge "$minpop" ] && [ "$popcount" -le "$maxpop" ]
then
	printtotals $popcount $myagetotals
fi

