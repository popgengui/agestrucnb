'''
Description
'''
from builtins import range
__filename__ = "drivetestseed.py"
__date__ = "20160822"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"
import subprocess
import sys

if __name__ == "__main__":

	
	inumprocs=int( sys.argv[1] )
	sfilebase=sys.argv[2] 

	for i in range( inumprocs ):

		sfile=sfilebase + str( i ) 
		o_sub=subprocess.Popen( [ "python", "-c", "import testseed; testseed.mymain(  \"" + sfile + "\" )" ] )

	#end for i	

	
	#end for range
	pass
#end if main

