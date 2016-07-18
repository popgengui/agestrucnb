#!/bin/bash

numargs=1

if [ "$#" -ne "$numargs" ]
then
	echo "usage: <out table>"
	exit 0
fi

linecount=0

mytable="$1"

while read myline
do

	linecount=$( expr $linecount + 1 )

	if [ "$linecount" -eq 1 ]
	then
		echo $myline
		continue
	fi

	echo "$myline" | awk '{ 
			split( $1,  mya, "_" ); 
			split( mya[1], myb, "BY" );
			print myb[1] "\t" myb[2] "\t" $0 }'

done < "$mytable"
