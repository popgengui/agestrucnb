'''
Description
This class takes a gui interface as an intit param, extracts the
neLineRegress paramater values from the the interface, and uses
them to write a config file that can be used by the neLineRegress program(s)>
'''
__filename__ = "pglineregressconfigfilemaker.py"
__date__ = "20161115"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from ConfigParser import ConfigParser
import os 
class PGLineRegressConfigFileMaker( object ):
	def __init__( self, o_gui_interface, s_config_file_out_name ):
		self.__ds_params_and_vals_by_section={ "labels":{ "xlab":None , "ylab":None},
				"destination":{ "desttype":None, "regressionfile":None, "boxplotfile":None, "scatterfile":None },
				"comparison":{ "type":None, "expectedSlope":None },
				"limits":{ "xMin":None, "xMax":None },
				"data":{ "startCollect":None },
				"confidence":{ "alpha":None, "outputFilename":None } }
		self.__interface=o_gui_interface
		self.__config_outfile_name=s_config_file_out_name
		self.__config_parser_object=None
		self.__make_parser_object()
		return
	#end __init__

	def __make_parser_object( self ):
		o_parser=ConfigParser()
		o_parser.optionxform=str

		for s_section in self.__ds_params_and_vals_by_section:
			o_parser.add_section( s_section )
			for s_param_name in self.__ds_params_and_vals_by_section[ s_section ]:
				o_parser.set( s_section, s_param_name, getattr( self.__interface, s_param_name ) )
			#end for each param (option, in config file parlance), in this section
		#end for each section

		self.__config_parser_object=o_parser
		return
	#end __make_parser_object

	def writeConfigFile( self ):
		if self.__config_parser_object is not None:
			if os.path.exists( self.__config_outfile_name ):
				s_msg="In PGLineRegressConfigFileMaker instance, "  \
							+ "def, __write_config_file.  The file, " \
							+ self.__config_outfile_name + ", " \
							+ "already exists.  This class disallows " \
							+ "overwriting exisiting files."
				raise Exception( s_msg )

			#end if file exists

			o_file=open( self.__config_outfile_name, 'w' )
			self.__config_parser_object.write( o_file )
			o_file.close()
		else:
			s_msg="In PGLineRegressConfigFileMaker instance, "  \
						+ "def, __write_config_file, an existing " \
						+ "parser object is required to write " \
						+ "the config file.  Found a None value for the "
						+	"confg_parser_object member." \

			raise Exception( s_msg )
		#end if we have a config parser object else not

		return
	#end def write_config_file
#end class PgLineRegressConfigFileMaker

if __name__ == "__main__":
	pass
#end if main

