'''
Description

Class wraps a dictionary of configuration parser
objects, Each item in the dictionary is 
a ConfigParser instance with the life table information. 
The keys in the main dictionary give a model name, such as 
bison, btrout, bullpred, etc.

These values are the life table info from Tiago's
utility code in the original AgeStructureNe 
collection.

'''
from future import standard_library
standard_library.install_aliases()
from builtins import object
__filename__ = "pgsimupopresources.py"
__date__ = "20160418"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"


import glob
import configparser as cp
from configparser import NoSectionError
from configparser import NoOptionError
import sys
import os

class PGSimuPopResources( object ):
	'''

	'''
	def __init__( self, ls_life_table_files, b_write_warnings=False ):
		'''
		Param ls_life_table_files is a list of configuration file names,
			with table info, such as survivial and fecundity rates,
			gamma values, and ages.
		Param b_write_warnings is a flag. If true warnigs are written to stderr.
		'''
		self.__life_table_files=ls_life_table_files
		self.__write_warnings=b_write_warnings
		self.__lifetables={}
		self.__get_life_tables( ls_life_table_files )

		return
	#end __init__

	def __get_life_tables( self, ls_life_table_files ):
		""" 
		From the list of files with the life table information, Reads
		in each file using ConfigParser.
		"""
		for s_file in ls_life_table_files:

			o_this_parser=cp.ConfigParser()
			o_this_parser.read( s_file )
			s_model_name=None	
			try:
				s_model_name=o_this_parser.get( "model" , "name" )
			except NoSectionError as nse:
				'''
				This can happen when the parser is given
				a non-existent file, so we'll check:
				'''
				b_exists=os.path.exists( s_file )
				sys.stderr.write( "In PGSimuPopResources instance, def __get_life_tables, " \
						+ "file: " + s_file \
						+ ".  Config parser found no \"model\" section " \
						+ "with a \"name\" section\n" )
				raise nse
			#end try...except

			if s_model_name in self.__lifetables:
				raise Exception( "In PGSimuPopResources instance, found two life tables with the same model name: " \
						+ s_model_name )
			#end if dup model name

			self.__lifetables[ s_model_name ] = o_this_parser

		#end for each life table file

		return

	#end __get_life_tables

	def getLifeTableValue( self, s_model_name, s_section, s_option ):
		"""
		Tries to fetch the value, 
		Returns a None instance if any of 
		the parameter values are not found.

		On fail also records the first level
		that was not found, and
		if flag self.__write_warnings
		is true, reports the failure to
		stderr.
		"""

		v_value=None
		s_warning=None

		try:
			o_parser=self.__lifetables[ s_model_name ]
			v_value=o_parser.get( s_section, s_option )
		except KeyError as ke:

			s_warnings= "Warning: In PGSimuPopResources instance, def getLifeTableValue, " \
					+ "no life table found for model: "  \
					+ s_model_name + "\n" 

		except NoSectionError as nse:

			s_warning="Warning: In PGSimuPopResources instance, def getLifeTableValue, " \
					+ "no section in life table for model: "  \
					+ s_model_name + "section: " + s_section + "\n" 

		except NoOptionError as noe:

			s_warning= "Warning: In PGSimuPopResources instance, def getLifeTableValue, " \
					+ "no option in life table for model: "  \
					+ s_model_name + "section: " + s_section + "option: " \
					+ s_option + "\n" 
		#end try, except, except, except

		if self.__write_warnings and s_warning is not None:
			sys.stderr.write( s_warning )
		#end if write warnings 

		#eval will throw a type error if v_value is None
		return eval( v_value ) if v_value is not None else None

	#end getLifeTableValue

	@property
	def life_table_files( self ):
		return self.__life_table_files 
	#end getter life_table_files

#end class

