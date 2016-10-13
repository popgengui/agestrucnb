#!/bin/bash
# 2016_10_11
#We save the intermediate geneopop files (one per pop) from a run of
#pgdriveneestimator.py, with loci sampling, and a range of pops.  Then we
#re-make the genepop files using a bash script, then for each pair of single-pop
#genepop files, run md5sum to make sure our 2 files are identical.  This I use
#to test correctness of pgdriveneestimator.py's loci subsampling, assuming my
#bash script that collects samples form the same original genepop file is
#constructed sufficiently differently to obviate any logical errors and reveal
#simple errors as well, so that correctness in loci sampling is very likely if
#versions are identical.

mysc=$( basename $0 )
numargs="6"

if [ "$#" -ne "$numargs" ]
then

	echo "usage: $mysc <genepop file> <popstart> <popend> <locistart> <lociend> <maxloci>"
	exit 0
fi

myf=$1
p1=$2
p2=$3
l1=$4
l2=$5
maxl=$6

execloc="/home/ted/documents/source_code/python/negui"

python ${execloc}/pgdriveneestimator.py -f $myf -s none -p none -m 1 -a 99999 \
				-r "${p1}-${p2}" -e 0.01 -c 1 -l none -i none \
				-g ${l1}-${l2} -x ${maxl} -d debug3 1>/dev/null 2>/dev/null

locilist=$( head -n $( expr $maxl + 1)  *_g_${p1} | tail -n $maxl \
       			| awk '{ sub( "l",""  );mylist=mylist "," $0 + 1; } \
			END{ sub( /^,/, "", mylist ); print mylist}' )

matches="0"
misses="0"

for pn in $( seq $p1 $p2 )
do
	${execloc}/supplementary_scripts/get.genepop.filter.loci.by.list.bash \
			$myf $pn $pn $locilist > test_g_${pn} 
	
	declare -A mysums

	for gp in *_g_${pn}
	do

		thissum=$( md5sum $gp | cut -d " " -f 1 )
		mysums[$thissum]=$( expr ${mysums[$thissum]} + 1 )
	done

	sumcount=0

	for i in "${!mysums[@]}"
	do
		sumcount=$( expr $sumcount + ${mysums[$i]} )
	done


	if [ "${#mysums[@]}" -eq 1 ] && [ "$sumcount" -eq 2 ]
	then
		matches=$( expr ${matches} + 1 )
	else
		misses=$( expr ${misses} + 1 )
	fi
	#Note without this unset statemen, and despite the declare statement above,
	#the array mysums will not be reset for each iteration.
	unset mysums

done


echo "matches: $matches"
echo "misses: $misses"

