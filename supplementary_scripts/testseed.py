'''
Description
'''
__filename__ = "testseed.py"
__date__ = "20160822"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"


import numpy
import sys

RANGE=100
SAMPSIZE=100

def mymain ( sfile ):

	numpy.random.seed()

	liints=list( numpy.random.randint( 1,RANGE+1, SAMPSIZE ) )
	
	ofile=open( sfile, 'w' )

	ofile.write( "\t".join( str( i ) for i in liints ) + "\n"  )

#end mymain




if __name__ == "__main__":
	sfile=sys.argv[1]
	
	mymain( sfile )

#end if main

