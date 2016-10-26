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
numargs="10"

#table format will be 2 cols, tab sep,
#matches<tab>misses
#
outformat="table"

if [ "$#" -ne "$numargs" ]
then

	echo "usage: $mysc"
	echo -e  "args: <genepop file>\n--<indiv sampling scheme>\n--<indiv sampling scheme params>\n--<popstart>\n--<popend>\n--<loci sampling scheme>\n--<loci scheme param>\n--<locistart>\n--<lociend>\n--<maxloci>"
	exit 0
fi

myf="$1"
ps="$2"
pp="$3"
p1="$4"
p2="$5"
lsch="$6"
lp="$7"
l1="$8"
l2="$9"
#2-digit arg requires braces
maxl="${10}"


tempfilebase="tmp.$RANDOM"

execloc="/home/ted/documents/source_code/python/negui"




python ${execloc}/pgdriveneestimator.py -f $myf -s ${ps} -p "${pp}" -m 1 -a 99999 \
				-r "${p1}-${p2}" -e 0.01 -c 1 -l ${lsch} -i ${lp} \
				-g ${l1}-${l2} -x ${maxl} -d debug3 \
				1>${tempfilebase}.out 2>${tempfilebase}.err

#This will collect the list from
#the genepop file regardless of any loci range
#spec:
locilist=$( awk 'BEGIN{ 
			saw_first_pop=0;
	 		mylist="";
		}
		{ 
			if ( tolower( $0 ) == "pop" )
			{
				saw_first_pop=1
			}
			else if ( NR > 1 && saw_first_pop==0 )
			{
				sub( "l",""  );
				mylist=mylist "," $0 + 1; 
				
			} 
		}
		END{ 
			sub( /^,/, "", mylist ); 
			print mylist
		}' *_g_${p1} )

#The table output by pgdriveneestimator.py to stderr in "debug3"		
#mode has the pop number in the second column and the
#indiv num list in the 5th
colpopnum="2"
colindiv="5"

#Assoc array with indiv. list for each
#pop by pop number.
declare -A indivsbypop

while read myline
do
	mypopindex=$( echo "$myline" | cut -f "$colpopnum")
	myindivs=$( echo "$myline" | cut -f "$colindiv")
	myindivs=$( echo "myl=[ int( i ) for i in '${myindivs}'.split( ',') ];myl.sort();print ','.join( [ str(i) for i in myl ]);" \
		 | python  )
	
	#pgdriveneestimator.py's table does not srot the indiv indices,
	#but to match the pgdriveneestimator.py output genepop,
	#we sort the indices, so that the call below to filter the
	#individuals in the orig genepop will write them in sorted order:
	myindivs=$( echo "$myindivs" | gawk '{ split( $0, mya, "," );
						asort( mya );
					}END{
						for ( a in mya )
						{
							mys=mys "," mya[a];
						}

						sub( /^,/,"",mys );
						print mys; }' )

						
	indivsbypop[${mypopindex}]="${myindivs}"
done < "$tempfilebase.err"

matches="0"
misses="0"
popcount="0"

for pn in $( seq $p1 $p2 )
do
	#gp file for this pop, derived from the original
	#that is filtered  for the indiv, as given
	#by the list of indiv numbers output by
	#pgdriveneestimator.py
	tmpgp="${tempfilebase}.${pn}.gp"

	indivlist="${indivsbypop[${pn}]}"

	${execloc}/supplementary_scripts/get.genepop.filtered.by.indiv.list.and.pop.number.bash \
			${myf} ${indivlist} ${pn} > ${tmpgp}

	#note we want pop number 1, which is the sole pop in the
	#tmp get (but the pn_th pop from the orig:
	${execloc}/supplementary_scripts/get.genepop.filter.loci.by.list.bash \
			${tmpgp} 1 1 $locilist > test_g_${pn} 

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

rm *_g_*
rm *indiv.table
rm ${tempfilebase}*


if [ outformat=="table" ]
then
	echo -e "${matches}\t${misses}"
else
	echo "matches: $matches"
	echo "misses: $misses"
fi

