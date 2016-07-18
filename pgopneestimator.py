'''
Description
For the Ne-estimation gui, the operation object
that takes simupop-operation results (from the pgopsimupop
object), and performes and ldne analysis using Tiago Antao's
ne.py code and his other utilitites.
'''
__filename__ = "pgopneestimator.py"
__date__ = "20160502"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from genomics.popgen.ne2.controller import NeEstimator2Controller
from genomics.popgen import ne2


from apgoperation import APGOperation

from pginputneestimator import PGInputNeEstimator
from pgoutputneestimator import PGOutputNeEstimator

import sys
import os

class PGOpNeEstimator( APGOperation ):
	'''
	For the Ne-estimation gui, the operation object
	that takes simupop-operation results (from the pgopsimupop
	object), and performes and ldne analysis using Tiago Antao's
	ne.py code and his other utilitites.
	'''
	def __init__( self, o_input=None, o_output=None  ):

		super( PGOpNeEstimator, self ).__init__( o_input, o_output )

		return
	#end __init__

	def prepareOp( self ):
		'''
		abstract base class requires this def
		'''
		raise Exception( "def not implemented" )
	#end prepareOp

	def __get_separate_dir_and_file_name(self,  s_filename ):

		s_dir=os.path.dirname( s_filename )
		s_file=os.path.basename( s_filename )

		if s_dir=="":
			s_dir="."
		#end if no dir name, return currdir

		return(  s_dir, s_file ) 
	#end get_separate_dir

	def doOp( self ): 

		ne2c=NeEstimator2Controller()

		s_outdir, s_outfile=self.__get_separate_dir_and_file_name ( self.output.run_output_file  )

		s_indir, s_infile=self.__get_separate_dir_and_file_name( self.input.genepop_file )
	
		ne2c.run( s_indir, s_infile, s_outdir, s_outfile, **( self.input.run_params  ) )
		
		self.output.parseOutput()

		#in case the NeEstimator
		#generated a NoDat.txt file
		#we parse (output object
		#checks for NoDat.txt file,
		#does nothing if there is 
		#no file)
		self.output.parseNoDatFile()

	#end doOP

	def deliverResults( self ):
		'''
		abstract base class requres this def
		'''
		return self.output.parsed_output

	#end deliver results 

#end class PGOpNeEstimator 

if __name__ == "__main__":

	s_datdir="/home/ted/documents/source_code/python/negui"
	sys.path.append( s_datdir )

	import genepopfilemanager as gpf
#	s_gpfile="AlpowaCreekBY2006_14.txt"
#	s_gpfile="AsotinCreekBY2006_104.txt"
	s_gpfile="BigCreekBY2006_29.txt"

	s_genepop_file="/".join( [ s_datdir,  "temp_data/genepop_from_brian_20160506", s_gpfile ] )
	
	f_prop=0.10

	o_gp=gpf.GenepopFileManager( s_genepop_file )
	o_gp.subsampleIndividualsRandomly( f_prop,  str( f_prop ) )

	s_subsample_genepop_file=o_gp.original_file_name + "." + str( f_prop )
	o_gp.writeGenePopFile( s_subsample_genepop_file, str( f_prop ) )

	#run orig or the subsample:
	s_file_to_run=s_genepop_file

	o_input=PGInputNeEstimator( s_file_to_run )
	o_output=PGOutputNeEstimator( s_file_to_run + ".ne.est" )
	f_thres= 0.011 
	o_input.run_params = { "crits":[ f_thres ]  } 
	o_estimator=PGOpNeEstimator( o_input, o_output )
	o_estimator.doOp()
			
	pass
#end if main

