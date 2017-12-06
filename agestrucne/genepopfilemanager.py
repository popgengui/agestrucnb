'''
Description
'''
from __future__ import division
from __future__ import print_function
from builtins import range
from builtins import object
from past.utils import old_div
__filename__ = "genepopfilemanager.py"
__date__ = "20160505"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import os
import random	
from agestrucne.genepopindividualid import GenepopIndivIdVals
from agestrucne.genepopindividualid import GenepopIndividualId

COMMA_DELIMITED_LOCI_LIST_HAS_LEADING_SPACE=True
'''
2017_05_01.  Py3 compatiblity requires decoding
file lines read in from a file opened 'rb'.
This value is accessed dynamically in defs
__get_indiv_entry and getListIndividuals. 
'''
SYSENCODING=sys.getdefaultencoding()

class GenepopFileManager( object ):

	'''
	wraps 2 dictionaries, one for header and loci byte addresses, the other for 
			byte addresses of "pop" lines and individual addresses.  The header dict 
			has one level, the pop dict  has 3 levels:
			outer key: for the pop dict, pop number: 1,2..., for header/loci simply the line number
			middle key: pop dict only,   item number: 0,1,2
				for the pop dictionsary the first "pop" line itself is the zeroth item
				and for pop 1,2,..., the entry "pop"
			innermost key:  item-line number, 0,1,2...
				this key needed because genepop allows multi line entries for
				a single individual
		value: byte address of the first byte of the line

		example, if (as most often) the individual entry takes up only one line, 
		to find the entry for the 2nd indiv at pop 2, point the file pointer at 
		the byte address given by self.__byte_addresses[2][2][1], and execute a readline().  
		If this individual was on more than one line, say 2 lines, the entry would 8
		be given by concatenating the lines read at self.__byte_addresses[2][2][1] 
		and self.__byte_addresses[2][2][2]

		Note that we aim to parse the genepop file in accordance with the format described
		in http://genepop.curtin.edu.au/help_input.html#Input as accessed most recently
		on 2016_10_03.
	'''

	'''
	These constants are added on 2016_10_03
	and will be incorporated into new code
	as reminders of the correct keys that
	fetches the dictionary that holds byte addresse(s) 
	(plural only if the id + loci are entered
	on multiple lines) of the first indiv:
	'''
	KEY_FIRST_INDIV_NUMBER=1
	'''
	And for any indiv, the key to the first
	(usually the only) line that holds id + loci:
	'''
	KEY_FIRST_LINE_INDIV_ENTRY=1

	'''
	THe "pop" entry, signalling the start
	of a new population, is always the first
	key ( value = 0 ) in a dict of byte addresses
	for a given pop.
	'''
	KEY_POP_ENTRY=0

	def __init__( self, s_filename ):
		self.__filename=s_filename
		self.__loci_count=None

		self.__setup_addresses( s_filename )
		self.__init_subsamples()
		self.__get_loci_count()
		return
	#end __init__

	def __setup_addresses( self, s_filename ):
		i_currver=sys.version_info.major
		
		#for compat with python 3 (we need to cast
		#byte addresses as long in python 2, else very big files
		#have byte addresses that overrun py2's max int)
		self.__byte_address_type=int if i_currver==2 else int
		self.__range_iterator=xrange if i_currver==2 else range
		self.__first_pop_address=None
		self.__pop_byte_addresses={}
		self.__header_and_loci_byte_addresses={}
		self.__read_byte_addresses()
		return
	#end __init_object

	def __init_subsamples( self ):
		self.__indiv_subsamples={}
		self.__loci_subsamples={}
		self.__pop_subsamples={}
		return
	#end __delete_subsamples

	def __get_loci_count( self ):

		'''
		Get the count of loci as given by
		the header/loci info at top of genepop
		file.  Note that "Loci names can appear 
		on separate lines, or on one line if separated by commas.		
		'''

		i_loci_count=None

		'''
		Genepop file has one header line, then loci lines (up to first pop).
		'''
		i_loci_line_count=len( self.__header_and_loci_byte_addresses ) - 1

		'''
		If the file has only one loci line, then
		then all loci will be on this one line,
		comma-separated.
		'''

		if i_loci_line_count==1:
			IDX_LOCI_LINE=1
			o_orig_file=open( self.__filename, "rb" )
			l_byte_address=\
					self.__header_and_loci_byte_addresses[ \
												IDX_LOCI_LINE ] 
			o_orig_file.seek( l_byte_address )
			v_loci_line=o_orig_file.readline()

			if type( v_loci_line )==bytes:
				v_loci_line=v_loci_line.decode( SYSENCODING )
			#end if type is bytes

			ls_loci=v_loci_line.split( "," )
			i_loci_count=len( ls_loci )
		else:
			i_loci_count=i_loci_line_count
		#end

		self.__loci_count=i_loci_count

		return
	#end __get_loci_count
	
	def __is_pop_line( self, b_line ):
		'''
		assumes b_line is a bytearray object
		representing a file line:
		'''
		b_lower=b_line.lower()
		
		#does the line begin with (case insensitive) "pop", followed
		#by an endline (unix/OSX (\n) or windows(\r\n) )?
		if b_lower.find( b'pop\n' ) == 0 or b_lower.find( b'pop\r\n' ) == 0:
			return True
		else:
			return False
		#end if pop line else not

		raise Exception( "in object instance of GenepopFileAddresses, def __is_pop_line, " \
				+ "should have returned in the if... else statement" )
	#end __is_pop_line

	def __is_indiv_line( self, b_line ): 
		'''
		assumes b_line is a bytearray object
		assumes b_line comes from from a pop section 
		(i.e. not from the header/loci-name
		part of the file)
		'''

		if b_line.find( b',' ) != -1:
			return True
		else:
			return False
		#end if line has a comma, else not
	#end __is_idiv_line

	def __get_byte_address_first_byte_in_line( self, o_file, b_line ):
		'''
		assumes b_line is a python bytearray object
		'''
		return self.__byte_address_type( o_file.tell() ) - self.__byte_address_type( len( b_line ) )
	#ene __get_byte_address_first_byte_in_line

	def __read_header_and_loci_entries( self ):
		'''
		finds byte addresses for each item preceeding
		the first "pop" line in the genepop file,
		inserts the byte addresses for each at the 
		incremented int keys for member dict __header_and_loci_byte_addresses

		assumes one item (loci name, or loci list) to a line, 
		so that each item will have one line only (see class description)
		'''
		o_file=open( self.__filename, 'rb' )
		i_item_count=0
		s_line=o_file.readline()

		while s_line:
			#for python3, need to convert the bytes object returnd by readline():
			b_line=bytearray( s_line )


			l_byte_address=self.__get_byte_address_first_byte_in_line( o_file, b_line )

			if self.__is_pop_line( b_line ):
				#no more loci lines, so record
				#the address to the firsrt "pop"
				#and return
				self.__first_pop_address=l_byte_address
				return
			else:
				self.__header_and_loci_byte_addresses[ i_item_count ] = l_byte_address
				i_item_count+=1
			#end if nonpop line . . . else
			s_line=o_file.readline()
		#end for line in file
		
		#with correct genepop line and code, should never reach this line:
		raise Exception( "In GenepopFileManager instance, def __read_header_and_loci, " \
				+ "found no \"pop\" line (case insensitive) in file, " \
				+ self.__filename + "." )

	#end __read_header_and_loci

	def __read_pops( self ):
		'''
		assumes object instance member __first_pop_address 
		has a long value (int in python 3) that was set in 
		def __read_header_and_loci that points to the first 
		byte in the first line in the file that reads 
		(case insensitive) as "pop"
		'''
		i_pop_count=0
		i_total_indiv_this_pop=0
		i_total_lines_this_indiv=0

		o_gpfile=open ( self.__filename, 'rb' )
		o_gpfile.seek( self.__first_pop_address )
		s_line=o_gpfile.readline()
		while  s_line:

			b_line=bytearray( s_line )

			l_byte_address=self.__get_byte_address_first_byte_in_line( o_gpfile, b_line )

			if self.__is_pop_line( b_line ):
				i_pop_count+=1
				#we record the "pop" line as the zeroth item in this pop
				#and we also assume it is a single-lined item:
				i_total_indiv_this_pop=0
				self.__pop_byte_addresses[ i_pop_count]={ i_total_indiv_this_pop: { 1 : l_byte_address } }
				i_total_lines_this_indiv=0
			elif self.__is_indiv_line:
				#is the first (if not only) line giving loci info for a single individual
				i_total_indiv_this_pop+=1
				i_total_lines_this_indiv=1
				self.__pop_byte_addresses[ i_pop_count ][ i_total_indiv_this_pop ]={ 1 : l_byte_address } 
			else:
				i_total_lines_this_indiv +=1
				self.__pop_byte_addresses[ i_pop_count ][ i_total_indiv_this_pop ][ i_total_lines_this_indiv ] = l_byte_address
			#end if line starts with pop esle has comma (so is first line of indiv entry), else neither, so must be next line in loci
			#for individual
			s_line=o_gpfile.readline()
		#end for each line
	#end __read_pops

	def __read_byte_addresses( self ):
		self.__read_header_and_loci_entries()
		self.__read_pops()
		return
	#end __read_byte_addresses

	def __remove_individual_subsample( self, s_subsample_tag ):
		try:
			self.__indiv_subsamples.pop( s_subsample_tag )
		except Exception as oex:
			s_msg="In GenepopFileManager instance, def __remove_individual_subsample, " \
					+ "exception when trying to remove subsample, " \
					+ s_subsample_tag \
					+ ".  Exception thrown: " + str( oex ) + "." 
			raise Exception( s_msg )
		#end try, except
		return
	#end __remove_individual_subsample
	
	def __combine_individual_subsamples_for_one_pop( self, ls_individual_subsample_tags, i_pop_number=1 ):
		set_indivs=set()
		for s_subsample_tag in ls_individual_subsample_tags:
			li_indiv_list=self.__get_list_indiv_numbers( i_pop_number=i_pop_number, 
												s_indiv_subsample_tag=s_subsample_tag )
			set_indivs=set_indivs.union( li_indiv_list )
		#end for each subsample, add new individuals
		li_combined=list(set_indivs )
		li_combined.sort()
		return li_combined
	#end __combine_individual_subsamples_for_one_pop

	def __sample_individuals_randomly_from_one_pop( self, i_pop_number, 
															i_sample_size, 
																s_subsample_tag=None ):
			'''
			If s_subsample_tag arg is not None, instead of the whole indiv list
			for the given pop number, the subsample of indivs assoc with the tag
			is sampled.
			'''

			i_pop_size=None
			li_indiv_list=None

			if s_subsample_tag is None:
				i_pop_size=self.__get_count_indiv( self.__pop_byte_addresses[ i_pop_number ] )
				li_indiv_list=self.__get_list_indiv_numbers( i_pop_number=i_pop_number )
			else:

				i_pop_size=self.__get_count_indiv( \
						self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ] )
				li_indiv_list=self.__get_list_indiv_numbers( i_pop_number=i_pop_number, 
														s_indiv_subsample_tag=s_subsample_tag )
			#end if no subsample tag else we want to sample a subsample

			
			i_sample_size=min( i_sample_size, i_pop_size )

			#we don't include zero as sample-able (zeo is the "pop" entry), 
			#and 2nd arg range def is series max + 1:
			li_subsample=random.sample( li_indiv_list, i_sample_size ) 

			#to preserve the indiv list order in the orig file:
			li_subsample.sort()

			return li_subsample

	#end __sample_individuals_randomly_from_one_pop

	def __remove_n_individuals_randomly_from_one_pop( self, i_pop_number, i_n_to_remove ):
		li_indiv_list=self.__get_list_indiv_numbers( i_pop_number=i_pop_number ) 		
		random.shuffle( li_indiv_list ) 
		li_shuffled_indiv_list_with_n_removed=li_indiv_list[ i_n_to_remove : ]
		li_shuffled_indiv_list_with_n_removed.sort()
		return li_shuffled_indiv_list_with_n_removed
	#end __remove_n_individuals_randomly_from_one_pop

	def __get_count_populations( self ):
		#recall the pops are numbered 1,2,3...N for N populations,
		#and that these numbers are the keys in the dict of byte addresses
		#giving the first line (the "pop" line ) of each pop
		return len( list(self.__pop_byte_addresses.keys()) )
	#end __get_count_populations

	def __get_pop_list( self, s_pop_subsample_tag = None ):

		li_pop_numbers=None

		if s_pop_subsample_tag is None:
			li_pop_numbers=list( self.__pop_byte_addresses.keys() )
		else:
			li_pop_numbers=self.__pop_subsamples[ s_pop_subsample_tag ]
		#end if no pop subsample tag else use subsample

		'''
		Not knowledgable enough to convince myself
		that keys will always be in order, though
		individual lists are sorted after random sampling.  
		Also, I am not sure that sort will never matter, so:
		'''
		li_pop_numbers.sort()

		return li_pop_numbers
	#end __get_pop_list
	
	def __write_genepop_file_to_file_object( self, o_file_object, 
			s_pop_subsample_tag=None,
			s_indiv_subsample_tag=None, 
			s_loci_subsample_tag=None,
			i_min_pop_size=0 ):

		'''
		We convert all endlines to unix endlines. Found
		that in testing some dos-endline files, that
		simply writing whole lines from the file, then
		mixing with my subsampled loci lines, that i had
		genepop files with mixed endlines.  Note that testing
		these iwth NeEstimator shows they werre properly
		processed, but rather than test for which endline in 
		orig, I'll simply use strip() and replace all whole
		line read/writes form the original with the unix endline.
		'''

		UNIX_ENDLINE="\n"

		#here we open the file without the 'b' flag, so we
		#will read string in both python 2 and 3
		'''
		2017_05_01.  Restoring the 'rb' flag, and adjusting code below to
		handle bytes objects, if the interpretor is python3.
		'''
		o_origfile=open( self.__filename, 'rb' )
		o_newfile=o_file_object

		li_header_and_loci_lines=None
		li_pop_numbers=None

		if s_pop_subsample_tag is None:
			li_pop_numbers=list(self.__pop_byte_addresses.keys())
		else:
			if s_pop_subsample_tag not in self.__pop_subsamples:
				s_msg="In GenepopFileManager instance, " \
								+ "def __write_genepop_file_to_file_object, " \
								+ "no population subsample with tag: " \
								+ s_pop_subsample_tag + "."
				raise Exception( s_msg )
			#end if no such population subsample tag
			li_pop_numbers=self.__pop_subsamples[ s_pop_subsample_tag ]
		#end if all pops to be written, else only those subsampled

		ls_subsampled_single_line_loci=None
		
		if s_loci_subsample_tag is None:
			li_header_and_loci_lines=list(self.__header_and_loci_byte_addresses.keys())
		elif len( self.__header_and_loci_byte_addresses ) == 2:
			'''
			This elsif conditional added 2017_12_05, to handle subsampled loci
			when the input file has all of its loci entered on line 2,
			with comma separators. Note that in this case the header and loci
			byte address dict will have only 2 keys, indicating two lines preceed
			the first "pop" entry.
			'''
			li_header_and_loci_lines=[ self.__header_and_loci_byte_addresses[ 0 ] ]
			o_origfile.seek( self.__header_and_loci_byte_addresses[ 1 ] )
			v_line_stripped=( o_origfile.readline() ).strip()
			if type( v_line_stripped ) == bytes:
				v_line_stripped=v_line_stripped.decode( SYSENCODING )
			#end if bytes type, decode
			ls_all_loci_on_one_line=v_line_stripped.split( "," )
			#loci subsampling is 1-based, but we have zero-based indexes
			#(e.g. loci 1 is the zeroth item in our list):
			ls_subsampled_single_line_loci=[ ls_all_loci_on_one_line[idx-1] \
					for idx in self.__loci_subsamples[ s_loci_subsample_tag ] ]
		else:
			l_header_address=self.__header_and_loci_byte_addresses[ 0 ]
			li_header_and_loci_lines=[ l_header_address ] \
					+ [ idx for idx in  self.__loci_subsamples[ s_loci_subsample_tag ] ]
		#end if we include all loci, else subsample

		#write header and loci list:
		for i_line_number in li_header_and_loci_lines:

			o_origfile.seek( self.__header_and_loci_byte_addresses[ i_line_number ] )

			'''
			In python 3, readline() will deliver a bytes object, which
			has the strip() method, just like a string in python 2.
			'''
			v_line_stripped=( o_origfile.readline() ).strip()

			if type( v_line_stripped ) == bytes:
				v_line_stripped=v_line_stripped.decode( SYSENCODING )
			#end if bytes type, decode

			o_newfile.write( v_line_stripped + UNIX_ENDLINE )

			o_newfile.flush()

		#end for each line in the header and loci section

		'''
		Added 2017_12_05, with new conditional above,
		when our original file uses single line loci entry.
		In this case only the header was written in the
		for loop above, and we now write the loci line
		that was computed in the conditional.
		'''
		if ls_subsampled_single_line_loci is not None:
			o_newfile.write( \
					",".join( ls_subsampled_single_line_loci ) \
					+ UNIX_ENDLINE )
		#end if we have subsampled, single-line loci entries.

		#write pops:
		for i_pop_number in li_pop_numbers:

			li_indiv_list=None
			i_tot_indiv=None

			if s_indiv_subsample_tag is None:
				li_indiv_list=list(self.__pop_byte_addresses[ i_pop_number ].keys())
				i_tot_indiv=self.__get_count_indiv( li_indiv_list )
			else:
				ddli_subsamples=self.__indiv_subsamples
				if s_indiv_subsample_tag not in ddli_subsamples:
					s_msg="In GenepopFileManager instance, def __write_genepop_file_to_file_object, " \
							"no indiv subsample with tag: " + s_indiv_subsample_tag
					raise Exception( s_msg )
				#end if no such tag

				if i_pop_number not in ddli_subsamples[ s_indiv_subsample_tag ]:
					s_msg="In GenepopFileManager instance, def __write_genepop_file_to_file_object, " \
							+ "subsample with tag " + s_indiv_subsample_tag \
							+ " has no subsample for population number " + str( i_pop_number ) + "."
				
					raise Exception( s_msg )
				#end if no such pop for this subsample
				li_indiv_list=ddli_subsamples[ s_indiv_subsample_tag ][ i_pop_number ] 
				i_tot_indiv=self.__get_count_indiv( \
						ddli_subsamples[ s_indiv_subsample_tag ] [ i_pop_number ] )
			#end if no subsample, else subsample

			if i_tot_indiv >= i_min_pop_size:

				for i_indiv_number in li_indiv_list:

					#if this is the "pop" entry we can simply write it to file,
					#or, if we have no loci subsample, we can also write the indiv
					#entry as given in our original file:

					if i_indiv_number==GenepopFileManager.KEY_POP_ENTRY or s_loci_subsample_tag is None:
						for i_line_number in self.__pop_byte_addresses[ i_pop_number ][ i_indiv_number ]:
							o_origfile.seek( self.__pop_byte_addresses[ i_pop_number ]\
															[ i_indiv_number ][ i_line_number ] )
							v_line_stripped=( o_origfile.readline() ).strip()

							if type( v_line_stripped ) == bytes:
								v_line_stripped=v_line_stripped.decode( SYSENCODING )
							#end if bytes type, decode
							o_newfile.write( v_line_stripped + UNIX_ENDLINE )
						#end for each line number
					#otherwise we need to get loci via subsample:
					else:
					
						#Get ID separately:
						#We assume the complete individual ID is in line 1 of
						#the individual entry:
						s_id=self.__get_individual_id( o_origfile, self.__pop_byte_addresses[ i_pop_number ][ i_indiv_number ][ 1 ] )
						#Loci subsampled:
						s_loci=self.__get_loci_for_indiv( o_orig_file=o_origfile,
														i_pop_number=i_pop_number, 
														i_indiv_number=i_indiv_number, 
														s_loci_subsample_tag=s_loci_subsample_tag )

						if COMMA_DELIMITED_LOCI_LIST_HAS_LEADING_SPACE:
							s_line_to_write = s_id + ", " + s_loci
						else:
							s_line_to_write = s_id + "," + s_loci
						#end if we should insert a leading space in the loci list

						o_newfile.write( s_line_to_write + UNIX_ENDLINE )
					#end if no loci subsample, simply print orig entry, else get loci subsample
				#end for each individual number
			#end if num individuals in this pop at or over min
		#end for each pop number
		
		o_origfile.close()
		return
	#end __write_genepop_file_to_file_object

	def __get_count_indiv( self, iter_indiv_list ):
		'''
		To centralize the computation of counting 
		num indiv -- in case the scheme of subracting
		one to account for the "pop" line changes.

		Passed iterable may be either a list of ints
		that give an indiv list, or the dictionary
		given by self.__byte_addresses[ pop_number], 
		in which case we get the indiv numbers via
		the keys (we also sort to make sure we get
		the individual numbers in sorted order).
		'''
		
		if type( iter_indiv_list ) == dict:
			li_indiv_list=list( iter_indiv_list.keys() )
			li_indiv_list.sort()
		elif type( iter_indiv_list ) == list:
			li_indiv_list=iter_indiv_list
		else:
			s_msg="In GenepopFileManager instance, " \
					+ "def __get_count_indiv, "\
					+ "invalid type passed. " \
					+ "Expecting dictionary or list, " \
					+ "but received type: " \
					+ str( type( iter_indiv_list ) ) \
					+ "."
			raise Exception( s_msg )
		#end if arg is dict, else list, else error

		if li_indiv_list[ 0 ] != 0:
			s_msg="In GenepopFileManager instance, " \
						+ "def __get_count_indiv, " \
						+ "expected first item in list " \
						+ "to be zero, to indicate the " \
						+ "\"pop\" line.  List passed to def: " \
						+ str( li_indiv_list ) + "."
			raise Exception( s_msg )
		i_result=len( li_indiv_list )  - 1
		return i_result
	#end __get_count_indiv

	def __get_count_indiv_per_pop( self, s_indiv_subsample_tag=None, s_pop_subsample_tag=None ):

		li_counts=[]

		iter_pops_with_indiv_lists=None

		li_pop_numbers=self.__get_pop_list( s_pop_subsample_tag ) 

		if s_indiv_subsample_tag is None:
			iter_pops_with_indiv_lists=self.__pop_byte_addresses
		else:
			iter_pops_with_indiv_lists=self.__indiv_subsamples[ s_indiv_subsample_tag ] 
		#end if we're counting all or a subsample

		for i_pop_number in li_pop_numbers:
			i_tot_this_pop=self.__get_count_indiv( iter_pops_with_indiv_lists[ i_pop_number ] )
			li_counts.append( i_tot_this_pop )
		#end for each pop number

		return li_counts
	#end get_count_indiv_per_pop
					
	def  writeGenePopFile( self, s_newfilename,
			s_pop_subsample_tag=None,
			s_indiv_subsample_tag=None, 
			s_loci_subsample_tag=None, 
			i_min_pop_size=0 ):

		if os.path.exists( s_newfilename ):
			s_msg="In GenepopFileManager object instance, " \
					+ "def writeGenePopFile(), can't write file, " \
					+ s_newfilename + ".  File already exists."
			raise Exception( s_msg )
		#end if file exists

		o_newfile=open( s_newfilename, 'w' )

		self.__write_genepop_file_to_file_object( o_newfile, 
				s_pop_subsample_tag,
				s_indiv_subsample_tag, 
				s_loci_subsample_tag,  
				i_min_pop_size )

		o_newfile.close()

		return
	#end writeGenePopFile

	def printGenePopFile( self, 
			s_pop_subsample_tag=None, 
			s_indiv_subsample_tag=None, 
			s_loci_subsample_tag=None, 
			i_min_pop_size=0,
			o_outstream=sys.stdout ):

		self.__write_genepop_file_to_file_object( o_outstream, 
													s_pop_subsample_tag, 
													s_indiv_subsample_tag, 
													s_loci_subsample_tag,  
													i_min_pop_size )	
		return
	#end printGenePopFile

	def getListIndividualNumbers( self, i_pop_number=1, s_indiv_subsample_tag=None):
		li_indiv=self.__get_list_indiv_numbers( i_pop_number, s_indiv_subsample_tag )
		return [ i_indiv for i_indiv in li_indiv ]
	#end def getListIndividualNumbers

	def __get_list_indiv_numbers( self, i_pop_number, s_indiv_subsample_tag = None ):
		li_indiv_numbers=[]

		if i_pop_number not in self.__pop_byte_addresses:
			s_msg="In GenepopFileManager object instance,  getListIndiv(), " \
					+ "no pop number, " + str( i_pop_number )
			raise Exception( s_msg )
		#end if no pop with number
		
		if s_indiv_subsample_tag is None:
			#if python 3 we can't sort the "dict_keys" object that py3 returns
			li_indiv_numbers=list( self.__pop_byte_addresses[ i_pop_number ].keys() )
			#These numbers should always be contiguous ints 0,1,2,3...totalIndivCount
			#We'll sort the keys (though tests with dicts with contiguous, increasing ints
			#show that keys are sorted already -- may not be guaranteed in all settings)
			li_indiv_numbers.sort()
		else:
			li_indiv_numbers=self.__indiv_subsamples[ s_indiv_subsample_tag ][ i_pop_number ]
		#end if no subsample else subsample
		#recall that all indiv lists include indiv "0", that is, the "pop" entry, 
		#so we return only the numbers for tthe indivduals proper.
		return li_indiv_numbers [ 1 : ]
	#end __get_list_indiv_numbers

	def __get_list_loci_numbers( self, s_loci_subsample_tag=None ):
		li_loci_numbers=None
		if s_loci_subsample_tag is None:
			li_loci_numbers=list(range( 1, self.__loci_count + 1))
		else:
			li_loci_numbers=self.__loci_subsamples[ s_loci_subsample_tag ]
		#end if we have no loci subsample tag, else we have one	

		return li_loci_numbers
	#end __get_list_loci_numbers
		
	def __get_individual_id( self, o_orig_file, l_address ):
		'''
		param o_filehandle is a file object open with 'rb' for reading
			the genepop file.  We ask for an open handle in order
			to avoid many open() commands if this def is called
			in a long loop

		'''

		s_indiv=None

		o_orig_file.seek( l_address )

		v_this_indiv_line=o_orig_file.readline()
		'''
		We assume the file was opened 'rb'.  If the interpretor
		is python3, then we need to convert the bytes object.
		'''
		if type( v_this_indiv_line ) == bytes:
			v_this_indiv_line=v_this_indiv_line.decode( SYSENCODING )
		#end if readline returned bytes, decode


		if "," not in v_this_indiv_line:
			s_msg="In GenepopFileManager instance, " \
						+ "def, __get_individual_id, " \
						+ "no comma found in entry line: " \
						+ v_this_indiv_line + "."
			raise Exception( s_msg )
		#end if no comma in line

		ls_this_indiv=v_this_indiv_line.split( "," )

		#possible to have a blank field in genepop
		#individual entry (i.e. line starts with comma),
		#in which case we return None
		if len( ls_this_indiv ) == 1 :
			s_indiv=None	
		elif len( ls_this_indiv) == 2 :
			s_indiv= ls_this_indiv [ 0 ] 
		else:
			s_msg = "In GenepopFileManager object instance,  getListIndiv(), " \
					+ "more than one comma found in individual listing.  Line reads: " \
					+ v_this_indiv_line.strip() + "\n"
			raise Exception( s_msg )
		#end if no id, else id, else parsing error

		return s_indiv

	#end __get_individual

	def __get_indiv_entry( self,
							o_orig_file,
							i_pop_number,
							i_indiv_number ):

		'''
		In the open file object given by o_orig_file,
		for each line in the individual given by i_indiv_number,
		and for the pop number given by i_pop_number,
		append to string var and return the string of
		concatenated entry lines.  Note that most often
		there will be only one entry line (id,loci-list).
		'''
		s_entry=""

		i_num_lines_this_indiv_entry=len( self.__pop_byte_addresses[ i_pop_number ][ i_indiv_number ] )

		if i_num_lines_this_indiv_entry==0:
			s_msg="In GenepopFileManager instance, " \
						+ "def __get_indiv_entry" \
						+ "found no entry for pop " \
						+ str( i_pop_number ) \
						+ " and individual number " \
						+ str( i_indiv_number ) + "."
			raise Exception( s_msg )
		#ene if no lines this pop/indiv

		li_entry_line_numbers_sorted=list( self.__pop_byte_addresses[ \
								i_pop_number ][ i_indiv_number ].keys() )	

		li_entry_line_numbers_sorted.sort()
	
		for i_line_number in li_entry_line_numbers_sorted:
			l_address=self.__pop_byte_addresses[ i_pop_number ][ i_indiv_number ][ i_line_number ]		
			o_orig_file.seek( l_address )

			'''
			For python 3, when reading in bytes from 
			the 'rb' opened file:
			'''
			v_line=o_orig_file.readline()

			if type( v_line ) == bytes:
				v_line=v_line.decode( SYSENCODING )
			#end if we read in bytes

			s_entry+=v_line		

		#end for each line in entry

		return s_entry
	#end __get_indiv_entry

	def __get_loci_for_indiv( self, 
				o_orig_file,
				i_pop_number, 
				i_indiv_number,
				s_loci_subsample_tag=None ):

		'''
		In the open file given by o_orig_file,
		for the population given by i_pop_number,
		and the individual given by i_indiv_number,
		return the loci, either the original set,
		or, if not None, the subsampled loci given
		by s_loci_subsample_tag.
		'''
		IDX_LOCI=1

		s_loci=""

		s_entry=self.__get_indiv_entry( o_orig_file, 
										i_pop_number, 
										i_indiv_number )

		ls_id_and_loci=s_entry.split( "," ) 

		if len( ls_id_and_loci ) != 2: 
			s_msg="In GenepopFileManager instance, " \
						+ "def __get_loci_for_indiv, " \
						+ "No single-comma delimiter found " \
						+ "separating id and loci in entry " \
						+ "line or lines: " + s_entry + "."
			raise Exception( s_msg )
		#end if not a 2-item list, then can't tell id from loci

		s_loci_line_or_lines=ls_id_and_loci[ IDX_LOCI ]

		if s_loci_subsample_tag is None:
			s_loci=s_loci_line_or_lines
		else:
			'''
			We must split the loci to get 
			the subsamples.  See format 
			spec at web address listed in
			comments head of this file.
			''' 		

			#To combine multiple loci lines,
			#replace newlines with spaces:
			s_loci_line=s_loci_line_or_lines.replace( "\n", " " )

			'''
			Seperator of loci can be either space
			or tab.  Python split() with no arg
			splits on either and deletes empty
			strings (i.e. 2 ormore "blank" delimiters 
			in a row )
			'''
					
			ls_loci=s_loci_line.split()

			li_loci_numbers=\
					self.__loci_subsamples[ \
								s_loci_subsample_tag ]

			#Note that loci numbers are 1-based, so we subtract
			#one to find them in our loci list:
			
			s_loci=" ".join( [ ls_loci[ i_num-1 ] for i_num in li_loci_numbers ] )
			
		#end if loci not subsampled else subsampled

		return s_loci
	#end getLociForIndiv

	def __get_range_loci_nums( self, 
									i_min_loci_position,
									i_max_loci_position,
									b_truncate_max_to_total ):
		'''
		Returns a range object (in python3, not synonymous
		with a list type).  Checks for valid range.  if the 
		b_truncate_max_to_total is True, then it truncates
		to the max loci number N (1,2,3...N for N total loci).
		'''

		li_range_loci_numbers=None

		'''
		Allows use of any value for max
		without knowing how many loci are
		available.  We still sample from
		correct range:
		'''
		if b_truncate_max_to_total:
			i_max_loci_position=min( self.__loci_count, i_max_loci_position )
		#end if truncate

		b_min_out_of_range=i_min_loci_position < 1 or \
				i_min_loci_position >= i_max_loci_position \
				or  i_min_loci_position >= self.__loci_count 

		b_max_out_of_range=i_max_loci_position > self.__loci_count
							
		if b_min_out_of_range or b_max_out_of_range:
			s_msg="In GenepopFileManager instance, " \
						+ "def __get_range_loci_nums, " \
						+ "start-end loci range requested, " \
						+ str( i_min_loci_position ) \
						+ "-" + str( i_max_loci_position ) \
						+ ", out of range for file, " \
						+ self.__filename \
						+ ", with loci total, " \
						+ str( self.__loci_count ) + "."
			raise Exception( s_msg )
		#end if requested range invalid

	
		li_range_loci_numbers=list(range( i_min_loci_position, ( i_max_loci_position + 1 )))

		return li_range_loci_numbers
	#end def __get_range_loci_nums

	def subsampleLociByRangeAndMax( self, i_min_loci_position, 
			i_max_loci_position,
			s_loci_subsample_tag,
			i_min_total_loci=None,
			i_max_total_loci=None,
			b_truncate_max_to_total=True ):
			
		'''
		Generate list of integers that stand for loci positions,
		and as such allow for printing all or a subset of the loci
		for a given pop/indiv.  Given we have a set of N loci l_x in a
		genepop file listed in order l_1, l_2, l_3...l_N.

		param i_min_loci_position : integer giving lower index for range of loci numbers
		param i_max_loci_position : integer giving upper index for range of loci numbers
		param i_min_total: sample at least this many loci, or throw error
		param i_max_total: sample at most this many loci, randomly select if range exceeds
		param b_truncate_max_to_total : boolean, if True, then, when the param i_max_loci_position
			                            exceeds the total available loci, N, we set it to N.  
										If false then we keep the max position, in order to 
										throw an error if it exceeds N (see def __get_range_loci_nums), 
										default is True.

		'''

		self.__loci_subsamples[ s_loci_subsample_tag ]=[]

		o_range_to_sample=self.__get_range_loci_nums( i_min_loci_position, 
															i_max_loci_position,
															b_truncate_max_to_total )
		
		i_loci_range_interval_size=len( o_range_to_sample )

		i_sample_size=i_loci_range_interval_size 

		if i_min_total_loci is not None:
			if i_sample_size < i_min_total_loci:
				s_msg="In GenepopFileManager instance, def " \
							+ "subsampleLociByRangeAndMax " \
							+ "loci sample size, " \
							+ str( i_sample_size )  \
							+ ", is less than the minimum " \
							+ "given by the passed argument: "  \
							+ str( i_min_total_loci ) + "."
				raise Exception( s_msg )
			#end if sample size under min
		#end if min total loci is not None

		if i_max_total_loci is not None:
			i_sample_size=\
					min( i_loci_range_interval_size, i_max_total_loci )	
		#end if we have a value for max total loci 

		li_subsample=random.sample( o_range_to_sample, i_sample_size )

		li_subsample.sort()

		self.__loci_subsamples[ s_loci_subsample_tag ]=li_subsample

		return
	#end def subsampleLociByRangeAndMax

	def subsampleLociByRangeAndProportion( self, 
			i_min_loci_position, 
			i_max_loci_position,
			s_loci_subsample_tag,
			f_proportion_of_total_loci,
			i_min_total_loci=None,
			b_truncate_max_to_total=True ):
			
		'''
		Generate list of integers that stand for loci positions,
		and as such allow for printing the given proportion of loci
		with the indices range given.  Flag b_truncate_max_to_total
		when True will truncate the max-loci-position param to the
		max loci number, when the given value exceeds.  Otherwise,
		if max is out of range an error will be thrown.

		'''

		self.__loci_subsamples[ s_loci_subsample_tag ]=[]

		o_range_to_sample=self.__get_range_loci_nums( i_min_loci_position, 
															i_max_loci_position,
															b_truncate_max_to_total )
		
		i_loci_range_interval_size=len( o_range_to_sample )

		f_proportion_of_sample=float (i_loci_range_interval_size  ) * f_proportion_of_total_loci 

		i_sample_size=int( round(  f_proportion_of_sample ) )
		
		if i_min_total_loci is not None:
			if i_sample_size < i_min_total_loci:
				s_msg="In GenepopFileManager instance, def " \
							+ "subsampleLociByRangeAndProportion, " \
							+ "loci sample size, " \
							+ str( i_sample_size )  \
							+ " is less than the minimum " \
							+ "given by the passed argument: "  \
							+ str( i_min_total_loci ) + "."
				raise Exception( s_msg )
			#end if sample size under min
		#end if i_min_total_loci is not None

		li_subsample=random.sample( o_range_to_sample, i_sample_size )

		li_subsample.sort()

		self.__loci_subsamples[ s_loci_subsample_tag ]=li_subsample

		return

	#end subsampleLociByRangeAndProportion

	def getListIndividuals( self, i_pop_number=1, s_indiv_subsample_tag = None ):

		ls_individuals=[]

		li_indiv_numbers= self.__get_list_indiv_numbers( i_pop_number, s_indiv_subsample_tag )
		o_orig_file = open( self.__filename, 'rb' )

		for i_this_indiv in li_indiv_numbers:

			l_address=self.__pop_byte_addresses[ i_pop_number ][ i_this_indiv ][1]		
			o_orig_file.seek( l_address )
			v_this_indiv_line=o_orig_file.readline()

			'''
			2017_05_01. For python3, we need to convert
			the bytes read-in to a string type:
			'''
			if type( v_this_indiv_line )==bytes:
				v_this_indiv_line=v_this_indiv_line.decode( SYSENCODING )
			#end if bytes, decode

			ls_this_indiv=v_this_indiv_line.split( "," )

			#possible to have a blank field in genepop
			#individual entry (i.e. line starts with comma),
			#in which case we'll simply return the number
			#indicating this is the nth individual in the list
			if len( ls_this_indiv ) == 1 :
				s_msg= "In GenepopFileManager instance, " \
						+ "def getListIndiv, " \
						+ "Expecting commat delimiter between " \
						+ "ID and Loci, but comma found on id line: " \
						+ s_this_indiv_line.strip() + "."
				raise Exception( s_msg )
			elif len( ls_this_indiv) == 2 :
				ls_individuals.append( ls_this_indiv [ 0 ] )
			else:
				s_msg = "In GenepopFileManager object instance,  getListIndiv(), " \
						+ "more than one comma found in individual listing.  Line reads: " \
						+ s_this_indiv_line.strip() + "\n"
				raise Exception( s_msg )
		#end for each index in list of individuals for pop
		
		o_orig_file.close()

		return ls_individuals 
	#end getListIndividuals

	def getListPopulationNumbers( self, s_pop_subsample_tag=None ):

		li_pop_numbers=self.__get_pop_list( s_pop_subsample_tag )

		#to secure the list,
		#return a copy of 		
		return [ i_num for i_num in li_pop_numbers ]
	#end getListPopulationNumbers

	def getListEmptyPopulationNumbers( self, 
			s_pop_subsample_tag=None,
			s_indiv_subsample_tag=None ):
	
		li_empty_pops=[]

		li_pop_numbers=self.__get_pop_list( s_pop_subsample_tag )

		for i_pop_number in li_pop_numbers:
			li_indiv_numbers=None

			if s_indiv_subsample_tag is None:
				li_indiv_numbers=list(self.__pop_byte_addresses[ i_pop_number ].keys())
			else:
				li_indiv_numbers=self.__indiv_subsamples[ s_indiv_subsample_tag ] [ i_pop_number ]
			#end if we son't have an indiv subsample tag else we do

			#subtract one from the indiv list
			#to account for the "pop" line:
			i_num_indivs=self.__get_count_indiv( li_indiv_numbers )
			if i_num_indivs == 0:
				li_empty_pops.append( i_pop_number )
			#end if no indiv in this pop
		#end for each pop number

		return li_empty_pops
	#end getListEmptyPops

	def subsampleIndividualsRandomlyByProportion( self, f_proportion_to_sample, s_subsample_tag ):
		'''
		for each "pop" in the original genepop file,
		randomly select round( total_indiv_in_this_pop * f_proportion_to_sample )
		
		if zero is the subsample size, then an empty list will be assoc with the pop number
		stores the subset list of individuals as ints, ordered as they are in the orig, as 		
		self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ]
		'''

		self.__indiv_subsamples[ s_subsample_tag ]={}

		for i_pop_number in self.__pop_byte_addresses:

			i_pop_size=self.__get_count_indiv( self.__pop_byte_addresses[ i_pop_number ] )

			i_sample_size=int( round( i_pop_size * f_proportion_to_sample ) )

			li_subsample=self.__sample_individuals_randomly_from_one_pop( i_pop_number,i_sample_size )

			#we always include the "pop" entry, and we sort the subsample
			self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number]= \
					 [ 0 ] +  li_subsample
		#end for each pop number

		return
	#end subsampleIndividualsRandomlyByProportion

	def subsampleNIndividualsRandomlyFromEachPop( self, i_n, s_subsample_tag ):

		'''
		for each "pop" in the original genepop file,
		randomly select N individuals
		
		if N is larger than a given population, an error is thrown
		by random.sample.  The sampled pops are stored as 
		the subset list ints, ordered as they are in the orig, as 		
		self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ]
		'''

		self.__indiv_subsamples[ s_subsample_tag ] = {}

		for i_pop_number in self.__pop_byte_addresses:
			
			li_subsample=self.__sample_individuals_randomly_from_one_pop( i_pop_number, i_n )

			#we always include the "pop" entry, and we sort the subsample
			self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number]= \
					 [ 0 ] +  li_subsample
		#end for each pop number
	#end subsampleNIndividualsRandomlyFromEachPop
	
	def subsampleLociByName( self, ls_loci_names, s_subsample_tag ):
		raise Exception( "not implemented" )
		return
	#end subsampleLociByName

	def subsampleIndividualsMinusRandomNFromEachPop( self, i_n_remove, s_subsample_tag ):

		self.__indiv_subsamples[ s_subsample_tag ] = {}

		for i_pop_number in self.__pop_byte_addresses:
			li_sample=self.__remove_n_individuals_randomly_from_one_pop( i_pop_number, i_n_remove )
			self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ] = [0] + li_sample
		#end for each pop number

		return
	#end subsampleIndividualsMinusRandomNFromEachPop

	def subsampleIndividualsLeaveNthOutFromPop( self, i_n, 
													s_indiv_subsample_tag ):
		'''
		Remove the nth of M individuals, 
		where individuals are numbered 1,2,3...M

		Requires value for i_n, 0<i_n.  If i_n > pop size,
		we enter an empty list for the pop for ths given subsample tag.
		'''

		self.__indiv_subsamples[ s_indiv_subsample_tag ] = {}

		li_all_population_numbers=self.__get_pop_list()
		
		li_indiv_list_copy=None

		for i_pop_number in li_all_population_numbers:

			li_indiv_list=self.__get_list_indiv_numbers( i_pop_number, s_indiv_subsample_tag=None )

			i_pop_size=len( li_indiv_list )

			if  i_n < 1:
				s_msg="In GenepopFileManager instance, def " \
						+ "subsampleIndividualsLeaveNthOutFromPop, " \
						+ "invalid N.  With " + str( i_pop_size ) \
						+ " individuals, and N = " \
						+ str( i_n ) + "."

				raise Exception ( s_msg )
			elif i_n>i_pop_size:
				#Can't leave out nth indiv, since n too large,
				#so we assign an emtpy list for this pop:
				li_indiv_list_copy=[]

			else:	
				#want a copy of the list:
				li_indiv_list_copy = [ i_indiv for i_indiv in li_indiv_list ]
				li_indiv_list_copy.remove( i_n )
			#end if n < 1, n>pop size, else in range
			
			#to any sample we always add the zeroth
			#indiviudal number, which is the "pop"
			#entry
			self.__indiv_subsamples[ s_indiv_subsample_tag ] [ i_pop_number ] = \
					[0] + li_indiv_list_copy
		#end for each pop number
		return
	#end subsampleIndividualsLeaveNthOutFromPop

	def subsampleIndividualsByIdCriteria( self,
											o_genepop_indiv_id_fields, 
											o_genepop_indiv_criteria,
											s_subsample_tag,
											i_min_pop_sample_size=None,
											i_max_pop_sample_size=None ):
		'''
		param o_genepop_indiv_id_fields, an instance of GenepopIndivIdFields

		param o_genepop_indiv_criteria, a GenepopIndivCriteria instance,
			itself a list of GenepopIndivCriterion instances, with
			the ability to perform all criterion tests and return True or False

		Assumes that the list of individual (ids)
		from call to getListIndividuals gives ids
		in the same order as they occur in the 
		original genepop file.
		'''
		self.__indiv_subsamples[ s_subsample_tag ]={}

		for i_pop_number in self.__pop_byte_addresses:

			ls_individuals=self.getListIndividuals( i_pop_number )

			li_indiv_numbers=[]

			for idx in range( len( ls_individuals ) ):
				s_this_id=ls_individuals[ idx ]
				o_genepop_id_vals=GenepopIndivIdVals( s_this_id, 
											o_genepop_indiv_id_fields )

				o_genepop_individual_id=GenepopIndividualId( o_genepop_id_vals, o_genepop_indiv_criteria )
				
				if o_genepop_individual_id.allCriteriaAreTrue():

					#recall that the indices into individuals 
					#start with "1", since the 0th individual
					#is the "pop" entry itself:
					li_indiv_numbers.append( idx + 1 )
				#end if criteria all True, add indiv to subsample
			#end for each individual

			#we always include the "pop" entry, and we sort the subsample
			self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number]= \
												 [ 0 ] +  li_indiv_numbers

			if i_max_pop_sample_size is not None:

				i_indiv_count=self.__get_count_indiv( self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ] )

				
				if i_indiv_count> i_max_pop_sample_size:

					li_reduced_indiv_list=self.__sample_individuals_randomly_from_one_pop( \
															i_pop_number=i_pop_number,
															i_sample_size=i_max_pop_sample_size,
															s_subsample_tag=s_subsample_tag )

					self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ] = \
														[0] + li_reduced_indiv_list
				#end if we're over the max and need to randomly select
			#end if we have a max value for indiv count

			#Reduce to no individuals if we have a min pop size and our sampled pop
			#is under the minimum.
			if i_min_pop_sample_size is not None:
				i_indiv_count=self.__get_count_indiv( self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ] )
				if i_indiv_count < i_min_pop_sample_size:
					self.__indiv_subsamples[ s_subsample_tag ][ i_pop_number ] = [0]
				#end if under min count, reduce to no individuals
			#end if we have a minimum indiv count number
		#end for each pop number

		return
	#end subsampleIndividualsByIdCriteria


	def subsampleIndividualsByNumberList( self, dli_individual_numbers,
			s_subsample):
		'''
		param dli_individual_numbers, dictionary keyed to population
				numbers.  For each key the value is an ordered list
				of increasing ints i, 1<=i<=N, that make a set of individual
				numbers for the population in the kay.

		Note that this subsampling will put an empty list in populations whose
		numbers exist in the genepop file, but not among the dictionary keys.
		'''

		li_all_population_numbers=self.__get_pop_list()
		self.__indiv_subsamples[ s_subsample ] = {}
		for i_pop_num in li_all_population_numbers:
			'''
			If caller's dictionary keys lack this pop number
			the subsample is an empty list, except for the
			"pop" line (item 0 in any given indiv list):
			'''
			li_this_indiv_list=[0]
			if i_pop_num in dli_individual_numbers:
				
				#all indiv subsample lists include the zeroth item,
				#the "pop" entry
				li_this_indiv_list =  [ 0 ] +  dli_individual_numbers[ i_pop_num ] 

				#we always store sorted indiv ordinals
				#in the subsample lists:
				li_this_indiv_list.sort()
			#end if we have a list of indiv for this pop
			self.__indiv_subsamples[ s_subsample ] [ i_pop_num ] = li_this_indiv_list
		#end for each pop number in file
		return
	#end subsampleIndividualsByNumberList

	def subsampleIndividualsByPopSize( self, i_min_pop_size, i_max_pop_size, s_subsample ):
		'''
		For each pop, sample is identical to original, unless 
		its indiv count is under i_min_pop_size, in which case
		it is reduced to zero individuals, or its indiv count
		exceeds i_max_pop_size, in which case i_max_pop_size 
		individuals aret randomly sampled .
		'''

		li_all_population_numbers=self.__get_pop_list()
		self.__indiv_subsamples[ s_subsample ] = {}

		for i_pop_number in li_all_population_numbers:

			li_sample_this_pop=None

			i_indiv_count=self.getIndividualCount( i_pop_number )

			if i_indiv_count < i_min_pop_size:
				li_sample_this_pop=[0]

			else:				
				if i_indiv_count <= i_max_pop_size:
					li_sample_this_pop=[ 0 ] + self.__get_list_indiv_numbers( i_pop_number )
				else:
					li_sample_this_pop= [ 0 ] + \
							self.__sample_individuals_randomly_from_one_pop( \
																 i_pop_number=i_pop_number,
																 i_sample_size=i_max_pop_size )
				#end if indiv count under or equal to max, else over
			#end if under min, no indiv sampled, else sample

			self.__indiv_subsamples[ s_subsample ][ i_pop_number ]=li_sample_this_pop
		#end for each pop
		return
	#end subsampleIndividualsByPopSize

	def getListTuplesValuesIndivIdFields( self, 
							o_genepop_indiv_id_fields,
							ls_field_names ):

		'''
		Need a method to get the set (i.e. unique tuple) of 
		existing values for seom combo of ID fields 
		(may be only one field).  This would 
		be step one in a generalized implementation of Tiago's 
		sampleIndivsRelated.py code. Once we have the set of tuples 
		giving existing values, we can then use criteria matching 
		to subsample pops by testing each indiv for (a) matching 
		field value(s), using def subsampleIndividualsByIdCriteria.  
		Note that we can add criteria to the tests, for example, 
		to add age==1 to a criteria that also requires a father==i 
		and mother==j match, each i and j supplied by this def.

		arg o_genepop_indiv_id_fields, an instance of GenepopIndivIdFields
		arg ls_field_names, a list of strings that ell which of the field names
				in o_genepop_indiv_id_fields gives the fields to group to find
				all uniq value combos.

		As of 2016_09_08, this not yet implemented
		'''

		li_pop_numbers=self.__get_pop_list() 
		set_tuples_values=set()

		for i_pop_number in li_pop_numbers:
			ls_indiv_ids_this_pop=self.getListIndividuals( i_pop_number=i_pop_number )

			for s_id in ls_indiv_ids_this_pop:

				o_genepop_id_vals=GenepopIndivIdVals( s_id, o_genepop_indiv_id_fields )

				tv_vals_this_id=tuple() 

				for s_field_name in ls_field_names:
					v_val_this_field=o_genepop_id_vals.getVal( s_field_name )
					tv_vals_this_id += ( v_val_this_field, )
				#end for each field, add to tuple

				set_tuples_values.union( { tv_vals_this_id } )

			#end for indiv id in this pop
		#end for each pop in file

		return list( set_tuples_values )

	#end getListTuplesValuesIndivIdFields

	def subsamplePopulationsByList( self, li_pop_numbers, s_subsample_tag ):


		i_total_pops=self.__get_count_populations()

		li_pop_numbers.sort()

		i_min_sampnum=min( li_pop_numbers )
		i_max_sampnum=max( li_pop_numbers )

		if i_min_sampnum >= 1 and i_max_sampnum <= i_total_pops:
			#we want to copy the list -- not just have a reference
			self.__pop_subsamples[ s_subsample_tag ] = [ idx for idx in li_pop_numbers ]
		else:
			s_msg="In GenepopFileManager instance, def subsamplePopulationsByList, " \
					+ "genepop file has " + str( i_total_pops ) + " populations.  " \
					+ "sample list ranges out of bounds, with min: " + str( i_min_sampnum ) \
					+ ", and max: " + str( i_max_sampnum )

			raise Exception( s_msg )
		#end if all pop numbers in range, else error

		return
	#end subsamplePopulationsByList

	def getIndividualCounts( self, s_pop_subsample_tag=None, s_indiv_subsample_tag=None ):

		'''
		Returns a list of individual counts (total individuals) for each of N populations
		numbered 1,2,3,...N, representing the "pop" entries in order in the genepop file
		to which this GenepopFileManager instance corresponds.

		If s_pop_subsample_tag is not None, then the list will contain counts for each
		population in some subset of the original N, as listed by population nunber 
		list associated with the population subsample tag.

		If s_indiv_subsample_tag is not None, then the counts will be for the individuals
		in each pop as subsampled.
		'''
		li_counts=None

		li_counts=self.__get_count_indiv_per_pop( s_indiv_subsample_tag, s_pop_subsample_tag )	

		return li_counts

	#end getIndividualCounts

	def getIndividualCount( self, i_pop_number, s_indiv_subsample_tag=None ):
		'''
		Expects 1-based population number.
		Returns the individual count for the ith of N populations, i=1,2,3...N
		If s_indiv_subsample_tag is supplied, then the counts will
		reflect those of the individuals in the ith population after
		the sampling named by the tag.
		'''

		i_total_pops_in_file=self.__get_count_populations()	

		if i_pop_number < 1 or i_pop_number > i_total_pops_in_file:

			s_msg="In GenepopFileManager instance, def getIndividualCount, " \
					+ "invalid population number for file with total populations, " \
					+ str( i_total_pops_in_file ) \
					+ ".  Pop number requested: " + str( i_pop_number ) + "."

			raise Exception( s_msg )

		#end if  invalid population number

		li_counts=None

		li_counts=self.__get_count_indiv_per_pop( s_indiv_subsample_tag )
		#end if we get counts from subsample

		return li_counts[ i_pop_number - 1 ]
	#end getIndividualCount

	def combineIndividualSubsamples( self, ls_subsample_tags, 
							s_tag_for_combined_subsample ):

		li_population_numbers=self.__get_pop_list()	
		self.__indiv_subsamples[ s_tag_for_combined_subsample ] = {}

		for i_pop in li_population_numbers:
			li_combined_indiv_list= \
						self.__combine_individual_subsamples_for_one_pop( \
															ls_subsample_tags,
															i_pop_number=i_pop )
			self.__indiv_subsamples[ s_tag_for_combined_subsample ][ i_pop ] = \
					[ 0 ] + li_combined_indiv_list
		#end for each pop, combine 

		return
	#end combineIndividualSubsamples

	def removeIndividualSubsamples( self, ls_subsample_tags ):
		for s_subsample_tag in ls_subsample_tags:
			self.__remove_individual_subsample( s_subsample_tag )
		#end for each subsample tag, remove
		return
	#end removeIndividualSubsamples

	@property 
	def pop_total( self ):
		return self.__get_count_populations()
	#end getNumberOfPops

	@property
	def loci_total( self ):
		return self.__loci_count
	#end loci_total

	@property
	def population_subsample_tags( self ):
		'''
		so user can iterate over populations
		as subsampled
		'''
		return [ s_tag for s_tag in self.__pop_subsamples ]
	#end population_subsample_tags

	@property
	def indiv_subsample_tags( self ):
		'''
		so user can iterate over subsamples,
		we return a list of their tags:
		'''
		return [ s_tag for s_tag in self.__indiv_subsamples ]
	# end def indiv_subsample_tags

	@property
	def loci_subsample_tags( self ):
		'''
		so user can iterate over subsamples,
		we return a list of their tags:
		'''
		return [ s_tag for s_tag in self.__loci_subsamples ]
	#end def loci_subsample_tags

	@property
	def original_file_name( self ):
		return self.__filename
	#end original_file_name

	@original_file_name.setter
	def original_file_name( self, s_filename ):
		'''
		this setter essentially creates a new object
		based on the genepop file with the filename 
		given by param s_filename
		'''
		self.__filename=s_filename
		self.__setup_addresses( s_filename )
		self.__init_subsamples()
		return
	#end original_file_name (setter)

	def __get_allele_counts( self, s_pop_subsample_tag=None, 
										s_indiv_subsample_tag=None, 
										s_loci_subsample_tag=None,
										b_skip_loci_with_parial_data=True ):
		
		'''
		For each pop in the file (or as filtered by pop subsample tag), count the
		alleles.  When a loci has no data for an individual, counts are unchanged.
		When a loci has partial, the flag param is used do either leave unchanged
		or count the non-missing allele (see comment below).
		param tags give keys to subsamples of pops, individuals, or loci.
		param b_skip_loci_with_parial_data is meant to imitate the Genepop program,
			  which, when computing allele frequencies on diploid entries, apparently 
			  skips non-zero alleles when the other is zero (missing).  Default 
			  True will imitate, false will only skip alleles when both alleles are
			  zero (missing).
		'''

		MISSING_ALLELE=0

		#For assertion messages:
		s_location_msg="in GenepopFileManager instance " \
								+ "def __get_allele_counts, "
		li_pop_nums=None
		li_indiv_nums=None
		li_loci_nums=None

		dddi_allele_counts_by_pop_by_loci={}

		o_this_genepop_file=open( self.__filename, 'r' )

		li_pop_nums=self.__get_pop_list( s_pop_subsample_tag )
		li_loci_nums=self.__get_list_loci_numbers( s_loci_subsample_tag )
		i_total_loci=len( li_loci_nums )

		for i_pop_number in li_pop_nums:

			dddi_allele_counts_by_pop_by_loci[ i_pop_number ] = { i_loci_number : {} 
																	for i_loci_number in li_loci_nums }

			li_indiv_nums=self.__get_list_indiv_numbers( i_pop_number, s_indiv_subsample_tag )

			for i_indiv_number in li_indiv_nums:

				s_loci_as_genepop_entry=self.__get_loci_for_indiv( o_this_genepop_file, 
																	i_pop_number, 
																		i_indiv_number, 
																		s_loci_subsample_tag )

				ls_loci_list=s_loci_as_genepop_entry.split()
				assert i_total_loci == len( ls_loci_list ), s_location_msg \
											+ "individual loci list total, " \
											+ str( len( ls_loci_list ) ) \
											+ ", differs from expected total loci, " \
											+ str( i_total_loci ) \
											+ "using loci subsample with tag: " \
											+ str( s_loci_subsample_tag ) + "." 


				for idx in range( i_total_loci ):

					s_this_loci=ls_loci_list[ idx ]
					i_this_loci_number=li_loci_nums[ idx ]

					#The sub-dictionary that holds running allele counts for this pop and loci:
					ddi_alleles_this_pop_and_loci= \
								dddi_allele_counts_by_pop_by_loci[i_pop_number ][ i_this_loci_number ]
					i_char_count=len( s_this_loci )

					#If loci entry diploid, then it will have at least 4 characters,
					#and no more than 6:
					assert i_char_count > 3 and i_char_count <= 6, s_location_msg \
										+ "loci entry, " + s_this_loci + ", " \
										+ "has character count: " \
										+  str( i_char_count ) + ".  " \
										+ "Current version requires diploid loci."
										
					#If the loci entry is diploid, then its length must be halvable:
					assert i_char_count % 2 == 0,  s_location_msg \
										+ "loci entry, " + s_this_loci \
										+ ", character count not divisible by two."

					i_chars_per_allele=old_div(i_char_count,2)
					
					try:
						i_allele_1=int( s_this_loci[ 0:i_chars_per_allele ] )
						i_allele_2=int( s_this_loci[ i_chars_per_allele:i_char_count ] )
					except ValueError as ove:
						raise Exception( s_location_msg  \
										+ "loci entry, " + s_this_loci \
										+ ", can't be converted " \
										+ "into 2 integers. Error: " + str( ove ) )
					#end try...except

					li_alleles=[ i_allele_1, i_allele_2 ]

					if sum( li_alleles ) == MISSING_ALLELE \
							or ( ( MISSING_ALLELE in li_alleles ) \
									and b_skip_loci_with_parial_data ):
						continue
					#end if missing all data, or missing at least one and flag says skip.
						
					for i_this_allele in li_alleles:
						if i_this_allele != MISSING_ALLELE:
							if i_this_allele not in ddi_alleles_this_pop_and_loci:
								ddi_alleles_this_pop_and_loci[ i_this_allele ] = 1
								
							else:
								ddi_alleles_this_pop_and_loci[ i_this_allele ] += 1
							#end if allele already recorded, else not
						#end if not a missing allele --(zero allele (missing data) is
						#possible when the b_skip_loci_with_parial_data flag is False.
					#end for each allele
				#end for each loci
			#end for each individual
		#end for each pop
				
		return dddi_allele_counts_by_pop_by_loci

	#end __get_allele_counts

	def getAlleleCounts( self, s_pop_subsample_tag = None, 
									s_indiv_subsample_tag = None, 
									s_loci_subsample_tag = None,
									b_skip_loci_with_parial_data=True ):

		dddi_allele_counts_by_pop_by_loci=self.__get_allele_counts( s_pop_subsample_tag,
																		s_indiv_subsample_tag,
																		s_loci_subsample_tag,
																		b_skip_loci_with_parial_data )

		return dddi_allele_counts_by_pop_by_loci
	#end getAlleleCounts

	@property
	def header( self ):
		'''
		This getter was added 2017_02_12 to allow clients to get
		the header string, and so look for an Nb/Ne value in the 
		header text.  The current implementation stores this
		value for the Nb estimation in the header line
		as the final text, reading "nbne=<value>".  See 
		pgdriveneestimator.py, def 
		get_nbne_ratio_from_genepop_file_header.
		'''
		o_origfile=open( self.__filename, 'r' )
		o_origfile.seek( self.__header_and_loci_byte_addresses[0] )
		s_line_stripped=( o_origfile.readline() ).strip()
		return s_line_stripped
#end class GenepopFileManager

if __name__ == "__main__":
#	test the code
#	mydir=os.path.sep + os.path.join( "home","ted","documents","source_code","python","negui","temp_data","genepop_from_brian_20160506" )
#	restag="py" + str( sys.version_info.major ) + "test"
#	filecount=0
#	for myfile in [ "AlpowaCreekBY2006_14.txt", "AsotinCreekBY2006_104.txt", "BigCreekBY2006_29.txt" ]:
#		filecount+=1
#		mygpfile=mydir + os.path.sep + myfile
#	
#		o_gp=GenepopFileManager( mygpfile )
#		lf_props=[ 0.10, 0.20, 0.30 ]	
#		for f_prop in lf_props:
#			o_gp.subsampleIndividualsRandomly( f_prop, s_subsample_tag=str( f_prop ) )
#		#end for each proportion
#
#		s_newfile="_".join( [ mygpfile, restag, str( filecount ) ] )
#		o_gp.writeGenePopFile( s_newfile  )
#		for s_tag in o_gp.indiv_subsample_tags:
#			o_gp.writeGenePopFile( s_newfile + s_tag, s_indiv_subsample_tag=s_tag )
#		#end for each proportion
	#end for each file

	#testing new allele counts defs
	
	import sys

	f_genepopfile=None
	if len( sys.argv ) == 2:
		f_genepopfile=sys.argv[ 1 ]
	#end if

	MINLOCINUM=20
	MAXLOCINUM=21
	LOCILIST=[ 3,5 ]

	MININDIV=44
	MAXINDIV=45

	MINPOPNUM=24
	MAXPOPNUM=24

	opg=GenepopFileManager( f_genepopfile )

	li_pop_numbers=list(  range( MINPOPNUM, MAXPOPNUM + 1 ) )
	li_indiv_numbers=list( range( MININDIV, MAXINDIV + 1 ) ) 

	opg.subsamplePopulationsByList( li_pop_numbers , "popsamp" )
	opg.subsampleIndividualsByNumberList( { ipopnum : li_indiv_numbers  for ipopnum in li_pop_numbers }	, "indivsamp" )
	opg.subsampleLociByRangeAndMax( MINLOCINUM, MAXLOCINUM, "locisamp" )

	dddi_allelecounts=opg.getAlleleCounts( "popsamp", "indivsamp", "locisamp" )

	print( dddi_allelecounts )

#end if main

