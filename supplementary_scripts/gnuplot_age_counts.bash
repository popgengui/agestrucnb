#/bin/bash
#Do a gnuplot age-counts bar plot.
#input table file should have cols (for N age classes)
#generation_number<tab>age1<tab>age2<tab>....ageN

#naive gnuplot usage, copying mostly
#from http://psy.swansea.ac.uk/staff/carter/gnuplot/gnuplot_histograms.htm"
#Note: if your gnuplot installation doesn't have "term" type "qt", then on linux
#try "x11", or on windows, maybe "wxt" (?).


#requires gnuplot program.

numrequiredargs="4"
numwithopt="5"

mys=$( basename $0 )

if [ "$#" -ne "$numrequiredargs" ] && [ "$#" -ne "$numwithopt" ]
then
	echo "usage: $mys "
	echo "args: "
	echo "       <file with age-counts-table> "
	echo "       <int, number of age classes in table> "
	echo "       <int, number of generations> "
	echo "       <title>"
	echo "       optional, <term name> (default is \"qt\", but try \"wxt\" or \"x11 (linux)\" if no qt)"

	exit 0
fi


mytable="$1"
total_ages="$2"
total_gens="$3"
mytitle="$4"

if [ "$#" -eq "${numwithopt}" ]
then
	const_term="$5"
else
	const_term="qt"
fi



const_pad_right=8
const_term="qt"
const_width=$( echo "${total_gens}" | awk '{ print $0 * 22 }' )
const_height="600"
const_size="size ${const_width}, ${const_height}"

gnuplot_statements="set term ${const_term} ${const_size}; \
			set style data histogram; \
			set style histogram rowstacked; \
			set boxwidth 0.6 relative; \
			set style fill solid 0.5 border; \
			set xlabel 'generation'; \
			set ylabel 'count' ; \
			set title '${mytitle}'; \
			set xrange [ 0 : ${total_gens} + ${const_pad_right} ]; \
			plot for [COL = 2:( ${total_ages} + 1 ) ] '${mytable}' using COL:xticlabels(1) title columnheader;"

gnuplot -p -e "${gnuplot_statements}"

