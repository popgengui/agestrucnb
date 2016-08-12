'''
Description

Class ParamSet is used to associate
parameter names as given by code variables
(called class attribute shortname),
each with a more user-friendly
name.  These long names (attribute longname) are used
for example, as labels in the gui interface
that allows  users to set the parameters.
'''
__filename__ = "pgparamset.py"
__date__ = "20160429"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class PGParamSet( object ):

	'''
	Class ParamSet is used to replace
	parameter names as given by code variables
	and associates each with a more user-friendly
	name.  These longer, fuller names are used
	for example, as labels in the gui interface
	that allows users to set the parameters.
	'''

	DELIMITER_TAG_FIELDS=";"
	IDX_PARAM_SHORTNAME=0
	IDX_PARAM_LONGNAME=1
	IDX_PARAM_TAG=2

	PARAM_FIELDS_TOTAL=3

	IDX_TAG_FIELD_CONFIG_SECTION=0
	IDX_TAG_FIELD_PLACEMENT_ORDER=1
	IDX_TAG_FIELD_DEFAULT_VALUE=2

	COMMENT_CHAR="#"

	def __init__( self, s_file_with_param_names = None ):

		'''
		If provided, arg s_file_with_param_names
		should be a file with 2 or more strings on each line,
		tab-separated, the first value giving the short
		name of the parameter, the second the long (full)
		name, the third (if present)
		'''
		self.__file_with_param_names=s_file_with_param_names
		self.__params_by_shortname={}
		self.__params_by_longname={}
		self.__tags_by_shortname={}
		self.__tags_by_longname={}

		if s_file_with_param_names is not None:
			self.__init_from_file( s_file_with_param_names )
		#end if file name given
		return
	#end __init__

	def __init_from_file( self, s_file_with_param_names ):
		o_file=open( s_file_with_param_names )

		for s_line in o_file:
			if s_line.startswith( PGParamSet.COMMENT_CHAR ):
				continue
			#end if comment

			s_tag=None
			ls_vals= s_line.strip().split( "\t" )
			s_shortname=ls_vals[ PGParamSet.IDX_PARAM_SHORTNAME ]
			s_longname=ls_vals[ PGParamSet.IDX_PARAM_LONGNAME ]

			self.__set_parameter( s_shortname, s_longname )
			if len( ls_vals )>=PGParamSet.PARAM_FIELDS_TOTAL:
				s_tag=ls_vals[ PGParamSet.IDX_PARAM_TAG ] if ls_vals[ 2 ] != "None" else None
			#end if we have a 3rd string 
				
			self.__tags_by_shortname[ s_shortname ] = s_tag
			self.__tags_by_longname[ s_longname ] = s_tag
			#end if more than 2 vals in list
		#end for each line in file

		o_file.close()
		return
	#end __init_from_file

	def __get_tag_field( self, s_tag, i_idx ):

		ls_tag_values=s_tag.split( PGParamSet.DELIMITER_TAG_FIELDS )

		if len( ls_tag_values ) <= i_idx:
			s_msg="In PGParamSet instance, def get_tag_field, "  \
					+ "tag, " + s_tag \
					+ " has too few fields to retrieve index number: " \
					+ str( i_idx ) + "."			
			raise Exception( s_msg )
		#end if field list is too short

		s_field_val=ls_tag_values[ i_idx ]

		return s_field_val

	#end __get_tag_field

	def getConfigSectionNameFromTag( self, s_tag ):
		s_section_name = self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_CONFIG_SECTION ) 
		return s_section_name
	#end getConfigSectionNameForParam

	def getDefaultValueFromTag( self, s_tag ):
		s_default_val_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_DEFAULT_VALUE )
		return s_default_val_as_string
	#end getDefaultValueFromParamTag

	def getSectionOrderFromTag( self, s_tag ):
		s_section_order_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_PLACEMENT_ORDER )
		return s_section_order_as_string
	#end getSectionOrderFromParamTag


	def getConfigSectionNameForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_section_name = self.__get_tag_field( s_tag, 
								PGParamSet.IDX_TAG_FIELD_CONFIG_SECTION ) 
		return s_section_name
	#end getConfigSectionNameForParam

	def getDefaultValueForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_default_val_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_DEFAULT_VALUE )
		return s_default_val_as_string
	#end getDefaultValueFromParamTag

	def getSectionOrderForParam( self, s_name ):
		s_section_order_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_PLACEMENT_ORDER )
		return s_section_order_as_string
	#end getSectionOrderFromParamTag

	def longname( self, s_shortname ):
		s_val=None
		if s_shortname in self.__params_by_shortname:
			s_val=self.__params_by_shortname[ s_shortname ]
		#end if name is in params

		return s_val
	#end longname

	def shortname( self, s_longname ):
		s_val=None
		
		if s_longname in self.__params_by_longname:
			s_val=self.__params_by_longname[ s_longname ]
		#end if name is in param longnames

		return s_val
	#end shortname

	def tag( self, s_name ):
		'''
		param s_name can be either among the 
		short or long names (or both). Shortnames
		are checked first.  First instance of name
		provides its tag as the return value.
		'''
		s_val=None

		if s_name in self.__tags_by_shortname:
			s_val = self.__tags_by_shortname[ s_name ]
		elif s_name in self.__tags_by_longname:
			s_val = self.__tags_by_longname[ s_name ]
		else:
			s_msg="In PGParamSet instance, def tag(), no tag " \
					+ "associated with " \
					+ "param name, " + s_name + "."
			raise Exception ( s_msg )
		#end if tag in short else if tag in long

		return s_val
	#end tag
	def __set_parameter( self, s_shortname, s_longname, s_tag=None ):
		self.__params_by_shortname[ s_shortname ] = s_longname
		self.__params_by_longname[ s_longname ] = s_shortname

		self.__tags_by_shortname[ s_shortname ] = s_tag
		self.__tags_by_longname[ s_longname ] = s_tag

		return
	#end setParam

	def setParam( self, s_shortname, s_longname ):
		self.__set_parameter( s_shortname, s_longname )
		return
	#end setParam

	def initFromFile( self, s_param_name_file ):
		self.__init_from_file( s_param_name_file )
		return
	#end initFromFile

	@property
	def param_names_file( self ):
		return self.__file_with_param_names
	#end param_names_file getter


	@property
	def longnames(self):
		ls_longnames=self.__params_by_longname.keys()
		ls_longnames.sort()
		return ls_longnames
	#end longnames

			
	@property
	def shortnames(self):
		ls_shortnames=self.__params_by_shortname.keys()
		ls_shortnames.sort()
		return ls_shortnames
	#end shortnames

	@property
	def tags(self):
		'''
		returns a list of tags, without their associated
		param names (short or long).  Useful to get
		the set of unique tags if the tags categorize
		the paramset into groups
		'''
		ls_tags=self.__tags_by_shortname.values()
		ls_tags.sort()
		return ls_tags
	#end shortnames

#end class ParamSet

if __name__=="__main__":
	mytestfile="resources/simupop.param.names"

	o_p=PGParamSet( mytestfile )

	print( o_p.shortnames )
	print( o_p.longnames )

	print ( o_p.shortname( "Generations" ) )
	print ( o_p.longname( "gens" ) )

	print( "tags: " )
	print ( o_p.tags )
	print("" )

	o_p.setParam( "shortname", "Long name" )

	print( o_p.shortnames )
	print( o_p.longnames )

	print( o_p.shortname( "Long name" ) )
	print( o_p.longname( "shortname" ) )

	print ( o_p.tag( "dataDir" ) ) 
	print ( o_p.tag( "param_names" ) ) 

#end if run as main, then test

