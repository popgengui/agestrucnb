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

		'''
		2018_04_28.  These new params are passed to LDNe2, and are not part
		of the original set of params Tiago used calling NeEstimator. 
		Note that NeEstimator, then or in later versions, does implement
		the loci/chrom table, but we have implemented a direct call to LDNe2
		customized for our program, to take these params.
		'''
		self.__ldne2_only_params={ "chromlocifile":"None", "allele_pairing_scheme":0 }
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

	'''
	2018_04_28. Added to implement new chromlocifile
	and allele_pairing_scheme parameters passed to LDNe2.
	'''
	@property
	def ldne2_only_params( self ):
		#not to be used as a setter
		#for parms, so pass a deep copy
		return copy.deepcopy( self.__ldne2_only_params )
	#end property ldne2_only_params

	@ldne2_only_params.setter
	def ldne2_only_params( self, dv_params ):
		for s_name in dv_params:
			self.__ldne2_only_params[ s_name ] = dv_params[ s_name ]
		#end for each param
		return
	#end setter for ldne2_only_params

#end class PgInputNeEstimator

if __name__ == "__main__":
	pass
#end if main

