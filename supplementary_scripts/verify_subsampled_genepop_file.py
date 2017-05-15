'''
Description
Given an original genepop file, and one made 
by pgdrivenestimator with subsampling parameters,
check that the latter correctly associates
individual id's with correct loci.

We deliberately eschew using the genepopfilemanager.py
and related code, to make sure we don't introduce
bugs present in that code that needs to be revealed
in our tests, into our testing code.


Assumptions:
	1. genepop files use the 1-loci-name-per-line scheme (no comma-delimited loci list)
	2. genepop files use 1 line per individual entry (no entries inn which the 
		indivicuals allele list uses more than one line.
'''

__filename__ = "verify_subsampled_genepop_file.py"
__date__ = "20170506"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import argparse as ap
import sys
'''
In genepop files generated
by the negui.py simulation interface
we can extract the age values from
the individual ids:
'''
TOTAL_FIELDS_IN_SIM_ID=5
IDX_AGE_FIELD=4

class GP( object ):
	def __init__( self, s_file ):
		self.header=None
		self.pops=None
		self.locibyname=None
		self.locibynum=None
		self.popbyids=None
		self.dub_ids=None
		self.ages_totals_by_age=None

		self.__readin( s_file )
		return
	#end __init__

	def __get_age_from_id( self, s_id ):

		ls_fields=s_id.split( ";" )

		i_age=None

		if len( ls_fields )==TOTAL_FIELDS_IN_SIM_ID:
			try:
				f_age=float(ls_fields[ IDX_AGE_FIELD ] ) 
				i_age=int( f_age )
			except TypeError:
				i_age=None
			#end try
		#end if correct total for sim-generated id

		return i_age
	#end __get_age_from_id
	
	def __readin( self, s_file ):

		of=open( s_file )

		i_linenum=0
		i_popnum=0
		i_locinum=0

		self.locibyname={}
		self.locibynum={}
		self.popsbyid={}
		self.pops={}
		self.dup_ids=False
		self.ages_totals_by_age={}

		for s_line in of:
			i_linenum +=1
			if i_linenum==1:
				self.header=s_line.strip()
				continue
			#end if line 1

			s_line_stripped=s_line.strip() 

			if s_line_stripped == "pop":
				i_popnum+=1
				if i_popnum > 0:
					self.pops[ i_popnum ]={}
				#end if popnum
			elif i_popnum==0:
				i_locinum+=1
				self.locibyname[ s_line_stripped ] = i_locinum
				self.locibynum[ i_locinum ]=s_line_stripped
			else:
				ls_indiv_and_loci=s_line_stripped.split( "," )
				s_indiv=ls_indiv_and_loci[ 0 ]
				
				i_age=self.__get_age_from_id( s_indiv )

				if i_age is not None:
					if i_age in self.ages_totals_by_age:
						self.ages_totals_by_age[ i_age ] += 1
					else:
						self.ages_totals_by_age[ i_age ] = 1
					#end if age seen, else new age
				#end if age not none

				s_loci=ls_indiv_and_loci[ 1 ]
				#Remove leading space in the loci list:	
				s_loci=s_loci.strip()
				ls_loci=s_loci.split( " " )
				self.pops[ i_popnum ][ s_indiv ]=ls_loci

				if s_indiv in self.popsbyid:
					self.dup_ids=True
					self.popsbyid[ s_indiv ].append( s_id )
				else:
					self.popsbyid[ s_indiv ]=[ i_popnum ]
				#end if indiv in another pop, else new indiv
			#end if pop line else loci line else indiv
		#end for each ine
	#end __readin
		
#end class

def mymain( s_original_file, s_subsampled_file, li_pop_nums_in_orig ):

	o_orig=GP( s_original_file )
	o_sub=GP( s_subsampled_file )

	i_pop_count=0

	i_match_count=0
	i_miss_count=0
	li_orig_pop_numbers_matched=[]

	for i_pop in o_sub.pops:
		i_pop_count+=1
		i_current_pop_num=None
		for s_id in o_sub.pops[ i_pop ]:

			i_loci_count=0

			for s_alleles_in_sub in o_sub.pops[ i_pop ][ s_id ]:

				i_loci_count+=1

				s_loci_name=o_sub.locibynum[ i_loci_count ]

				i_loci_number_in_orig=o_orig.locibyname[ s_loci_name ] 

				if len( li_pop_nums_in_orig ) > 0:
					i_pop_number_in_orig=li_pop_nums_in_orig[ i_pop_count - 1 ]
				elif o_orig.dup_ids==False:
					i_pop_number_in_orig=o_orig.popsbyid[ s_id ] [ 0 ]
					#Make sure that in both files the individuals
					#are grouped within the same pop.
					if i_current_pop_num is None:
						i_current_pop_num=i_pop_number_in_orig
					elif i_current_pop_num != i_pop_number_in_orig:
						sys.stderr.write( "Error: pop number in original file changed for indiv ids  " \
												+ "within the same pop in the subsampled file.\n" )
				else:
					sys.stderr.write( "Error: the script was not passed a list of pop nums for " \
											+ "the origninal file, but can't get the pop " \
											+ "number from the subsammpled file, because "  \
											+ "some ids occur in more than one pop in the original file.\n" )
				#end if we have pop list, else use object attribute, else error
			
				if i_pop_number_in_orig not in li_orig_pop_numbers_matched:
					li_orig_pop_numbers_matched.append( i_pop_number_in_orig ) 
				#end if new pop number, add to list

				#Since the alleles are in a zero-indexed list, we subtract one 
				#from the loci number to get the correct alleles.
				s_alleles_in_orig=o_orig.pops[ i_pop_number_in_orig ][ s_id ][ i_loci_number_in_orig - 1 ]

				if s_alleles_in_sub != s_alleles_in_orig:
					i_miss_count += 1
				else:
					i_match_count += 1
				#end if alleles equal	
			#end for each alleles entry
		#for each indiv
	#for each pop	

	print( "indiv/allele/loci-num matches: " + str( i_match_count ) )
	print( "indiv/allele/loci-num misses: " + str( i_miss_count ) )
	print( "pop numbers in orig file matched: " + ",".join( [ str( i_pop ) for  i_pop in  li_orig_pop_numbers_matched  ] ) )

	if len( o_sub.ages_totals_by_age ) > 0:
		print( "{age: totals}: " + str( o_sub.ages_totals_by_age ) )
	#end if ages

	return
#end mymain

if __name__ == "__main__":
	
	LS_FLAGS_SHORT_REQUIRED=[ "-o",  "-s" , "-n" ]

	LS_FLAGS_LONG_REQUIRED=[ "--originalfile", "--subsampledfile", "--popnumlist" ]

	LS_ARGS_HELP_REQUIRED=[ "original genepop file", "subsampled genepop file", "list, comma-delimited ints, " \
									+ " i,j,k, such that i gives the pop number in the original " \
									+ "file of the first pop in the subsampled file, j gives the pop number " \
									+ "in the original file of the 2nd pop in the subsampled file, " 
									+ "and so on. If an empty string is passed , the script assumes "
									+ "that all individual ids in the genepop files are unique, "  \
									+ "so that pop numbers in the original file can be inferred from the " \
									+ "individual ids." ] 
	
	o_parser=ap.ArgumentParser()

	o_arglist=o_parser.add_argument_group( "args" )

	i_total_nonopt=len( LS_FLAGS_SHORT_REQUIRED )

	for idx in range( i_total_nonopt ):
		o_arglist.add_argument( \
				LS_FLAGS_SHORT_REQUIRED[ idx ],
				LS_FLAGS_LONG_REQUIRED[ idx ],
				help=LS_ARGS_HELP_REQUIRED[ idx ],
				required=True )
	#end for each required argument
	o_args=o_parser.parse_args()

	ls_args_passed={}

	for s_flag in LS_FLAGS_LONG_REQUIRED:
		s_argname=s_flag.replace( "--", "" )
		s_val=getattr( o_args, s_argname )
		ls_args_passed[ s_argname ] = s_val 
	#end for each arg flag

	s_list_arg=ls_args_passed[ "popnumlist" ]
	if s_list_arg== "":
		li_orig_pop_nums=[]
	else:
		li_orig_pop_nums=[ int( s_pop )  for s_pop in s_list_arg.split( "," ) ]
	#end if list of pop nums

	mymain( ls_args_passed[ "originalfile"] , ls_args_passed[ "subsampledfile" ], li_orig_pop_nums )
	pass
#end if main

