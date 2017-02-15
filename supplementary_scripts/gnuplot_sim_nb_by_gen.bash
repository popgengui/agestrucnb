#/bin/bash
#Do a gnuplot of the Nb values generated in the sim
#via the sim's restrictedGenerator and its calling
#calcNb.  

#input table file should have cols generation<tab>Nb value

#naive gnuplot usage, copying mostly
#from http://psy.swansea.ac.uk/staff/carter/gnuplot/gnuplot_histograms.htm"
#Note: if your gnuplot installation doesn't have "term" type "qt", then on linux
#try "x11", or on windows, maybe "wxt" (?).


#requires gnuplot program.

numrequiredargs="5"
numwithopt="6"

mys=$( basename $0 )

if [ "$#" -ne "$numrequiredargs" ] && [ "$#" -ne "$numwithopt" ]
then
	echo "usage: $mys "
	echo "args: "
	echo "       <file with nb counts-table> "
	echo "       <int, number of generations> "
	echo "       <int, min value for Nb axis (y-axis)"
	echo "       <int, target Nb>"
	echo "       <title>"
	echo "       optional, <term name> (default is \"qt\", but try \"wxt\" or \"x11 (linux)\" if no qt)"

	exit 0
fi


mytable="$1"
total_gens="$2"
minyval="$3"
target_nb="$4"
mytitle="$5"

if [ "$#" -eq "${numwithopt}" ]
then
	const_term="$6"
else
	const_term="qt"
fi



const_pad_right=0
const_term="qt"
const_width=$( echo "${total_gens}" | awk '{ print $0 * 22 }' )
const_height="600"
const_size="size ${const_width}, ${const_height}"

gnuplot_statements="set term ${const_term} ${const_size}; \
			set xlabel 'generation'; \
			set ylabel 'Nb'; \
			set title '${mytitle}'; \
			set yrange [ ${minyval} : ]; \
			set xrange [ 0 : ${total_gens} + ${const_pad_right} ]; \
			set arrow 1 from 0,${target_nb} to ${total_gens},${target_nb} nohead; \
			set label 'expected' at 0,${target_nb} offset 0.5,1; \
			plot '${mytable}' using 1:2 title '' with linespoints;"

gnuplot -p -e "${gnuplot_statements}"

