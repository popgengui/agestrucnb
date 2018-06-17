'''
Description
This class wraps defs to validate a chromosome
loci table file used by LDNe2 to filter out loci
pairs that share a chromosome.
'''
__filename__ = "pgchromlocifilemanager.py"
__date__ = "20180502"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

'''
This string designates that
there is no chrom loci file,
in the case expected by LDNe2:
'''

NO_CHROM_LOCI_FILE="None"

CHROM_TOTAL_ZERO=0

CHROM_LOCI_FILE_DELIMITER="\t"

#Field order in the file
IDX_CHROM_NAME=0
IDX_LOCI_NAME=1

LDNE_LOCI_PAIRING_SCHEME_IGNORE_CHROM=0
LDNE_LOCI_PAIRING_SCHEME_SAME_CHROM=1
LDNE_LOCI_PAIRING_SCHEME_DIFF_CHROM=2

LOCI_PAIRING_SCHEME_DESCRIPT={ LDNE_LOCI_PAIRING_SCHEME_IGNORE_CHROM:"use all pairs",
					LDNE_LOCI_PAIRING_SCHEME_SAME_CHROM:"loci pair p1,p2 must be from the same chromosome",
					LDNE_LOCI_PAIRING_SCHEME_DIFF_CHROM:"loci pair p1,p2, must be from different chromosomes" }

import os

class GenepopLociScraper( object ):
	'''
	This is a convenience class to 
	segregate the code needed just
	to get the limited loci info
	needed for the ChromLociFileManager.
	'''
	def __init__( self, s_genepop_file ):
		self.__gpfile=s_genepop_file
		self.__get_loci_list()
		return
	#end __init__

	def __get_loci_list( self ):

		FIRST_LINE=1

		POPLINE="pop"

		DELIMITER_WHEN_LOCI_ARE_LISTED_ON_ONE_LINE=","

		ls_loci_list=[]

		o_file=open( self.__gpfile, 'r'  )

		i_line_number = 0

		s_second_line_entry=None

		for s_line in o_file:

			i_line_number += 1

			if i_line_number==FIRST_LINE:
				continue
			elif i_line_number == 2:
				s_second_line_entry=s_line.strip()
				#If second line is not only loci line,
				#we continue to build our loci list, 
				#line by line:
				ls_loci_list.append( s_line.strip() )
			elif s_line.strip().lower() == POPLINE:
				if i_line_number == 3:
					#all loci were on line 2, 
					#and entered as a list, so se
					#reassign our loci_list thusly:
					ls_loci_list=s_second_line_entry.split( \
									DELIMITER_WHEN_LOCI_ARE_LISTED_ON_ONE_LINE )
				#end if first pop line is file's 3rd line, then loci format is list
				break
			else:
				ls_loci_list.append( s_line.strip() )
			#end if first line, else second line, else pop line, else loci line	
		#end for each linn in file	

		o_file.close()

		self.__loci_list=ls_loci_list		

		return 

	#end __get_loci_list

	@property
	def loci_list( self ):
		return self.__loci_list
	#end property loci_list

#end class GenepopLociScraper

class ChromLociFileManager( object ):
	'''
	2018_05_02.  This class is created, inititally,
	to validate files to be used by LDNe2 to get
	chromosome/loci pairs, for use in filtering
	loci pairs that share a chromsome.  We may
	want to put it to other uses later.
	Note that it also is the single source for
	the string that designates that no such 
	file is to be used, and which chromosome
	totals are invalid (see mod-level assignments).
	'''

	def __init__( self, 
					s_file_name=NO_CHROM_LOCI_FILE,
					ls_genepop_files_that_use_the_file=[],
					i_ldne_pairing_scheme=None ):

		self.__filename=s_file_name

		'''
		Note -- no list.copy() def for python2:
		'''
		self.__genepop_files=[ v_item for v_item 
							in ls_genepop_files_that_use_the_file ]

		self.__total_chromosomes=None
		self.__chromloci_table=None
		self.__unlisted_loci=[]
		self.__loci_pairing_scheme=i_ldne_pairing_scheme

		return
	#end __init__

	def __validate_file( self ):

		s_error_message=""	

		b_is_valid=False

		b_is_file=os.path.isfile( self.__filename ) 

		if b_is_file:

			self.__get_total_chromosomes()

			b_each_loci_paired_with_one_chromosome=\
					self.__each_loci_is_assigned_to_exactly_one_chromosome()

			b_all_loci_listed=self.__all_genepop_loci_are_listed()

			'''
			2018_05_07. The only loci pairing violation detected so far,
			occurs when the client has a chrom/loci file that contains just one
			chromosome, and also requests the loci pairing sheme that requires
			pairs l1,l2, from chrom c1,c2, have c1 != c2.
			'''
			b_pairing_violation=\
					self.__loci_pairing_scheme is not None \
					and self.__loci_pairing_scheme \
									== LDNE_LOCI_PAIRING_SCHEME_DIFF_CHROM \
					and self.__total_chromosomes == 1
			
			if not b_each_loci_paired_with_one_chromosome:

					s_error_message += "\nAt least one loci is paired with " \
									+ "more than one chromosome." \

			if not b_all_loci_listed:
				s_error_message += "\n" \
									+ " in chrom/loci file, " \
									+ self.__filename + ", " \
									+ "Genepop file(s) has (have) the " \
									+ "following loci not " \
									+ "assigned to chromosomes: \n" \
									+ str( self.__unlisted_loci )
			#end if some loci unlisted

			if b_pairing_violation:
				s_error_message += "\n" \
									+ " in chrom/loci file, " \
									+ self.__filename + ", " \
									+ " the chromosome total, " \
									+ str( self.__total_chromosomes ) \
									+ ", is incompatible with the " \
									+ "loci pairing scheme: " \
									+ LOCI_PAIRING_SCHEME_DESCRIPT[ \
												self.__loci_pairing_scheme ]
			#end if loci pairing violation						 

		else:
			s_error_message="\nFile, " + self.__filename + "does not exist."
			
		#end if we have a chrom/loci file else not

		if s_error_message != "":
			raise Exception( "In ChromLociFileManager instance, " \
								+ "def __validate_file, " \
								+ "file found to be invalid with message: " \
								+ s_error_message  )
		#end if we noted an error, raise exception

		return
	#end __validate_file

	def __get_chrom_loci_table( self ):

		MIN_NUM_FIELDS=2

		o_file=open( self.__filename, 'r' )

		self.__chromloci_table={}

		for s_line in o_file:
			ls_fields=s_line.strip().split( CHROM_LOCI_FILE_DELIMITER )

			s_chrom=ls_fields[ IDX_CHROM_NAME ]

			if len( ls_fields ) < MIN_NUM_FIELDS:
				raise Exception( "In ChromLociFileManager, " \
									+ "def __get_chrom_loci_table, " \
									+ "a file line has fewer than the " \
									+ "required " + str( MIN_NUM_FIELDS ) \
									+ " fields for a chrom/loci table file. " \
									+ "The file line is: \"" + s_line.strip() + "\"" )
			#end if too few fields
			s_loci_name=ls_fields[ IDX_LOCI_NAME ]

			if s_chrom in self.__chromloci_table:
				self.__chromloci_table[ s_chrom ].append( s_loci_name )
			else:
				self.__chromloci_table[ s_chrom ]=[ s_loci_name ]
			#end if chrom already in dict, else add
		#end for each line in file

		o_file.close()

		return
	#end __get_chrom_loci_table

	def __all_genepop_loci_are_listed( self ):

		b_all_listed=False

		set_loci_listed_in_chrom_loci_file=self.__get_set_loci_list_from_chrom_loci_file()

		i_total_unlisted_loci=0
		
		for s_genepop_file in self.__genepop_files:
			ls_loci_in_this_gp_file=\
					self.__get_loci_list_from_genepop_file( s_genepop_file )
				
			set_loci_in_this_gp_file=set( ls_loci_in_this_gp_file )

			if not( set_loci_in_this_gp_file.issubset( set_loci_listed_in_chrom_loci_file  ) ):
				set_diff=set_loci_in_this_gp_file.difference( set_loci_listed_in_chrom_loci_file )
				i_total_unlisted_loci += len( set_diff )
				self.__unlisted_loci += list( set_diff )
			#end if gp list not a subset of our table's loci 
		#end for each genepop file

		b_all_listed=( i_total_unlisted_loci==0 )

		return b_all_listed
	#end __all_genepop_loci_are_listed

	def __each_loci_is_assigned_to_exactly_one_chromosome( self ):

		b_loci_assignments_valid=True

		if self.__chromloci_table is None:
			self.__get_chrom_loci_table()
		#end if not table, make one
	
		ds_chrom_names_by_loci_name={}

		for s_chrom in self.__chromloci_table:
			ls_loci=self.__chromloci_table[ s_chrom ]

			for s_loci in ls_loci:

				if s_loci in ds_chrom_names_by_loci_name:
					b_loci_assignments_valid=False
					break
				else:
					ds_chrom_names_by_loci_name[ s_loci ]=s_chrom
				#end if loci already paired with a chrom
			#end for each loci in this chrom's loci list
		#end for each chrom

		return b_loci_assignments_valid
	#end def __each_loci_is_assigned_to_exactly_one_chromosome

	def validateFile( self ):
		self.__validate_file()
		return
	#end validateFile

	def __get_loci_list_from_genepop_file( self, s_genepop_file ):
		o_gp_loci_scraper=GenepopLociScraper( s_genepop_file )
		return o_gp_loci_scraper.loci_list
	#end __get_loci_list_from_chrom_loci_file

	def __get_set_loci_list_from_chrom_loci_file( self ):
		ls_loci_list=[]

		set_loci_list=None

		if self.__chromloci_table is None:
			self.__get_chrom_loci_table()
		#end if no table, get it

		for s_chrom in self.__chromloci_table:
			ls_loci_list +=self.__chromloci_table[ s_chrom ]
		#end for each chrom, append loci list

		set_loci_list=set( ls_loci_list )

		return set_loci_list
	#end def __get_loci_list_from_chrom_loci_file

	def __get_total_chromosomes( self ):
		if self.__total_chromosomes is None:
			if self.__chromloci_table is None:
				self.__get_chrom_loci_table()
			#end if no table
			self.__total_chromosomes=len( self.__chromloci_table )
		#end if total not yet calc'd
		return 
	#end __get_total_chromosomes

#end class ChromLociFileManager

if __name__ == "__main__":
	s_test_file="/home/ted/temp/tclf.tsv"
	s_gp="/home/ted/temp/gp.gp"

	o_clfm=ChromLociFileManager( s_test_file, [ s_gp ] )
	o_clfm.validateFile() 

	pass
#end if main

