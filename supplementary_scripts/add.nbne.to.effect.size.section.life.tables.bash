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
	echo "usage: $mys <s1 table from waples2014, underscores connecting multi-part species names (col1), and multi-part latin names (col2), tab delimited, header on line 1"
	exit 1
fi

colsp="1"
colnbne="5"

mytable="$1"
default_nbne="0.0"
nbnevarname="NbNe"
linecount="0"

#a couple of fixes manually:
declare -A samespecies
samespecies[mole_crab]=mcrab
samespecies[wood_frog]=wfrog
samespecies[loggerhead_turtle]=lturtle
samespecies[sea_urchin]=surchin

declare -A matchingfiles

function write_revised_life_table {
	origtable=$1
	mynbne=$2

	newtable=${origtable/with.nb.life.table/with.nbne.life.table}

	#####
#	echo "----------------"
#	echo "orig: $origtable"
#	echo "new: $newtable"
#	echo "nb: $mynb"
#	echo "nb: $mynbnc"
	#####

	cat $origtable > $newtable

	#we assume that the "effective_size"
	#section is the last one in the file,
	#and simply append our new NbNe value
	#entry to the new file.

	echo "$nbnevarname = ${mynbne}" >> "$newtable"

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
	nbne=$( echo "$myline" | cut -f "$colnbne" )

	sporiglower=${sp,,}
	splower=${sp,,}
	#check the matches found by manual inspection:
	if [ ! -z ${samespecies[${sporiglower}]} ]
	then
		splower=${samespecies[${splower}]}
	fi

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

		echo -e "${sporiglower}\t${filematch}"
		matchingfiles[${filematch}]=1
		write_revised_life_table $filematch $nbne
	else
		echo -e "${sporiglower}\tnone"
	fi
	
done < $mytable

#Use default values for those which did not match
all_orig_tables=$( ls *with.nb.life.table.info | grep -v "with.nbne" )

for thisorig in $all_orig_tables
do
	if [ ! -z "$thisorig" ] && [ -z "${matchingfiles[$thisorig]}" ]
	then
		echo -e "none\t${thisorig}"
		write_revised_life_table "${thisorig}" "${default_nbne}"
	fi

done

