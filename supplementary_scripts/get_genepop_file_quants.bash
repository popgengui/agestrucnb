#!/bin/bash


maxargs=2
minargs=1
mysc=$( basename $0 )

if [ "$#" -gt "$maxargs" ] || [ "$#" -lt "$minargs" ]
then
	echo "usage: $mysc <genepop file> <optional, term|window, use gnuplot to plot to terminal or its default gui window>"
	exit 1
fi

dopipe=""

plottype=""

if [ "$#" -eq "$maxargs" ]
then
	dopipe="do"

	if [ "$2" == "term" ]
	then
		plottype="set terminal dumb;"
	fi

fi




mytots=$( awk 'BEGIN{ 
		popnum=0;
		indiv_count=0; 
		loci_count=0; 
		mycounts=""
	} #end BEGIN
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
				     mycounts=mycounts " "  popnum-1  ","  indiv_count
				     indiv_count=0
			     }
			     else
			     {

				    # print "total loci: "  loci_count
				    pass=1
			     }
		     }
		     else
		     {
			     indiv_count++
		     }
	   } #end main
	     END{ 
		#last populaion count is not printed in main loop:

		mycounts=mycounts " " popnum "," indiv_count
		
		print mycounts
		print "header: "  myheader > "/dev/stderr"
		print "total loci: "  loci_count > "/dev/stderr"
		print "total pops: "  popnum > "/dev/stderr"
	}'  $1 ) 

	if [ -z "$dopipe" ]
	then
		echo "Indiv counts per cycle (\"cycle,count\"): $mytots"
	else
		for myc in $mytots
		do
			echo -e "${myc/,/\\t}"
		done | gnuplot -p -e "unset key; set xlabel 'reprocycle'; set title 'indiv count by repro cycle';${plottype}plot '<cat' with lines" 
	fi
