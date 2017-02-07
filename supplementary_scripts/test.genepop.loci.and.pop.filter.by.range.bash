#!/bin/bash

#Compare genepop files created using pgdriveneestimator.py, with loci
#and pop filtration, and bash script test.genepop.loci.and.pop.filter.bash

#Comparison requires using a single pop, so we output one test per pop 
#in the range of pop indices.  Also there can be no subsampling 
#(Hence we use no sampling scheme, nor any max pop size,  
#in pgdriveneestimator.py from the loci or pop range ),

execdir="/home/ted/documents/source_code/python/negui"

numargs="5"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <genepop file> <pop start index> <pop stop index> <start loci index> <end loci index>"
	exit 0
fi

myfile="$1"
idxpopstart="$2"
idxpopend="$3"
idxlocistart="$4"
idxlociend="$5"

testoutfile=$( date +%s.%N ).gp

matchcount=0
mismatchcount=0

for idxpop in $( seq $idxpopstart $idxpopend )
do

	pgoutfile=$( echo "$myfile" | sed 's/\./_/g' )
	pgoutfile="${pgoutfile}_o_n_r_0_g_${idxpop}"

	#recall "debug3" preserves the intermediate files, including the per-pop genepop files
	#Since we only want the intermediate genepop file we direct the Ne estimation output to /dev/null:
	python ${execdir}/pgdriveneestimator.py -f $myfile -s none -p none -m 1 -a 99999 -r ${idxpop}-${idxpop} \
					-e 0.01 -c 1 -l none -i none -g ${idxlocistart}-${idxlociend} -x 99999 -d debug3 1>/dev/null 2>/dev/null

	${execdir}/supplementary_scripts/get.genepop.filter.loci.by.range.bash $myfile $idxpop $idxpop $idxlocistart $idxlociend > $testoutfile

	md5_pg=$( md5sum $pgoutfile | cut -f 1 -d " " ) 
	md5_bash=$( md5sum $testoutfile | cut -f 1 -d " " )

	if [ "$md5_pg" == "$md5_bash" ]
	then
		matchcount=$( expr $matchcount + 1 )
	else
		mismatchcount=$( expr $mismatchcount + 1 )
		echo "mismatch on pg file: $pgoutfile" 1>&2
	fi
	
	#this gets rid of all the intermediate
	#files made by pgdriveneestimator.py:
	rm *_g_*
	myd=$( date +%Y.%m.%d )
	rm ${myd}*indiv.table

	rm $testoutfile

echo "identical files: $matchcount"
echo "mismatched files: $mismatchcount"

