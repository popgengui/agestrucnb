#!/bin/bash
#want to add Nb/N (aka Nb/Nc) ratio,
#and Nb entries in the table s2 from
#Waples, R. S., Luikart, G., Faulkner, 
#J. R. & Tallmon, D. A. Simple life-history 
#traits explain key effective population size 
#ratios across diverse taxa. Proceedings of the 
#Royal Society of London B: Biological Sciences 280, 
#20131339 (2013).

#Using species names from col 1 of the table,
#search for matching species among our existing
#life tables, then add the Nb/N and Nb values in 
#the table to the life history file, renaming
#the life table appropriatesly

numargs="1"

mys=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mys <s2 table file, tab delimited, header on line 1"
	exit 1
fi

colsp="1"
colnb="5"
colnbnc="8"

mytable="$1"
default_nbnc="0.0"
default_nb="0.0"

newconfigsection="[effective_size]"
nbvarname="Nb"
nbncvarname="NbNc"

linecount="0"

declare -A matchingfiles

function write_revised_life_table {
	origtable=$1
	mynb=$2
	mynbnc="$3"

	newtable=${origtable/life.table/with.nb.life.table}

	#####
#	echo "----------------"
#	echo "orig: $origtable"
#	echo "new: $newtable"
#	echo "nb: $mynb"
#	echo "nb: $mynbnc"
	#####

	cat $origtable > $newtable

	echo "$newconfigsection" >> "$newtable"
	echo "$nbvarname = ${mynb}" >> "$newtable"
	echo "$nbncvarname = ${mynbnc}" >> "$newtable"

}

while read myline 
do
	linecount=$( expr $linecount + 1 )

	#skip header line
	if [ "$linecount" -eq "1" ]
	then
		continue
	fi

	sp=$( echo "$myline" | cut -f "$colsp"  )
	nb=$( echo "$myline" | cut -f "$colnb" )
	nbnc=$( echo "$myline" | cut -f "$colnbnc" )

	splower=${sp,,}
	splowerconcat=${splower/_}
	spwholename="${splowerconcat}"
	spfirstname="${splower%_*}"
	splastname="${splower#*_}"

	##### temp
#	echo "----------------"
#	echo "sp: $splower"
#	echo "first: $spfirstname"
#	echo "last: $splastname"
	#####

	filematchwhole=$( ls ${spwholename}.*life.table.info 2>/dev/null )
	filematchfirst=$( ls ${spfirstname}.*life.table.info 2>/dev/null )
	filematchlast=$( ls ${splastname}.*life.table.info 2>/dev/null )

	filematch=""

	if [ ! -z "$filematchwhole" ]
	then
		hitcount=$( echo "$filematchwhole" | awk 'END{ print NR }' )

		if [ "$hitcount" -eq 1 ] 
		then
			filematch="$filematchwhole"
		fi
	elif [ ! -z "$filematchfirst" ]
	then

		hitcount=$( echo "$filematchfirst" | awk 'END{ print NR }' )

		if [ "$hitcount" -eq 1 ] 
		then
			filematch="$filematchfirst"
		fi
	elif [ ! -z "$filematchlast" ]
	then

		hitcount=$( echo "$filematchlast" | awk 'END{ print NR }' )

		if [ "$hitcount" -eq 1 ] 
		then
			filematch="$filematchlast"
		fi
	fi

	if [ ! -z "$filematch" ]
	then
		matchingfiles[${filematch}]=1
		write_revised_life_table $filematch $nb $nbnc
	fi
	
done < $mytable

#Use default values for those which did not match
all_orig_tables=$( ls *life.table.info | grep -v "with.nb" )

for thisorig in $all_orig_tables
do
	if [ ! -z "$thisorig" ] && [ -z "${matchingfiles[$thisorig]}" ]
	then
		write_revised_life_table "${thisorig}" "${default_nb}" "${default_nbnc}"
	fi

done

