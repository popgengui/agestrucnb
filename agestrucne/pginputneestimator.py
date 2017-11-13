'''
Description
Object manages input data to be used by the pgopneestimator object.
'''
from builtins import object
__filename__ = "pginputneestimator.py"
__date__ = "20160502"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import copy

class PGInputNeEstimator (object):
	'''
	CLass to provide class PGOpNeEstimator
	with input file and params needed to run
	the ne-estimator object as coded in Tiago Antao's
	ne2.py, one the age structure modules
	'''
	def __init__( self, s_genepop_filename = None ):
		self.__genepopfile=s_genepop_filename

		#these are the default params in the signature of the run method of
		#Tiago's NeEstimator2Controller

		self.__run_params={ "crits":None, "LD":True, 
							"hets":False, "coanc":False, 
							"temp":None, "monogamy":False, "options":None }
		return
	#end __init__
	
	@property
	def genepop_file(self):
		return self.__genepopfile
	#end genepop_file

	@property
	def run_params( self ):
		#not to be used as a setter
		#for parms, so pass a deep copy
		return copy.deepcopy( self.__run_params )
	#end run_params

	@run_params.setter
	def run_params( self, dv_params ):
		for s_name in dv_params:
			self.__run_params[ s_name ] = dv_params[ s_name ]
		#end for each param
		return
	#end setRunParams

#end class PgInputNeEstimator

if __name__ == "__main__":
	pass
#end if main

