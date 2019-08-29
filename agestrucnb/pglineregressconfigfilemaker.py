'''
Description
This class takes a gui interface as an intit param, extracts the
neLineRegress paramater values from the the interface, and uses
them to write a config file that can be used by the neLineRegress program(s).
'''

from future import standard_library
standard_library.install_aliases()
from builtins import object
__filename__ = "pglineregressconfigfilemaker.py"
__date__ = "20161115"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from configparser import ConfigParser
import os 
import agestrucne.pgutilities as pgut

class PGLineRegressConfigFileMaker( object ):

	CONFIG_FILE_EXT=".viz.config"
	'''
	In the Gui, in order to preserve unique
	attribute names, the viz attributes
	are in 4 parts, delimted.  The name
	that will be recognized by the viz
	program (hence to be written to 
	the config file) is the fourth item,
	and the third gives the config file
	section name in which the 4th item 
	resides.
	'''
	GUI_ATTRIBUTE_DELIMIT="_"
	IDX_GUI_ATTRIB_CONFIG_FILE_SECTION=2
	IDX_GUI_ATTRIB_CONFIG_FILE_PARAM=3

	'''
	2017_05_17. Information to help determine
	which outputFilename value to use. See
	comments in __init__
	'''
	IDX_GUI_ATTRIB_VIZ_TYPE=1

	DICT_ATTRBUTE_TYPE_BY_VIZ_TYPE={ "Regression":"regress", 
										"Subsample":"subsample" }


	def __init__( self, o_gui_interface, b_omit_x_range=True ):
		'''
		Param b_omit_x_range, if True, results in a config file
		missing the xMin and xMax config options, to let (per Brian T)
		matplot lib auto-set the x range.

	
		'''

		self.__interface=o_gui_interface
		self.__omit_x_range=b_omit_x_range
		self.__ds_interface_param_values_by_param_names_by_section={}

		self.__mangled_attribute_prefix=None
		self.__plot_type=None
		self.__config_outfile_name=None
		self.__config_parser_object=None


		self.__make_mangled_attribute_prefix()
		'''
		2017_05_17.  New parameter for object plot_type, which
		the caller interface supplies via its viztype attribute, 
		as either "Regression" or "Subsample", gives us a way to tell 
		which outputFilename value to use (see the test in 
		def __make_dict_interface_param_values.  The PGGuiViz objects 
		attribute, __viztype, gives the user-readable name, and our 
		member dict above will translate that into the field name used 
		in the attributes that give the viz param info "viz_type_section_param".  
		We need this because the viz code uses the same option name "outputFilename" 
		for both the regression stats and the subsample info output that gives the 
		keys to each plot.
		'''
		self.__get_attr_field_plot_type()
		self.__make_dict_interface_param_values()
		self.__make_outfile_name()
		self.__make_parser_object()
		return
	#end __init__

	def __get_attr_field_plot_type( self ):

		s_gui_viz_type=getattr( self.__interface, self.__mangled_attribute_prefix + "viztype" )		
		ds_attr_by_viz=PGLineRegressConfigFileMaker.DICT_ATTRBUTE_TYPE_BY_VIZ_TYPE

		if s_gui_viz_type not in ds_attr_by_viz:
			s_known_types= ", ".join( list( ds_attr_by_viz.keys() ) )

			s_msg="In PGLineRegressConfigFileMaker instance, " \
						+ "def __get_attr_field_plot_type, " \
						+ "the gui viz type passed, " \
						+ s_gui_viz_type + ", " \
						+ "is not one of the known types: " \
						+ s_known_types + "."
			
			raise Exception( s_msg )
		else:
			self.__plot_type=ds_attr_by_viz[ s_gui_viz_type ]
		#end if viz plot type name not known, else is	
	
		return
	#end def __get_attr_field_plot_type

	def __make_mangled_attribute_prefix( self ):
		'''
		I can't use the simpler type() method to
		get the class name, becuase the (grand)parent 
		Frame class (must be) old style, hence no metadata
		for type().  I instead use this tortured bit of code.
		'''
		s_gui_class_name=( self.__interface ).__class__.__name__ 

		self.__mangled_attribute_prefix= \
				"_"  + s_gui_class_name + "__"
		return
	#end __make_mangled_attribute_prefix

	def __make_dict_interface_param_values( self ):
		ls_interface_member_names=dir( self.__interface )
	
		#GUI interface members for viz all begin
		#with this prefix--we need the trailing delimiter
		#because a generel attribute "viztype" is used only 
		#by the GUI (not a plotting param)
		s_viz_prefix=self.__mangled_attribute_prefix + "viz" \
					+ PGLineRegressConfigFileMaker.GUI_ATTRIBUTE_DELIMIT
		for s_member_name in ls_interface_member_names:

			if s_member_name.startswith( s_viz_prefix ):
			
				#strip off the mangling:
				s_member_name_unmangled=s_member_name.replace( self.__mangled_attribute_prefix, "" )

				#Extract the param name (used by the viz program):
				ls_member_name_parts=s_member_name_unmangled.split( \
						PGLineRegressConfigFileMaker.GUI_ATTRIBUTE_DELIMIT )
				s_viz_section_name=ls_member_name_parts[ \
						PGLineRegressConfigFileMaker.IDX_GUI_ATTRIB_CONFIG_FILE_SECTION ]
				s_viz_param_name=ls_member_name_parts[ \
						PGLineRegressConfigFileMaker.IDX_GUI_ATTRIB_CONFIG_FILE_PARAM ] 
				v_value_this_param = getattr( self.__interface, s_member_name )

				if s_viz_section_name not in self.__ds_interface_param_values_by_param_names_by_section:
					self.__ds_interface_param_values_by_param_names_by_section[ s_viz_section_name ] = {}
				#end if section name new to dict, add it
				
				#If its an output file (either one of the plot file names in the "destination" section
				#or the stats out file, whose param name is "outputFileName" (different section in the
				#Vis config file -- the "confidence" section).

				if s_viz_section_name == "destination" or s_viz_param_name == "outputFilename":
					'''
					2017_05_17. We skip writing the outputFilename param if its plot_type
					attribute is not the one current in the gui (see comments in __init__).
					'''
					if s_viz_param_name == "outputFilename":
						s_this_attr_plot_type=ls_member_name_parts[ \
								PGLineRegressConfigFileMaker.IDX_GUI_ATTRIB_VIZ_TYPE ]
						if s_this_attr_plot_type != self.__plot_type:
							continue
						#end if wrong type for outputFilename, don't write it into dict
					#end if this is the outputFilename

					if v_value_this_param not in [ "show", "none" ]:
						#returns a StrVal tkinter object

						v_outdir=getattr( self.__interface, self.__mangled_attribute_prefix + "output_directory" )
						s_outdir=v_outdir.get()
						v_value_this_param = s_outdir + "/" + v_value_this_param
						if pgut.is_windows_platform():
							v_value_this_param=pgut.fix_windows_path( v_value_this_param )
						#end if using Windows, fix the path

					if s_viz_section_name == "destination":
						if not ( v_value_this_param in [ "show", "none" ] \
												or v_value_this_param.endswith( ".png" ) \
												or v_value_this_param.endswith( ".pdf" ) ) :
							
							v_value_this_param = v_value_this_param + ".png"
						#end if not show, or already has png or pdf extension
					#end if this is a plotted file without a known image file ext, default to png
				#end if this is a destination, or stats out "outputFileName" option
			
				if not self.__omit_x_range \
							or s_viz_param_name  not in [ "xMin", "xMax" ]:
						self.__ds_interface_param_values_by_param_names_by_section[ s_viz_section_name ] [ \
															s_viz_param_name ] = v_value_this_param
				#end if we're not omitting x range options, or if the option is not an x range option

			#end if the member is a viz param

		#end for each member of the interface
		return
	#end __make_dict_interface_param_values

	def __make_outfile_name( self ):
		o_strvar_outputdir=getattr( self.__interface, 
				self.__mangled_attribute_prefix \
								+ "output_directory" )

		s_outputdir=o_strvar_outputdir.get()

		s_outfile_basename=self.__interface.output_base_name

		if pgut.is_windows_platform():
			s_outputdir=pgut.fix_windows_path( s_outputdir )
			'''
			In case the GUI user entered a path separator into
			the basename entry
			'''
			s_outfile_basename=pgut.fix_windows_path( s_outfile_basename )
		#end if windows platform
		
		self.__config_outfile_name= \
				s_outputdir + "/" + s_outfile_basename \
				+ PGLineRegressConfigFileMaker.CONFIG_FILE_EXT
		return
	#end __make_outfile_name

	def __make_parser_object( self ):
		o_parser=ConfigParser()
		o_parser.optionxform=str

		for s_section in self.__ds_interface_param_values_by_param_names_by_section:
			o_parser.add_section( s_section )
			dv_param_values_by_param_name=self.__ds_interface_param_values_by_param_names_by_section[ s_section ]
			for s_param_name in dv_param_values_by_param_name:
				v_value_this_param=dv_param_values_by_param_name[ s_param_name ]
				o_parser.set( s_section, s_param_name, str( v_value_this_param ) )
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
							+ "overwriting exisiting files"
				raise Exception( s_msg )

			#end if file exists

			o_file=open( self.__config_outfile_name, 'w' )
			self.__config_parser_object.write( o_file )
			o_file.close()
		else:
			s_msg="In PGLineRegressConfigFileMaker instance, "  \
						+ "def, __write_config_file, an existing " \
						+ "parser object is required to write " \
						+ "the config file.  Found a None value for the " \
						+	"confg_parser_object member" \

			raise Exception( s_msg )
		#end if we have a config parser object else not

		return
	#end def write_config_file

	@property
	def config_file_name( self ):
		return self.__config_outfile_name
	#end property config_file_name
#end class PgLineRegressConfigFileMaker

if __name__ == "__main__":
	pass
#end if main

