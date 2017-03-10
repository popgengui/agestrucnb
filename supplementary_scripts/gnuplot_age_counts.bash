#/bin/bash
#Do a gnuplot age-counts bar plot.
#input table file should have cols (for N age classes)
#generation_number<tab>age1<tab>age2<tab>....ageN

#naive gnuplot usage, copying mostly
#from http://psy.swansea.ac.uk/staff/carter/gnuplot/gnuplot_histograms.htm"
#Note: if your gnuplot installation doesn't have "term" type "qt", then on linux
#try "x11", or on windows, maybe "wxt" (?).


#requires gnuplot program.

numrequiredargs="6"
numwithopt="7"

mys=$( basename $0 )

if [ "$#" -ne "$numrequiredargs" ] && [ "$#" -ne "$numwithopt" ]
then
	echo "usage: $mys "
	echo "args: "
	echo "       <file with age-counts-table> "
	echo "       <int, number of age classes in table> "
	echo "       <int, number of cycles> "
	echo "       <min:max | \"all\"> age range (\"all\" plots all ages) "
	echo "       <min:max | \"all\"> cycle range (\"all\" plots all cycles) "
	echo "       <title>"
	echo "       optional, <term name> (default is \"qt\", but try \"wxt\" or \"x11 (linux)\" if no qt)"

	exit 0
fi


mytable="$1"
total_ages="$2"
total_gens="$3"
myages="$4"
mycycles="$5"
mytitle="$6"

if [ "$#" -eq "${numwithopt}" ]
then
	const_term="$7"
else
	const_term="qt"
fi

const_pad_right=8
const_width=$( echo "${total_gens}" | awk '{ print $0 * 22 }' )
const_height="600"
const_size="size ${const_width}, ${const_height}"

myxrange="[ 0 : ${total_gens} + ${const_pad_right} ]"

if [ "$mycycles" != "all" ]
then
	myxrange="[ ${mycycles} + ${const_pad_right} ]"
fi

myagerange="2: ( ${total_ages} + 1 )"
if [ "$myages" != "all" ]
then
	myagerange="1 + ${myages} + 1"
fi

gnuplot_statements="set term ${const_term} ${const_size}; \
			set style data histogram; \
			set style histogram rowstacked; \
			set boxwidth 0.6 relative; \
			set style fill solid 0.5 border; \
			set xtics rotate by 55 offset -0.8,-0.9;
			set xlabel 'cycle'; \
			set ylabel 'count' ; \
			set title '${mytitle}'; \
			set xrange ${myxrange} ; \
			plot for [COL = ${myagerange} ] '${mytable}' using COL:xticlabels(1) title columnheader;"

gnuplot -p -e "${gnuplot_statements}"

