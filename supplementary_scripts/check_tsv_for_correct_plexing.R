#!/usr/bin/env Rscript

args=commandArgs(trailingOnly = TRUE)

s.file="../temp_data/my.tsv"
s.file="../../p3negui/nb.test2.ldne.tsv"


getlvlcount=function( v_vector )
{
	return( length( levels( as.factor ( v_vector ) ) ) )
}	

if( length( args ) == 1 )
{
	s.file= args[ 1 ]
}

mydf=read.table( s.file, header=T )

#make the df names visible:
attach( mydf )

l.counts=list()
l.counts[ "total.entries.by.file.line.count" ]=dim( mydf )[ 1 ]
l.counts[ "total.files" ]=getlvlcount(  original_file )
l.counts[ "total.pops" ]=getlvlcount( pop )
l.counts[ "total.pop.reps" ]=getlvlcount( replicate_number )
l.counts[ "total.pop.svals" ]=getlvlcount( sample_value )
l.counts[ "total.loci.reps" ]=getlvlcount( loci_replicate_number ) 
l.counts[ "total.loci.svals" ]=getlvlcount( loci_sample_value ) 

total.by.plex=as.numeric( l.counts[ 2  ] )
print( total.by.plex )
for( i in 3:length( l.counts ) )
{
	total.by.plex=total.by.plex*as.numeric( l.counts[ i ] )
}#end for

l.counts[ "total.entries.by.plex" ]=total.by.plex
	
print( as.matrix( l.counts ) )

v.file.levels=levels( original_file )

v.files.as.numbers=c()

for( f in original_file )
{
	idx=which( v.file.levels==f )
	v.files.as.numbers=c( v.files.as.numbers, idx )
}


v.uniq.reps=paste(  v.files.as.numbers, sample_value, 
		  	replicate_number, loci_sample_value, loci_replicate_number, sep="_" )
getvals=function( vvals)
{
	return( vvals )
}	

l.uniq.reps.ne=tapply( X=est_ne , INDEX= v.uniq.reps,  FUN=getvals )
l.uniq.reps.median.ne=tapply( X=est_ne , INDEX=v.uniq.reps,  FUN=median )

print( "-----------------" )

#print( as.matrix( l.uniq.reps.median.ne ) )

#boxplot( l.uniq.reps.ne )
#axis( side=1, 1:length( l.uniq.reps.median.ne ), labels=names( l.uniq.reps.median.ne ) )

#points( l.uniq.reps.ne )

x11( width=14, height=6 ) 

plot( l.uniq.reps.median.ne, axes=F , xlab="sample by file_popsamp_poprep_locisamp_locirep", ylab="median Ne or Nb estimate")

axis( side=1, at=seq( 1:length( l.uniq.reps.ne ) ), labels=names( l.uniq.reps.median.ne ), cex.axis=0.4, las=2 )
axis( side=2 )

grid()

message( "Press Return" )

invisible( readLines( "stdin", n=1 ) )






