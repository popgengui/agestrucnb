#!/bin/bash


numargs=1
mysc=$( basename $0 )

if [ "$numargs" -ne "$#" ]
then
	echo "usage: $mysc <genepop file>"
	exit 1
fi



awk 'BEGIN{ 
	popnum=0;
	indiv_count=0; 
	loci_count=0; }
     {
	     ispop=( tolower($0) ~ /^pop/ )
	     if( NR==1 )
	     { 
		     myheader= $0 	     
	     }
	     else if ( popnum==0 && ispop == 0 )
	     {
		     loci_count++
	     }
	     else if ( $0 ~ /pop/ )
	     {
		     popnum++

		     if( popnum > 1 )
		     {
			     print  popnum-1  "\t"  indiv_count
			     indiv_count=0
		     }
		     else
		     {

			     print "total loci: "  loci_count
		     }
	     }
	     else
	     {
		     indiv_count++
	     }
     }
     END{ 
     	#last populaion count is not printed in main loop:
	print popnum "\t" indiv_count

     	print "header: "  myheader > "/dev/stderr"
	print "total loci: "  loci_count > "/dev/stderr"
     	print "total pops: "  popnum > "/dev/stderr"
     }' "$1"
     

