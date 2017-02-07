#!/bin/bash

mysc=$( basename $0 )

minargs=3

if [ "$#" -lt "$minargs" ]
then
	echo "usage: $mysc"
	echo "args: "
	echo "  <source genepop file>"
      	echo "  <sampled genepop file>"
	echo "  <list of pop numbers \"i,j,k..\">" 
	echo "  [\"noheaders\"]"
	echo "Note:  in the list, i refers to the first pop in the sampled file, " 
	echo "  the value i indicating that is the ith pop in the original, "
	echo "  j referring similarly to the second pop in sthe sampled file, " 
	echo "  being the jth pop in the original, etc"
	echo "Note: All files must have matching endline schemes.  In the present "
	echo "  cases, this means unix endlines -- the forced endline scheme output "
	echo "  by the genepopfilemanager.py code."

	exit 0
fi

origgp="$1"
sampledgp="$2"
poplist="$3"

popnum="0"
linecount="0"

#Lookup array, given the orig
#pop number and the indiv id,
#find the loci list.
declare -A locibypopandindiv

#Lookup array, given the loci name
#as listed in the loci seciont of
#the orig genepop file, get its
#ordinal in the listing.
declare -A locinumbersbyname

if [ -z "$4" ] 
then
	echo -e "orig_pop\tsampled_pop\tid\tloci_matches\tloci_misses"
	echo -e "samppop_num\ttot_indiv\tindiv_misses\ttot_loci_sampled\tloci_matches\tloci_missses" 1>&2
fi

#For each pop in the orig file
#Get the alleles for each individual
while read myline
do

	linecount=$( expr $linecount  + 1 )

	if [ "$linecount" -eq "1" ]
	then
		continue

	elif [ "$myline" == "pop" ]
	then
		popnum=$( expr $popnum + 1 )

	elif [ "$popnum" -eq "0" ]
	then
		locinum=$( expr $linecount - 1 )
		locinumbersbyname[$myline]="$locinum"
	else
		myid=$( echo "$myline" | cut -d "," -f 1 )
		#Gets space-delimited list of loci
		myloci="$( echo "$myline" | cut -d "," -f 2 )"
		locibypopandindiv["${popnum}_${myid}"]="${myloci}"
	fi
done < "$origgp"

#Lookup array, given the ordinal for
#each pop in the subsample file, 
#find the pop number in the original
declare -A origpopnumbysuborder
loopcount="0"

for thispop in $poplist
do
	loopcount=$( expr "$loopcount" + 1 )

	origpopnumbysuborder[$loopcount]="$thispop"
done

linecount="0"
popnum="0"
locicount="0"
indivcount="0"
#How many times do we look up
#an indiv in a given pop in
#the orig and find no loci entry:
indivmisses="0"

declare -A sampledlocinums

while read myline
do
	linecount=$( expr $linecount  + 1 )

	if [ "$linecount" -eq "1" ]
	then
		continue

	elif [ "$myline" == "pop" ]
	then
		if [ "$popnum" -gt 0 ]
		then
			echo -e "${popnum}\t${indivcount}\t${indivmisses}\t${locicountsampled}\t${cummatches}\t${cummisses}" 1>&2
			indivcount="0"
			cummatches="0"
			cummisses="0"
		fi
		popnum=$( expr $popnum + 1 )

	elif [ "$popnum" -eq "0" ]
	then
		locicount=$( expr $locicount + 1 )
		sampledlocinums[$locicount]="${locinumbersbyname[$myline]}"
	else
		myid=$( echo "$myline" | cut -d "," -f 1 )
		#Gets space-delimited list of loci
		myloci=($( echo "$myline" | cut -d "," -f 2 ))

		origpop="${origpopnumbysuborder[$popnum]}"		
		mainkey="${origpop}_${myid}"
		
		origloci="${locibypopandindiv[${origpop}_${myid}]}"
		origlocilist=($origloci)

		if [ -z "$origlocilist" ]
		then
			indivmisses=$( expr ${indivmisses} + 1 )
		else
			locimatches="0"
			locimisses="0"
			locicountsampled="${#sampledlocinums[@]}"

			for sublocinum in $( seq 1 "$locicountsampled" )		
			do
				origlocinum=${sampledlocinums[$sublocinum]}
				origallele=${origlocilist[$origlocinum-1]}
				idx=$( expr $sublocinum - 1 )
				sampledallele="${myloci[$idx]}"

				if [ "$origallele" == "$sampledallele" ]
				then
					locimatches=$( expr $locimatches + 1 )
				else
					locimisses=$( expr $locimisses + 1 )
				fi
			done

			cummatches=$( expr $cummatches + $locimatches )
			cummisses=$( expr $cummisses + $locimisses )

			echo -e "${origpop}\t${popnum}\t${myid}\t${locimatches}\t${locimisses}"
		fi

		indivcount=$( expr $indivcount + 1 )
	fi
done < "$sampledgp"

#last pop totals

echo -e "${popnum}\t${indivcount}\t${indivmisses}\t${locicountsampled}\t${cummatches}\t${cummisses}" 1>&2
