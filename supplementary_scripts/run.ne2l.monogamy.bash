#!/bin/bash
# create a temporary config file for the Ne2L
#program, using the default settings given by
#its gui default settings, except for:
#--value for methods is "1" (line 1) instead of "15" 
#  so that Ne2L runls LD method only, rather than LD and Coan
#--input and output dir/file names.  
#The script then runs Ne2L
#using the configuration file just created.
#Then it deletes the config file it created.

numargs=3

mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <input file> <output file> <integer, sum of methods (1=LD, 2=Het, 4=Coan, 8=Temporal)"
	exit 0
fi

infile="$1"
outfile="$2"
sumofmethods="$3"

basein=$( basename $infile )
dirin=$( dirname $infile )

baseout=$( basename $outfile )
dirout=$( dirname $outfile )

declare -A neconfiglines

#comments are from the NeEstimator-GUI-generated config file
neconfiglines[1]="${sumofmethods}   0"          # First number n = sum of method(s) to run: LD(=1), Het(=2), Coan(=4), Temporal(=8). Second number k is for various temporals; see below
neconfiglines[2]="${dirin}/"         # Input Directory
neconfiglines[3]="${basein}"      # Input file name
neconfiglines[4]="2"                       # 1 = FSTAT format, 2 = GENEPOP format
neconfiglines[5]="${dirout}/"         # Output Directory
neconfiglines[6]="${baseout}"     # Output file name (put asterisk adjacent to the name to append)
neconfiglines[7]="3"                       # Number of critical values
neconfiglines[8]="0.05  0.02  0.01"        # Critical values
neconfiglines[9]="1"               # 0: Random mating, 1: Monogamy (LD method)
neconfiglines[10]="0 0 1.5"         # One set of generations per line. The first entry is N > 0 for plan I, 0 for plan II. Then generations follow.
neconfiglines[11]="0"               # Only 0 entered: End of generations input

tempfile="$(date +%Y%m%d%H%M_%N).ne2l.config"

for linenum in $( seq 1 ${#neconfiglines[@]} )
do
	thisline="${neconfiglines[${linenum}]}"
	echo $thisline  >> ${tempfile}
done

Ne2L i:${tempfile}

rm ${tempfile}
