#!/bin/bash
#2017_09_21
#Converts a negui life table into an AgeNe2 input file.
#
#Uses a uniformly unity poisson factor.
#
#Assumes that the survival list  in the  life table
#has one less value than does the fecundity value list,
#and that the excluded survival rate is 0.0 for the final age class.
#assumes equal number of values for Male and Female, but writes each
#set independantly (i.e. does not assume equal values).


numargs="2"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <negui life table file> <sex ratio>"
	exit 0
fi

lifetable="$1"
sexrat="$2"

modname=$( grep "name=" $lifetable | cut -f 2 -d "=" )

nbnc=$( grep "NbNc =" $lifetable | sed 's/NbNc = //')
nb=$( grep "Nb =" $lifetable | sed 's/Nb = //')
nc=$( echo "$nbnc" | awk -v mynb="$nb" '{ invnc=$0/mynb; print int( 1/invnc ); }' )

#add the last age group with survival 0.0:
femalesur=($( grep "survivalFemale" $lifetable | cut -f 2 -d "=" | sed 's/\s\+//g' | sed 's/\[//' | sed 's/\]//' | sed 's/,/ /g') "0.0")
malesur=($( grep "survivalMale" $lifetable | cut -f 2 -d "=" | sed 's/\s\+//g' | sed 's/\[//g' | sed 's/\]//' | sed 's/,/ /g' ) "0.0" )

femalefec=($( grep "fecFemale" $lifetable | cut -f 2 -d "=" | sed 's/\s\+//g' | sed 's/\[//' | sed 's/\]//' | sed 's/,/ /g' ))
malefec=($( grep "fecMale" $lifetable | cut -f 2 -d "=" | sed 's/\s\+//g' | sed 's/\[//g' | sed 's/\]//' | sed 's/,/ /g' ))

#echo "mod: $modname"
#echo "fesur: $femalesur"
#echo "malesur: $malesur"
#echo "fefec: $femalefec"
#echo "malefec: $malefec"
#echo "NbNc: $nbnc"
#echo "Nb: $nb"
#echo "Nc: $nc"

lensur="${#femalesur[@]}"
lenfec="${#femalefec[@]}"

lastidx=$( expr $lensur - 1 )

#echo "len sur:  $lensur"
#echo "len fec: $lenfec"

if [ $lensur -ne $lenfec ]
then
	echo "parsing error: total for survival values (${lensur}) and fecundity values (${lenfec}) differ." 
	exit 1
fi
echo -e "$modname"
echo -e "${lensur}\t${nc}\t${sexrat}"
ageclass="0"
for idx in $( seq 0 $lastidx )
do
	ageclass=$(expr $ageclass + 1 )

	entryraw="${ageclass}\t${femalesur[${idx}]}\t${femalefec[${idx}]}\t1\t${malesur[${idx}]}\t${malefec[${idx}]}\t1"

	entryallfloats="$( echo "$entryraw" | sed 's/\\t0\\t/\\t0.0\\t/g' | sed 's/\\t0\\t/\\t0.0\\t/g' )"

	echo -e "$entryallfloats" 

done






