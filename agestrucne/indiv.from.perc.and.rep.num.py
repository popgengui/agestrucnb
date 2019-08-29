'''
Description

Input:
	A table that has columns:
		1. genepop file (curretnly with a signel pop only)
		2. individual name in genepop file
		3. replicate number that includes the individual, at the lowest proportion subsampled
		4. if more proportions, then as above, at the next lowest proportion subsampled
		.
		.
		.
		n. if more proportions, then as above, at highest proportion subsampled
	
	A proportion between 0 and 1.0
	A preplicate number

Output:
	1 To standard out, individual names, one to a line, that are included in the 
	replicate at that proportion.

'''
from __future__ import print_function
from builtins import range
__filename__ = "indiv.from.perc.and.rep.num.py"
__date__ = "20160524"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"


import sys

DELIM_TABLE="\t"
DELIM_REP_NUMS=","
INDEX_TABLE_INDIV_NAME=1
INDEX_TABLE_GP_FILE=0

def do_usage_check( ls_this_argv, 
		ls_required_arg_descriptions, 
		ls_optional_arg_descriptions = [],
		b_multi_line_msg=False,
		b_unlimited_final_args=False,
		s_note=None):
	'''
	arg 1 expects sys.argv, or a copy
	arg 2 expects a list strings, in order, required args
	arg 3 expects a list of strings, in order, any optional args
	'''
	i_num_args_required = len( ls_required_arg_descriptions )
	i_num_args_optional = len( ls_optional_arg_descriptions )
	i_max_poss_num_args = i_num_args_required + i_num_args_optional 
	i_num_args_passed = len( ls_this_argv ) - 1  
	s_usage_string = ""
	s_arg_delimit=""
	if b_multi_line_msg == True:
		s_arg_delimit=OUTPUT_ENDLINE
	#end if we put each arg descript on a 
	#separate line of output

	if i_num_args_passed <  i_num_args_required  \
			or (i_num_args_passed > i_max_poss_num_args and b_unlimited_final_args == False ): 
	
		import os
		
		s_scriptname = os.path.basename( ls_this_argv[ 0 ] )	
		s_usage_string = "usage: " + s_scriptname 

		if b_multi_line_msg:
			s_usage_string="usage: " + s_scriptname \
					+ OUTPUT_ENDLINE + "args:" + OUTPUT_ENDLINE
		else:
			s_usage_string = "usage: " + s_scriptname 
		#end if multi line else not

		for s_arg in ls_required_arg_descriptions:

			s_usage_string += " <" \
				+ s_arg + ">" \
				+ s_arg_delimit
		#end for each requried arg

		for s_arg in ls_optional_arg_descriptions:

			s_usage_string += " <(optional) " \
				+ s_arg + ">" \
				+ s_arg_delimit
		#end for each required arg

	#end if number of args is out of range

	if s_usage_string != "" and s_note is not None:
		s_usage_string=s_usage_string + OUTPUT_ENDLINE + s_note
	#end if note 

	return  s_usage_string 
#def do_usage_check

def get_proportion_col_number( s_first_line_in_table, s_proportion ):
	'''
	returns the zero-based index of the column number
	that gives replicate number lists asssociated with
	the s_proportion

	returns None if the s_proportion has no match in the field names
	'''

	ls_first_line_in_table=s_first_line_in_table.strip().split( DELIM_TABLE )
	i_num_fields=len( ls_first_line_in_table )
	i_col_num=None

	#first 2 cols are filename and indiv name, so we search idx 2..end:
	for idx in range( 2, i_num_fields ):

		if ls_first_line_in_table[ idx ] == s_proportion:
			i_col_num=idx
			break
		#end if match
	#end

	if i_col_num is None:

		s_msg="Can't match given proportion " + s_proportion + "." \
				+ "Here are the proportions: " \
				+ ", ".join( ls_first_line_in_table[ 2: ] ) \
				+ "  Please match number of digits exactly."
			
		sys.stderr.write( s_msg + "\n" )
		sys.exit()
	#end if no match

	return i_col_num 

#end get_proportion_col_number

def get_reps( s_line, i_proportion_col_index ):

	ls_reps = None
	
	ls_vals=s_line.strip().split( DELIM_TABLE )
	
	s_reps = ls_vals[ i_proportion_col_index ]

	ls_reps=s_reps.split( DELIM_REP_NUMS )

	return ls_reps
#end get_reps

def get_non_rep_fields( s_line ):
	ls_vals=s_line.strip().split( DELIM_TABLE )
	return { "gpfile" : ls_vals[ INDEX_TABLE_GP_FILE ],
			"indiv" : ls_vals[ INDEX_TABLE_INDIV_NAME ] }
#end get_individual_name

def get_individuals( s_gp_file, s_table, s_proportion, s_replicate ):

	o_table=open( s_table,'r' )

	i_proportion_col_index=None
	
	i_line_count = 0

	ls_individuals=[]

	for s_line in o_table:

		i_line_count+=1

		if i_line_count == 1:

			i_proportion_col_index = get_proportion_col_number( s_line, s_proportion )
		else:
			ds_non_rep_fields=get_non_rep_fields( s_line )

		
			if ds_non_rep_fields[ "gpfile" ] == s_gp_file:
				ls_reps_this_indiv=get_reps( s_line, i_proportion_col_index )
				if s_replicate in ls_reps_this_indiv:
					s_individual=ds_non_rep_fields[ "indiv" ] 
					ls_individuals.append( s_individual )
			#end if rep is in list
		#end if first line else not	
	#end for each line in file

	o_table.close()

	for s_individual in ls_individuals:
		sys.stdout.write( s_individual + "\n" )
	#end for each individual

	return
#end get_individuals

if __name__ == "__main__":

	ls_args=[ "source genepop file name", "table file name", "proportion", "replicate number" ]
	
	s_usage=do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage
	s_gp_file=sys.argv[1]
	s_table=sys.argv[2]
	s_proportion=sys.argv[3]
	s_replicate_num=sys.argv[4]

	get_individuals(s_gp_file, s_table, s_proportion, s_replicate_num )
#end if main

