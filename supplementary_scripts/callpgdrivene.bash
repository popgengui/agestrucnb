#!/bin/bash

#2017_07_11.  This script is an easy way to call
#pgdriveneestimator.py.  The parameters can be
#reset below.


numargs="1"
mysc=$( basename $0 )

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <quoted glob fetching genepop files>"
	echo "note: edit this script to change any parameter of the Ne estimation driver."
	exit 0
fi

PYTHONEXE="python3"

DRIVERLOC="/home/ted/documents/source_code/python/negui/pgdriveneestimator.py"

INCLUDEMAX="99999"
RANGEALL="1-99999"

GPFILES="$1"
SCHEME="cohortsperc"
PARAMS="id;sex;father;mother;age,float;int;float;float;float,1;50"
MINPOPSIZE="1"
MAXPOPSIZE="${INCLUDEMAX}"
#POPRANGE="${RANGEALL}"
POPRANGE="12-15"
MINALLELEFREQ="0.05"
REPLICATES="1"
LOCISCHEME="total"
LOCISCHEMEPARAMS="30"
MINTOTALLOCI="1"
#MAXTOTALLOCI="${INCLUDEMAX}"
MAXTOTALLOCI="40"
LOCIRANGE="1-50"
LOCIREPLICATES="1"
PROCESSES="8"
MODE="debug3"
NBNERATIO="0.0"
DONBBIASADJUST="False"

$PYTHONEXE $DRIVERLOC -f "$GPFILES" -s $SCHEME -p $PARAMS -m $MINPOPSIZE \
                             -a $MAXPOPSIZE -r $POPRANGE -e $MINALLELEFREQ  \
                             -c $REPLICATES -l $LOCISCHEME -i $LOCISCHEMEPARAMS \
                             -n $MINTOTALLOCI -x $MAXTOTALLOCI -g $LOCIRANGE \
                             -q $LOCIREPLICATES -o $PROCESSES -d $MODE \
                             -b $NBNERATIO -j $DONBBIASADJUST
