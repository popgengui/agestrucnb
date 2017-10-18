#!/bin/bash

sizelist=$(ls -ltrh *genepop | sed 's/\s\+/ /g' | cut -d " " -f 5 | sort | uniq -c )
totalfiles=$(ls -ltrh *genepop | sed 's/\s\+/ /g' | cut -d " " -f 5 | sort | uniq -c \
       	| sed 's/^\s\+//' | sed 's/\s\+/\t/g' | awk '{ mycount+=$1;}END{print mycount}' )

echo -e "$sizelist"
echo -e "total gp files: $totalfiles"

