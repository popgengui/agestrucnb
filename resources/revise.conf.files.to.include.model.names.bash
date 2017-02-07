#!/bin/bash

numargs="1"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <file, comma delimited list of model names>"
	echo "note: execute in directory with *.conf files that match model names"
	exit 1
fi

mynames=$( cat "$1" )

newfiletab="with.model.name"

for myf in *conf
do
	modelname=$( echo "$myf" | awk -v mynms="$mynames" '{ \
		split( mynms, mya, "," );
		for ( idx in mya )
		{
			#print "this mod: " mya[ idx ]
			if( $0 ~ mya[idx] )
			{
				print mya[idx];
				break;
			}
		}}' )

	mynewfile="${myf}.${newfiletab}"

	echo "[model]" > ${mynewfile}
	echo "name=${modelname}" >> ${mynewfile}
	cat "${myf}" >> ${mynewfile}
	
done


