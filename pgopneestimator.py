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
import sys

sys.path.append("/home/sinless/myPyLibs/pygenomics")

from genomics.popgen.ne2.controller import NeEstimator2Controller
from genomics.popgen import ne2


from apgoperation import APGOperation

from pginputneestimator import PGInputNeEstimator
from pgoutputneestimator import PGOutputNeEstimator

import pgutilities as pgut

import sys
import os
#so we can the NeEstimator session in its own
#temporary directory:
import tempfile
#so we can delete the temporary directory
#and all of its files:
import shutil
#so we can copy renamed input files
import glob

class PGOpNeEstimator( APGOperation ):
	'''
	For the Ne-estimation gui, the operation object
	that takes simupop-operation results (from the pgopsimupop
	object), and performes and ldne analysis using Tiago Antao's
	ne.py code and his other utilitites.
	'''
	def __init__( self, o_input=None, o_output=None  ):

		super( PGOpNeEstimator, self ).__init__( o_input, o_output )

		self.__indir=None
		self.__outdir=None
		self.__infile=None
		self.__outfile=None

		return
	#end __init__

	def prepareOp( self ):
		'''
		abstract base class requires this def
		'''
		raise Exception( "def not implemented" )
	#end prepareOp

	def __extract_file_in_out_info( self ):
		'''
		Because we are, per Tiago's advice, running
		the NeEstimator with currdir in a temp directory,
		we use absolute paths to input/output files to 
		simplify copying to/from temp dir:
		'''

		self.__indir, self.__infile= \
				self.__get_separate_dir_and_file_name( self.input.genepop_file )

		self.__outdir, self.__outfile= \
				self.__get_separate_dir_and_file_name (  self.output.run_output_file  )
		return
	#end __extract_file_in_out_info

	def __get_separate_dir_and_file_name(self,  s_filename ):

		s_abs_path_and_file=os.path.abspath( s_filename )
		s_dir=os.path.dirname( s_abs_path_and_file )
		s_file=os.path.basename( s_abs_path_and_file )

		return(  s_dir, s_file ) 
	#end get_separate_dir

	def __change_current_directory_to_temporary_directory_inside_current( self ):

		s_temp_dir=None

		s_abs_path_current_directory = \
				os.path.abspath( os.path.curdir )

		#make the temp dir inside the current directory
		s_temp_dir=tempfile.mkdtemp( dir=s_abs_path_current_directory )
	
		os.chdir( s_temp_dir )

		return s_temp_dir
	#end __change_current_directory_to_temporary_directory_inside_current

	def __return_to_original_non_temporary_directory( self ):
		'''
		Assumes that the temporary directory is
		the current directory when this def is called,
		and that the original directory to which to return
		is the parent of the current directory
		'''

		os.chdir( "../" )

		return
	#end __return_to_original_non_temporary_directory


	def __remove_temporary_directory_and_all_of_its_contents( self, s_temp_dir ):
		'''
		Note: shutil.rmtree fails on encountering readonly files
		We add a few paranoia-induced checks, in case the arg s_temp_dir
		is not, as intended, solely the garbage dump for NeEstimator
		'''

		CORRECT_TMP_DIR_PREFIX="tmp"
		NUMBER_SUBDIRS_EXPECTED=0
		SUSPICOUSLY_HIGH_FILE_COUNT=4


		tup_path_head_tail =  os.path.split( s_temp_dir )
		
		s_dir_name=tup_path_head_tail[ 1 ]


		if not( s_dir_name.startswith( CORRECT_TMP_DIR_PREFIX ) ):
				s_msg = "in PGOpNeEstimator instance, " \
							+ "def __remove_temporary_directory_and_all_its_contents, " \
							+ "s_temp_dir directory name, " \
							+ s_temp_dir \
							+ " should begin with \"tmp\"."

				raise Exception(  s_msg )
		#end if non-tmp name

		i_num_subdirs=len( pgut.get_list_subdirectories( s_temp_dir ) )
		i_num_files=len( pgut.get_list_file_objects( s_temp_dir ) )
		
		if i_num_subdirs > NUMBER_SUBDIRS_EXPECTED \
				or i_num_files >= SUSPICOUSLY_HIGH_FILE_COUNT:
				s_msg="in PGOpNeEstimator instance, " \
							+ "def __remove_temporary_directory_and_all_its_contents, " \
							+ "temp dir: " + s_temp_dir \
							+ ", not able to remove temp directory " \
							+ "due to unexpectedly high " \
							+ "file count, " + str( i_num_files )  \
							+ ", and/or subdirectory count, " + str(i_num_subdirs ) + "."
				raise Exception( s_msg )
		else:
				shutil.rmtree( s_temp_dir )
		#end if high file or subdir count, error, else remove 


		return
	#end __remove_temporary_directory_and_all_its_contents

	def __copy_genepop_input_and_get_temp_file_names( self ):

		s_temp_input_filename="tempgp"
		s_temp_output_base="tempout"

		s_currdir=os.path.abspath( os.curdir )

		shutil.copy( self.__indir + os.path.sep + self.__infile, 
						s_currdir + os.path.sep + s_temp_input_filename )

		return s_temp_input_filename, s_temp_output_base
	#end __prepare_temp_files_and_get_temp_file_names

	def __copy_results_to_orig_dir( self, s_temp_out_base ):
		'''
		This def assumes our current dir is still the 
		temp dir with result files inside.
		'''
		ls_output_files=glob.glob( s_temp_out_base + "*" )
		
		for s_file in ls_output_files:
			s_copy_for_orig_dir=self.__outdir + os.path.sep \
					+ s_file.replace( s_temp_out_base, self.__outfile )
			shutil.copy( s_file, s_copy_for_orig_dir  )
		#end for each file prefixed with our temp output file name

		return
	#end __copy_results_to_orig_dir

	def doOp( self ): 

		ne2c=NeEstimator2Controller()

		#This gives our instance attributes
		#values for dirnames and filenames
		#for the input genepop file and the
		#output base name:
		self.__extract_file_in_out_info()
	
		#run the estimator in a temporary directory, per Tiago's recommendation:
		s_temp_dir=self.__change_current_directory_to_temporary_directory_inside_current()

		s_temp_in, s_temp_out=self.__copy_genepop_input_and_get_temp_file_names()	

		#run estimator -- give it full path to currdir:
		s_currdir=os.path.abspath( os.curdir )

		ne2c.run( s_currdir, s_temp_in, s_currdir, s_temp_out, **( self.input.run_params  ) )

		self.__copy_results_to_orig_dir( s_temp_out )
			
		#make the current directory the original, before the change to a temporary dir:
		self.__return_to_original_non_temporary_directory()

		self.__remove_temporary_directory_and_all_of_its_contents( s_temp_dir )
		
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

	def getOutputColumnNumberForFieldName( self, s_field_name ):
		'''
		2017_02_11. In implementing a bias adjustment to NeEstimator
		ldne estimates, in pgdriveneestimator, we need a way to
		easily get the Nb (i.e. Nb when Ne calculated on a cohort),
		value from this object, since we want to keep the PGOutputNeEstimator
		objecte well hidden inside this "Op" object.
		'''
		return self.output.getColumnNumberForFieldName (s_field_name )
	#end def getColumnNumberForFieldName

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

