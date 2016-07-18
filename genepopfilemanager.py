'''
Description
'''
__filename__ = "genepopfilemanager.py"
__date__ = "20160505"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import os
import random	

class GenepopFileManager( object ):

	'''
	wraps 2 dictionaries, one for header and loci byte addresses, the other for byte addresses of "pop" lines 
		and individual addresses.  The header dict has one level, the pop dict  has 3 levels:
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
	'''

	def __init__( self, s_filename ):
		self.__filename=s_filename
		self.__setup_addresses( s_filename )
		self.__init_subsamples()
		return
	#end __init__

	def __setup_addresses( self, s_filename ):
		i_currver=sys.version_info.major
		
		#for compat with python 3 (we need to cast
		#byte addresses as long in python 2, else very big files
		#have byte addresses that overrun py2's max int)
		self.__byte_address_type=long if i_currver==2 else int
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
		raise Exception( "GenepopFileAddresses object, in def __read_header_and_loci, " \
				+ "found no \"pop\" line (case insensitive) in file, " \
				+ self.__filename )

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

	def __sample_individuals_randomly_from_one_pop( self, i_pop_number, i_sample_size ):

			i_pop_size=self.__get_count_indiv( self.__pop_byte_addresses[ i_pop_number ] )
	
			#we don't include zero as sample-able (zeo is the "pop" entry), 
			#and 2nd arg range def is series max + 1:
			li_subsample=random.sample( list( self.__range_iterator( 1, i_pop_size + 1 ) ) , i_sample_size ) 

			#to preserve the indiv list order in the orig file:
			li_subsample.sort()

			return li_subsample

	#end __sample_individuals_randomly_from_one_pop

	def __remove_n_individuals_randomly_from_one_pop( self, i_pop_number, i_n_to_remove ):
		i_pop_size=self.__get_count_indiv( self.__pop_byte_addresses[ i_pop_number ] )
		li_indiv_list=list( self.__range_iterator( 1, i_pop_size + 1 ) )
		random.shuffle( li_indiv_list ) 
		li_shuffled_indiv_list_with_n_removed=li_indiv_list[ i_n_to_remove : ]
		li_shuffled_indiv_list_with_n_removed.sort()
		return li_shuffled_indiv_list_with_n_removed
	#end __remove_n_individuals_randomly_from_one_pop

	def __get_count_populations( self ):
		#recall the pops are numbered 1,2,3...N for N populations,
		#and that these numbers are the keys in the dict of byte addresses
		#giving the first line (the "pop" line ) of each pop
		return len( self.__pop_byte_addresses.keys() )
	#end __get_count_populations

	def __get_pop_list( self, s_pop_subsample_tag = None ):

		li_pop_numbers=None

		if s_pop_subsample_tag is None:
			li_pop_numbers=self.__pop_byte_addresses.keys()
		else:
			li_pop_numbers=self.__pop_subsamples[ s_pop_subsample_tag ]
		#end if no pop subsample tag else use subsample

		return li_pop_numbers
	#end __get_pop_list

	def __write_genepop_file_to_file_object( self, o_file_object, 
			s_pop_subsample_tag=None,
			s_indiv_subsample_tag=None, 
			s_loci_subsample_tag=None,
			i_min_pop_size=0 ):

		#here we open the file without the 'b' flag, so we
		#will read string in both python 2 and 3
		o_origfile=open( self.__filename, 'r' )
		o_newfile=o_file_object

		li_header_and_loci_lines=None
		li_pop_numbers=None

		if s_pop_subsample_tag is None:
			li_pop_numbers=self.__pop_byte_addresses.keys()
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
		
		if s_loci_subsample_tag is None:
			li_header_and_loci_lines=self.__header_and_loci_byte_addresses.keys()
		else:
			li_header_and_loci_lines=self.__loci_subsamples[ s_loci_subsample_tag ]
		#end if we include all loci, else subsample
			
		#write header and loci list:
		for i_line_number in li_header_and_loci_lines:
			o_origfile.seek( self.__header_and_loci_byte_addresses[ i_line_number ] )
			o_newfile.write( o_origfile.readline() )
		#end for each line in the header and loci section

		#write pops:
		for i_pop_number in li_pop_numbers:

			li_indiv_list=None

			if s_indiv_subsample_tag is None:
				li_indiv_list=self.__pop_byte_addresses[ i_pop_number ].keys()
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
				i_tot_indiv=self.__get_count_indiv( \
						ddli_subsamples[ s_indiv_subsample_tag ] [ i_pop_number ] )
			#end if no subsample, else subsample

			if i_tot_indiv >= i_min_pop_size:
				li_indiv_list=ddli_subsamples[ s_indiv_subsample_tag ][ i_pop_number ] 
				for i_indiv_number in li_indiv_list:
					for i_line_number in self.__pop_byte_addresses[ i_pop_number ][ i_indiv_number ]:
						o_origfile.seek( self.__pop_byte_addresses[ i_pop_number ][ i_indiv_number ][ i_line_number ] )
						o_newfile.write( o_origfile.readline() )
					#end for each line number
				#end for each item number
			#end if num individuals in this pop at or over min
		#end for each pop number
		
		o_origfile.close()
		return
	#end __write_genepop_file_to_file_object

	def __get_count_indiv( self, li_indiv_list ):
		#to centralize the computation of counting 
		#num indiv -- in case the scheme of subracting
		#one to account for the "pop" line changes
		i_result=len( li_indiv_list )  - 1
		return i_result
	#end __get_count_indiv

	def __get_count_indiv_per_pop( self, s_indiv_subsample_tag=None, s_pop_subsample_tag=None ):

		li_counts=[]
		iter_pops_with_indiv_lists=None

		if s_indiv_subsample_tag is None:
			iter_pops_with_indiv_lists=self.__pop_byte_addresses
		else:
			iter_pops_with_indiv_lists=self.__indiv_subsamples[ s_indiv_subsample_tag ] 
		#end if we're counting all or a subsample

		for i_pop_number in iter_pops_with_indiv_lists:
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
					+ "in writeGenePopFile(), can't write file, " \
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
			i_min_pop_size=0 ):

		self.__write_genepop_file_to_file_object( sys.stdout, s_indiv_subsample_tag, 
				s_loci_subsample_tag, s_pop_subsample_tag, i_min_pop_size )	
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
			li_indiv_numbers=self.__pop_byte_addresses[ i_pop_number ].keys()
		else:
			li_indiv_numbers=self.__indiv_subsamples[ s_indiv_subsample_tag ][ i_pop_number ]
		#end if no subsample else subsample
		#recall that all indiv lists include indiv "0", that is, the "pop" =entry, so wer return only the numbers for tindiv proper
		return li_indiv_numbers [ 1 : ]
	#end __get_list_indiv_numbers

	def getListIndividuals( self, i_pop_number=1, s_indiv_subsample_tag = None ):

		ll_byte_addesses=[]
		ls_individuals=[]

		li_indiv_numbers= self.__get_list_indiv_numbers( i_pop_number, s_indiv_subsample_tag )
		o_orig_file = open( self.__filename, 'rb' )
		
		i_num_indiv=len( li_indiv_numbers )

		for i_this_indiv in li_indiv_numbers:

			l_address=self.__pop_byte_addresses[ i_pop_number ][ i_this_indiv ][1]		
			o_orig_file.seek( l_address )
			s_this_indiv_line=o_orig_file.readline()

			ls_this_indiv=s_this_indiv_line.split( "," )

			#possible to have a blank field in genepop
			#individual entry (i.e. line starts with comma),
			#in which case we'll simply return the number
			#indicating this is the nth individual in the list
			if len( ls_this_indiv ) == 1 :
				ls_individuals.append( str( i_this_indiv ) )
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
		#because the list is poteneially the one copy in this instance,
		#return a copy of the list, not the list itself
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
				li_indiv_numbers=self.__pop_byte_addresses[ i_pop_number ].keys()
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
			
			li_subsample=self.__sample_individuals_randomly_from_one_pop( i_pop_number, i_N )

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
													i_pop_number, 
													s_indiv_subsample_tag ):
		'''
		From a singleh pop in the file remove the nth of M individuals, 
		where individuals are numbered 1,2,3...M

		Requires value for i_n, 0<i_n<i_

		Also requires both an individual and a population subsample tag,
		As this subsample must involve only a single population
		'''
	
		i_tot_pops=self.__get_count_populations()

		if i_pop_number < 1 or i_pop_number > i_tot_pops:
			s_msg="In GenepopFileManager instance, def " \
					+ "subsampleIndividualsLeaveNthOutFromPop, " \
					+ "invalid population nunmber.  With " + str( i_tot_pops ) \
					+ " populatins and  population number, " \
					+ str( i_pop_number ) + "."

			raise Exception ( s_msg )
		#end if invalid pop number

		li_indiv_list=self.__get_list_indiv_numbers( i_pop_number, s_indiv_subsample_tag=None )

		#want a copy of the list:
		li_indiv_list_copy=[ i_indiv for i_indiv in li_indiv_list ]

		i_pop_size=len( li_indiv_list_copy )

		self.__indiv_subsamples[ s_indiv_subsample_tag ] = {}

		if i_n>i_pop_size or i_n < 1:
			s_msg="In GenepopFileManager instance, def " \
					+ "subsampleIndividualsLeaveNthOutFromPop, " \
					+ "invalid N.  With " + str( i_pop_size ) \
					+ " individuals, and N = " \
					+ str( i_n ) + "."

			raise Exception ( s_msg )
		#end if n out of bounds
		
			
		li_indiv_list_copy.remove( i_n )
		
		#to any sample we always add the zeroth
		#indiviudal number, which is the "pop"
		#entry
		self.__indiv_subsamples[ s_indiv_subsample_tag ] [ i_pop_number ] = \
				[0] + li_indiv_list_copy

		return
	#end subsampleIndividualsLeaveNthOutFromPop

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
					+ "genepop file has " + str( i_total_pops ) + " populations " \
					+ "sample list ranges out of bounds, with min: " + str( i_min_sampnum ) \
					+ "and max: " + str( i_max_sampnum )

			raise Exception( s_msg )
		#end if all pop numbers in range, else error

		return
	#end subsamplePopulationsByList

	def getIndivCountPerSubsampleForPop( self, s_indiv_subsample_tag, i_popnumber ):
		li_counts=self.__get_count_indiv_per_pop( s_indiv_subsample_tag )
		return li_counts[ i_popnumber - 1 ]
	#end getIndivCountPerSubsampleForPop

	def getIndivCountPerSubsample( self, s_indiv_subsample_tag, s_pop_subsample_tag=None ):

		li_results=None

		li_counts_for_all_pops=self.__get_count_indiv_per_pop( s_indiv_subsample_tag )	
		
		#if caller wants a subset of pops:
		if s_pop_subsample_tag is not None:
			li_results=[]
			li_pop_numbers=self.__pop_subsamples[ s_pop_subsample_tag ]
			for i_pop_number in li_pop_numbers:
				li_results.append( li_counts_for_all_pops[ i_pop_number - 1 ] )
			#end for each pop_num
		else:
			li_results = [ i_count for i_count in li_counts_for_all_pops ]
		return li_results
	#end getIndivCountPerSubsample

	def getIndivCountForPop( self, i_pop_number ):
		'''
		Expects pop number to be 1-based
		'''

		li_indiv_counts=self.__get_count_indiv_per_pop()

		return li_indiv_counts[ i_pop_number - 1 ]
	#end getIndivCountForPop

	@property
	def indiv_count_per_pop( self ):
		li_res=self.__get_count_indiv_per_pop()	
		return li_res
	#end getIndivCountPerPop

	@property 
	def pop_total( self ):
		return self.__get_count_populations()
	#end getNumberOfPops

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
#end class GenepopFileManager

if __name__ == "__main__":
	#test the code
	mydir="/home/ted/documents/source_code/python/negui/temp_data/genepop_from_brian_20160506"
	restag="py" + str( sys.version_info.major ) + "test"
	filecount=0
	for myfile in [ "AlpowaCreekBY2006_14.txt", "AsotinCreekBY2006_104.txt", "BigCreekBY2006_29.txt" ]:
		filecount+=1
		mygpfile=mydir + "/" + myfile
	
		o_gp=GenepopFileManager( mygpfile )
		lf_props=[ 0.10, 0.20, 0.30 ]	
		for f_prop in lf_props:
			o_gp.subsampleIndividualsRandomly( f_prop, s_subsample_tag=str( f_prop ) )
		#end for each proportion

		s_newfile="_".join( [ mygpfile, restag, str( filecount ) ] )
		o_gp.writeGenePopFile( s_newfile  )
		for s_tag in o_gp.indiv_subsample_tags:
			o_gp.writeGenePopFile( s_newfile + s_tag, s_indiv_subsample_tag=s_tag )
		#end for each proportion
	#end for each file
#end if main

