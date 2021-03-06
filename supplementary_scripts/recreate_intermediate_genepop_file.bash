#!/bin/bash

#2017_07_11.  This script recreates a sampled genepop file as
#based on an original generated by a simupop simulation via pg* modules.
#It uses the loci list of the sampled genepop file, and the original genepop
#file, to write the individuals an loci for each entry in the original,
#within the range of pops as given on the command line. 

#
#This script can test the loci sampler to make sure it is selecting the
#correct alleles given the loci list of the sampled loci.
#



numargs="5"
mysc="$( basename $0 )"

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <original genepop file> <sampled genepop file> <lowestpopnum> <highestpopnum> <samplepopoffset>"
	echo "note: sample pop offset is the int n that gives the pop num in the original that is the first in the sampled"
	exit 0
fi

myoriggp="$1"
mysampgp="$2"
popstart="$3"
popend="$4"
popoffset="$5"


function get_loci_list()
{

	mygp="$1"
	local linecount="0"

	while read myline
	do
		linecount="$(expr $linecount + 1 )"

		if [ "$linecount" -gt 1 ]
		then

			is_popline=$( echo "$myline" | grep "^pop$" )

			if [ ! -z "$is_popline" ]
			then	
				break
			fi

			arloci=( "${arloci[@]}" "$myline" )
		fi
	done < "$mygp"
}

function isinrange()
{
	mynum="$1"

	if [ "$mynum" -ge "$popstart" ] && [ "$mynum" -le "$popend" ]
	then	
		popsinrange=1
	else
		popsinrange=0
	fi

}

function getid()
{
	local aline="$1"

	currid=$( echo "$aline" | awk '{ split( $0, ar, "," ); print ar[1] }' )
}

function getalleles()
{
	local aline="$1"

	local alleles=$( echo "$aline" | awk '{ split( $0, ar, "," ); print ar[2] }' )

	curralleles=(${alleles})

}

function getidlist()
{
	local mygp="$1"
	local mypopnum="$2"
	local popcount=0	
	local linecount=0
	local is_popline=0

	idlist=""

	
	while read lineforid
	do
		linecount=$( expr $linecount + 1 )

		is_popline=$( echo "$lineforid" | grep "^pop$" )

		if [ "$linecount" -eq "1" ]
		then
			continue

		elif [  ! -z "$is_popline" ]
		then
			popcount=$( expr $popcount + 1 )
		elif [ "$popcount" -eq "$mypopnum" ]
		then
			local thisid=$( echo "$lineforid" | awk '{ split( $0, ar, "," ); print ar[1] }' )			

			if [ -z "$idlist" ]
			then
				idlist="~~${thisid}~~"
			else
				idlist="${idlist}${thisid}~~"
			fi
		fi

	done < "$mygp"
}


function getidinlist()
{
	local thisid="$1"
	local listedform="~~${thisid}~~"

	idinlist=0

	idinlist=$(  echo "$listedform" | awk -v myids="${idlist}" '{ print ( myids ~ $0 ); }' )

} #end getidinlist

function getlociidxlist()
{
	lociindices=""

	for listloci in "${arloci[@]}"
	do
		lociindices="${lociindices}${origlociposbyname[$listloci]},"
	done

}


declare -a arloci
declare -A origlociposbyname

idlist=""

get_loci_list "$myoriggp"

locicount="0"

#Associative array that is indexed
#to the loci name, and gives its
#zero-based index into its place
#in the loci entries, first,second..last.
for loci in "${arloci[@]}"
do
	origlociposbyname[$loci]="$locicount"
	#we increment after indexing, since
	#we're using bash zero-based arrays.
	locicount=$( expr $locicount + 1 )
done

#reset the array to empty
arloci=()

get_loci_list "$mysampgp"

firstlineinsampfile=$( head -n 1 "$mysampgp" )

#header for our result file, to match the sample file,
#so that we can use md5sum to see if we have identical
#sample files:
echo "$firstlineinsampfile"

#loci list section for results file:
for loci in "${arloci[@]}"
do
	echo  "$loci"
done


#for stderr at end of script:
getlociidxlist 

popcount=0
linecount=0



while read myline
do
	linecount="$( expr $linecount + 1 )"

	if [ "$linecount" -gt "1" ]
	then
		ispop=$( echo $myline | grep "^pop$" ) 

		if [ ! -z "$ispop" ]
		then
			popcount=$( expr $popcount + 1 )

			linetowrite=myline

			isinrange $popcount

			if [ $popsinrange -eq 1 ]
			then
				popnumcorrect=$( expr $popcount - $popoffset )
				popnumcorrect=$( expr $popnumcorrect + 1 )

				getidlist "$mysampgp" "$popnumcorrect"
				echo "$myline"

				if [ ! -z "$indivlist" ]
				then
					echo "$indivlist" 1>&2
				fi

				indivlist=""
				indivcount=0
			fi
		else
			isinrange $popcount

			firstindivfound="0"

			if [ $popsinrange -eq 1 ]
			then
				indivcount=$( expr $indivcount + 1 )

				getid "$myline"

				getidinlist "$currid"
				
				if [ "$indivcount" -eq 1 ]
				then
					indivlist="pop ${popcount}: "
				fi

				if [ $idinlist -eq 1 ]
				then
					indivlist="${indivlist}${indivcount},"

					getalleles "$myline"

					writethis="${currid},"

					for loci in "${arloci[@]}" 
					do
						thislociindex="${origlociposbyname[$loci]}"

						writethis="${writethis} ${curralleles[$thislociindex]}"
					done


					echo "$writethis"


				fi #if id in list
			fi #if pop in range
		fi #if pop line else not

		if [ "$popcount" -gt "$popend" ]
		then
			break
		fi
	fi #if line count > 1
done < "$myoriggp"

echo "$indivlist" 1>&2
echo "loci: $lociindices" 1>&2

