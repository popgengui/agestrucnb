'''
Description
2017_01_27

Class to give users an interface to get information about the loci
in a genepop file.

Motivation: calculate allele frequencies from a genpop file.  The
fastest implementation would be to add the program genepop to our
dependancies, but for now, that it's only use would be to caluclate
allele frequences, we've added allele counts to the info that the
GenepopFileManager can deliver. 

The class instances use a GenepopFileManager object, and, if
present in the object, any filters that have been pre-applied to
exclude pop sections, individuals within pop sections, and/or
loci, keyed to the object's member tags (see __init__).

'''
from __future__ import division
from builtins import object
from past.utils import old_div
__filename__ = "genepopfilelociinfo.py"
__date__ = "20170127"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class GenepopFileLociInfo( object ):

	def __init__( self, o_genepopfile, 
							s_population_subsample_tag=None,
							s_individual_subsample_tag=None,
							s_loci_subsample_tag=None ):

		'''
		param o_genepopfile, a GenepopFileManager object
		param s_population_subsample_tag, string giving the
		      tag for a subsampling of the pops (pop sections)
			  in the gnepop file managed by the GenepopFileManager
			  object. If None, all pop sections are included.
		param s_individual_subsample_tag, string giving the
		      tag for a subsampling of the individuals in the
			  included pops in the genepop file managed by the 
			  GenepopFileManager object. If None, all individuals
			  are included in each included pop section.
			  all pop sections are included.
		param s_individual_subsample_tag, string giving the
		      tag for a subsampling of the loci in the
			  included pops in the genepop file managed by the 
			  GenepopFileManager object. If None, all individuals
			  are included in each included pop section.
			  all pop sections are included.
		'''

		self.__genepop_file=o_genepopfile
		self.__pop_subsample=s_population_subsample_tag
		self.__indiv_subsample=s_individual_subsample_tag
		self.__loci_subsample=s_loci_subsample_tag
		
		return
	#end __init__

	def __get_allele_frequencies( self ):

		dddf_allele_frequencies={}

		dddf_allele_counts = self.__genepop_file.getAlleleCounts( \
													self.__pop_subsample,
													self.__indiv_subsample,
													self.__loci_subsample,
													b_skip_loci_with_parial_data=True )
		for i_pop_number in dddf_allele_counts:

			dddf_allele_frequencies[ i_pop_number ]={}

			for i_loci_number in dddf_allele_counts[ i_pop_number ]:
				di_allele_counts=dddf_allele_counts[ i_pop_number ] [ i_loci_number ]

				i_total_allele_instances=sum( di_allele_counts.values() )

				'''
				2017_07_12.  Revmoved the assert and exception when a loci has no 
				allieles (i.e. the entries are all-zeros for all individuals). We now
				simply skip the loci.
				'''
#				assert i_total_allele_instances != 0, "In GenepopFileLociInfo instance, " \
#											+ "def __get_allele_frequencies, " \
#											+ "for genepop file, " \
#											+ self.__genepop_file.original_file_name \
#											+ ", found zero alleles for pop number, " \
#											+ str( i_pop_number ) \
#											+ ", and loci number, " \
#											+ str( i_loci_number ) + "." 
				
				if i_total_allele_instances == 0:
					continue
				#end if no allele instances, skip this loci
			
				di_allele_freqs={}

				for i_this_allele in di_allele_counts:
					i_this_count=di_allele_counts[ i_this_allele ]
					f_this_freq=old_div(float( i_this_count ), float( i_total_allele_instances )) 
					di_allele_freqs[ i_this_allele ] = f_this_freq
				#end for each allele

				dddf_allele_frequencies[ i_pop_number ] [ i_loci_number ] = di_allele_freqs 

			#end for each loci
		#end for each pop

		return dddf_allele_frequencies
	#end __get_allele_frequencies

	def __get_heterozygosity( self):

		'''
		After Tiago's AgeStructureNe script "testHz.py"
		'''
		dddf_allele_frequencies=self.__get_allele_frequencies()
		ddf_heterozygosity_per_pop_per_loci={}

		for i_pop in dddf_allele_frequencies:
			ddf_heterozygosity_per_pop_per_loci[ i_pop ] = {}
			for i_loci in dddf_allele_frequencies[ i_pop ]:
				f_sum_squared_allele_freqs=0.0
				lf_frequencies=list( dddf_allele_frequencies[ i_pop ][ i_loci ].values() )
				for f_frequency in lf_frequencies:
					f_sum_squared_allele_freqs += f_frequency**2
				#end for each frequency
				ddf_heterozygosity_per_pop_per_loci[ i_pop ][ i_loci ] = \
															1.0 - f_sum_squared_allele_freqs
			#end for each loci
		#end for each pop

		return ddf_heterozygosity_per_pop_per_loci

	#end __get_heterozygosity

	def getAlleleFrequencies( self ):
		dddf_allele_frequencies=self.__get_allele_frequencies()
		return dddf_allele_frequencies
	#end getAlleleFrequencies

	def getHeterozygosity( self ):
		ddf_heterozygosity_per_pop_per_loci = \
							self.__get_heterozygosity()
		return ddf_heterozygosity_per_pop_per_loci
	#end getHeterozygosity

	@property
	def population_subsample_name( self ):
		return self.__pop_subsample
	#end property population_subsample_name

	@population_subsample_name.setter
	def population_subsample_name( self, s_name ):
		self.__pop_subsample=s_name
		return
	#end setter, population_subsample_name

	@property
	def individual_subsample_name( self ):
		return self.__indiv_subsample
	#end property individual_subsample_name

	@individual_subsample_name.setter
	def individual_subsample_name( self, s_name ):
		self.__indiv_subsample=s_name
		return
	#end setter, individual_subsample_name

	@property
	def loci_subsample_name( self ):
		return self.__loci_subsample
	#end property loci_subsample_name

	@loci_subsample_name.setter
	def loci_subsample_name( self, s_name ):
		self.__loci_subsample=s_name
		return
	#end setter, loci_subsample_name

#end class GenpopFileLociInfo

if __name__ == "__main__":
	pass
#end if main

