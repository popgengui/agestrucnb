#!/bin/bash

numargs="3"
mysc=$( basename $0 )

if [ "$#" -ne  "$numargs" ]
then
	echo "usage: $mysc <filename> <min litter size to show> <[gp|sim] filetype, genepop or *.sim>"
	exit 1
fi	

awk -v ftype="$3" -v minlitter="$2" \
	'BEGIN {
		curr_gen=-1

		SIMCOL_GEN=1
		SIMCOL_MOM=6
		SIMCOL_DAD=5

		GPCOL_MOM=4
		GPCOL_DAD=3

	}
	{
		if ( ftype=="gp" && $0  == "pop"  )
		{
			curr_gen++
		}
		else if ( ftype=="sim" )
		{
			split( $0, mya, " " )
			curr_gen=mya[ SIMCOL_GEN ]
			mom=mya[ SIMCOL_MOM ]
			dad=mya[ SIMCOL_DAD ]
			myp[ curr_gen  ";"  mom  ";"  dad ] ++
		}
		else if ( ftype=="gp" && gennum > -1 )
		{
		
			if( curr_gen > -1 )
			{
				split( $0, mya, "," )
				split( mya[ 1 ], myb, ";" )
				mom=myb[ GPCOL_MOM ]
				dad=myb[ GPCOL_DAD ]
				myp[ curr_gen  ";"  mom  ";"  dad ] ++
			}
		}#end if gp and new pop entry, else sim, else gp and past first "pop" line
	}
	END{
		for( p in myp )
		{
			if( myp[ p ] >= minlitter )
			{
				print p  "\t"  myp[ p ]
			}
		}
	}' "$1" | sort -n -k '1,1' -t ";"
		








