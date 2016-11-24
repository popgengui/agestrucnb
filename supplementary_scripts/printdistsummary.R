#!/usr/bin/Rscript

args<-commandArgs(TRUE)

mydf=read.table( file=args[1], header=F )

print ( args[2] )
numindivs=as.numeric( args[2] )
freqsbyindiv=rep( 0, numindivs )

for( slist in mydf$V5 )
{

	llist=strsplit( slist, split="," )

	vvals=as.numeric( llist[[1]] )
	
	#the first individual in each
	#list is always indiv "0",
	#but we skip, as this is simply
	#the "pop" entry:

	#Fri Jul 15 23:43:58 MDT 2016
	#new version of output now does
	#not include indiv 0
	for( i in 1:length( vvals ) )
	{
		indiv=vvals[i]
		currval=freqsbyindiv[ indiv ]
		freqsbyindiv[ indiv ] = currval + 1
	}	
}


idxmin=which( freqsbyindiv==min( freqsbyindiv ) )
idxmax=which( freqsbyindiv==max( freqsbyindiv ) )
mins=paste( as.character( idxmin ), collapse=", " )
maxs=paste( as.character( idxmax ), collapse=", " )
mysdev=round( sd( freqsbyindiv ), 3 )



summary( freqsbyindiv )


print( paste( "stddev:", mysdev, "indiv lowest occurance:", mins, " indiv highest occurance:", maxs ) )

