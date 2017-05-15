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
import os

DELIM_TABLE="\t"
DELIM_REP_NUMS=","
INDEX_TABLE_INDIV_NAME=1
INDEX_TABLE_GP_FILE=0

#indicates how much output info to produce:
INDIV_ONLY=0
INDIV_AND_ALLELES=1

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


def get_dict_alleles_by_indiv_from_genepop_file( s_gp_file ):

	ds_alleles_by_indiv={}

	o_gp_file=open( s_gp_file, 'r' )

	#iterate past the header and loci entries:
	for s_line in o_gp_file:
		if s_line.lower().startswith( "pop" ):
			break
		#end if first pop line reached, break
	#end for each line

	#next line in iteration should be first indiv
	#first pop, but for simplicity, we
	#always check for a "pop" line:
	for s_line in o_gp_file:
		s_line_stripped=s_line.strip()
		if not( s_line_stripped.lower() == "pop" ):
			if "," not in s_line:
				raise Exception( "pop entry in " + s_gp_file \
						+ " found no comma seperator. Line: " \
						+ s_line )
			#end if no comma
			ls_indiv_and_alleles=s_line.strip().split( "," )
			s_indiv=ls_indiv_and_alleles[ 0 ].strip()
			s_alleles=ls_indiv_and_alleles[ 1 ].strip()

			#we replace the spaces between alleles with tabs
			#so that each (bi)allele can have its own col
			#if loaded in R or spreadsheet
			ds_alleles_by_indiv[ s_indiv  ] = s_alleles.replace( " ", "\t" )
		#end if line not "pop" then
	#end for each file line
	
	return ds_alleles_by_indiv

#end get_dict_alleles_by_indiv_from_genepop_file

def get_individuals( s_gp_file, s_table, s_proportion, s_replicate, i_output_type ):

	o_table=open( s_table,'r' )

	i_proportion_col_index=None
	
	i_line_count = 0

	ds_alleles_by_indiv=None

	if i_output_type==INDIV_AND_ALLELES:
		ds_alleles_by_indiv=get_dict_alleles_by_indiv_from_genepop_file( s_gp_file )
	#end if output is indiv and alleles	

	ls_individuals=[]

	for s_line in o_table:

		i_line_count+=1

		if i_line_count == 1:

			i_proportion_col_index = get_proportion_col_number( s_line, s_proportion )
		else:
			ds_non_rep_fields=get_non_rep_fields( s_line )

			#we want just the file name, so that it will
			#match the entry in the table:
			s_gp_file_no_path=os.path.basename( s_gp_file )
		
			if ds_non_rep_fields[ "gpfile" ] == s_gp_file_no_path:
				ls_reps_this_indiv=get_reps( s_line, i_proportion_col_index )
				if s_replicate in ls_reps_this_indiv:
					s_individual=ds_non_rep_fields[ "indiv" ] 
					ls_individuals.append( s_individual )
			#end if rep is in list
		#end if first line else not	
	#end for each line in file

	o_table.close()

	for s_individual in ls_individuals:

		if i_output_type==INDIV_AND_ALLELES:
			sys.stdout.write( s_individual + "\t" \
					+ ds_alleles_by_indiv[ s_individual ] + "\n" )
		elif i_output_type==INDIV_ONLY:
			sys.stdout.write( s_individual + "\n" )
		else:
			raise Exception( "in def get_individuals, unknown value for output type: " \
					+ str( i_output_type ) )
	#end for each individual

	return
#end get_individuals

if __name__ == "__main__":

	di_output_inclusions={ "indiv":INDIV_ONLY, "alleles":INDIV_AND_ALLELES }

	ls_args=[ "genepop file", "table file", 
			"proportion", "replicate number", 
			"\"indiv\" or \"alleles\" -- " \
			+ "output will list individuals only or individuals and their alleles (tab-delimited)" ] 
	
	s_usage=do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	s_gp_file=sys.argv[1]
	s_table=sys.argv[2]
	s_proportion=sys.argv[3]
	s_replicate_num=sys.argv[4]
	s_output_request=sys.argv[5]
	
	if s_output_request not in di_output_inclusions:
			raise Exception( "5th argument must one of "  \
					+ " or ".join( [ "\"" + skey + "\"" for skey \
					in list(di_output_inclusions.keys()) ] ) )
	else:
		i_output_type=di_output_inclusions[ s_output_request ]
	#end if 5th arg invalid else get vals

	get_individuals( s_gp_file, s_table, s_proportion, s_replicate_num, i_output_type )

#end if main

