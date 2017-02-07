#!/bin/bash

numargs="2"

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <orig genepop file> <comma-delimited list of indiviudals>"
	exit 0
fi




myf="$1"
mylist="$2"


awk -v indivlist="${mylist}" \
	'BEGIN{
		pop_number=0
	}
	{
		
		if( NR>1 && match( $0, /^pop[[:space:]]|^pop$/ ) )
		{
			print $0
			pop_number++
		}
		else if(  pop_number==0 ) 
		{
			print $0
		}
		else if( pop_number>0 )
		{
			split( $0, mya, "," )
			indiv_name=mya[1]
			mval= match( indivlist, mya[1] ) 
			if (mval>0)
			{	
				print $0
			} #end if indiv in list
		}
		else
		{
			print "Error: genepop line uncategorized" > "/dev/stderr"
			exit
		} #end if pop line, else preamble, else indiv line
	}' "$myf"
		
		
		
		

