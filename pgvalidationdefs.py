'''
Description
'''
__filename__ = "pgvalidationdefs.py"
__date__ = "20170326"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False
VERY_VERBOSE=False


def validateNbAdjustment( s_adjustment, i_highest_cycle_number=1e20 ):
	'''
	2017_03_08. This def is created to handle the PGInputSimuPop
	parameter nbadjustment, which requires a more elaborate
	validation than do the others that can be validated using
	a simple boolean statement.
	We test the user's entry into the list of strings that give
	the cycle range and adjustment rate by creating an 
	NbAdjustmentRangeAndRate object, solely to test it using
	that objects validation code.  See the class description
	and code for NbAdjustmentRangeAndRate in module pgutilityclasses.

	2017_03_26.  This def was originally in the pgguisimupop.py class,
	but, as called there from KeyValueFrame objects via the ValueValidator
	object instances, a recursive set of validations sometimes occurred.
	This module is imported by the pgutilityclasses.ValueValidator class,
	so that def names can be passed as simple strings to the ValueValidator,
	and the latter object can test the string to see if it is defined and
	callable.  This means that the i_highest_cycle_number parameter is 
	currently not passed, since the value validator can  only pass a single
	value to its validation defs.  This is a difficult restriction to overcome,
	since we are trying to automate validation defs in the resources/*param.names
	entries, and need non-parametric calls and expressions.

	Note, too that the validation message "s_msg" below, that I am reatining,
	and that used to be raised when this was a def member of PGGuiSimuPop objects, 
	is currently not used.  This is again due to the restricted return values 
	required by ValueValidator's minimalist interface.

	'''

	b_return_val=True
	i_lowest_cycle_number=1

	s_msg="In mod pgvalidationdefs.py, def validateNbAdjustment, " \
						+ "there was an error in the range " \
						+ "and rate entry. The entry was: " \
						+ s_adjustment + ".  " \
						+ "\n\nThe correct format is min-max:rate, where " \
						+ "min is a starting cycle number, " \
						+ "max is an ending cycle number, " \
						+ "and rate is the proportion by which to " \
						+ "multiply Nb and the age/class individual counts " \
						+ "to be applied for each cycle in the range." 


	if VERY_VERBOSE:
		print( "--------------------" )
		print( "in pgguisimupop, validateNbAdjustment with value: "  + s_adjustment )
	#end very verbose 

	if  i_highest_cycle_number < i_lowest_cycle_number:

		if VERY_VERBOSE:
			print( "returning false on cycle number test" )
		#end if very verbose

		s_msg="In mod pgvalidationdefs.py, def validateNbAdjustment, " \
				"cannot validate cycle range:  current setting for " \
				+ "total generations is less than 1."

		b_return_val = False

	else:

		ls_adj_vals=s_adjustment.split( ":" )

		if len( ls_adj_vals ) != 2:
			b_return_val = False
		else:

			s_cycle_range=ls_adj_vals[ 0 ]

			ls_min_max=s_cycle_range.split( "-" )			

			if len( ls_min_max ) != 2:
				b_return_val = False

			else:

				try:
					i_min=int( ls_min_max[ 0 ] )

					i_max=int( ls_min_max[ 1 ] )

					f_rate=float( ls_adj_vals[ 1 ] )
					
					if i_min < 1 \
							or i_max > i_highest_cycle_number \
							or i_min > i_max:
						b_return_val = False
					#end if min-max invalid range

				except ValueError as ove:
					b_return_val = False
				#end try except

			#end if min-max list not 2 items
		#end if entry not colon-splittable into 2 items
	#end if no input, else if current input.gens < 1, else test entry

	return b_return_val
#end validateNbAdjustment






if __name__ == "__main__":
	pass
#end if main

