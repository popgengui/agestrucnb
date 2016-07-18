'''
Description
Class GenepopFileSampler instances operate on GenepopFileManager objects,
adding subsamples to the GenepopFileManager's subsample collections according,
to one of mulitple sampling schemes.  Class GenepopFileSampleParams give 
values used in sampling.
'''

__filename__ = "genepopfilesampler.py"
__date__ = "20160710"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"


#mod level helper defs and assignments:

TAG_DELIMITER="_"

SCHEME_PROPORTION="proportion"
SCHEME_REMOVAL="remove"

def make_subsample_tag( i_value, i_replicate_number, s_scheme ):
	if s_scheme==SCHEME_PROPORTION:
		s_val_initial="p"
	elif s_scheme==SCHEME_REMOVAL:
		s_val_initial="n"
	else:
		s_msg = "In genpopfilesampler.py, def make_subsample_tag, " \
								+ "unknown scheme: " + s_scheme + "."
		raise Exception( s_msg )
	#end if scheme proportion, else removal, else error

	return TAG_DELIMITER.join( [ s_val_initial, 
									str( i_value ), "r", 
									str( i_replicate_number ) ] )
#end make_subsample_tag

def get_sample_value_and_replicate_number_from_sample_tag( s_sample_tag, s_scheme ):
		
		ls_fields=s_sample_tag.split( TAG_DELIMITER )

		v_sample_value=None	
		if s_scheme==SCHEME_PROPORTION:
			v_sample_value=float( ls_fields[ 1 ] )
		elif s_scheme==SCHEME_REMOVAL:
			v_sample_value=int( ls_fields[ 1 ] )
		else:
			s_msg = "In genpopfilesampler.py, def get_sample_value_and_replicate_number_from_sample_tag, " \
								+ "unknown scheme: " + s_scheme + "."
			raise Exception( s_msg )
		#end if scheme is proportion, else removal, else error

		i_replicate_number=int( ls_fields[ 3 ] )

		return ( v_sample_value, i_replicate_number )
#end get_sample_value_and_replicate_number_from_sample_tag

class GenepopFileSampler( object ):
	'''
	Class GenepopFileSampler instances operate on GenepopFileManager objects,
	adding subsamples to the GenepopFileManager's subsample according to one of
	mulitple sampling schemes.  It's chief motivation is a need to enccapsulate 
	a session in which a large number of samples need to be taken from a single
	genepop file, according to one of various possible sampling schemes.
	'''


	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		self.__filemanager=o_genepopfilemanager
		self.__sampleparams=o_genepopfilesampleparams
		return
	#end __init__
	
	@property
	def filemanager( self ):
		return self.__filemanager
	#end property filemanager

	@property
	def sampleparams( self ):
		return self.__sampleparams
	#end property sampleparams

	def __doSample( self ):
		return
	#end __do_sampling

#end class GenepopFileSampler

class GenepopFileSampleParams( object ):
	'''
	Supporting objects for GenepopFileSampler instances,
	proving the sampling parameters.  For example, for 
	sampling by proportions, this object would provide
	a list of proportions of which each population is to 
	be sampled, and a number of replicates indicating how
	many samples to take at each proportion.  Further,
	These objects also supply a list of population numbers,
	from the range 1,2,3,...,N of the genepop files N
	populations
	'''
	def __init__( self, li_population_numbers, 
				s_population_subsample_name="population_numbers" ):
		'''
		Param li_populations is a list of integers,
		each of i of which refers to the ith population
		in the genepop file as represented by a 
		genepopfilemanager object
		'''
		self.__populationnumbers=li_population_numbers
		self.__populationsubsamplename=s_population_subsample_name
		return
	#end __init__

	@property
	def population_numbers( self ):
		return self.__populationnumbers
	#end populationnumbers

	@property
	def population_subsample_name( self ):
		return self.__populationsubsamplename
	#end populationsubsamplename

#end  class GenepopFileSampleParams

class GenepopFileSampleParamsProportion( GenepopFileSampleParams ):
	def __init__( self, li_population_numbers, 
			lf_proportions, 
			i_replicates, 
			s_population_subsample_name="population_numbers" ):

		'''
		param li_populations, list of ints, which pops to sample (see remarks, parant class )
		param lf_proportions, list of floats, each pop sampled at each of these proportions
		param i_replicates, one integer, each pop sampled at each proportion this many times
		GenepopFileSampleParams.__init__( self, li_populations )
		'''

		GenepopFileSampleParams.__init__(self, li_population_numbers=li_population_numbers, 
				s_population_subsample_name=s_population_subsample_name )
		self.__proportions=lf_proportions
		self.__replicates=i_replicates
		return
	#end __init__

	@property
	def proportions( self ):
		return self.__proportions
	#end property proportions
	
	@property
	def replicates( self ):
		return self.__replicates
	#end property replicates

#end class GenepopFileSampleParamsProportion

class GenepopFileSampleParamsRemoval( GenepopFileSampleParams ):

	'''
	Parameters for sampling scheme such that for each population
	we randomly remove N of the M individuals, removing all M where
	N>=M, repeating i_replicate times. 
	
	When the b_do_all_combos_when_n_equals_one flag in __init__ is
	set to True (the default), we treat N=1 differently, and 
	exhaust all possible removals -- i.e, in each pop_i 
	of size M_i, removing each N where N=1,2,3...M_i.
	'''

	def __init__( self, 
			li_population_numbers,
			li_n_to_remove,
			i_replicates,
			s_population_subsample_name="poplulation_numbers",
			b_do_all_combos_when_n_equals_one=True ):
		'''
		param li_population_numbers, list of ints, see parent class
		param li_n_to_remove, list of ints, indicating, for each pop, randomly 
			  remove n individuals
		param i_replicates, for each i_n, repeat i_replicates times
		param s_population_subsample_name, see parent class
		param b_do_all_combos_when_n_equals_one -- if true treat n=1 differently,
			  by repeating a remove-one-indiv for each indiv in each pop.
		'''

		GenepopFileSampleParams.__init__(self, 
					li_population_numbers=li_population_numbers, 
					s_population_subsample_name=s_population_subsample_name )

		self.__n_to_remove=li_n_to_remove
		self.__replicates=i_replicates
		self.__do_all_combos_when_n_equals_one=b_do_all_combos_when_n_equals_one
		return
	#end __init

	@property
	def n_to_remove( self ):
		return self.__n_to_remove
	#end property n_to_remove

	@property
	def replicates( self ):
		return self.__replicates
	#end property replicates

	@property
	def do_all_combos_when_n_equals_one( self ):
		return self.__do_all_combos_when_n_equals_one
	#end property do_all_combos_when_n_equals_one

#end class GenepopFileSampleParamsRemoval

class GenepopFileSamplerIndividualsByProportion( GenepopFileSampler ):
	'''
	GenepopFileManager object that samples the individuals in each population
	according one or more proportions (percentages).
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, o_genepopfilesampleparams )
		return
	#end __init __
	
	def doSample( self ):

		#as of Mon Jul 11 20:17:02 MDT 2016, for simplicity, the GenepopFileManager subsampling
		#defs that subsample individuals or loci, do so across all populations,
		#so that the subset of populations given by this objects member sampleparams property 
		#"population_numbers", will only be applied as a filter when writeGenePopFile (or printGenePopFile)
		#is applied to this objects GenepopFileManager object (self.filemanager ). The call
		#to the GenepopFileManager.writeGenePopFile, will need to include among its args the 
		#population subsample name ( assigned as the GenepopFileSampleParams object's
		#member "population_subsample_name") 

		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers, 
				s_subsample_tag=self.sampleparams.population_subsample_name )

		lf_proportions=self.sampleparams.proportions
		i_total_replicates=self.sampleparams.replicates

		for f_proportion in lf_proportions:
			for i_replicate_number in range( i_total_replicates ):
				
				#standardized subsample tag uses the proportion and the rep number:
				#note that the "." char delimiter will need to be replaced by a diff
				#char when using this tag to name input or output file names for
				#NeEstimator (which truncates filenames using pattern .* for some of 
				#its output files)
				s_subsampletag=make_subsample_tag(  f_proportion, i_replicate_number , SCHEME_PROPORTION )
				self.filemanager.subsampleIndividualsRandomlyByProportion( f_proportion, s_subsampletag ) 
					#end for each replicate number	
		#end for each proportion
		return
#end class GenepopFileSamplerIndividualsByProportion

class GenepopFileSamplerIndividualsByRemoval( GenepopFileSampler ):
	'''
	GenepopFileSampler object that samples individuals in each population
	according to an N-removal scheme, that is, by removing N individuals 
	randomly from the population, some M number of times, for some list of Ns
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, o_genepopfilesampleparams )
		return
	#end __init__

	def __do_remove_one( self ):

		'''
		if the member GenepopFileSampleParamsRemoval flag
		"b_do_all_combos_when_n_equals_one" is True,
		then this def gets called, which for each pop
		in the pop list, with M indiv, is subsampled
		M times, by turns leaving out the nth indiv for N
		in 1,2,3...M
		'''

		li_pop_numbers=self.sampleparams.population_numbers

		for i_pop_number in li_pop_numbers:
			i_tot_indiv=self.filemanager.getIndivCountForPop( i_pop_number ) 

			for i_indiv in range( 1, i_tot_indiv + 1 ):

				s_indiv_subsample_tag=make_subsample_tag( 1, i_indiv, SCHEME_REMOVAL )

				self.filemanager.subsampleIndividualsLeaveNthOutFromPop( i_indiv, 
																		i_pop_number,
																		s_indiv_subsample_tag )
			#end for each indiv, leave it out of sample
		#end for each pop number
		return
	#end __do_remove_one

	def doSample( self ):
		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers, 
				s_subsample_tag=self.sampleparams.population_subsample_name )
		
		li_n_values=self.sampleparams.n_to_remove
		i_replicate_total=self.sampleparams.replicates

		for i_n in li_n_values:
			if i_n == 1 \
					and self.sampleparams.do_all_combos_when_n_equals_one == True:
				self.__do_remove_one()
			else:
				for idx in range( i_replicate_total ):
					s_subsample_tag=make_subsample_tag( str( i_n ),  idx, SCHEME_REMOVAL )
					self.filemanager.subsampleIndividualsMinusRandomNFromEachPop( i_n, s_subsample_tag )
				#end for each replicate
			#end if n==1, else not
		#end for each n value

		return
	#end doSample
#end class GenepopFileSamplerByRemoval

if __name__ == "__main__":
	import sys
	import MyUtilities.misc_utilities as modut
	import genepopfilemanager as gpf	

	ls_args=[ "genepop file" ]

	s_usage=modut.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage
	
	s_genepopfile=sys.argv[ 1 ]
	
	o_gpmanager_proportion=gpf.GenepopFileManager( s_genepopfile )
	o_gpmanager_removal=gpf.GenepopFileManager( s_genepopfile )

	i_numpops=o_gpmanager_proportion.pop_total
	li_poplist=range( 1, i_numpops + 1 )

	#for proportional sampling
	s_popsamptag_proportions="sample_prop"
	lf_proportions= [ 0.01, 0.1, 0.2, 1.0 ]
	i_replicate_total=1

	#for removal sampling
	s_popsamptag_removal="remove_n"
	li_n_remove=[ 3,4,5,6,7  ]
	i_removal_replicate_total=3

	o_sampleparams_proportion=GenepopFileSampleParamsProportion( li_poplist, 
							lf_proportions, 
							i_replicate_total, 
							s_population_subsample_name=s_popsamptag_proportions )

	o_sampleparams_remove=GenepopFileSampleParamsRemoval( li_poplist,
															li_n_remove,
															i_removal_replicate_total,
															s_population_subsample_name=s_popsamptag_removal )

	o_sampler_proportion=GenepopFileSamplerIndividualsByProportion( o_gpmanager_proportion, o_sampleparams_proportion )
	o_sampler_proportion.doSample()

	o_sampler_removal=GenepopFileSamplerIndividualsByRemoval( o_gpmanager_removal, o_sampleparams_remove )
	o_sampler_removal.doSample()

	#now genepopfilemanager instances should contain the subsamples:
	ls_indiv_subsamplenames_proportions=o_gpmanager_proportion.indiv_subsample_tags
	ls_indiv_subsamplenames_removal=o_gpmanager_removal.indiv_subsample_tags

#	for o_sampler in [ o_sampler_proportion, o_sampler_removal ]:
	for o_sampler in [ o_sampler_removal ]:

		ls_indiv_subsamplenames=o_sampler.filemanager.indiv_subsample_tags

		s_pop_subsample_name=o_sampler.filemanager.population_subsample_tags[ 0 ]

		for s_indiv_sub in ls_indiv_subsamplenames:

			li_empty_pops=o_sampler.filemanager.getListEmptyPopulationNumbers( 
					s_pop_subsample_tag=s_pop_subsample_name,
					s_indiv_subsample_tag=s_indiv_sub  )

			if len( li_empty_pops ) == len( li_poplist ):
				print( "all pops emtpy for subsample: " + s_indiv_sub )
			#end if all emtpy

			s_filename=".".join( [ "test",s_pop_subsample_name, s_indiv_sub , "gp" ] )

			o_sampler.filemanager.writeGenePopFile( s_newfilename=s_filename,
					s_pop_subsample_tag = s_pop_subsample_name,
					s_indiv_subsample_tag=s_indiv_sub, 
					i_min_pop_size=1 )

		#end for each indiv sample
	#end for each sampler
#end if main

