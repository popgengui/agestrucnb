'''
Description

2017_03_17
Given an output file of ldne results from
LDNe2, this object parses the results and
delivers the values.

'''
from __future__ import print_function

from builtins import range
from builtins import object
__filename__ = "pgldneoutputparser.py"
__date__ = "20170317"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys

'''
We use regular expressions to check that the input
file has the expected format.  We also use them to
parse the data, and discard non data lines.
'''
import re

class PGLDNe2OutputParser( object ):

	'''
	Our first version of this class uses the
	tabular format output of LDNe2, using the
	configuration file as evaluated by the
	LDNe2 source function "RunMultiCommon".

	We assume that:
		1. The input files are restricted
		to a single genepop file.  See the class
		description in module pgldne2controller.py.

		2. Only a single critical value (i.e. min.
		allele frequency threshold) is used in the
		estimations. (See the pgldne2controller de-
		fault settings for the input parameters).

		3. The client has the tabular/columnar LDNe2 
		output format in a file, and supplies the output file
		basename (without the tabular file extension)
		in the __init__ def.
	'''

	COLUMN_OUTPUT_EXT="x.txt"

	#Note that the data columns use multiple spaces between
	#field values.
	PARSING_METRICS={ "DATA_DELIMIT": " ", 
						"POPNUM_DELIMIT":":",
						"FIELDNUM_POPNUM_IN_POPNUM_COLUMN":0,
						"TOTAL_LINES_FOLLOWING_DATA":8,
						"TOTAL_FIELDS_PER_DATA_LINE":12,
						"TOTAL_DIVIDER_LINES_BEFORE_DATA":4,
						"REGEX_PENULT_HEADER_LINE":"^[1-9].*",
						"REGEX_LINE_BEFORE_DATA":"^-+$",
						"REGEX_LINE_FOLLOWING_DATA":"^$",
						"REGEX_SECOND_LINE_AFTER_DATA":"^-+$",
						"REGEX_DIVIDER_LINE":"^-+$",
						"REGEX_THIRD_LINE_AFTER_DATA":"Total number of populations =.*",
						"COLNUM_POP_NUMBER":1,
						"COLNUM_SAMP_SIZE":2,
						"COLNUM_WEIGHTED_H_MEAN":3,
						"COLNUM_INDEP_ALLELES":4,
						"COLNUM_R_SQUARED":5,
						"COLNUM_EXP_R_SQUARED":6,
						"COLNUM_NE_ESTIMATE":7,
						"COLNUM_CI_PARAM_LOW":8,
						"COLNUM_CI_PARAM_HI":9,
						"COLNUM_CI_JACKKNIFE_LOW":10,
						"COLNUM_CI_JACKKNIFE_HI":11,
						"COLNUM_EFF_DF":12 }

	OUTPUT_VALUE_KEYS_BY_COLNUM={ 1:"pop_number", 2:"samp_size", 
									3:"weighted_h_mean", 4:"indep_alleles", 
									5:"r_squared", 6:"exp_r_squared", 
									7:"ne_estimate", 8:"ci_param_low", 
									9:"ci_param_hi", 
									10:"ci_jackknife_low", 
									11:"ci_jackknife_hi", 
									12:"eff_df" }

	OUTPUT_VALUE_TYPES_BY_COLNUM={ 1:int, 2:float, 3:float, 4:float, 
									5:float, 6:float, 7:float, 8:float, 
									9:float, 10:float, 11:float, 12:float }

	FILE_LOOKS_VALID=1
	FILE_LOOKS_INVALID=0
	FILE_HAS_NO_DATA_LINES=2

	def __init__( self, s_tabular_output_file_basename=None ):
		#A convenience, for referencing class-wide
		#constant PARSING_METRICS.
		self.me=self.__class__

		self.__tabular_file=s_tabular_output_file_basename  \
					+ PGLDNe2OutputParser.COLUMN_OUTPUT_EXT

		self.__tabular_file_lines=None

		self.__parsed_data=None

		if self.__tabular_file is not None:
			self.__parse_data()
		#end if output file name is not none

		return
	#end __init__

	def __match_is_found( self, s_regex, s_subject ):

		b_found=False
		o_match=re.match( s_regex, s_subject)
		
		b_found=o_match is not None

		return b_found
	#end __match_is_found

	def __get_line_number_first_data_line( self, ls_file_lines ):
		'''
		Returns the ith file line, 1-based count, such that it
		is the first line of data in the tabular output. Note
		that we assume that the data lines directly follow the jth
		divider line in the header, as given in the parsing metrics
		dict.
		'''

		s_regex_divider=self.me.PARSING_METRICS[ "REGEX_DIVIDER_LINE" ]
		i_total_dividers_before_data = \
				self.me.PARSING_METRICS[ "TOTAL_DIVIDER_LINES_BEFORE_DATA" ]
		i_divider_count=0	

		for idx in range( len( ls_file_lines ) ):
			if re.match( s_regex_divider, ls_file_lines[ idx ] ):
				i_divider_count+=1
			#end if divider line
			if i_divider_count==3:
				break
			#end if third divider
		#end for each file line	
		#Add two, one to adjust for python 0-based list indexing,
		#and one to desgnate that the first data line is the next
		#down from the last divider in the header.
		return idx + 2
	#end __get_line_number_first_data_line

	def __get_data_range( self, ls_file_lines ):
		'''
		This def returns a range object for iterating
		over the data lines only.
		'''
		i_total_lines=len( ls_file_lines )

		i_line_num_first_data=self.__get_line_number_first_data_line( ls_file_lines )

		idx_range_start=i_line_num_first_data - 1

		idx_range_end=i_total_lines  \
						- self.me.PARSING_METRICS[ "TOTAL_LINES_FOLLOWING_DATA" ]
		
		return list(range( idx_range_start, idx_range_end))
	#end __get_data_range

	def __extract_pop_number_from_string_entry( self , s_string_value ):

		s_pop_number=None
		s_delimit_pop_num=self.me.PARSING_METRICS[ "POPNUM_DELIMIT" ]
		idx_popnum=self.me.PARSING_METRICS[ "FIELDNUM_POPNUM_IN_POPNUM_COLUMN" ]

		ls_popnum_fields=s_string_value.split(s_delimit_pop_num )

		s_popnum=ls_popnum_fields[ idx_popnum ]

		return s_popnum
	#end __extract_pop_number_from_string_entry

	def __looks_like_output_file_format( self, ls_tabular_file_lines ):
		
		i_line_count=len( ls_tabular_file_lines )
		i_line_num_first_data=self.__get_line_number_first_data_line( ls_tabular_file_lines )
		i_total_non_data_lines=self.me.PARSING_METRICS[ "TOTAL_LINES_FOLLOWING_DATA" ] \
						+ ( i_line_num_first_data - 1 )

		if i_line_count < i_total_non_data_lines + 1:
			return self.me.FILE_HAS_NO_DATA_LINES, \
					"No data found in output file.  " \
					+ "Total line count is less than or equals the count of non-data lines." 
		#end line count too small

		#Our parsing metrics use 1-based line numbers, so we must subract 2
		#to get the index of a preceeding line:

		idx_line_before_data=i_line_num_first_data - 2
		idx_line_following_data= i_line_count - self.me.PARSING_METRICS[ "TOTAL_LINES_FOLLOWING_DATA" ] 
		
		s_line_before_data=ls_tabular_file_lines[ idx_line_before_data ]
		s_line_following_data=ls_tabular_file_lines[ idx_line_following_data ]
		s_second_line_after_data=ls_tabular_file_lines[ idx_line_following_data + 1 ]
		s_third_line_after_data=ls_tabular_file_lines[ idx_line_following_data + 2 ]

		class TestAndResults( object ):
			pass
		#end class tests

		lo_tests=[]

		o_test=TestAndResults()
		o_test.result=self.__match_is_found( \
							self.me.PARSING_METRICS[ "REGEX_LINE_BEFORE_DATA" ], 
														s_line_before_data )
		o_test.msg="Mismatch in regex with line before data."

		lo_tests.append( o_test )

		o_test=TestAndResults()
		o_test.result=self.__match_is_found( \
						self.me.PARSING_METRICS[ "REGEX_LINE_FOLLOWING_DATA" ], 
														s_line_following_data ) 
		o_test.msg="Mismatch in regex with line following data."
		lo_tests.append( o_test )

		o_test=TestAndResults()
		o_test.result=self.__match_is_found( \
						self.me.PARSING_METRICS[ "REGEX_SECOND_LINE_AFTER_DATA" ], 
														s_second_line_after_data ) 
		o_test.msg="Mismatch in regex with second line after data."
		lo_tests.append( o_test )

		o_test=TestAndResults()
		o_test.result=self.__match_is_found( \
						self.me.PARSING_METRICS[ "REGEX_THIRD_LINE_AFTER_DATA" ], 
														s_third_line_after_data ) 
		o_test.msg="Mismatch in regex with third line after data."

		lo_tests.append( o_test )

		i_field_count=self.me.PARSING_METRICS[ "TOTAL_FIELDS_PER_DATA_LINE" ] 

		idx_first_data_line=idx_line_before_data + 1

		'''
		The following line depends on the data fields being
		delimited by spaces, and including values separated
		by multi-spaces are used in the output file to 
		"pretty-print" the output, so that we need to collapse 
		concatenated spaces to get a list of data values. 
		We do this test to make sure we can call strip() 
		without arguments, which will by default collapse 
		adjacent delimiters. Note that the str.strip() def 
		has no paramater that implements collapsing.
		'''

		lb_data_line_correct_field_count=[ len( ls_tabular_file_lines[ idx ].split() ) == i_field_count \
						for idx in range( idx_first_data_line, idx_line_following_data ) ]

		o_test=TestAndResults()
		o_test.result=not( False in lb_data_line_correct_field_count )
		o_test.msg="Mismatch in expected total field count for at least one data line."

		lo_tests.append( o_test )

		b_tests_good=True

		ls_return_messages=[]

		for o_test in lo_tests:

			b_tests_good &= o_test.result

			if o_test.result==False:
				ls_return_messages.append( o_test.msg )
			#end if failed test, add message

		#end for each test
		
		s_return_messages="\n".join( ls_return_messages )

		b_return_value=None

		if b_tests_good:
			b_return_value=self.me.FILE_LOOKS_VALID
		else:
			b_return_value=self.me.FILE_LOOKS_INVALID
		#end if all tests good, else at least one bad

		return b_return_value, s_return_messages	
	#end def __looks_like_output_file_format

	def __parse_data( self ):

		ls_file_lines=None
		self.__parsed_data=[]

		try:
			o_file=open( self.__tabular_file )
			ls_file_lines=[ s_line.strip() for s_line in o_file.readlines() ]
		except Exception as oex:
			s_msg="In PGLDNe2OutputParser instance, " \
						+ "def parse_data, " \
						+ "Exception opening and reading file. " \
						+ "Exception msg: " + str( oex ) + "."
			raise Exception( s_msg )
		#end try ... except

		b_format_check_result, s_err_msg=self.__looks_like_output_file_format( ls_file_lines )

		if b_format_check_result==self.me.FILE_LOOKS_INVALID:
			s_msg="In PGLDNe2OutputParser, instance, " \
						+ "def parse_data, " \
						+ "an invalidity found in the format " \
						+ "of file, " + self.__tabular_file + ".  "  \
						+ "Message: " + s_err_msg
	
			raise Exception( s_msg )
		elif b_format_check_result==self.me.FILE_HAS_NO_DATA_LINES:
			s_msg="Warning: in PGLDNe2OutputParser, instance, " \
						+ "def parse_data, " \
						+ "no data lines were found in file, " \
						+ self.__tabular_file + ".  "  

			sys.stderr.write( s_msg + "\n" )
		#end if invalid, exception, else if no data so return empty list
		
		o_data_range=self.__get_data_range( ls_file_lines )

		try:

			for idx in o_data_range:
				s_this_data_line=ls_file_lines[ idx ]

				ls_these_values=s_this_data_line.split()

				dv_this_value_set={}

				for idx_field in range( len( ls_these_values ) ):

					i_column_number=idx_field + 1

					s_value_key=self.me.OUTPUT_VALUE_KEYS_BY_COLNUM[ i_column_number ]
					o_value_type=self.me.OUTPUT_VALUE_TYPES_BY_COLNUM[ i_column_number ]

					v_this_value=None
					
					if s_value_key=="pop_number":
						s_pop_number=self.__extract_pop_number_from_string_entry( ls_these_values[ idx_field ] )
						v_this_value=o_value_type( s_pop_number )
					else:
						try:
							v_this_value=o_value_type( ls_these_values[ idx_field ] )
						except ValueError as ove:

							if o_value_type==float and ls_these_values[ idx_field ]=="Infinite":
								v_this_value=float( "inf" )
							else:
								raise ( ove )
							#end if type did not work, fix if its a float-type field and valued at infinity
						#end try ... except

					#end if

					dv_this_value_set[ s_value_key ]=v_this_value
				#end for each index in the value list

				self.__parsed_data.append( dv_this_value_set )
			#end for each data line in the file

		except Exception as oex:
			s_msg="In PGLDNe2OutputParser, instance, " \
						+ "def parse_data, " \
						+ "an exception was raised while " \
						+ "parsing the data values.  Exception " \
						+ "message: " + str( oex ) 
			raise Exception( s_msg )
		#end try...except

		return
	#end __parse_data

	@property
	def parsed_output( self ):
		lv_result=None
		if len( self.__parsed_data ) == 0:
			lv_result=[]
		else:
			lv_result=[ dv_this_data.copy() for dv_this_data in self.__parsed_data ]
		#end if no data lines found, else data lines
		return lv_result 
	#end property parsed_output

#end class PGLDNe2OutputParser

if __name__ == "__main__":

	s_output_file="ldnenozerox.txt"
	myo=PGLDNe2OutputParser(  s_output_file )

	print( myo.parsed_output )
#end if main

