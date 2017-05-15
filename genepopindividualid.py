'''
Description
Classes representing genepop individual ID
entries, the fields (maybe just an integer,
or maybe many fields like age, parent numbers,
etc as delimited in the individual ID.
'''
from __future__ import print_function
from builtins import range
from builtins import object
__filename__ = "genepopindividualid.py"
__date__ = "20160831"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class GenepopIndivIdAgeStructure( object ):
	'''
	Wraps the individual ID's as found in genepop
	files as output by objects of class PGOutputSimuPop
	'''
	DELIMITER_FIELDS=";"
	IDX_ID=0
	IDX_SEX=1
	IDX_FATHER=2
	IDX_MOTHER=3
	IDX_AGE=4

	TOTAL_FIELDS=5

	def __init__( self, s_id ):
		
		self.__get_Fields( s_id )
	#end __init__

	def __get_fields( self, s_id ):

		s_errmsg="In GenepopIndivIdAgeStructure instance, " \
							+ "def __get_fields, found Errors:\n"
						
		i_total_errors=0


		ls_vals=s_id.split( GenepopIndivIdAgeStructure.DELIMITER )
		i_num_fields=len( ls_vals )
		if i_num_fields != GenepopIndivIdAgeStructure.TOTAL_FIELDS:
			s_errmsg+="expecting " \
						+ str( GenepopIndivIdAgeStructure.TOTAL_FIELDS ) \
						+ " fields, received " \
						+ str( i_num_fields ) \
						+ " fields.  The input string is: " \
						+ s_id + "."

			i_total_errors += 1
		else:
			try:
				s_field_val=ls_vals[ GenepopIndivIdAgeStructure.IDX_ID ]
				self.__id=float( s_field_val )
			except Exception as oex:
				s_errmsg+="Error converting id field with value, " \
								 + s_field_val \
								 + ".  Exception raised: " \
								 + str( oex ) + ".\n"			
				i_total_errors+=1
			#end try...except

			try:
				s_field_val=ls_vals[ GenepopIndivIdAgeStructure.IDX_SEX ]
				self.__sex=int( s_field_val )
			except Exception as oex:
				s_errmsg+="Error converting sex field with value, " \
								 + s_field_val \
								 + ".  Exception raised: " \
								 + str( oex ) + ".\n"			
				i_total_errors+=1
			#end try...except

			try:
				s_field_val=ls_vals[ GenepopIndivIdAgeStructure.IDX_FATHER ]
				self.__father=float( s_field_val )
			except Exception as oex:
				s_errmsg+="Error converting father field with value, " \
								 + s_field_val \
								 + ".  Exception raised: " \
								 + str( oex ) + ".\n"			
				i_total_errors+=1
			#end try...except

			try:
				s_field_val=ls_vals[ GenepopIndivIdAgeStructure.IDX_MOTHER ]
				self.__mother=float( s_field_val )
			except Exception as oex:
				s_errmsg+="Error converting mother field with value, " \
								 + s_field_val \
								 + ".  Exception raised: " \
								 + str( oex ) + ".\n"			
				i_total_errors+=1
			#end try...except

			try:
				s_field_val=ls_vals[ GenepopIndivIdAgeStructure.IDX_AGE ]
				self.__age=float( s_field_val )
			except Exception as oex:
				s_errmsg+="Error converting mother field with value, " \
								 + s_field_val + \
								 ".  Exception raised: " \
								 + str( oex ) + ".\n"			
				i_total_errors+=1
			#end try...except
		#end if incorrect field total, else try to get fields

		if i_total_errors > 0:
			raise Exception( s_errmsg )
		#end if at least one error

		return
	#end __get_fields
	pass
#end class GenepopIndivIdAgeStructure

class GenepopIndivIdFields( object ):

	def __init__( self, ls_field_names = [ "number" ], 
				lo_field_types=[ int ] ):

		self.__fieldcount=len( ls_field_names )

		#copy list items into new list
		#so we don't depend on immutable values
		#via reference:
		self.__fieldnames=[ s_field_name for \
					s_field_name in ls_field_names ]
		self.__fieldtypes=[ o_type for \
					o_type in lo_field_types ]

		i_typecount=len( self.__fieldtypes )

		if self.__fieldcount != i_typecount:
			s_msg="In GenepopIndivIdFields instance, def __init__, " \
					+ "number of field names: " + str( self.__fieldcount ) \
					+ ", not equal to number of types: " \
					+ str( i_typecount ) + "."
			raise Exception(  s_msg )
		#end if mismatch in totals
		return
	#end __init__

	@property
	def types( self ):
		return self.__fieldtypes
	#end types

	@property
	def names( self ):
		return self.__fieldnames 
	#end names

#end class GenepopIndivIdFields

class GenepopIndivIdVals( object ):
	def __init__( self, s_id, 
				o_genepop_indiv_fields,
				s_delimiter=";"  ):

		self.__id=s_id
		self.__delimiter=s_delimiter
		self.__fieldvaluesbyname={}
		self.__fields=o_genepop_indiv_fields
		self.__make_dict_field_vals_by_name()
		return
	#end __init__

	def __make_dict_field_vals_by_name( self ):

		ls_fields=self.__fields.names

		i_numfields=len( ls_fields )

		ls_values=self.__id.split( self.__delimiter )

		if len( ls_values ) != i_numfields:
			s_msg="In GenepopIndivIdVals instance, " \
					+ "number of values found in id: " \
					+ str( ls_values ) + ", " \
					+ "is not equal to the number of fields " \
					+ "given by the GenepopIndivIdFields member: " \
					+ str( i_numfields ) + ".  Field names: " \
					+ str( ls_fields ) + "."

			raise Exception( s_msg )
		#end if value count ne field count			

		for idx in range( i_numfields ):

			s_value=ls_values[ idx ]
			v_value_evaluated=None

			try: 

				if self.__fields.types[ idx ] == str:
					s_value="\"" + s_value + "\""
				#end if string add quotes for eval

				v_value_evaluated=eval ( s_value )
				
				if type( v_value_evaluated ) !=  self.__fields.types[ idx ]:
					s_msg="In GenepopIndivIdVals instance, " \
									+ " type mismatch in Id field: " \
									+ self.__fields.names[ idx ] + "." \
									+ "  Value from Id string: " + str( v_value_evaluated ) + "." \
									+ "  Field type as set in GenepopIndivIdFields object: " \
									+ str( self.__fields.types[ idx ] ) \
									+ ",  Type in id after eval: " + str( type( v_value_evaluated ) ) \
									+ "." 

					raise Exception ( s_msg )

				#end if type mismatch

			except Exception as oex:

					s_msg="In GenepopIndivIdVals instance, eval of id field value failed. " \
							+ "Value: " +  s_value + ".  Id Field: " \
							+ str( self.__fields.names[ idx ] ) \
							+ ".  Error raised:  " + str( oex ) + "." 
					raise Exception( s_msg )

			#end try . . . except . . .
			self.__fieldvaluesbyname[ self.__fields.names[ idx ] ] = v_value_evaluated
		#end for each item in values list
		return	
	#end __make_dict_field_vals_by_name

	def getVal( self, s_name ):
		return self.__fieldvaluesbyname[ s_name ] 
	#end getVal

	@property
	def fieldnames( self ):
		return self.__fields.names
	#end fieldnames

#end class GenepopIndivIdVals

class GenepopIndivCriterion( object ):
	'''
	Class wraps a boolean test of one or more field
	in a genepop file individual id.  Instances
	of this class are members of a dictionary that
	is used by class GenepopIndivCriteria, so that
	a client can test the id against an number of
	such criteria.
	'''

	FIELD_DELIMITER_FOR_TEST_EXPRESSION="%"

	def make_test_variable( s_field_name ):

		return GenepopIndivCriterion.FIELD_DELIMITER_FOR_TEST_EXPRESSION \
				+ s_field_name \
				+ GenepopIndivCriterion.FIELD_DELIMITER_FOR_TEST_EXPRESSION
	#end make_test_variable

	def __init__( self, s_criterion_name, 
							ls_field_names,
							s_test_expression ):
		'''
		param s_criterion_name, string giving a name for the
			criterion.  This name will be used by objects of
			class GenepopIndividualId as keys to a dictionary
			of instances of this class.
		param s_field_names, list of strings, the ID field names to which the criteria
			is being applied.  These string should be present, surroundedused in the
			test expression (see next param).
		param s_test_expression, string.  When evaluated, should generate
			True or False, as passing or failing the criterion's test.  The
			field name in this expression will be identified (field name surrounded
			by percent signs )and replaced by its value when
			this objects doTest() is called by the client, which passes the
			value in to the doTest def.  Example, if a field in the id stands
			for the individuals age, and is called "age", then the test expression might be, 
			"%age%==1".  When a client calls doTest, then, the "age" string will be replaced
			by the value, then eval will be called on the expression, and the boolean returned.
		'''

		self.__criterionname=s_criterion_name
		self.__fieldnames=[ s_name for s_name in ls_field_names ]
		self.__test=s_test_expression
		return
	#end __init__

	def doTest( self, lv_values ):
		'''
		See param definitions in __init__ for an example
		and explanation of how this def works

		We assume that the values are ordered in the arg list,
		such that each nth value corresponds to the nth fields
		in the list of field names.
		'''
		#make sure we have exactly one value for each field

		i_num_vals=len( lv_values )
		i_num_fieldnames=len( self.__fieldnames )

		if i_num_vals != i_num_fieldnames:
			s_msg="In GenepopIndivCriterion instance, def doTest, " \
						+ "number of values passed in as arg, " \
						+ str( i_num_vals ) + " does not equal " \
						+ "the number of field names, " \
						+ "for this criterion, " \
						+ str( i_num_fieldnames ) + "." \
						+ "Field name list: " + str( self.__fieldnames ) \
						+ ".  Value list: " + str( lv_values ) + "."
			raise Exception( s_msg )
		#end if num fields not equal num vals

		v_result=None

		ls_field_vars=[]
		lv_vetted_field_vals=[]

		#convert field names to their variable form
		#as used in the test:
		for s_field_name in self.__fieldnames:

			s_field_variable= \
					GenepopIndivCriterion.FIELD_DELIMITER_FOR_TEST_EXPRESSION \
					+ s_field_name \
					+ GenepopIndivCriterion.FIELD_DELIMITER_FOR_TEST_EXPRESSION

			#Make sure the test expression includes
			#the field name surrounded by quotes:
			if s_field_variable  not in self.__test:
				s_msg="In GenepopIndivCriterion instance, " \
						+ "test expression: " + self.__test \
						+ " does not contain the field-name string for substitution: " \
						+ s_field_name + "."
				raise Exception( s_msg )
			#end if sub string not present in test expression

			ls_field_vars.append( s_field_variable )

		#end for each field name
		
		#as required put string values in quotes:
		for v_value in lv_values:
			if type( v_value ) == str:
				v_value="\"" + v_value + "\""
			#end if value is a string, add quotes for eval

			lv_vetted_field_vals.append( v_value )
		#end for each value, check if quotes needed
	
		#we iterively replace the variables with their
		#values
		s_test_with_val=self.__test
	
		for idx in range( len( ls_field_vars ) ):

			s_field_variable=ls_field_vars[ idx ]
			v_vetted_field_val=lv_vetted_field_vals[ idx ]
			s_test_with_val=s_test_with_val.replace( s_field_variable, str( v_vetted_field_val ) )

		try:
			v_result=eval( s_test_with_val ) 	
		except Exception as oex:
			s_msg="In GenepopIndivCriterion instance, " \
					+ "eval of test failed.  Test: " \
					+ s_test_with_val \
					+ ".  Eval raised exception: " \
					+ str( oex ) + "."
			raise Exception ( s_msg )
		#end try...except

		if v_result not in [ True, False ]:
			s_msg = "In GenepopIndivCriterion instance, def doTest, " \
							+ "test returned non-boolean value: " + str( v_result ) \
							+ ".  Boolean value is required."
			raise Exception( s_msg )
		#end if v_result not boolean

		return v_result
	#end doTest

	@property
	def name( self ):
		return self.__criterionname
	#end criterion

	@name.setter
	def name( self, s_name ):
		self.__criterionname=s_name 
		return
	#end setter criterion

	@property
	def fields( self ):
		return 	[ s_name for s_name in self.__fieldnames ]
	#end def field

	@fields.setter
	def fields( self, ls_fieldnames ):
		self.__fields=[ s_name for s_name in ls_fieldnames ]
		return
	#end set fields
		
	@property
	def test( self ):
		return self.__test
	#end def test

	@test.setter
	def test( self, s_expression ):
		self.__test=s_expression 
		return
	#end setter test

#end class GenepopIndivCriterion

class GenepopIndivCriteria( object ):
	'''
	Wraps a list of GenepopIndivCriteria.
	Can evaluate all tests when a list of
	field names and values is provided.
	'''
	def __init__( self, lo_criteria=None ):

		#Assign empty list if no list passed,
		#else copy the references to each criterion
		#into a new list:
		self.__criteria=[] if lo_criteria is None \
						else [ o_crit for o_crit in lo_criteria ] 
		self.__criteriacount=None if lo_criteria is None else len( lo_criteria )
		return
	#end __init__

	def __get_dict_list_test_results( self, ls_field_names, lv_field_values ):
		'''
		Assumes field value list arg is in order such
		that its nth value is corresponds to the nth
		value in the list of field names.

		Assumes no two criteria in the dict of
		GenepopIndivCriterion instances have
		the same name.

		Assumes field names include at least
		any field name in any of the criterion objects
		(may contain more field names).
		'''

		db_test_results={}

		for o_criterion in self.__criteria:
			ls_fields_evaled=o_criterion.fields
			lv_vals_for_these_fields=[]
			for s_field in ls_fields_evaled:
				idx=ls_field_names.index( s_field )
				lv_vals_for_these_fields.append( \
						 lv_field_values[ idx ] )
			#end for each field
			db_test_results[ o_criterion.name ] = \
							o_criterion.doTest( lv_vals_for_these_fields )
		#end for each criterion, test
		return db_test_results
	#end __get_dict_list_test_results

	def allTestsAreTrue( self, ls_field_names, lv_field_values ):
		'''
		Assumes field value list arg is in order such
		that its nth value is corresponds to the nth
		value in the list of field names.
		'''
		db_test_results=self.__get_dict_list_test_results( ls_field_names, lv_field_values )


		'''
		If the client called this def on an instance
		with no criteria to test, raise an exception:
		'''
		if len( db_test_results ) == 0:
			s_msg="In GenepopIndivCriteria instance, " \
					+ "def allTestsAreTrue, " \
					+ "called on an instance with no " \
					+ "criterion objects for tests."
			raise Exception( s_msg )
		#end if no test results

		set_test_results=set( db_test_results.values() )
		return set_test_results=={True}

	#end allTestsAreTrue

	def getSubsetOfCriteriaAsNewCriteriaObject( self, li_criterion_indices ):
		'''
		Needed a way to use only one of the criterion objects in an instance of
		this class, to pass into a GenepopFileSampler operation, which requires 
		an Instance of this class.  I didn't want to import this mod into 
		genepopfilesampler.py, and so added this pseudo 'partial copy' operation.
		'''
		o_new_criteria_object=None
		lo_subset_of_criterion_objects=[]

		for idx in li_criterion_indices:
			if idx in range ( self.__criteriacount ):
				lo_subset_of_criterion_objects.append( self.__criteria[ idx ] )
			else:
				s_msg = "In GenepopIndivCriteria instance, " \
						+ "def getSubsetOfCriteriaAsNewCriteriaObject, " \
						+ "index passed is out of range for number of criterion objects." \
						+ "  Total criterion objects: " + str( self.__criteriacount ) \
						+ ".  List of indices passed: " + str( li_criterion_indices ) \
						+ "."

				raise Exception( s_msg )
			#end if idx in range, else exception
		#end for each index

		o_new_criteria_object=GenepopIndivCriteria( lo_subset_of_criterion_objects )
		
		return o_new_criteria_object
	#end def getSubsetOfCriteriaAsNewCriteriaObject


	def copy( self ):
		lo_criterion_copy=[ o_criterion for o_criterion in self._criteria ]
		o_copy=GenepopIndivCriteria( lo_criterion_copy )
		return o_copy
	#end copy

	def addCriterion( self, s_criterion_name, ls_field_names, s_test ):
		o_new_criterion = GenepopIndivCriterion( s_criterion_name,
													ls_field_names,
													s_test )
		
		self.__criteria.append( o_new_criterion )
		self.__criteriacount=len( self.__criteria )
		return
	#end addCriterion
	
	@property
	def criteriacount( self ):
		return self.__criteriacount
	#end criteriacount

	@property
	def criteria( self ):
		return self.__criteria
	#end poperty criteria
#end class GenepopIndivCritera

class GenepopIndividualId( object ):
	'''
	Wraps genepop indiv. ids as
	represented by member class instances
	of GenepopIndivIdFields and GenepopIndivCriteria
	'''

	def __init__( self,	
				o_genepop_indiv_vals,
				o_genepop_criteria=None ):

		self.__values=o_genepop_indiv_vals

		'''
		dictionary of genepopIndivCriterion objects
		by name
		'''
		self.__criteria=o_genepop_criteria
		self.__validate_id()
		return
	#end __init__

	def __validate_id( self ):
		return
	#end __validate_id

	def allCriteriaAreTrue( self ):
		'''
		Returns True if there are no
		criteria, otherwise the "and"
		operation of all criteria tests
		(see class GenepopIndivCriteria).
		'''
		b_result=True
		ls_field_names=self.__values.fieldnames
		lv_field_values=[]
		if self.__criteria is not None:
			for s_field in ls_field_names:				
				lv_field_values.append( \
						self.__values.getVal( s_field ) )
			#end for each field, get value
			
			b_result=self.__criteria.allTestsAreTrue( \
							ls_field_names, lv_field_values )
		#end if we have criteria to test

		return b_result
	#end allCriteriaAreTrue
#end class GenepopIndividualId

if __name__ == "__main__":
	myid="33;1;3;4;mystream"
	ls_fields=[ "num", "age", "p1", "p2", "location"  ]
	ls_types=[ int, int, int, int, str ]
	s_test_name="agetest"
	s_test_expression="%age% == 1"
	s_loc_test_expression="%location% == \"mystream\""

	o_idfields=GenepopIndivIdFields( \
			ls_fields, ls_types )

	o_age_criterion=GenepopIndivCriterion( "agetest", ["age"], s_test_expression )

	o_loc_crit=GenepopIndivCriterion( "loctest" , ["location"], s_loc_test_expression )

	o_criteria=GenepopIndivCriteria( [ o_age_criterion, o_loc_crit ] )

	o_idvals=GenepopIndivIdVals( myid, o_idfields )

	o_indiv=GenepopIndividualId( o_idvals, o_criteria )
	
	print( "all tests pass: " + str( o_indiv.allCriteriaAreTrue() ) )

#end if main

