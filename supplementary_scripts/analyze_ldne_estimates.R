
datadir="/home/ted/documents/source_code/python/negui/temp_data"

tsv_file_ne="wf.esr.tol01.b50.c600.ne.ldne.tsv"
tsv_file_nb="wf.esr.tol01.b50.c600.nb.ldne.tsv"

df_ne=read.table( paste( datadir,tsv_file_ne,sep="/"), header=T )
df_nb=read.table( paste( datadir,tsv_file_nb,sep="/" ), header=T )

ne_adjusted_estimate=df_ne$ne_est_adj
nb_adjusted_estimate=df_nb$ne_est_adj

