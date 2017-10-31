#!/bin/bash
#Uses gnoplot's "stats" command to get the mean, stddev, min, max of the
#bias-adjusted Nb value (column 21) and the heterozygosity value (column 22)
#of the tsv file produced by the negui pgdriveneestimator.py driver module.

numargs="1"
mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <tsv file, tab-delimited, with Nb value in col 21 and het val in col 22>"
	echo "note: assumes you have gnuplot in your path, and that the first line is the header (and thus skipped)."
	exit 0
fi

mytsv="$1"


cut -f 21,22 "$mytsv" \
		| gnuplot -e "stats '<cat' every ::1"  2>&1 \
		| awk 'BEGIN{ \
			fldrecs="Records:"
			fldmean="Mean:"
			#We parse Std Dev without a space (see below)
			fldstd="StdDev:"
			fldmed="Median:"
			fldmin="Minimum:"
			fldmax="Maximum:"

			myrecs=""

			mynbmean=""
			mynbmed=""
			mynbstd=""
			mynbmin=""
			mynbmax=""

			myhetmean=""
			myhetmed=""
			myhetstd=""
			myhetmin=""
			myhetmax=""
		}
		{ 

			#get rid of the row number entries 
			gsub ( /\[\s+/,"")
			gsub ( /\[[0-9]+/,"")
			gsub ( /[0-9]+\]/, "")

			#can not have space in std dev:
			sub( /Std Dev/, "StdDev" )

			gsub ( /\s+/, "\t" )
			sub( /^\t/,"" )

			numitems=split( $0, mya, "\t" )
			thisstat=mya[1]

			if( thisstat == fldrecs )
			{
				myrecs=mya[2]
			}

			if( thisstat == fldmean)
			{
				mynbmean=mya[2]
				myhetmean=mya[3]
			}

			if( thisstat == fldmed )
			{
				mynbmed=mya[2]
				myhetmed=mya[3]
			}

			if( thisstat == fldstd && $0 !~/Err/ )
			{
				mynbstd=mya[2]
				myhetstd=mya[3]
			}

			if( thisstat == fldmin )
			{
				mynbmin=mya[2]
				myhetmin=mya[3]
			}

			if( thisstat == fldmax )
			{
				mynbmax=mya[2]
				myhetmax=mya[3]
			}
				

		} #end main
		END{
			print myrecs "\t" mynbmean "\t" mynbmed "\t" mynbstd "\t" mynbmin "\t" mynbmax "\t" myhetmean "\t" myhetmed "\t" myhetstd "\t" myhetmin "\t" myhetmax;
		}'




					
		 	

