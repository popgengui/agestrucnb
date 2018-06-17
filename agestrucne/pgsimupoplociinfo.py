'''
Description
'''
__filename__ = "pglociinfo.py"
__date__ = "20180517"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

'''
2018_05_27.  This constant is used to tell whether
a file name purporting to be a loci file table
is the default value that means no file is to be used.
'''
NO_LOCI_FILE="None"

class PGSimupopLociInfoFileManager( object ):
	'''
	This class is meant to work with the PGSimupopLociInfo
	class by reading in (and maybe writing out, too, if 
	needed), tabular files that give loci information to 
	be used in intializing a simuPOP Population object.

	We base our standardized format of the file from
	our correspondence and meeting with Sarah Lehnert.
	'''

	IDX_LOCUS_NAME=0
	IDX_CHROM_NAME=1
	IDX_POSITION=2

	TOTAL_FIELDS_EXPECTED=3

	VALID_DELIMITERS=[ ",", "\t" ]
	
	def __init__( self, s_file_name, 
					i_total_header_lines=0,
					s_delimiter="," ):

		self.__filename=s_file_name
		self.__total_header_lines=i_total_header_lines
		self.__delimiter=s_delimiter
		self.__loci_name_by_position_by_chrom=None

		self.__read_file()
		return
	#end __init

	'''
	2018_05_27. We allow clients to call
	these validation defs  without creating an instance,
	so the file can be validated before
	a client tries to create an instance
	of this class.
	'''

	@staticmethod
	def getDelimiter( s_file_line ):

		myclass=PGSimupopLociInfoFileManager
		s_delimiter=None
		ls_fields=s_file_line.split( s_delimiter )

		for s_this_delim in myclass.VALID_DELIMITERS:
			ls_fields=s_file_line.split( s_this_delim )
			if len( ls_fields ) == myclass.TOTAL_FIELDS_EXPECTED:
				s_delimiter=s_this_delim
				break
			#end if correctd
		#end for each delimiter

		return s_delimiter
	#end getDelimiter

	@staticmethod
	def validateFile( s_file_name ):
		'''
		2018_05_27.  This def throws an 
		exception if any of the tests fail.
		If it returns without throwing an exception,
		the file passed all tests.
		'''

		myclass=PGSimupopLociInfoFileManager
		o_file=None
		try:
			o_file=open( s_file_name )
		except IOError as ioe:
			s_msg="In PGSimupopLociInfoFileManager " \
						+ "instance, the loci info file, " \
						+ s_file_name \
						+ ", could not be opened, " \
						+ "with the following error message: " \
						+ str( ioe ) 
			raise Exception( s_msg )
		#end try...except

		i_line_count=0
		s_delimiter=None
		for s_line in o_file:

			i_line_count+=1

			if i_line_count==1:
				s_delimiter=myclass.getDelimiter( s_line )

				if s_delimiter is None:
					s_msg="In PGSimupopLociInfoFileManager, " \
						+ "instance, " \
						+ "def validateFile, " \
						+ "the first line in the " \
						+ "loci info file, " \
						+ s_line \
						+ ", could not be parsed properly into " \
						+ "the expected fields." 
					raise Exception( s_msg )
				#end if no delimiter
			#end if first line

			ls_fields=s_line.split( s_delimiter )

			if len( ls_fields ) != myclass.TOTAL_FIELDS_EXPECTED:
				s_msg="In PGSimupopLociInfoFileManager, " \
						+ "def validateFile, " \
						+ "instance, line number " \
						+ str( i_line_count ) \
						+ " could not be split into the " \
						+ "expected number of fields: " \
						+ s_line 
				raise Exception( s_msg )
			#end if incorrect length

			try:
				f_numeric_field=float( ls_fields[ myclass.IDX_POSITION ] )
			except TypeError as ote:
				s_msg="In PGSimupopLociInfoFileManager, " \
					+ "def validateFile, " \
					+ "instance, line number " \
					+ str( i_line_count ) \
					+ "the postiion field value, " \
					+ str( ls_fields[ myclass.IDX_POSITION ] ) \
					+ "could not be converted to a numeric type" 

				raise Exception( s_msg )
			#end try...except
		return
	#end validateFile

	def __read_file( self ):
		myc=PGSimupopLociInfoFileManager

		self.__loci_name_by_position_by_chrom={}
		o_file=open( self.__filename, 'r' )
		i_line_count=0
		for s_line in o_file:
			i_line_count+=1
			if i_line_count <= self.__total_header_lines:
				continue
			#end if header line, no processing

			ls_fields=s_line.split( self.__delimiter )

			s_locus_name=ls_fields[ myc.IDX_LOCUS_NAME ]
			s_chrom=ls_fields[ myc.IDX_CHROM_NAME ]
			f_position=float( ls_fields[ myc.IDX_POSITION ] )

			if s_chrom in self.__loci_name_by_position_by_chrom:
				
				'''
				In our example input file, we see loci with distinct
				name but identical chromosome and position. Although
				for simuPOP's purposes, such loci are indistinguishable, 
				but we preserve this ambiguity, as we can resove these
				by "jiggling" the position just enougth (1e-15)
				for simupop to allow them to be input as separate loci
				(see def below in class PGSimupopLociInfo):
				'''
				if  f_position not in self.__loci_name_by_position_by_chrom[ s_chrom ]:
					self.__loci_name_by_position_by_chrom[ s_chrom ][ f_position ]=[ s_locus_name ]
				else:
					self.__loci_name_by_position_by_chrom[ s_chrom ][ f_position ].append( s_locus_name )
				#end if new position, else not
			else:
				self.__loci_name_by_position_by_chrom[ s_chrom ]= { f_position : [ s_locus_name ] }
			#end if we've already recorded the chrom, else new chrom
		#end for each line in the file
		o_file.close()
		return
	#end def __read_file

	@property 
	def dictLociByPosByChrom( self ):
		return self.__loci_name_by_position_by_chrom
	#end dictLociByPosByChrom

#end class PGSimupopLociInfoFileManager

class PGSimupopLociInfo( object ):

	'''
	This is the smallest difference in adjacent
	loci positions that Simupop will recognize.
	Otherwide the two loci will be considered
	indistinguishable, and an attempt to create
	both with result in an error.
	'''

	SIMUPOP_MIN_POSITION_DIFFERENCE=1e-13

	'''
	Class LociInfo.py is created record loci information 
	in a format suitable for initializing SimuPOP's 
	Population structure.
	'''

	def __init__( self, s_loci_info_file ):
		self.__file_manager=None
		self.__loci_names_by_chrom_and_pos=None
		self.__loci_totals_by_chromosome=None
		self.__total_loci=None

		self.__get_file_manager( s_loci_info_file )
		self.__get_simupop_lists()
		return
	#end __init__

	def __get_file_manager( self, s_filename ):
		self.__file_manager=\
				PGSimupopLociInfoFileManager( s_filename )
		return
	#end __get_file_manager

	def __get_simupop_lists( self ):

		dsfs_file_info=\
				self.__file_manager.dictLociByPosByChrom
		
		self.__loci_names_by_chrom_and_pos={}
		self.__loci_totals_by_chromosome={}
		self.__total_loci=0

		for s_chrom in dsfs_file_info:
			'''
			Dict has chrom names as first key, and each such points
			to another dict whose keys are floats giving positions 
			and values are lists of loci_names (often just 1 loci name,
			but may have multi loci names at same position, as when cM
			units are equal, though loci are physically separated on
			the chromosome).
			'''

			lf_positions_sorted=list( dsfs_file_info[ s_chrom ].keys() )

			lf_positions_sorted.sort()

			if s_chrom not in self.__loci_names_by_chrom_and_pos:
				self.__loci_names_by_chrom_and_pos[ s_chrom ]={}	
				self.__loci_totals_by_chromosome[ s_chrom ]=0
			#if first time seen, add chrom name to dict

			for f_position in lf_positions_sorted:

				
				self.__loci_names_by_chrom_and_pos[ s_chrom ][ \
							f_position ]=dsfs_file_info[ s_chrom ][ f_position ]		

				self.__loci_totals_by_chromosome[ s_chrom ] += \
											len( dsfs_file_info[ s_chrom ][ f_position ] )
				
				self.__total_loci+=len( dsfs_file_info[ s_chrom ][ f_position ] )
			#end for each position, sorted
		#end for each chromosome
		return
	#end __get_simupop_lists

	def getPositionsUsingSmallOffsetForNonUniquePositions( self ):
		'''
		This def creates the loci position list that goes along with
		the chroms and loci names, and can be used in the simupop
		Population initialization to assign the lociPos parameter.
		This def solves the problem of 2 loci on the same chrom,
		with the same position, which can't be both intitialized
		in simupop, unless the distance between them is increased
		to at least the small value of 1e-15 (as assigned to our
		class constant).
		'''
		MYJIGGLE=PGSimupopLociInfo.SIMUPOP_MIN_POSITION_DIFFERENCE

		dsf_positions_by_chrom={}

		for s_chrom in self.__loci_names_by_chrom_and_pos:
			if s_chrom not in dsf_positions_by_chrom:
				dsf_positions_by_chrom[ s_chrom ]= []
			#end if

			lf_positions=list( self.__loci_names_by_chrom_and_pos[ s_chrom ].keys() )

			lf_positions.sort()

			#We have a list of loci names (though ususally we expect only one 
			#item in the list) for each position.
			for f_position in lf_positions:

				i_jiggle_count=0

				for loci_name in self.__loci_names_by_chrom_and_pos[ s_chrom ][ f_position ]:
					#this should only append the jiggle amount if there is more than one loci name
					#at the current position -- and increment the jiggle units as we see > 2 loci names:
					f_this_jiggle_amount = MYJIGGLE * i_jiggle_count
					dsf_positions_by_chrom[ s_chrom ].append( f_position + f_this_jiggle_amount )
					i_jiggle_count+=1
				#end for each loci name
			#end for each position on this chrom
		#end for each chrom

		return dsf_positions_by_chrom
	#end def  getPositionsUsingSmallOffsetForNonUniquePositions

	@property
	def loci_names_by_chrom_and_sorted_pos( self ):
		return self.__loci_names_by_chrom_and_pos
	#end property loci_names

	@property
	def loci_totals_by_chromosome( self ):
		return self.__loci_totals_by_chromosome
	#end property loci_names

	@property
	def total_loci( self ):
		return self.__total_loci
	#end property total_loci

#end class PGSimupopLociInfo

if __name__ == "__main__":
	
	s_file="/home/ted/documents/negui_project/from_sarah_lehnert/map_position.csv"

	o_fm=PGSimupopLociInfoFileManager( s_file )
	d_info=o_fm.dictLociByPosByChrom
	ls_chroms=list( d_info.keys() )
	li_chroms_sorted=[ int( s_chrom ) for s_chrom in ls_chroms ]
	li_chroms_sorted.sort()

	for i_chrom in li_chroms_sorted:
		s_chrom=str( i_chrom )
		lf_sorted_pos=list( d_info[ s_chrom ].keys() )
		lf_sorted_pos.sort()
		for f_pos in lf_sorted_pos:
			s_pos=str( f_pos ) if f_pos>0 else "0"
			for s_name in d_info[ s_chrom ][ f_pos ]:
				print(  ",".join( [ s_name, s_chrom, s_pos ] ) )
			#end for name
		#end for pos
	#end for chrom

	pass
#end if main

