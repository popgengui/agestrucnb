'''
Description
'''
from __future__ import division
from __future__ import print_function

from builtins import range
from past.utils import old_div
from builtins import object

__filename__ = "pgneestimationfilemanager.py"
__date__ = "20170926"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import numpy
'''
2017_09_28.  Possibly becasue of the __future__
or related imports, python (2 and 3) complain
they don't know the name "reduce", supposedly
a python base def.  per stack overflow help, 
found that this solves the problem:
'''
from functools import reduce

class NeEstimationTableFileManager(object):
	'''
	Class to read and write the table 
	files with Ne estimations generated 
	by pgdriveneestimator.py.

	Motivation: Needed in order to filter the
	table for plotting using Brian T's
	line regresss program, when the table
	has more than one subsample value for 
	the "pop" sections and/or "loci" list. For example,
	if the user has subsampled a genepop file
	to get 95 and 85 percent fot individuals
	per pop, and and also subsampled the loci
	to get 95 and 85 percent of loci (however
	many replicates in each), then the reaults
	will need to be filtered to include only
	rows whose pop subsdample value i and loci 
	subsample value j are fixed, so that i,j
	is 85,85 or 85,95 or 95,85 or 95,95.

	The file is loaded into a numpy array,
	and all fields are typed as bytes.
	(There's a type problem if we type the array 
	"str", so that  we get different types depending 
	on py2 vs py3:

	"if you create a NumPy array containing strings, 
	the array will use the numpy.string_ type (or 
	the numpy.unicode_ type in Python 3)." More precisely, 
	the array will use a sub-datatype of np.string_

	This class returns its items as strings, after
	decoding the bytes using sys.stdout.encoding.
	I think this gives items compatible with 
	the string methods in both py2 and py3.

	
	2017_09_28
	I am adding code to return the data lines
	grouped on an arbitrary number of fields
	(with const limits on total grouping,
	as the growth of the total 
	groupings will explode as number of unique
	values for each grouping increases).
	
	'''

	DELIM_TABLE="\t"
	DELIM_GROUPED_FIELD_NAMES="__"

	COL_NAME_FILE_NAME=b'original_file'
	COL_NAME_POP_SAMPLE_VAL=b'sample_value'
	COL_NAME_LOCI_SAMPLE_VAL=b'loci_sample_value'
	COL_NAME_POP_NUM=b'pop'
	COL_NAME_POP_REPLICATE=b'replicate_number'
	COL_NAME_LOCI_REPLICATE=b'loci_replicate_number'

	ENCODING=sys.stdout.encoding

	MAX_NUM_GROUPING_FIELDS=4
	MAX_NUM_GROUPINGS=3000

	'''
	2017_10_07. These are added for clients who need
	to show users self-explanatory column names, rather
	than those used in the tsv file.
	'''
	COLUMN_NAME_ALIASES_BY_COLUMN_NAME={ 'original_file':'genepop file',
						'pop':'pop',
						'census':'total indiv',
						'indiv_count':'total indiv sampled',
						'sample_value':'pop subsample value',
						'replicate_number':'pop sampling replicate',
						'loci_sample_value':'loci subsample value',
						'loci_replicate_number':'loci sampling replicate',
						'min_allele_freq':'min allele frequency',
						'est_type':'estimation_type',
						'est_ne':'LDNe estimation',
						'95ci_low':'low 95% CI',
						'95ci_high':'high 95% CI',
						'overall_rsquared':'overall r-squared',
						'expected_rsquared':'expected r-squared',
						'indep_comparisons':'independant comparisons',
						'harmon_mean_samp_size':'harmonic mean sample size',
						'alt_ci_low':'alternate low 95% CI',
						'alt_ci_high':'alternate high 95% CI',
						'nbne':'Nb/Ne',
						'ne_est_adj':'adjusted LDNe estimation',
						'mean_het':'pop mean expected heterozygosity' }
		
	COLUMN_NAMES_BY_ALIAS={ 'genepop file':'original_file',
						'pop':'pop',
						'total indiv':'census',
						'total indiv sampled':'indiv_count',
						'pop subsample value':'sample_value',
						'pop sampling replicate':'replicate_number',
						'loci subsample value':'loci_sample_value',
						'loci sampling replicate':'loci_replicate_number',
						'min allele frequency':'min_allele_freq',
						'estimation_type':'est_type',
						'LDNe estimation':'est_ne',
						'low 95% CI':'95ci_low',
						'high 95% CI':'95ci_high',
						'overall r-squared':'overall_rsquared',
						'expected r-squared':'expected_rsquared',
						'independant comparisons':'indep_comparisons',
						'harmonic mean sample size':'harmon_mean_samp_size',
						'alternate low 95% CI':'alt_ci_low',
						'alternate high 95% CI':'alt_ci_high',
						'Nb/Ne':'nbne',
						'adjusted LDNe estimation':'ne_est_adj',
						'pop mean expected heterozygosity':'mean_het' }

	'''
	2017_10_14. This list added when implementing the embedded
	regression plotting, which requires that y values are single
	estimates.  Clients will use this, for example, to get unique
	keys for dicts of plot values.
	'''
	INPUT_FIELDS_ASSOC_WITH_ONE_ESTIMATE=[ 'original_file', 'pop', 'sample_value',
													'replicate_number', 'loci_sample_value',
													'loci_replicate_number' ]

	def __init__( self, s_file_name, 
					i_header_is_first_n_lines=1,
					i_col_names_line_num=1,
					s_tsv_file_delimiter="\t" ):
		'''
		param s_file_name gives the name
		of a file output by pgdriveneestimator.py,
		and is the main (*tsv) output file giving
		Ne estimations and related quants.

		param i_header_is_first_n_lines gives the number 
		of lines at the beginning of the file that are
		non-data.

		param i_col_names_line_num gives the file's line number
		that holds the delimited column names
		
		param s_tsv_file_delimiter gives the character that
		delimits the columns in the tsv file. The default
		is <tab>.
		'''

		self.__filename=s_file_name
		self.__header_line_tot=i_header_is_first_n_lines
		self.__line_number_col_names=i_col_names_line_num
		self.__tsv_file_delimiter=s_tsv_file_delimiter

		self.__myclassname=NeEstimationTableFileManager
		self.__table_array=None
		self.__load_file_into_array()
				
		'''
		Dictionary of references to functions keyed to column numbers. Valid
		values are None or a ref to a def that takes a single 
		string value and returns a boolean.  This dictionary 
		is used to write a filtered version of the input file 
		that includes only lines that pass all filters (all 
		return True). Users add these via def setFilter
		below.
		'''
		self.__filters={}

		return
	#end __init__

	def __load_file_into_array( self ):

		self.__table_array=numpy.loadtxt( fname=self.__filename, 
														dtype=bytes, 
														delimiter=self.__tsv_file_delimiter )
		return
	#end __load_file_into_array

	def __colname_is_in_header( self, s_colname ):
		b_return_value=False
		b_col_name=self.__get_bytes_from_string_value( s_colname )
		ar_col_names=self.__table_array[ self.__line_number_col_names - 1, : ]

		for b_this_name in ar_col_names:
			if b_this_name==b_col_name:
				b_return_value=True
				break
			#end if match found, return is True
		#end for each col name
		
		return b_return_value
	#end __colname_is_in_header

	def __get_col_nums_for_col_name( self, b_col_name, b_enforce_uniq=True ):
		'''
		param b_col_name is a bytes object, to be compared
		to those read in to the first line of the table array.
		
		2017_02_16.  param b_enforce_uniq, when True employes an assert statment
		that the tup[0] returned by numpy.where (i.e. the tuple with
		indices for true values for the conditional) has exactly one
		item, indicating a single column number that matches the b_col_name arg.
		'''
		ar_col_names=self.__table_array[ self.__line_number_col_names - 1, : ]

		#Returns a tuple of arrays, the first array being the
		#index or indices in the bool array wherein ar_col_names has the match.
		tup_ar_col_nums=numpy.where( ar_col_names==b_col_name )
		ar_col_nums=tup_ar_col_nums[ 0 ]

		if b_enforce_uniq:
				s_msg="In NeEstimationTableFileManager instance, " \
							+ "def __get_col_nums_for_col_name, " \
							+ "non-unique column number for match for " \
							+ "column name, " + str( b_col_name ) + "."
				
				assert len( ar_col_nums ) == 1, s_msg
		#end if we are to enforce a unique column number

		return ar_col_nums
	#end __get_col_nums_for_col_name

	def __get_set_values_for_column( self, i_col_number ):
		'''
		This def returns a list givein the set (unique)
		string-typed values for the column given by i_col_number.
		'''
		ar_table=self.__table_array
		i_min_row=self.__header_line_tot

		return set( ar_table[ i_min_row : , i_col_number ] )
	#end __get_set_values_for_column

	def __get_set_bytes_values_for_column_name( self, b_col_name ):

		ar_col_nums=self.__get_col_nums_for_col_name( b_col_name  )

		if len( ar_col_nums ) != 1:
			s_msg="In NeEstimationTableFileManager instance, " \
							+ "def __get_set_bytes_values_for_col_name, " \
							+ "in fetching column number for name, " + str( b_col_name ) \
							+ " from the file header, a non unique column " \
							+ "number was returned, using sample value column " \
							+ "list of column numbers found for this column name: " \
							+ str( ar_col_nums ) + "."
			raise Exception( s_msg )
		#end if non uniq col number

		set_values=self.__get_set_values_for_column( ar_col_nums [ 0 ] )
		
		return list( set_values )

	#end def __get_set_bytes_values_for_col_name

	def __get_string_from_bytes_value( self, b_bytes ):
		s_bytes=str( b_bytes.decode( self.__myclassname.ENCODING ) )
		return s_bytes
	#end __get_string_from_bytes_value

	def __get_bytes_from_string_value( self, s_strval ):
		b_strval=bytes( s_strval.encode( self.__myclassname.ENCODING ) )
		return b_strval
	#end __get_bytes_from_string_value

	def __get_list_of_strings_from_list_of_bytes( self, lb_list ):
		ls_as_strings=[ str(  \
				b_val.decode( self.__myclassname.ENCODING )  )
											for b_val in lb_list ]
		return ls_as_strings
	#end __get_list_of_strings_from_list_of_bytes

	def __get_list_bytes_pop_sample_values( self ):
		b_col_name=self.__myclassname.COL_NAME_POP_SAMPLE_VAL
		set_pop_sample_values=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_pop_sample_values )
	#end __get_list_pop_sample_values

	def __get_list_bytes_loci_sample_values( self ):
		b_col_name=self.__myclassname.COL_NAME_LOCI_SAMPLE_VAL
		set_loci_sample_values=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_loci_sample_values )
	#end __get_list_bytes_loci_sample_values

	def __get_list_bytes_file_names( self ):
		b_col_name=self.__myclassname.COL_NAME_FILE_NAME
		set_file_names=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_file_names )
	#end __get_list_bytes_file_names

	def __get_list_bytes_pop_numbers( self ):
		b_col_name=self.__myclassname.COL_NAME_POP_NUM
		set_pop_numbers=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_pop_numbers )
	#end __get_list_bytes_pop_numbers

	def __get_list_bytes_pop_replicate_numbers( self ):
		b_col_name=self.__myclassname.COL_NAME_POP_REPLICATE
		set_pop_replicates=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_pop_replicates )
	#end __get_list_bytes_pop_replicate_numbers

	def __get_list_bytes_loci_replicate_numbers( self ):
		b_col_name=self.__myclassname.COL_NAME_LOCI_REPLICATE
		set_pop_replicates=self.__get_set_bytes_values_for_column_name( b_col_name )
		return list( set_pop_replicates )
	#end __get_list_bytes_loci_replicate_numbers

	def __get_list_of_column_numbers_for_list_of_column_names( self, ls_col_names ):

		li_column_numbers=[]
		for s_column_name in ls_col_names:
			b_column_name=self.__get_bytes_from_string_value( s_column_name )
			#Default 2nd arg for this call ensures we get back only one
			#column number in the returned array:
			ar_col_nums=self.__get_col_nums_for_col_name( b_column_name )
			i_col_num=ar_col_nums[ 0 ]
			li_column_numbers.append( i_col_num )
		#end for each column name
		return li_column_numbers
	#end __get_list_of_column_numbers_for_list_of_column_names

	def __get_filtered_table_as_list_of_strings( self, 
								ls_exclusive_cols=None,
								b_skip_header=False ):
		ls_entries=[]

		i_line_count=0

		li_exclusive_col_nums=None

		if ls_exclusive_cols is not None:
			li_exclusive_col_nums= \
					self.__get_list_of_column_numbers_for_list_of_column_names( \
														ls_exclusive_cols )
		#end if we have exclusive col names

		for ar_line in self.__table_array:
			i_line_count+=1

			#We do an "and" op to this bool
			#with all non-None filters.
			b_line_should_be_included=True

			if i_line_count == 1:
				if b_skip_header == True:
					b_line_should_be_included=False
				else:
					'''
					Header line, no tests needed, and our write flag,
					b_line_should_be_included is already set to True, 
					so pass
					'''
					pass
				#end if flag says skip header, else include
			else:
				for i_colnum in self.__filters:
					if self.__filters[ i_colnum ] is not None:
						b_table_value=ar_line[ i_colnum ]
						s_table_value=self.__get_string_from_bytes_value( b_table_value )
						b_line_should_be_included &= self.__filters[ i_colnum ] ( s_table_value ) 
					#end if non-None filter
				#end for each filter

			if b_line_should_be_included:
				ls_line_as_list_of_strings= \
						self.__get_list_of_strings_from_list_of_bytes( ar_line )

				#If we are to collect only a subset of the columns,
				#reduce the list:
				if li_exclusive_col_nums is not None:
					ls_line_as_list_of_strings=[ ls_line_as_list_of_strings[ i ] \
														for i in li_exclusive_col_nums ]
				#end if we have exlcusive col nums

				s_entry=self.__myclassname.DELIM_TABLE.join( \
													ls_line_as_list_of_strings )
				ls_entries.append( s_entry )
			#end if line should be included, append to list
		#end for each line in array
		return ls_entries
	#end def __get_filtered_table_as_list_of_strings

	def __get_unfiltered_table_as_list_of_strings( self, 
									ls_exclusive_cols=None,
									b_skip_header=False ):
		ls_entries=[]

		i_line_count=0

		li_exclusive_col_nums=None

		if ls_exclusive_cols is not None:
			li_exclusive_col_nums= \
					self.__get_list_of_column_numbers_for_list_of_column_names( \
														ls_exclusive_cols )
		#end if we have exclusive col names

		for ar_line in self.__table_array:
			i_line_count += 1
			if i_line_count == 1:
				if b_skip_header == True:
					continue
				#end if we should skip the header
			else:

				ls_line_as_list_of_strings= \
						self.__get_list_of_strings_from_list_of_bytes( ar_line )

				#If we are to collect only a subset of the columns,
				#reduce the list:
				if li_exclusive_col_nums is not None:
					ls_line_as_list_of_strings=[ ls_line_as_list_of_strings[ i ] \
														for i in li_exclusive_col_nums ]
				#end if we have exlcusive col nums

				s_entry=self.__myclassname.DELIM_TABLE.join( \
													ls_line_as_list_of_strings )
				ls_entries.append( s_entry )
			#end if header, check for header incluseion, else append
		#end for each line in array
		return ls_entries
	#end def __get_filtered_table_as_list_of_strings

	def __write_filtered_table_to_open_file_object( self, o_open_file ):

		ls_entries=self.__get_filtered_table_as_list_of_strings()

		for s_entry in ls_entries:
			o_open_file.write( s_entry + "\n" )
		#end for each string entry

		return
	#end __write_filtered_table_to_open_file_object

	'''
	2017_09_28.  The code below is used to deliver data grouped by an
	arbitrary number of fields.
	'''
	def __get_list_groupings( self, ls_group_by_column_names ):

		ls_groupby_values=[]

		def_valgetter=self.getUniqueStringValuesForColumn

		dsv_values_by_column_name={ s_col:def_valgetter( s_col ) \
									for s_col in ls_group_by_column_names }

		i_num_grouping_fields=len( ls_group_by_column_names )

		if i_num_grouping_fields > NeEstimationTableFileManager.MAX_NUM_GROUPING_FIELDS:
			s_msg="In NeEstimationTableFileManager, instance, " \
					+ "def __get_list_groupings, " \
					+ "number of grouping fields exceeds limit (" \
					+ str( NeEstimationTableFileManager.MAX_NUM_GROUPING_FIELDS ) \
					+ ") set in class code."
			raise Exception( s_msg )
		#end if too many groups

		lls_value_lists_by_sorted_field_name=[ dsv_values_by_column_name[ s_name ] \
									for s_name in sorted( dsv_values_by_column_name ) ]

		li_values_per_sorted_field=[ len( list( ls_vals ) ) \
				for ls_vals	 in lls_value_lists_by_sorted_field_name ]

		i_total_groups=reduce( lambda x,y : x*y, li_values_per_sorted_field )
	
		if i_total_groups > NeEstimationTableFileManager.MAX_NUM_GROUPINGS:
			s_msg="In NeEstimationTableFileManager, instance, " \
					+ "def __get_list_groupings, " \
					+ "number of groupings exceeds limit (" \
					+ str( NeEstimationTableFileManager.MAX_NUM_GROUPINGS ) \
					+ ") set in class code."
			raise Exception( s_msg )
		#end if too many groups

		ls_grouping_values=self.__concat_list_items( lls_value_lists_by_sorted_field_name[0], 
						lls_value_lists_by_sorted_field_name, 2 )
	
		return ls_grouping_values
	#end __get_list_groupings

	def __concat_list_items( self, ls_current, lls_lists_of_strings, i_list_num ):

		if i_list_num > len( lls_lists_of_strings ):
			return ls_current
		#end if last list has been incorporated

		ls_new_current=[]
		ls_next_in_list=lls_lists_of_strings[ i_list_num - 1 ]
		for s_this in ls_current:
			for s_that in ls_next_in_list:
				ls_new_current.append( str( s_this ) 
						+ NeEstimationTableFileManager.DELIM_GROUPED_FIELD_NAMES 
						+ str( s_that ) )
			#end for each in next list
		#end for each in

		ls_ret_val=self.__concat_list_items( ls_new_current, lls_lists_of_strings, i_list_num+1 )

		return ls_ret_val
	#end __concat_list_items

	def __get_grouping_field_numbers_sorted_by_field_name( self, ls_group_by_column_names ):
		ls_sorted_field_names=sorted( ls_group_by_column_names )
		li_field_numbers_sorted_by_name=[]
		for s_name in ls_sorted_field_names:
			i_num_this_col=self.getColumnNumberByName( s_name )
			li_field_numbers_sorted_by_name.append( i_num_this_col )
		#end for each sorted field name

		return li_field_numbers_sorted_by_name
	#end __get_grouping_field_numbers_sorted_by_field_name

	def __get_data_field_numbers( self, ls_data_column_names ):
		li_field_numbers=[]
		for s_name in ls_data_column_names:
			i_num_this_col=self.getColumnNumberByName( s_name )
			li_field_numbers.append( i_num_this_col )
		#eend for each field

		return li_field_numbers
	#end __get_data_field_numbers

	def	__get_dict_data_by_group_names( self, ls_group_by_column_names, 
												ls_data_column_names,
												b_skip_header=True ):

		li_grouping_field_number_by_sorted_field_names = \
				self.__get_grouping_field_numbers_sorted_by_field_name( ls_group_by_column_names )

		li_data_field_numbers_by_field_names=self.__get_data_field_numbers( ls_data_column_names )

		ls_grouping_values=self.__get_list_groupings(ls_group_by_column_names )

		ls_data_lines=self.getFilteredTableAsList( b_skip_header=b_skip_header )

		dls_grouped_data_lines = { s_grouping:[]  for s_grouping in  ls_grouping_values }

		i_data_line_num=0

		for s_line in ls_data_lines:

			i_data_line_num+=1
			
			ls_vals=s_line.split( self.__myclassname.DELIM_TABLE )
			
			s_group_name=NeEstimationTableFileManager.DELIM_GROUPED_FIELD_NAMES.join( [ ls_vals[ idx ] \
					for idx in li_grouping_field_number_by_sorted_field_names ] )

			s_data_this_line=self.__myclassname.DELIM_TABLE.join( [ ls_vals[idx] \
									for idx in li_data_field_numbers_by_field_names ] )

			try:
				dls_grouped_data_lines[ s_group_name ].append( s_data_this_line )
			except KeyError as ove:
				s_msg="In NeEstimationTableFileManager instance, " \
							+ "def __get_dict_data_by_group_names, " \
							+ "the program could not find a match for " \
							+ "the grouping values, " + s_group_name + "."
				raise Exception( s_msg )
			#end try...except...
		#end for each data line
		return dls_grouped_data_lines
	#end  def  __get_dict_data_by_group_names

	def getGroupedDataLines( self, ls_group_by_column_names, 
										ls_data_column_names, 
										b_skip_header=True ):
		'''
		This def returns a dicitionary whose keys are the concatenated
		set of unique values for the group-by column names given in
		arg ls_group_by_column_names, and whose values are the fields
		from the tsv file as given by arg ls_data_column_names, that
		have matching values for the group-by columns. The data fecthed
		is also filtered by any existing filters as added by the setFilter
		functionality.


		Note that the number of fields and total groupings is limited 
		by the constants in this class MAX_NUM_GROUPING_FIELDS, and 
		MAX_NUM_GROUPINGS.
		'''

		dlv_grouped_data=None

		b_dont_group=ls_group_by_column_names is None \
					or len( ls_group_by_column_names ) == 0

		if b_dont_group == True:
			ls_data_lines=self.getFilteredTableAsList( ls_exclusive_inclusion_cols = ls_data_column_names,
																		b_skip_header=b_skip_header )
			dlv_grouped_data={ "":ls_data_lines }
		else:
			dlv_grouped_data=self.__get_dict_data_by_group_names( ls_group_by_column_names,
																	ls_data_column_names,
																	b_skip_header )
		#end if no groups

		return dlv_grouped_data
	#end getGroupedDataLines

	'''
	2017_09_28.  End of new defs added to deliver grouped data lines.
	'''

	def getDictDataLinesKeyedToColnames( self, ls_key_column_names, 
												ls_value_column_names,
												b_skip_header=False ):
		'''
		2017_10_12. This def is added in order to support class 
		PGPlottingFrameRegressionLinesFromFileManager, which needs
		for every instance in the tsv file, of a uniq value in 
		its set possible x-axis values (i.e. typically pop number), 
		the concatted values of the fields associated with it. Most
		appropriately, what is needed are the genpop file parameters
		associated with the pop number as x-value, in order to regress
		a line for each of the genpop file parameters, as it is assoc
		with a set of pop numbers.
		'''
		o_myc=NeEstimationTableFileManager
		li_key_column_numbers=\
				self.__get_list_of_column_numbers_for_list_of_column_names( \
														ls_key_column_names )
		li_value_column_numbers=\
				self.__get_list_of_column_numbers_for_list_of_column_names( \
														ls_value_column_names )

		ls_data_lines=self.getFilteredTableAsList( b_skip_header=b_skip_header )
		
		df_data_keyed_to_colnames={}

		for s_line in ls_data_lines:
			ls_vals=s_line.split( o_myc.DELIM_TABLE ) 
			ls_key=[ ls_vals[ idx ]  for idx in li_key_column_numbers ]		
			s_key=o_myc.DELIM_GROUPED_FIELD_NAMES.join( ls_key )

			ls_values=[ ls_vals[ idx ] for idx in li_value_column_numbers ]
			
			#We deliver the value field values delimited iusing
			#the same delimiter as used by the orig table (tsv):
			s_values=o_myc.DELIM_TABLE.join( ls_values )
			
			if s_key in df_data_keyed_to_colnames:
				df_data_keyed_to_colnames[ s_key ].append( s_values )	
			else:
				df_data_keyed_to_colnames[ s_key ] = [ s_values ]
			#end if key already in dict, else not
		#end for each data line

		return df_data_keyed_to_colnames
	#end getDictDataLinesKeyedToColnames
	
	def setFilter( self, s_column_name, def_filter ):
		'''
		param s_column_name, an item in the delimited header list of column
			names.
		param def_filter, a def that takes a single string arg and returns
			a boolean.  The usual case, if filtering for one value, say, v1,
			would be a def like, lambda x: x==v1. If def_filter is set to None, 
			no filter will be applied to this column. Setting to None is the 
			way to effectively remove a previously set filter.
		'''
		b_column_name=self.__get_bytes_from_string_value( s_column_name )
		ar_col_numbers=self.__get_col_nums_for_col_name( b_column_name )
		if len( ar_col_numbers ) != 1:
			s_msg="In NeEstimationTableFileManager instance, " \
							+ "def setFilter, " \
							+ "in fetching column number for sample value " \
							+ "from the file header, a non unique column " \
							+ "number was returned, using column " \
							+ "name: " + str( b_column_name ) + ", and getting list of " \
							+ "column numbers: " + str( ar_col_numbers ) + "."
			raise Exception( s_msg )
		#end if non uniq col number

		self.__filters[ ar_col_numbers[ 0 ] ] = def_filter
	#end setFilter

	def unsetAllFilters( self ):
		self.__filters={}
		return
	#end unsetAllFilters

	def writeFilteredTable( self, o_fileobject ):
		'''
		param o_fileobject is an open and writeable File object
		'''
		self.__write_filtered_table_to_open_file_object( o_fileobject )

		return
	#end writeFilteredTableToFile

	def getFilteredTableAsList( self, ls_exclusive_inclusion_cols=None, b_skip_header=False ):
		'''
		This def returns a list of strings, each a tab-delmited set of values
		corresponding to the tsv file, with all currentfilters in self.__filters
		applied.  If ls_exclusive_inclusion_cols is not None than it will return
		only those columns named in the list (column names that match those in 
		the header (line 1) of the tsv file.
		'''
		ls_filtered_table=self.__get_filtered_table_as_list_of_strings( ls_exclusive_inclusion_cols, b_skip_header=b_skip_header )
		return ls_filtered_table
	#end getFilteredTableAsList


	def getUnfilteredTableAsList( self, ls_exclusive_inclusion_cols=None, b_skip_header=False ):
		'''
		This def returns a list of strings, each a tab-delmited set of values
		corresponding to the tsv file, with none of the currentfilters in self.__filters
		applied.  If ls_exclusive_inclusion_cols is not None than it will return
		only those columns named in the list (column names that match those in 
		the header (line 1) of the tsv file.
		'''
		ls_unfiltered_table=self.__get_unfiltered_table_as_list_of_strings( ls_exclusive_inclusion_cols, 
																				b_skip_header=b_skip_header )
		return ls_unfiltered_table
	#end getFilteredTableAsList


	def getUniqueStringValuesForColumn( self, s_colname ):

		if not( self.__colname_is_in_header( s_colname  ) ):
			s_msg="In NeEstimationTableFileManager instance, " \
							+ "def getUniqueStringValuesForColumn, " \
							+ "in fetching column number for sample value " \
							+ "from the file header, no match for the name, " \
							+  s_colname  + "."
			raise Exception( s_msg )
		#end if no such col name

		b_column_name=self.__get_bytes_from_string_value( s_colname )
		ar_col_numbers=self.__get_col_nums_for_col_name( b_column_name )

		if len( ar_col_numbers ) != 1:
			s_msg="In NeEstimationTableFileManager instance, " \
							+ "def getUniqueStringValuesForColumn, " \
							+ "in fetching column number for sample value " \
							+ "from the file header, a non unique column " \
							+ "number was returned, using column " \
							+ "name: " + str( b_column_name ) + ", and getting list of " \
							+ "column numbers: " + str( ar_col_numbers ) + "."
			raise Exception( s_msg )
		#end if non uniq col number

		lb_column_values=list( self.__get_set_values_for_column( ar_col_numbers[ 0 ] ) )
		ls_column_values=self.__get_list_of_strings_from_list_of_bytes( lb_column_values )

		return ls_column_values

	#end getUniqueStringValuesForColumn

	def getColumnNumberByName( self, s_column_name ):
		b_column_name = self.__get_bytes_from_string_value( s_column_name )
		li_column_nums=self.__get_col_nums_for_col_name( b_column_name )
		return li_column_nums[ 0 ]
	#end getColumnNumberByName

	'''
	These two columns' value sets are given as properties because
	these are the motivating-user-case fields needed to select one
	value for each and write a so-filtered version of the tsv file.
	'''
	@property 
	def pop_sample_values( self ):
		lb_pop_sample_values=self.__get_list_bytes_pop_sample_values()
		ls_pop_sample_values=self.__get_list_of_strings_from_list_of_bytes( lb_pop_sample_values )
		return ls_pop_sample_values
	#end property pop_sample_values
	
	@property
	def loci_sample_values( self ):
		lb_loci_sample_values=self.__get_list_bytes_loci_sample_values()
		ls_loci_sample_values=self.__get_list_of_strings_from_list_of_bytes( lb_loci_sample_values )
		return ls_loci_sample_values
	#end property loci_sample_values

	@property
	def header( self ):
		ls_header_as_strings=self.__get_list_of_strings_from_list_of_bytes(  \
															self.__table_array[ 0, : ] )
		s_header=self.__myclassname.DELIM_TABLE.join( ls_header_as_strings )
		return s_header
	#end property header

	@property 
	def file_names(self ):
		lb_file_names=self.__get_list_bytes_file_names()
		ls_file_names=self.__get_list_of_strings_from_list_of_bytes( lb_file_names )
		return ls_file_names
	#end property file_names

	@property
	def pop_numbers( self ):
		lb_pop_numbers=self.__get_list_bytes_pop_numbers()
		ls_pop_numbers=self.__get_list_of_strings_from_list_of_bytes( lb_pop_numbers )
		return ls_pop_numbers
	#end pop_numbers

	@property
	def pop_replicate_numbers( self ):
		lb_pop_replicates=self.__get_list_bytes_pop_replicate_numbers()
		ls_pop_replicates=self.__get_list_of_strings_from_list_of_bytes( lb_pop_replicates )
		return ls_pop_replicates
	#end pop_numbers

	@property
	def loci_replicate_numbers( self ):
		lb_loci_replicates=self.__get_list_bytes_loci_replicate_numbers()
		ls_loci_replicates=self.__get_list_of_strings_from_list_of_bytes( lb_loci_replicates )
		return ls_loci_replicates
	#end pop_numbers

#end class NeEstimationTableFileManager

if __name__ == "__main__":
	pass
#end if main

