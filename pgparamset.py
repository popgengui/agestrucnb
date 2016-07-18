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
			s_tag=None
			ls_vals= s_line.strip().split( "\t" )
			s_shortname=ls_vals[ 0 ]
			s_longname=ls_vals[ 1 ]
			self.__set_parameter( s_shortname, s_longname )
			if len( ls_vals )>=3:
				s_tag=ls_vals[ 2 ] if ls_vals[ 2 ] != "None" else None
			#end if we have a 3rd string 
				
			self.__tags_by_shortname[ s_shortname ] = s_tag
			self.__tags_by_longname[ s_longname ] = s_tag
			#end if more than 2 vals in list
		#end for each line in file

		o_file.close()
		return
	#end __init_from_file

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
		provides its tag as the retur value.
		'''
		s_val=None

		if s_name in self.__tags_by_shortname:
			s_val = self.__tags_by_shortname[ s_name ]
		elif s_name in self.__tags_by_longname:
			s_val = self.__tags_by_longname[ s_name ]
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

