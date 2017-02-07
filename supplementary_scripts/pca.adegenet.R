
library( adegenet )

#myfile="chnk/UpperSalmonRiverMainstemBY2010_70.ade.gen"

#myfile="chnk/WallowaRiverBY2010_206.ade.gen"
#myfile="chnk/WallowaRiverBY2010_206.ade.gen"
#myfile="chnk/WallowaRiverBY2010_206.ade.gen"
#myfile="chnk/SFSalmonRiverMainstemBY2006_254.ade.gen"

#myfile="chnk/SFSalmonRiverBY2009_232.ade.gen"

#too small a sample to get pca:
myfile="chnk/BearValleyCreekBY2008_2.ade.gen"

ogen=read.genepop( myfile) 

X<-tab( ogen, NA.method="zero" )

opca=dudi.pca( X, scannf=FALSE, scale=FALSE )

temp=as.integer( pop( ogen  ) )

myCol<-transp( c( "blue", "red" ), .7 )[ temp ]

mypch<-c(15,17)[ temp ]

plot( opca$li, type='none'  )

text( opca$li, labels=rownames( opca$li ), cex=0.6 )


#chnk/SFSalmonRiverBY2006_409.ade.gen
#chnk/SFSalmonRiverBY2007_326.ade.gen
#chnk/SFSalmonRiverBY2008_361.ade.gen
#chnk/SFSalmonRiverBY2009_232.ade.gen
#chnk/SFSalmonRiverBY2010_612.ade.gen
#chnk/SFSalmonRiverMainstemBY2007_199.ade.gen
#chnk/SFSalmonRiverMainstemBY2008_144.ade.gen
#chnk/SFSalmonRiverMainstemBY2009_73.ade.gen
#chnk/SFSalmonRiverMainstemBY2010_213.ade.gen

#AsotinCreekBY2006_7.ade.gen
#AsotinCreekBY2007_3.ade.gen
#AsotinCreekBY2008_5.ade.gen
#AsotinCreekBY2010_2.ade.gen
#BearValleyCreekBY2006_11.ade.gen
#BearValleyCreekBY2007_9.ade.gen
#BearValleyCreekBY2008_2.ade.gen
#BearValleyCreekBY2010_4.ade.gen
#BigCreekBY2006_8.ade.gen
#BigCreekBY2007_29.ade.gen
#BigCreekBY2008_66.ade.gen
#BigCreekBY2009_69.ade.gen
#BigCreekBY2010_167.ade.gen
#BigSheepCreekBY2006_11.ade.gen
#BigSheepCreekBY2007_21.ade.gen
#BigSheepCreekBY2008_13.ade.gen
#BigSheepCreekBY2009_6.ade.gen
#BigSheepCreekBY2010_11.ade.gen
#CatherineCreekBY2006_10.ade.gen
#CatherineCreekBY2007_17.ade.gen
#CatherineCreekBY2008_51.ade.gen
#CatherineCreekBY2009_33.ade.gen
#CatherineCreekBY2010_90.ade.gen
#chnk.ade.gen.zip
#EastForkSalmonRiverBY2006_14.ade.gen
#EastForkSalmonRiverBY2007_17.ade.gen
#EastForkSalmonRiverBY2008_16.ade.gen
#EastForkSalmonRiverBY2009_11.ade.gen
#EastForkSalmonRiverBY2010_39.ade.gen
#EFSFSalmonRiverBY2006_58.ade.gen
#EFSFSalmonRiverBY2007_50.ade.gen
#EFSFSalmonRiverBY2008_91.ade.gen
#EFSFSalmonRiverBY2009_75.ade.gen
#EFSFSalmonRiverBY2010_150.ade.gen
#GrandeRondeRiverUpperMainstemBY2006_10.ade.gen
#GrandeRondeRiverUpperMainstemBY2007_17.ade.gen
#GrandeRondeRiverUpperMainstemBY2008_66.ade.gen
#GrandeRondeRiverUpperMainstemBY2009_66.ade.gen
#GrandeRondeRiverUpperMainstemBY2010_220.ade.gen
#ImnahaRiverBY2006_71.ade.gen
#ImnahaRiverBY2007_180.ade.gen
#ImnahaRiverBY2008_115.ade.gen
#ImnahaRiverBY2009_38.ade.gen
#ImnahaRiverBY2010_160.ade.gen
#LemhiRiverBY2006_8.ade.gen
#LemhiRiverBY2007_32.ade.gen
#LemhiRiverBY2008_11.ade.gen
#LemhiRiverBY2009_46.ade.gen
#LemhiRiverBY2010_91.ade.gen
#LoloCreekBY2007_7.ade.gen
#LoloCreekBY2008_29.ade.gen
#LoloCreekBY2009_12.ade.gen
#LoloCreekBY2010_10.ade.gen
#LookingglassCreekBY2006_7.ade.gen
#LookingglassCreekBY2007_15.ade.gen
#LookingglassCreekBY2008_21.ade.gen
#LookingglassCreekBY2009_10.ade.gen
#LookingglassCreekBY2010_21.ade.gen
#McCallHatcheryWeirBY2006_30.ade.gen
#McCallHatcheryWeirBY2007_41.ade.gen
#McCallHatcheryWeirBY2008_32.ade.gen
#McCallHatcheryWeirBY2009_26.ade.gen
#McCallHatcheryWeirBY2010_75.ade.gen
#PahsimeroiRiverBY2006_4.ade.gen
#PahsimeroiRiverBY2007_2.ade.gen
#PahsimeroiRiverBY2009_3.ade.gen
#PahsimeroiRiverBY2010_30.ade.gen
#RapidRiverBY2006_3.ade.gen
#RapidRiverBY2007_4.ade.gen
#RapidRiverBY2008_3.ade.gen
#SawtoothHatcheryWeirBY2006_53.ade.gen
#SawtoothHatcheryWeirBY2007_60.ade.gen
#SawtoothHatcheryWeirBY2008_54.ade.gen
#SawtoothHatcheryWeirBY2009_38.ade.gen
#SawtoothHatcheryWeirBY2010_70.ade.gen
#SeceshRiverBY2006_56.ade.gen
#SeceshRiverBY2007_66.ade.gen
#SeceshRiverBY2008_112.ade.gen
#SeceshRiverBY2009_79.ade.gen
#SeceshRiverBY2010_235.ade.gen
#SFSalmonRiverBY2006_409.ade.gen
#SFSalmonRiverBY2007_326.ade.gen
#SFSalmonRiverBY2008_361.ade.gen
#SFSalmonRiverBY2009_232.ade.gen
#SFSalmonRiverBY2010_612.ade.gen
#SFSalmonRiverMainstemBY2006_254.ade.gen
#SFSalmonRiverMainstemBY2007_199.ade.gen
#SFSalmonRiverMainstemBY2008_144.ade.gen
#SFSalmonRiverMainstemBY2009_73.ade.gen
#SFSalmonRiverMainstemBY2010_213.ade.gen
#SouthForkClearwaterRiverBY2006_4.ade.gen
#SouthForkClearwaterRiverBY2007_25.ade.gen
#SouthForkClearwaterRiverBY2008_121.ade.gen
#SouthForkClearwaterRiverBY2009_40.ade.gen
#SouthForkClearwaterRiverBY2010_73.ade.gen
#TucannonRiverBY2006_4.ade.gen
#TucannonRiverBY2007_3.ade.gen
#TucannonRiverBY2008_4.ade.gen
#TucannonRiverBY2009_5.ade.gen
#TucannonRiverBY2010_12.ade.gen
#UpperSalmonRiverBY2006_86.ade.gen
#UpperSalmonRiverBY2007_134.ade.gen
#UpperSalmonRiverBY2008_179.ade.gen
#UpperSalmonRiverBY2009_191.ade.gen
#UpperSalmonRiverBY2010_441.ade.gen
#UpperSalmonRiverMainstemBY2006_53.ade.gen
#UpperSalmonRiverMainstemBY2007_60.ade.gen
#UpperSalmonRiverMainstemBY2008_54.ade.gen
#UpperSalmonRiverMainstemBY2009_38.ade.gen
#UpperSalmonRiverMainstemBY2010_70.ade.gen
#ValleyCreekBY2006_15.ade.gen
#ValleyCreekBY2007_45.ade.gen
#ValleyCreekBY2008_39.ade.gen
#ValleyCreekBY2009_23.ade.gen
#ValleyCreekBY2010_74.ade.gen
#WallowaRiverBY2006_8.ade.gen
#WallowaRiverBY2007_15.ade.gen
#WallowaRiverBY2008_40.ade.gen
#WallowaRiverBY2009_23.ade.gen
#WallowaRiverBY2010_206.ade.gen
#YankeeForkSalmonRiverBY2007_10.ade.gen
#YankeeForkSalmonRiverBY2008_22.ade.gen
#YankeeForkSalmonRiverBY2009_30.ade.gen
#YankeeForkSalmonRiverBY2010_20.ade.gen
