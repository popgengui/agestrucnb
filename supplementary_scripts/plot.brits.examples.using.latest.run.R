


mytablefile="chnk.20160705.out.with.creek.and.year.brits.examples.from.email.05.19.csv"
mytablefile="sthd.20160705.out.with.creek.and.year.4.pops.after.brits.email.0522.csv"

mydf=read.table( mytablefile, header=F, col.names=c( "creek", "year", "file", "toti",  "prop", "rep", "af", "ne", "9low","9hi" , "rsq", "esq", "ic", "harm" ) )

seq( 0.1, 1.0, 0.1 )

lcreeks=levels( mydf$creek )

MYPCH=10
NE_THROW_OUT=1e5
REPSTOPLOT=50

l_dfs=list()

maxne=max( mydf$ne[ which( ! is.infinite( mydf$ne ) ) ] ) 
currmaxne=0

for( lcreek in lcreeks )
{
	idx.creek.10reps=which( mydf$creek==lcreek & mydf$rep<REPSTOPLOT & !is.infinite( mydf$ne) & mydf$ne < NE_THROW_OUT )

	l_dfs[[lcreek]]=mydf[ idx.creek.10reps, ]

	##### temp
	print( paste( "creek:", lcreek ) )
	print( paste( l_dfs[[lcreek]]$prop, l_dfs[[lcreek]]$ne ) )
	print ( "-------------------------" )
	#####

	thismax=max( l_dfs[[lcreek]]$ne )
	if(  thismax > currmaxne  )
	{
		currmaxne=thismax
	}

}

plottogether=function()
{

	plot( c( 0, currmaxne ), c( 0, currmaxne ), 
	type = 'n', 
	xlim=c( 0.1, 1.0), 
	main="2009 Pops, Ne estimates by proportion sampled\n10 replicates each pop\nNA's and Inf omitted",
	xlab="Proporion sampled",
	ylab="Ne estimate"
	)

	i_num_creeks=length( l_dfs )

	i_colorspercreek=seq( 1, i_num_creeks )
	i_colcount=1

	for( c in names( l_dfs ) )
	{
		points( l_dfs[[ c ]]$prop, l_dfs[[c]]$ne, col=i_colorspercreek[ i_colcount ], pch=MYPCH )
		i_colcount=i_colcount+1
	}


	legend( "topright",  legend=names( l_dfs ), pch=MYPCH, col=i_colorspercreek )

}


plotseparately=function()
{
	i_num_creeks=length( l_dfs )

	i_color=1

	dev.new()
	for( c in names( l_dfs ) )
	{

		s_filename=unique( l_dfs[[c]]$file )
		currmaxne=max( l_dfs[[c]]$ne )
		i_total_outliers=length( which( l_dfs[[c]]$ne  >= NE_THROW_OUT ) ) 

		dev.new()
		plot( c( 0, currmaxne ), c( 0, currmaxne ), 
		type = 'n', 
		xlim=c( 0.1, 1.0), 
		main=paste( s_filename,
			   "\nNe estimates by proportion sampled\n", 
			  "NA, Infinite, and values over", 
			   NE_THROW_OUT, 
			   " omitted" ),
		xlab=paste( "Proporion sampled (", REPSTOPLOT, " replicates each pop)", sep="" ),
		ylab="Ne estimate" )

		points( l_dfs[[ c ]]$prop, l_dfs[[c]]$ne, col=i_color, pch=MYPCH )
	}

}#end plotseparately

plotseparately()
