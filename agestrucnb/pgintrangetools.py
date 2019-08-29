'''
2019_01_22. These classes were part of the pgutilityclasses.py module,
but were moved here to prevent a cyclical import problem
when I wanted to use these classes to validate the pgguisimpupop.py
GUI processing of the cycle_filter parameter's text box.
'''

import sys

class IntRange( object ):
	'''
	This class stores the min and max integer values
	giving a (closed) interval [ min, max ].  Motivating
	case is the need for a cycle (pop, gen) filter during
	simulations, to filter which pops get written to output.
	'''
	
	def __init__( self, i_min_value, i_max_value ):
		
		self.validateMinMax( i_min_value, i_max_value )
		self.__min=i_min_value
		self.__max=i_max_value
		return
	#end init
	
	def validateMinMax( self, i_min_value, i_max_value ):
		
		s_err_msg=None
		
		s_err_msg_Prefix="In IntRange instance " \
							+ "def __init__, " \
							+ "invalid min and max args: "
						
		if i_min_value > i_max_value:
			s_err_msg="min value greater than max value"
		#end if min>max	
		
		if [ type( i_min_value ), type( i_max_value ) ] != [ int, int ]:
			s_err_msg="non-integer type for at least one of the min/max args" 
		#end if not both ints
		
		if s_err_msg is not None:
			raise Exception( s_err_msg )
		#end if error
		
		return 
	#end validateMinMax
	
	def isInRange( self, i_value ):
		
		b_return_value=False
		
		if i_value >= self.__min \
			and i_value <= self.__max:
			b_return_value=True
		#end if min <= val <= max
		
		return b_return_value
	
	#end isInRange
	
	def amEncompassedByRange( self, o_other_range ):
		b_return_value=False
		
		if self.__min >= o_other_range.rangemin \
				and self.__max <= o_other_range.rangemax:
			b_return_value=True
		#end if my min/max put me inside the other range
		
		return b_return_value
	#end amEncompassedByRange
	
	def rangesOverlap( self, o_another_range ):
		
		b_return_value=False
		if self.isInRange( o_another_range.rangemin ) \
				or self.isInRange( o_another_range.rangemax ):
			b_return_value=True
		elif o_another_range.isInRange( self.__min ) \
			or o_another_range.isInRange( self.__max ):
				b_return_value=True
		#end if either end of the other is in my range ... 
		#else if either end of my range in in the other's		
		
		return b_return_value
	#end rangesOverlap
	
	def getMergedRange( self, o_another_range ):
		'''
		This def returns None if the ranges don't overlap.
		'''
		o_merged_range=None
		i_new_min=None
		i_new_max=None
		
		if self.rangesOverlap( o_another_range ):
			
			if self.__min > o_another_range.rangemin:
				i_new_min=o_another_range.rangemin
			else:
				i_new_min=self.__min
			#end if the other range has a smaller min, else use mine	
			
			if self.__max < o_another_range.rangemax:
				i_new_max=o_another_range.rangemax
			else:
				i_new_max=self.__max
			#end if my max is smaller, else us mine	
			
			o_merged_range=IntRange( i_new_min, i_new_max )
		#end if ranges Overlap
		
		return o_merged_range
	#end getMergedRange
	
	def printRange( self ):
		print( "min: " + str( self.__min ) \
				+ ", max: " + str( self.__max ) )
	#end printRange	
	
	@property
	def rangemin( self ):
		return self.__min
	#end property rangemin
	
	@property
	def rangemax( self ):
		return self.__max
	#end property rangemin
	
#end class IntRange

class CycleRanges( object ):
	'''
	This class manages a series of i ranges 
	of integers extracted from a string 
	of the form m1-n1,m2-n2...m_i-n_i
	such that n_j>=m_j.  These are used
	by the PGOpSimuPop class to manage
	the writing of pop cycles only in specified
	ranges.
	
	This class uses the IntRange class, and,
	to build IntRanges from the range string,
	class IntRangeParser.  See the latter for
	details on string delimiters and the use
	of the hyphen vs a tilde when parsing individual
	ranges.
	'''

	
	def __init__( self, s_range_string=None, b_using_hyphen=False ):
		'''
		When the client expects no negative ints, and is using
		the hyphen char only for separating min from max, this
		should be set via flag arg to True:
		'''
		self.__client_using_hyphens_for_minmax_delimiter=b_using_hyphen
		
		self.__ranges=None
		self.__rangesbymax=None
		self.__extract_ranges( s_range_string )
		return 
	#end __init__
	
	def __extract_ranges( self, s_range_string ):
		
		s_err_msg="In CycleRanges instance, " \
					+ "def __extract_ranges, " \
					+ "could not convert range " \
					+ "into 2 integers: " 
				
		lo_ranges=[ ]
		
		
		ls_ranges=s_range_string.split( CycleRanges.CYCLE_RANGE_DELIMITER )
		self.__rangesbymax={ };
		
		o_last_range=None
		
		for s_range in ls_ranges:
			#We pass along the flag that tells the parser 
			#whether to use the default (tilde) or a hyphen
			#to split min~max pairs (see class IntRangeParser).
			o_range_parser=IntRangeParser( s_range, 
					self.__client_using_hyphens_for_minmax_delimiter )
			
			'''
			Note that clients can pass range strings that are one of:
			1. a single int i, producing 1 range object of size 1.
			2. two ints i-j, producing 1 range object
			3. three ints i-j;k, which may produce many range objects
			(see class IntRangeParser).
			'''
			for o_this_range in o_range_parser.__intrange_objects:
				lo_ranges.append( o_this_range )
			#end for each range parsed
		#end for each range

		#Refine the list by merging any overlapping pairs:
		lo_ranges=self.__merge_ranges( lo_ranges )
		
		for o_range in lo_ranges:
			self.__rangesbymax[ o_range.rangemax ] = o_range
		#end for each range, key it to the max value	
		
		self.__ranges=lo_ranges
		
		return 
	#end extract_ranges
	
	def __merge_ranges( self, lo_ranges ):
		
		o_last_range=None
		
		lo_new_range_list=[]
		
		lo_ranges.sort( key=lambda x : x.rangemin )
		
		for o_this_range in lo_ranges:
		
			o_merged_range=None
			
			if o_last_range is not None:
				'''
				Note:  getMergedRange returns None if the ranges 
				do not overlap
				'''
				o_merged_range=o_last_range.getMergedRange( o_this_range )
				
			#end if there is a last range
			
			if o_merged_range is not None:
				lo_new_range_list.remove( o_last_range )
				lo_new_range_list.append( o_merged_range )
				o_last_range=o_merged_range
			else:
				lo_new_range_list.append( o_this_range )
				o_last_range=o_this_range
			#end if	 we have a merged range, else
			#append this new range
		#end for each range

		return lo_new_range_list
	#end __merge_ranges
	
	def isInsideARange( self, i_value ):
		'''
		This def returns true if the argument integer is inside one
		of the ranges in our collection.  Note that a value that equals
		a min or max (end value) is considered inside the range.
		'''
		
		li_maxvals=list( self.__rangesbymax.keys() )
		
		li_maxvals.sort( reverse=True )
		
		i_num_ranges=len( li_maxvals )
		
		b_is_in_range=False
			
		for idx in range( i_num_ranges ):
			
			i_this_max=li_maxvals[idx]
			
			if i_this_max  <  i_value:
				break
			#end if our value is out of range, or we've found a range 
			#that incluces our value
			
			o_range=self.__rangesbymax[ i_this_max ]
				
			if o_range.isInRange( i_value ):
				b_is_in_range=True
				break
			#end if the value is inside this range	
			
		#end for each max_value (i.e. also, we assume, the number of ranges )
	
		return b_is_in_range
	
	#end def isInsideARange
	
	def allRangesAreInsideCurrentCycleSettings( self, 
											i_current_min_cycle, 
											i_current_max_cycle ):
		b_return_value=True
		
		o_cycle_settings_as_range=IntRange( i_current_min_cycle, 
												i_current_max_cycle )
		
		if self.__ranges is not None:
			for o_range in self.__ranges:
				if not o_range.amEncompassedByRange( o_cycle_settings_as_range ):
					b_return_value=False
					break
				#end if not inside the cycle range, we know
				#we have a range outside the passed min/max args
			#end for each range
		#end if we have at least one range
		
		return b_return_value
	#end def allRangesAreInsideCurrentCycleSettings
		
#end class CycleRanges

class IntRangeParser( object ):
	'''
	This class creates one or more IntRange object(s)
	from the string arg passed into __init__.
	
	Note that, to accomodate using negative ints
	in our ranges, we use a tilde instead of a 
	hyphen for the min-max separator.  For use 
	in our simupop GUI, however, as of now (20190120)
	we assume no negative cycle numbers, we ask users for
	hyphen-delimited ints, in which case require the
	client of this class to set the b_using_hyphen
	flag in the __init__ call to True.
	
	'''
	
	CYCLE_MINMAX_DELIMITER="~"
	CYCLE_INTERVAL_DELIMITER=":"
	
	def __init__( self, s_range_string, b_using_hyphen_as_delimiter=False ):
		self.__intrange_objects=[]
		self.__use_hyphen=b_using_hyphen_as_delimiter
		self.__parse_range_string( s_range_string )
		return 
	#end __init__
	
	def __make_range_from_one_term( self, s_term ):
		'''
		When the range string is one item only it must
		be an integer i, from which we make a single range
		of i through i.
		'''
		i_single_int=None
		try:
			i_single_int=int( s_term )
		except ValueError as ove:
			s_msg="In IntRangeParser instance, "  \
					+ "def __make_range_from_one_term, " \
					+ "could not convert range string item " \
					+ "into an integer: " \
					+ s_term
			raise Exception(s_msg)	
		#end try...except	
	
		self.__intrange_objects.append( \
				IntRange(i_single_int, i_single_int ) )
			
		return 
	#end __make_range_from_one_term
	
	def __make_range_from_two_terms( self, ls_terms ):
		'''
		This def checks for the interval delimiter ";"
		in the second of the two terms expected in arg
		ls_terms, and if found, calls a def to handle
		making ranges accordingly.  Otherwide it makes
		a range from terms i and j, i-j.
		'''
	
		s_err_msg="In IntRangeParser instance, "  \
					+ "def __make_range_from_two_terms " \
					+ "could not parse integers.  "
				
		i_this_min=None
		i_this_max=None
				
		if IntRangeParser.CYCLE_INTERVAL_DELIMITER in ls_terms[1]:
			self.__make_ranges_using_interval( ls_terms )
		else:
			try:
				i_this_min=int( ls_terms[ 0 ] )
				i_this_max=int( ls_terms[ 1 ] )
			except IndexError as oie:
				s_msg=s_err_msg \
					+ "index error thrown parsing terms: " \
					+ str( ls_terms )
				raise Exception( s_msg )
			except ValueError as ove:
				s_msg=s_err_msg \
						+ "value error thrown, parsing terms: " \
						+ str( ls_terms )
				raise Exception( s_msg )
			#end try ... except
			
			self.__intrange_objects.append( \
					IntRange( i_this_min, i_this_max ) )
		#end if there is an interval term, else make single range
		return 
	#end __make_range_from_two_terms
	
	def __make_ranges_using_interval( self, ls_terms ):
		
		'''
		Arg ls_terms is expected to be 2 strings of
		form [ i, j:k ], to be parsed range terms where
		the range i-j is to be broken up into
		i, i+k, i+2k, i+3k...q, where q <= j-i
		'''
	
		s_err_msg_prefix="In IntRangeParser instance, " \
							+ "def __make_ranges_using_interval, " \
							
		
		
		i_min=None
		i_max=None
		i_interval=None
		
		ls_max_and_interval=ls_terms[1].split( \
					IntRangeParser.CYCLE_INTERVAL_DELIMITER )
		
		if len( ls_max_and_interval ) != 2:
			s_err_msg= s_err_msg_prefix \
					+ "the second range term should be " \
					+ "two integers separated by a " \
					+ IntRangeParser.CYCLE_INTERVAL_DELIMITER \
					+ ", but found, " \
					+ str( ls_terms[ 1 ] )
			raise Exception( s_err_msg )
		
		try:
			
			
			i_min=int( ls_terms[0] )
			i_max=int( ls_max_and_interval[ 0 ] )
			i_interval=int( ls_max_and_interval[ 1 ] )
			
		except ValueError as ove:
			s_err_msg=s_err_msg_prefix \
					+ "could not convert all range terms to integer: " \
					+ "for min val: " + ls_terms[ 0 ] \
					+ "for max val: " + ls_max_and_interval[ 0 ] \
					+ "for interval: " + ls_max_and_interval[ 1 ] 
			raise Exception (s_err_msg )
		#end try
		
		'''
		This loop makes a 1-int range using the above min, max and interval.
		Note that we assume min<max and interval i <=  max-min.  Otherwise
		the range will simply return an empty interator and we will 
		add no ranges.
		'''
		i_range_count=0
		
		for idx in range( i_min, ( i_max + 1 ), i_interval ):
			
			self.__intrange_objects.append( IntRange( idx,idx ) )
			i_range_count += 1
			
		#end for each int in the range( i,j+1,k )
		
		if i_range_count==0:
			sys.stderr.write( "In IntRangeParser instance, " \
									+ "no ranges were produced " \
									+ "from range with min, " + str( i_min ) \
									+ "and max: " + str( i_max ) \
									+ "at interval: " + str( i_interval ) )
			
			
		return 
	#end __make_ranges_using_interval
	
	def __parse_range_string( self, s_range_string ):
		
		if self.__use_hyphen:
			s_range_string=s_range_string.replace( "-", IntRangeParser.CYCLE_MINMAX_DELIMITER )
		#end if client using hyphens, convert to our standard
		
		ls_minmax=s_range_string.split( IntRangeParser.CYCLE_MINMAX_DELIMITER )
		
		i_num_range_items=len( ls_minmax )
		
		if i_num_range_items == 1:
			self.__make_range_from_one_term( ls_minmax[0] )
		elif i_num_range_items == 2:
			self.__make_range_from_two_terms( ls_minmax )
		else:
			s_err_msg="In IntRangeParser instance, " \
					+ "def __parse_range_string, " \
					+ "range string splits into too " \
					+ "many items.  Range string: " \
					+ s_range_string
			raise Exception( s_err_msg )
		#end if 1 term, else if 2, else error
		return
	#end __parse_range_string
	
	@property
	def rangeobjects( self ):
		return self.__intrange_objects
	#end rangeobjects

#end class IntRangeParser

class IntRange( object ):
	
	def __init__( self, i_min_value, i_max_value ):
		
		self.validateMinMax( i_min_value, i_max_value )
		self.__min=i_min_value
		self.__max=i_max_value
		return
	#end init
	
	def validateMinMax( self, i_min_value, i_max_value ):
		
		s_err_msg=None
		
		s_err_msg_Prefix="In IntRange instance " \
							+ "def __init__, " \
							+ "invalid min and max args: "
						
		if i_min_value > i_max_value:
			s_err_msg="min value greater than max value"
		#end if min>max	
		
		if [ type( i_min_value ), type( i_max_value ) ] != [ int, int ]:
			s_err_msg="non-integer type for at least one of the min/max args" 
		#end if not both ints
		
		if s_err_msg is not None:
			raise Exception( s_err_msg )
		#end if error
		
		return 
	#end validateMinMax
	
	def isInRange( self, i_value ):
		
		b_return_value=False
		
		if i_value >= self.__min \
			and i_value <= self.__max:
			b_return_value=True
		#end if min <= val <= max
		
		return b_return_value
	
	#end isInRange
	
	def amEncompassedByRange( self, o_other_range ):
		b_return_value=False
		
		if self.__min >= o_other_range.rangemin \
				and self.__max <= o_other_range.rangemax:
			b_return_value=True
		#end if my min/max put me inside the other range
		
		return b_return_value
	#end amEncompassedByRange
	
	def rangesOverlap( self, o_another_range ):
		
		b_return_value=False
		if self.isInRange( o_another_range.rangemin ) \
				or self.isInRange( o_another_range.rangemax ):
			b_return_value=True
		elif o_another_range.isInRange( self.__min ) \
			or o_another_range.isInRange( self.__max ):
				b_return_value=True
		#end if either end of the other is in my range ... 
		#else if either end of my range in in the other's		
		
		return b_return_value
	#end rangesOverlap
	
	def getMergedRange( self, o_another_range ):
		'''
		This def returns None if the ranges don't overlap.
		'''
		o_merged_range=None
		i_new_min=None
		i_new_max=None
		
		if self.rangesOverlap( o_another_range ):
			
			if self.__min > o_another_range.rangemin:
				i_new_min=o_another_range.rangemin
			else:
				i_new_min=self.__min
			#end if the other range has a smaller min, else use mine	
			
			if self.__max < o_another_range.rangemax:
				i_new_max=o_another_range.rangemax
			else:
				i_new_max=self.__max
			#end if my max is smaller, else us mine	
			
			o_merged_range=IntRange( i_new_min, i_new_max )
		#end if ranges Overlap
		
		return o_merged_range
	#end getMergedRange
	
	def printRange( self ):
		print( "min: " + str( self.__min ) \
				+ ", max: " + str( self.__max ) )
	#end printRange	
	
	@property
	def rangemin( self ):
		return self.__min
	#end property rangemin
	
	@property
	def rangemax( self ):
		return self.__max
	#end property rangemin
	
#end class IntRange

class CycleRanges( object ):
	'''
	This class manages a series of i ranges 
	of integers extracted from a string 
	of the form m1-n1,m2-n2...m_i-n_i
	such that n_j>=m_j.  These are used
	by the PGOpSimuPop class to manage
	the writing of pop cycles only in specified
	ranges.
	
	This class uses the IntRange class, and,
	to build IntRanges from the range string,
	class IntRangeParser.  See the latter for
	details on string delimiters and the use
	of the hyphen vs a tilde when parsing individual
	ranges.
	'''

	
	CYCLE_RANGE_DELIMITER=","
	
	def __init__( self, s_range_string=None, b_using_hyphen=False ):
		'''
		When the client expects no negative ints, and is using
		the hyphen char only for separating min from max, this
		should be set via flag arg to True:
		'''
		self.__client_using_hyphens_for_minmax_delimiter=b_using_hyphen
		
		self.__ranges=None
		self.__rangesbymax=None
		self.__extract_ranges( s_range_string )
		return 
	#end __init__
	
	def __extract_ranges( self, s_range_string ):
		
		s_err_msg="In CycleRanges instance, " \
					+ "def __extract_ranges, " \
					+ "could not convert range " \
					+ "into 2 integers: " 
				
		lo_ranges=[ ]
		
		
		ls_ranges=s_range_string.split( CycleRanges.CYCLE_RANGE_DELIMITER )
		self.__rangesbymax={ };
		
		o_last_range=None
		
		for s_range in ls_ranges:
			#We pass along the flag that tells the parser 
			#whether to use the default (tilde) or a hyphen
			#to split min~max pairs (see class IntRangeParser).
			o_range_parser=IntRangeParser( s_range, 
					self.__client_using_hyphens_for_minmax_delimiter )
			
			'''
			Note that clients can pass range strings that are one of:
			1. a single int i, producing 1 range object of size 1.
			2. two ints i-j, producing 1 range object
			3. three ints i-j;k, which may produce many range objects
			(see class IntRangeParser).
			'''
			for o_this_range in o_range_parser.rangeobjects:
				lo_ranges.append( o_this_range )
			#end for each range parsed
		#end for each range

		#Refine the list by merging any overlapping pairs:
		lo_ranges=self.__merge_ranges( lo_ranges )
		
		for o_range in lo_ranges:
			self.__rangesbymax[ o_range.rangemax ] = o_range
		#end for each range, key it to the max value	
		
		self.__ranges=lo_ranges
		
		return 
	#end extract_ranges
	
	def __merge_ranges( self, lo_ranges ):
		
		o_last_range=None
		
		lo_new_range_list=[]
		
		lo_ranges.sort( key=lambda x : x.rangemin )
		
		for o_this_range in lo_ranges:
		
			o_merged_range=None
			
			if o_last_range is not None:
				'''
				Note:  getMergedRange returns None if the ranges 
				do not overlap
				'''
				o_merged_range=o_last_range.getMergedRange( o_this_range )
				
			#end if there is a last range
			
			if o_merged_range is not None:
				lo_new_range_list.remove( o_last_range )
				lo_new_range_list.append( o_merged_range )
				o_last_range=o_merged_range
			else:
				lo_new_range_list.append( o_this_range )
				o_last_range=o_this_range
			#end if	 we have a merged range, else
			#append this new range
		#end for each range

		return lo_new_range_list
	#end __merge_ranges
	
	def isInsideARange( self, i_value ):
		'''
		This def returns true if the argument integer is inside one
		of the ranges in our collection.  Note that a value that equals
		a min or max (end value) is considered inside the range.
		'''
		
		li_maxvals=list( self.__rangesbymax.keys() )
		
		li_maxvals.sort( reverse=True )
		
		i_num_ranges=len( li_maxvals )
		
		b_is_in_range=False
			
		for idx in range( i_num_ranges ):
			
			i_this_max=li_maxvals[idx]
			
			if i_this_max  <  i_value:
				break
			#end if our value is out of range, or we've found a range 
			#that incluces our value
			
			o_range=self.__rangesbymax[ i_this_max ]
				
			if o_range.isInRange( i_value ):
				b_is_in_range=True
				break
			#end if the value is inside this range	
			
		#end for each max_value (i.e. also, we assume, the number of ranges )
	
		return b_is_in_range
	
	#end def isInsideARange
	
	def allRangesAreInsideCurrentCycleSettings( self, 
											i_current_min_cycle, 
											i_current_max_cycle ):
		b_return_value=True
		
		o_cycle_settings_as_range=IntRange( i_current_min_cycle, 
												i_current_max_cycle )
		
		if self.__ranges is not None:
			for o_range in self.__ranges:
				if not o_range.amEncompassedByRange( o_cycle_settings_as_range ):
					b_return_value=False
					break
				#end if not inside the cycle range, we know
				#we have a range outside the passed min/max args
			#end for each range
		#end if we have at least one range
		
		return b_return_value
	#end def allRangesAreInsideCurrentCycleSettings
		
#end class CycleRanges

class IntRangeParser( object ):
	'''
	This class creates one or more IntRange object(s)
	from the string arg passed into __init__.
	
	Note that, to accomodate using negative ints
	in our ranges, we use a tilde instead of a 
	hyphen for the min-max separator.  For use 
	in our simupop GUI, however, as of now (20190120)
	we assume no negative cycle numbers, we ask users for
	hyphen-delimited ints, in which case require the
	client of this class to set the b_using_hyphen
	flag in the __init__ call to True.
	
	'''
	
	CYCLE_MINMAX_DELIMITER="~"
	CYCLE_INTERVAL_DELIMITER=":"
	
	def __init__( self, s_range_string, b_using_hyphen_as_delimiter=False ):
		self.__intrange_objects=[]
		self.__use_hyphen=b_using_hyphen_as_delimiter
		self.__parse_range_string( s_range_string )
		return 
	#end __init__
	
	def __make_range_from_one_term( self, s_term ):
		'''
		When the range string is one item only it must
		be an integer i, from which we make a single range
		of i through i.
		'''
		i_single_int=None
		try:
			i_single_int=int( s_term )
		except ValueError as ove:
			s_msg="In IntRangeParser instance, "  \
					+ "def __make_range_from_one_term, " \
					+ "could not convert range string item " \
					+ "into an integer: " \
					+ s_term
			raise Exception(s_msg)	
		#end try...except	
	
		self.__intrange_objects.append( \
				IntRange(i_single_int, i_single_int ) )
			
		return 
	#end __make_range_from_one_term
	
	def __make_range_from_two_terms( self, ls_terms ):
		'''
		This def checks for the interval delimiter ";"
		in the second of the two terms expected in arg
		ls_terms, and if found, calls a def to handle
		making ranges accordingly.  Otherwide it makes
		a range from terms i and j, i-j.
		'''
	
		s_err_msg="In IntRangeParser instance, "  \
					+ "def __make_range_from_two_terms " \
					+ "could not parse integers.  "
				
		i_this_min=None
		i_this_max=None
				
		if IntRangeParser.CYCLE_INTERVAL_DELIMITER in ls_terms[1]:
			self.__make_ranges_using_interval( ls_terms )
		else:
			try:
				i_this_min=int( ls_terms[ 0 ] )
				i_this_max=int( ls_terms[ 1 ] )
			except IndexError as oie:
				s_msg=s_err_msg \
					+ "index error thrown parsing terms: " \
					+ str( ls_terms )
				raise Exception( s_msg )
			except ValueError as ove:
				s_msg=s_err_msg \
						+ "value error thrown, parsing terms: " \
						+ str( ls_terms )
				raise Exception( s_msg )
			#end try ... except
			
			self.__intrange_objects.append( \
					IntRange( i_this_min, i_this_max ) )
		#end if there is an interval term, else make single range
		return 
	#end __make_range_from_two_terms
	
	def __make_ranges_using_interval( self, ls_terms ):
		
		'''
		Arg ls_terms is expected to be 2 strings of
		form [ i, j:k ], to be parsed range terms where
		the range i-j is to be broken up into
		i, i+k, i+2k, i+3k...q, where q <= j-i
		'''
	
		s_err_msg_prefix="In IntRangeParser instance, " \
							+ "def __make_ranges_using_interval, " \
							
		
		
		i_min=None
		i_max=None
		i_interval=None
		
		ls_max_and_interval=ls_terms[1].split( \
					IntRangeParser.CYCLE_INTERVAL_DELIMITER )
		
		if len( ls_max_and_interval ) != 2:
			s_err_msg= s_err_msg_prefix \
					+ "the second range term should be " \
					+ "two integers separated by a " \
					+ IntRangeParser.CYCLE_INTERVAL_DELIMITER \
					+ ", but found, " \
					+ str( ls_terms[ 1 ] )
			raise Exception( s_err_msg )
		
		try:
			
			
			i_min=int( ls_terms[0] )
			i_max=int( ls_max_and_interval[ 0 ] )
			i_interval=int( ls_max_and_interval[ 1 ] )
			
		except ValueError as ove:
			s_err_msg=s_err_msg_prefix \
					+ "could not convert all range terms to integer: " \
					+ "for min val: " + ls_terms[ 0 ] \
					+ "for max val: " + ls_max_and_interval[ 0 ] \
					+ "for interval: " + ls_max_and_interval[ 1 ] 
			raise Exception (s_err_msg )
		#end try
		
		'''
		This loop makes a 1-int range using the above min, max and interval.
		Note that we assume min<max and interval i <=  max-min.  Otherwise
		the range will simply return an empty interator and we will 
		add no ranges.
		'''
		i_range_count=0
		
		for idx in range( i_min, ( i_max + 1 ), i_interval ):
			
			self.__intrange_objects.append( IntRange( idx,idx ) )
			i_range_count += 1
			
		#end for each int in the range( i,j+1,k )
		
		if i_range_count==0:
			sys.stderr.write( "In IntRangeParser instance, " \
									+ "no ranges were produced " \
									+ "from range with min, " + str( i_min ) \
									+ "and max: " + str( i_max ) \
									+ "at interval: " + str( i_interval ) )
			
			
		return 
	#end __make_ranges_using_interval
	
	def __parse_range_string( self, s_range_string ):
		
		if self.__use_hyphen:
			s_range_string=s_range_string.replace( "-", IntRangeParser.CYCLE_MINMAX_DELIMITER )
		#end if client using hyphens, convert to our standard
		
		ls_minmax=s_range_string.split( IntRangeParser.CYCLE_MINMAX_DELIMITER )
		
		i_num_range_items=len( ls_minmax )
		
		if i_num_range_items == 1:
			self.__make_range_from_one_term( ls_minmax[0] )
		elif i_num_range_items == 2:
			self.__make_range_from_two_terms( ls_minmax )
		else:
			s_err_msg="In IntRangeParser instance, " \
					+ "def __parse_range_string, " \
					+ "range string splits into too " \
					+ "many items.  Range string: " \
					+ s_range_string
			raise Exception( s_err_msg )
		#end if 1 term, else if 2, else error
		return
	#end __parse_range_string
	
	@property
	def rangeobjects( self ):
		return self.__intrange_objects
	#end rangeobjects

#end class IntRangeParser

if __name__ == "__main__":
	
	mys="1-1,1-1,1-2,18-21, 10-20,100-100, 3-3"
	mys="1-20,1-1,1-2,18-21, 10-20,100-100, 3-3"
	mys="1-1,2-10,3-31"
	mys="1,2,4-10:2,199-210:3,3-11"

	o_mycrange=CycleRanges( mys, b_using_hyphen=True )
	
	print( "4 is in a range: " + str (o_mycrange.isInsideARange( 4) ) )
	print( "5 is in a range: " + str (o_mycrange.isInsideARange( 5) ) )
	print( "6 is in a range: " + str (o_mycrange.isInsideARange(  6) ) )
	print( "7 is in a range: " + str (o_mycrange.isInsideARange( 7) ) )
	print( "8 is in a range: " + str (o_mycrange.isInsideARange( 8) ) )
	print( "9 is in a range: " + str (o_mycrange.isInsideARange( 9) ) )
	print( "10 is in a range: " +  str( o_mycrange.isInsideARange( 10 ) ) )
	print( "1000000 is in a range: " +  str( o_mycrange.isInsideARange( 1000000 ) ) )
	print( "2 is in a range: " +  str( o_mycrange.isInsideARange( 2 ) ) )
	print( "199 is in a range: " +  str( o_mycrange.isInsideARange( 199 ) ) )
	print( "200 is in a range: " +  str( o_mycrange.isInsideARange( 200 ) ) )
	print( "201 is in a range: " +  str( o_mycrange.isInsideARange( 201 ) ) )
	print( "202 is in a range: " +  str( o_mycrange.isInsideARange( 202 ) ) )
	print( "203 is in a range: " +  str( o_mycrange.isInsideARange( 203 ) ) )
#	print( o_mycrange.isInsideARange( 3 ) )
#	print( o_mycrange.isInsideARange( 20 ) )
#	print( o_mycrange.isInsideARange( 101 ) )
#	print( o_mycrange.isInsideARange( -1 ) )
	print ( "ranges within cycles: " + str( o_mycrange.allRangesAreInsideCurrentCycleSettings( -101, 100) ) )

	pass
#end if main mod
