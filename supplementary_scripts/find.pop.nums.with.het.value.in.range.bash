#!/bin/bash

numargs=3
mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <tsv files (quoted glob)> <min het val> <max het val>"
	echo "note tsv file expected to have pop number in col 2 and het val in col 22"
	exit 0
fi

tsvglob="$1"
minhet="$2"
maxhet="$3"

tsvfiles="$( ls $tsvglob )"

echo "tsv files: $tsvfiles"

for myf in $tsvfiles
do

	cut -f 2,22 $myf \
		| awk -v hmin="${minhet}" -v hmax="${maxhet}" -v afile="${myf}" \
		'$2 >= hmin && $2 <= hmax{ print afile "\t" $1 "\t" $2}' ; 
done


