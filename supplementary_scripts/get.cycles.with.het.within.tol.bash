
numargs=6

mysc=$( basename $0 )

neguiscript="get_het_under_hw_using_allele_freqs.py"

if [ "$#" -ne "$numargs" ]
then
	echo "usage: $mysc <genepopfile> <target het val> <tolerance> <min cycle> <max cycle> <n, show top n results>"
	echo "Note: assumes script, get_het_under_hw_using_allele_freqs.py, is in your path, and is executable."
	echo "You'll find the script in the negui directory, subdirectory \"supplementary_scripts\"."
	exit 0
fi

mygp="$1"
myhet="$2"
mytol="$3"
mymincy="$4"
mymaxcy="$5"
myrestot="$6"

mintol=$( echo "$mytol" | awk -v hval="$myhet" '{ print( hval - $0 ) }' )
maxtol=$( echo "$mytol" | awk -v hval="$myhet" '{ print( hval + $0 ) }' )

$neguiscript -g $mygp -i $mymincy -f $mymaxcy \
	| awk -v hval="$myhet" -v hmin="$mintol" -v hmax="$maxtol"  \
		'$2>=hmin && $2<=hmax{ 
					diff=hval-$2;
					absdiff=(diff<0)?diff*-1:diff;
					print $1 "\t" $2 "\t" absdiff; }' \
	| sort -n -k '3,3' \
	| head -n "$myrestot"

	
