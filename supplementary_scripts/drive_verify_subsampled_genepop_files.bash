#!/bin/bash
#Assuming intermediate genpop files exist named after the original
#such that we have original name with underscores replacing the original
#dot chars, and, further that the intermediate files end in "_g_integer,
#where integer gives the pop number in the original that is replresented
#in the intermediate file, we compare intermediates to origianals and 
#ooutput a table that gives, for each pop in each intermediate, the 
#indiv count, the loci count, and the number of times for each pop that
#the indiv and the correct allele was found for each loci in the intermediate file.
#(see script verify_subsampled_genepop_file.bash).

numargs="2"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: ${mysc}" 
	echo "args: "
	echo "      <original genepop file>"
       	echo "      <quoted, space-delimted list of generation numbers, \"j k l ...\", "
	echo "     as seen terminating names of intermediate genepop files "
	echo "     (\"*_g_{j,k,l...}\")>"
	echo ""
	echo "Note:  all files must hae unix endlines.  Convert the Steelhead and Chinook file DOS endlines before using this script."
	exit 1
fi

myorig="$1"
mygs="$2"

colmisses="6"
colmatches="5"
colindivmisses="3"

totalmisses="0"
totalmatches="0"
totalindivmisses="0"
totallookupfails="0"

#header
echo -e "subsample_file\tsubsamp_pop_num\ttot_indiv\ttot_indiv_misses\ttot_loci\tloci_matches\tloci_misses"

subfile_key=$( echo "$myorig" | awk '{ gsub( /\./, "_" ); print $0; }' )

for myg in ${mygs}  
do
	for mys in "${subfile_key}"*_g_${myg}  
	do  	

		testres=$(../supplementary_scripts/verify_subsampled_genepop_file.bash "${myorig}" "${mys}" "${myg}" 1 noheaders 2>&1 1>/dev/null )

		thesemisses=$( echo -e "$testres" | cut -f ${colmisses} )
		thesematches=$( echo -e "$testres" | cut -f ${colmatches} )
		theseindivmisses=$( echo -e "$testres" | cut -f ${colindivmisses} )

		if [ -z $thesemisses ] || [ -z $thesematches ]
		then
			totallookupfails=$( expr $totallookupfails + 1 )
		fi

		totalmisses=$( expr "$totalmisses" + "$thesemisses" )
		totalmatches=$( expr "$totalmatches" + "$thesematches" )
		totalindivmisses=$( expr "$totalindivmisses" + "$theseindivmisses" )
		echo -e "${mys}\t${testres}"; 	

	done
done

echo "Total loci matches: $totalmatches" 1>&2
echo "Total loci misses: $totalmisses" 1>&2
echo "Total indiv misses: $totalindivmisses" 1>&2
echo "Total failures finding matches or misses: $totallookupfails" 1>&2

