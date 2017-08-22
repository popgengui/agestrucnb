#/bin/bash

# 2017_07_25. Script to convert the input and output files used to get Nb and related values
#from the AgeNeV2 program, into a life table and a configuration file.  The life table is written
#to stdout and the conf file to stderr.
#
#This script is tailored to the current chore of getting Nb/Ne/Nc values for bulltrout and WCT
#life tables in a pub draft, which means we assume equal survival and fecundity rates for male and
#female, and other settings, such as no msats and 100 SNPs, 1000 cycles -- in the conf file.

numargs=2
mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "$mysc <agene_infile> <agene_outfile>"
	echo "prints a life table to stdout, config file to stderr."
	exit 0
fi

age_in="$1"
age_out="$2"

mymodel=$( awk 'NR==1' "$age_in" )
myages=$( awk 'NR==2{print $1}' "$age_in" )

#sim configuration file needs ages value to exceed
#number of age classes by 1
myages=$( expr $myages + 1 )

#we ignore the survival value for the last age class (should be 0.00)
mysurvival=$( awk -v totages="$myages" 'BEGIN{ agecount=0 } \
					{ 
						if (NR>2 &&  NR < ( 1 + totages) && $0 != "" )
						{ 
							svl=svl $2 ","; 
						}
					}
					END {   
						sub( /,$/, "", svl ); 
						print "[" svl "]" 
					}' "$age_in" )

myfecund=$( awk 'NR>2 && $0 != ""{ fcnd=fcnd $3 ",";}END{ sub( /,$/, "", fcnd ); print "[" fcnd "]" }' "$age_in" )

mynb=$( grep "Nb" "$age_out" | awk 'NR==3' | sed 's/^.*Nb\s\+=\s\+//'  )
mynb=$( echo "print( int( round( ${mynb} ) ) )" | python )
mync=$( grep "^Total N" "$age_out" | sed 's/^.*=\s\+//' | sed 's/\s\+(.*//' )
myne=$( grep "Ne (Eq 2)  =" "${age_out}" | sed 's/^.*=\s\+//' | sed 's/\s\+(.*//'  )

mynbnc=$( echo -e "${mynb}\t${mync}\t${myne}" | awk "{print \$1/\$2}" )
mynbne=$( echo -e "${mynb}\t${mync}\t${myne}" | awk "{print \$1/\$3}" )

echo "[model]"
echo "name=${mymodel}"
echo "[resources]"
echo "ages = $myages"
echo "survivalFemale = $mysurvival"
echo "survivalMale = $mysurvival"
echo "fecFemale = $myfecund"
echo "fecMale = $myfecund"
echo "[meta]"
echo "name = $mymodel"
echo "[effective_size]"
echo "Nb = $mynb"
echo "NbNc = $mynbnc"
echo "NbNe = $mynbne"

myquotedmod="\"${mymodel}\""

#write config file
echo "[model]" 1>&2
echo "name=${mymodel}" 1>&2
echo "[pop]" 1>&2
echo "popSize=${mync}" 1>&2
echo "ages=ages[${myquotedmod}]" 1>&2
echo "N0=0" 1>&2
echo "survival.male=survivalMale[${myquotedmod}]" 1>&2
echo "survival.female=survivalFemale[${myquotedmod}]" 1>&2
echo "fecundity.male=fecFemale[${myquotedmod}]" 1>&2
echo "fecundity.female=fecFemale[${myquotedmod}]" 1>&2
echo "[genome]" 1>&2
echo "numMSats=0" 1>&2
echo "startAlleles=10" 1>&2
echo "mutFreq=0" 1>&2
echo "numSNPs=100" 1>&2
echo "[sim]" 1>&2
echo "gens=1000" 1>&2
echo "cull_method=equal_sex_ratio" 1>&2
echo "reps=1" 1>&2
echo "datadir=\"\"" 1>&2
