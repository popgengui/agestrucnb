#!/bin/bash

#Given a tsv file as output by pgdriveneestimator.py,
#and the presence of the intermediate genepop files produced
#to make the tsv, this script runs NeEstimator on the intermediate
#genepop file associated with each entry in the tsv, and confirms
#that the NeEstimates match.  Note that this script depends on
#the intermediate file naming conventions used in pgdriveneestimator.py


numargs="1"
mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <tsv file>"
	exit 101
fi
mytsv="$1"

colfile="1"
colpopnum="2"
colpopval="5"
colpoprep="6"
collocival="7"
collocirep="8"

colne="11"

colmanualne="5"

necommand="/home/ted/documents/source_code/python/negui/supplementary_scripts/run.ne2l.default.params.bash"

linecount="0"
matchcount="0"
misscount="0"
totalentries="0"

mystamp="$(date +%m%s%N)"
mytemp="tmp.${mystamp}"
mytempin="in.${mystamp}"

while read myline
do
	linecount=$( expr $linecount + 1 )

	if [ "$linecount" -eq "1" ]
	then
		continue
	fi

	
	thefile=$( echo "$myline" | cut -f "${colfile}" )
	thefilenopath=$( basename $thefile )
	thepopval=$( echo "$myline" | cut -f "${colpopval}" )
	thepoprep=$( echo "$myline" | cut -f "${colpoprep}" )
	thelocival=$( echo "$myline" | cut -f "${collocival}" )
	thelocirep=$( echo "$myline" | cut -f "${collocirep}" )
	thepopnum=$( echo "$myline" | cut -f "${colpopnum}" )

	myprotoglob="${thefilenopath}*_${thepopval}_${thepoprep}_*_${thelocival}_${thelocirep}_g_${thepopnum}"

	myglob=$( echo "${myprotoglob}" | awk '{ gsub( /\./, "_" ); print $0 }' )

	mygp=$( ls $myglob )

	thene=$( echo "$myline" | cut -f "${colne}" )

	#Ne crashes if input file name too long:

	cp ${mygp} ${mytempin}

	${necommand} ${mytempin} ${mytemp} 1 1>/dev/null 2>/dev/null

	rm ${mytempin}

	nemanual=$( grep -i "estimated ne" ${mytemp} | sed 's/\s\+/\t/g' | cut -f 6 )
	
	if [ "$thene" == "Inf" ]
	then
		thene="Infinite"
	fi

	equalnes=$(echo "$thene" | awk -v man="${nemanual}" '{ print ( $0 == man ); }' )

	if [ "$equalnes" -eq "1" ]
	then
		matchcount=$( expr $matchcount + 1  )
	else
		cp ${mytemp} ${mygp}.ne.mismatch
		misscount=$( expr $misscount + 1 ) 
	fi	

	totalentries=$( expr $totalentries + 1 )

	rm ${mytemp}

done < "$mytsv"

echo  -e "${totalentries}\t${matchcount}\t${misscount}"


