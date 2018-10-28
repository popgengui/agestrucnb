'''
Description
Implements abstract class AGPOperation for simuPop simulations,
as coded by Tiago Antao's sim.py modlule.  See class description.
'''
from __future__ import division
from __future__ import print_function
from builtins import range
from past.utils import old_div

__filename__ = "pgopsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False
VERY_VERBOSE=False
VERY_VERY_VERBOSE=False
PRINT_CULL_TOTALS=False

'''
2018_05_16. When set to True,
call simupops "dump(pop)"
in outputAge, for every cycle,
prints the default limited num
indiv = 100.
'''
DUMP_POPS=False

'''
2018_06_08. For testing we
want to aadd a def that computes LD
on a given number of loci pairs.
def __outputAge passes these
params to def __write_ld_on_sample:
'''
LD_WRITE_SAMPLE=False
LD_SAMPLE_LOCI_LINKED=True
LD_SAMPLE_LOCI_UNLINKED=True
LD_NUM_PAIRS=10000

'''
simuPOP offers these lD metrics (see
http://simupop.sourceforge.net/manual_svn/build/
userGuide_ch5_sec11.html):
'LD', 'LD_prime', 'R2', 'LD_ChiSq', 
'LD_ChiSq_p', 'CramerV',
'LD_prime_sp', 'LD_ChiSq_p_sp 
'''
LD_METHOD='R2'

#if empty and LD_WRITE_SAMPLE is true,
#outputAge will write LD sample for all
#cycles for which the pop is written
#to output
LD_CYCLES_LIST=[]

USE_GUI_MESSAGING=False

#if True, then invokes ncurses debugger
DO_PUDB=False

if DO_PUDB:
	from pudb import set_trace; set_trace()
#end if do pudb

import agestrucne.apgoperation as modop
import agestrucne.pgutilities as pgut

#for the lambda-ignore constant:
import agestrucne.pginputsimupop as pgin

#For the file names to use
#for recording age counts 
#and PWOP Nb estimnates:
import agestrucne.pgoutputsimupop as pgout

from simuOpt import simuOptions
simuOptions["Quiet"] = True
import simuPOP as sp
import sys
import random
import numpy
import copy
import os

'''
2018_07_05. We use the natsort "realsorted"
sort to sort the chromosomes as input by
a loci,chrom,position file, and delivered
to this module by the pgsimupoplociinfo 
object.  See the __createSinglePop def.
'''
import natsort

'''
2018_05_27. This new object manages extracting
the information from a loci table file that
lists loci_name, chromosome, and position. If
present, then this info will be used to intialize
the simulated genome. The module also provides
the constant given the string ("None") designating
no loci file is to be used.
'''
import agestrucne.pgsimupoplociinfo as pgsimloci
NO_LOCI_FILE=pgsimloci.NO_LOCI_FILE

'''
2018_06_06.  A central location to set
the precision to apply to the inititialization
of Microsat frequencies and, separately, SNP
frequencies, according to their 
respective initial mean heterozygosity values.
'''
MSAT_INIT_HET_PRECISION=0.001
'''
2018_07_11. Changed the call to pgutilities.py
def get_snp_allele_freqs_from_het_value_using_random_dist
so that it now expects a list of tolerances. This
was a response to a bug fix, showing that some of 
the SNP allele freq. sets that got through were actually
outside the 0.01, with trials showing that 0.02 would work
for the failing het values.
'''
SNP_HET_INIT_TOLERANCES=[ 0.01, 0.02 ]
'''
2018_07_09.  The call to pgutilities.py
def get_snp_allele_freqs_from_het_value_using_random_dist
(formerly called get_snp..."truncnorm_dist"), now
requries that the caller specifies a distribution.
'''
##### temp rem out:
'''
For testing allele frequency distributions,
I've created code to easily switch back to
the fixed-uniform method of deriving a single
allele_freqency using the quad roots, and 
a target het. 

2018_10_24. Moving back from fixed uniform
to truncnorm.
'''
SNP_ALLELE_FREQ_DISTRIBUTION="truncnorm"
#SNP_ALLELE_FREQ_DISTRIBUTION="fixed_uniform"


'''
2017_03_26. This mod-level def
to import and the pgguiutilities.PGGUI* classes and 
set a flag so that exeptions and other info during the
simulation will raise a message window, is needed because 
when I tried to make the import of the PGGUI* message
classed the default for this module, then an import
error was raised when I tried to start the main program
(negui.py).  There must be some recursive import problem.
Note that the import works when this module is imported
in a separate process (see pgutilities def 
"do_pgopsimupop_replicate_from_files" )

'''
class PGOpSimuPop( modop.APGOperation ):
	'''
	This class inherits its basic interface from class APGOperation, with its 3
	basic defs "prepareOp", "doOP", and "deliverResults"

	Its motivating role is to be a member object of a PGGuiApp object, and to contain the
	defs that do a simupop simulation and give results back to the gui.

	Should use no GUI classes, but strictly utils or pop-gen calls.

	This object has member two objects, an input object that fetches and prepares the
	data needed for the simuPop run, and an output object that formats and/or delivers
	the results.   These objects are exposed to users via getters.  The defs in these 
	member objects can thus be accessed by gui widgets when an object of this class  
	is used as a member of a PGGuiApp object

	The functionality in the name-mangled (self.__*) defs are from Tiago Anteo's sim.py module in 
	his AgeStructureNe project -- his mod-level variables simply assigned to self.
	'''

	INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS="numMSats"
	INPUT_ATTRIBUTE_NUMBER_OF_SNPS="numSNPs"
	DELIMITER_INDIV_ID=";"
	'''
	2017_02_13. For the restrictedGenerator, the maximum
	number of tries to obtain a pop with and Nb within tolerance
	of a target.
	2018_03_23.  We incrase the value from 100 to 10000.  Brian 
	reports success with some of the more difficult species/tolerance
	values with this allowance.
	
	2018_05_16.  We no longer use the mod-level
	value MAX_TRIES_AT_NB.  This param is now
	user selectable, is derived from the input
	object, and is set in this mod's
	def prepareOp
	'''
	#MAX_TRIES_AT_NB=10000

	'''
	2017_08_04.  New parameter the class object usess
	to determine which kind of output files are produced,
	the original set of 3 files *gen *sim *db, plus genepop,
	or just a genepop file.
	'''
	OUTPUT_ORIG=1
	OUTPUT_GENEPOP_ONLY=2

	HET_FILTER_ATTR_NAMES_IN_ORDER = [ "min_mean_heterozygosity", 
										"max_mean_heterozygosity",
										"total_filtered_pops_to_save" ]

	HET_FILTER_PARAM_TYPES_IN_ORDER= [ float, float, int ]

	POP_HET_FILTER_STRING_DELIM=","


	def __init__(self, o_input, o_output, b_compress_output=False, 
									b_remove_db_gen_sim_files=False,
									b_write_input_as_config_file=True,
									b_do_gui_messaging=False,
									b_write_the_once_only_files=False,
									b_is_replicate_1=False,
									i_output_mode=OUTPUT_GENEPOP_ONLY ):  

		'''
			o_input, a PGInputSimuPop object
			o_output, a PGOutputSimuPop object
			b_compress_output, if set to True
				will compress outputfiles using bz2
			b_remove_db_gen_sim_files, if set to True,
				will remove the output files with the
				indicated extensions.  This was added
				after some testing and noting that
				users most interested in using the genepop
				file output suffered from the many additional
				output files when trying to load genepop files
				for ne-estimation
			b_write_input_as_config_file, if set to false, will 
				skip the step in doOp that writes the current params
				to config file, via the input objects attributes 
				and defs. As for the above flag, this was added
				to prevent writing identical configuration files
				for replicate runs of the simulation, and thus
				reduce the number of output files. 
			b_do_gui_messaging.  This param was added 2017_03_26,
				to allow for message windows to pass exception and
				other info to gui users during the simulations,
				which are run in a python process separate from 
				that of the main program.  We could not leave the
				module-level GUI imports and USE_GUI_MESSAGING
				flag active by default, because the main gui 
				program negui.py throws an import error if this module,
				which is also used by the main interface,
				tries to import the PGGUI* classes.  
			b_write_the_once_only_files.  This param was added 20150407
				to allow the pgutilities.py def, 
				do_pgopsimupop_replicate_from_files , to produce
				the age counts and pwob nb values files only for
				the first replicate.
			b_is_replicate_1.  This param was added	2017_06_11 so that
				we can ignore sending a (blocking) gui info messaget
				about the lambda warning in non-first
				replicates (see warning in __createSinglePop).  This avoids
				the gui producing a series of blocking warning windows, one
				for each replicate, restating the warning.
				2018_04_01. Although we leave this parameter in the
				list, it is no longer needed since we changed
				the behavior of this class to no longer use GUI error
				messageing, to avoid blocking runs indef when use is
				not present to click on the error.
			i_output_mode.  This param was added 2017_08_04 to speed up
				the output and skip writing the *gen *db and *sim files used
				by Tiago in his original pipeline.  
		'''

		self.__guiinfo=None
		self.__guierr=None

		if b_do_gui_messaging:

			self.__activate_gui_messaging()

		#end if we are to use gui messaging

		super( PGOpSimuPop, self ).__init__( o_input, o_output )

		'''
		2017_05_20.  Checked the original sim.py code and its use 
		here and find that the lSizes variable is never accessed
		beyond it's items being incremented in __litterSkipGenerator,
		so that I'm removing it from its assignment here 
		"lSizes = [0, 0, 0, 0, 0, 0]"
		and its use in litterSkipGenerator: "lSizes[lSize] += 1".
		'''

		self.__reportOps = [ sp.Stat(popSize=True) ]
		self.__is_prepared=False
		self.__compress_output=b_compress_output
		self.__remove_db_gen_sim_files=b_remove_db_gen_sim_files
		self.__write_input_as_config_file=b_write_input_as_config_file
		self.__write_once_only_files=b_write_the_once_only_files
		self.__is_first_replicate=b_is_replicate_1
		
		'''
		2017_08_04.  In preperation for changing the 
		output to offer a mode that skips  writing the 
		*gen, *sim and *db files, and just write the genepop directly
		as pops are created.
		'''
		self.__output_mode=i_output_mode


		'''
		2017_08_05.  In preparation for implementing
		output het filtering,  These
		members will be used to get the range and total
		saved pops for a filter based on a pop's 
		heterozygosity.  See input param "het_filter"
		'''
		self.min_mean_heterozygosity=None
		self.max_mean_heterozygosity=None
		self.total_filtered_pops_to_save=None
		self.total_filtered_pops_saved=None

		#if this object is created in one of multiple
		#python so-called "Processes" objects from class
		#"multiprocessing", all pops in their separate "process"
		#will have identical individuals (same number/genotypes) 
		#unless we reseed the numpy random number generator 
		#for each "process:"
		numpy.random.seed()

		'''
		With introduction of the N0 as 
		calculated by other parameters,
		I chose to keep it unaltered in 
		the input object (see N0 property
		in the PGInputSimuPop class), and
		to accomodate lambda adustments,
		to use this attribute as the 
		N0 accessor in the simulation operations.
		We initiallize to the input object's value:
		'''
		self.__current_N0=self.input.N0

		'''
		2017_02_06, we add these attributes to implement,
		per recent meeting with Robin Waples, the 
		restrictedGenerator def to obtain generations
		whose Nb is within a tolerance of a target
		value.  These are set in
		the def createAge.
		'''
		self.__targetNb=None
		self.__toleranceNb=None
		PGOpSimuPop.VALUE_TO_IGNORE=99999

		DEFAULT_AGES=50

		self.__total_ages_for_age_file=DEFAULT_AGES \
										if self.input.ages is None \
												else self.input.ages
		
		self.__file_for_nb_records=None
		self.__file_for_age_counts=None

		'''
		2017_08_08. This file will be created
		when the het filter is applied,
		to record the cycle number and het value for the
		pops recorded in the output genepop file.	
		See def __set_het_filter_params for its creation. 
		'''
		self.__file_for_het_filter=None

		'''
		2018_02_18.  This flag will be setin def 
		outputAge, when a het filter is active and
		the min mean het is greater than the current
		pops' mean het. It will be tested at each evolve
		step in def __keep_collecting_filtered_pops.
		'''
		self.min_het_filter_greater_than_current_pop_het=False

		'''
		2018_04_01. The if block opening sim_nb_estimates and age_counts files if
		the flag to write  then is True, has been moved to def prepareOp, in order
		to now include the replicate number in their names (see the outbase is 
		tagged with a replicate number in def prepareOp)
		'''
#		if self.__write_once_only_files:
#			s_nb_values_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "sim_nb_estimates" ]
#			s_age_counts_file_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "age_counts" ]
#
#			self.__file_for_nb_records=open( self.output.basename + s_nb_values_ext, 'w' )
#			self.__file_for_age_counts=open( self.output.basename + s_age_counts_file_ext, 'w' )
#
#			s_header="\t".join( [ "generation" ] \
#						+ [ "age" + str( idx ) for idx \
#							in range( 1, self.__total_ages_for_age_file + 1 ) ] )
#
#			self.__file_for_age_counts.write( s_header + "\n" )
		#end if we are to write age counts and pwop nb values to file

		'''
		See the call to input.makePerCycleNbAdjustmentList in prepareOp.  This list 
		is used by def __harvest
		'''
		self.__nb_and_census_adjustment_by_cycle=None

		'''
		2018_03_13.  In the rare case of using a gamma distribution to assign
		fecundity in the __fitnessGenerator, and also use the Nb tolerance test,
		we need to change the way we assign generators in __createAge, such that
		if we have a target Nb, then we always call __restrictedGenerator, but we
		assign the following, according to the presense/absense of gamma values,
		assigning __fitnessGenerator in for former, __litterSkipGenerator in the
		latter:
		'''
		self.__generator_called_by_restricted_generator=None

		'''
		2018_04_01.  We add this member attribute to be assigned in
		def __restrictedGenerator, and used in def __outputAge, when
		the flag __write_once_only_files is True, to record
		the pwop Nb to file when (and only when) the pop is also being
		written.

		2018_04_17. Note that we have deleted the attribute 
		__current_pwop_nb_calc that would hold the pwop Nb value for 
		gens.  Because the order of  processing is, 
		Pop_i -> write_pop_to_file in def outputAge->
		reproduce_then_calc_pwop in def restrictedGenerator -> 
		cull in def __harvest producing ->	Pop_(i+1) -> write
		->etc, we can never record a pwop on Pop_0 in outputAge.
		'''

		'''
		2018_05_16. This is a new way to get the maximum number
		of tries to allow the __restrictedGenerator to add the
		pop, when its PWOP Nb calc is within tolerance.  This
		attribute comes from the new PGInputSimuPop attribute
		"tolerance_tries," which itself is a string value, so
		we set this as the int-coverted value, in prepareOp:
		'''
		self.__max_tries_at_tolerance=None

		'''
		2018_05_27. We have added a new parameter,
		locating a file that lists on each line a
		loci_name,chrom_name,position.  If given,
		we initialize the genome iwth these values.
		Otherwise we use the already present loci
		creation code. When a validated file name
		is present (see prepareOp), this object
		will be instantiated as a PGSimupopLociInfo
		object.

		'''
		self.__user_supplied_loci_info=None

		'''
		2018_07_27.  We add the ability to use
		user supplied SNP allele frequencies.
		In such a case the following member gets
		assigned a list of frequencies in order
		matching that of the loci order as assigned
		in __createSinglePop.  This list is then
		used in a new def that assigns them, analogous
		to the assignments in __createGenomeFromSNPAndMSatTotals,
		and __createGenomeFromLociFile
		'''
		self.__user_supplied_allele_frequencies=None
		
		
		return
	#end __init__

	def __activate_gui_messaging(self):

		'''
		2017_03_26. To be called only when the instance
		is in a new process, not that of the main program.

		These PGGUI* classes, if imported by this mod by
		default, cause an import error, possibly due to 
		recursive imports and/or TKinter threading conflicts.
		However, we can use these classes when this object is 
		run in a new python process -- see the creation of this
		object in pgparallelopmanager.py def 
		do_pgopsimupop_replicate_from_files.
		'''

		from agestrucne.pgguiutilities import PGGUIInfoMessage as guiinfo
		from agestrucne.pgguiutilities import PGGUIErrorMessage as guierr

		self.use_gui_messaging=True
		self.__guiinfo=guiinfo
		self.__guierr=guierr
		return

	#end if use gui messaging

	def __setup_genepop_file( self ):
		self.output.openGenepop()
		f_this_nbne=0.0
		if hasattr( self.input, "NbNe" ):
			f_this_nbne=self.input.NbNe
		#end if we have an NbNe value, use it.

		'''
		2018_05_28.
		We now get total depending on the 
		way the genome was intitialized:
		'''
		i_total_loci = None

		'''
		2018_07_03. In cases in which our loci
		were provided by a user supplied loci
		info file, we now pass a reference of
		the simupop pop object into the call
		to writeGenepopFileHeaderAndLociList,
		which has now been revised to get loci
		names from the pop object when a (non-None)
		reference to the population is passed to it.
		'''

		o_reference_to_pop=None

		if self.__user_supplied_loci_info is None:

			i_total_loci=self.input.numMSats + self.input.numSNPs
		else:
			i_total_loci=self.__user_supplied_loci_info.total_loci
			o_reference_to_pop=self.__pop
		#end if genome intitialized using totals, else user
		#supplied per-loci info.

		self.output.writeGenepopFileHeaderAndLociList( \
											self.output.genepop,
											i_total_loci,
											f_this_nbne,
											b_do_compress=False,
											o_simupop_population=o_reference_to_pop )
		return
	#end __setup_genepop_file

	def __set_het_filter_params( self ):

		mycl=PGOpSimuPop

		if self.input.het_filter is None:
			s_msg="In PGOpSimuPop instance, " \
						+ "def __set_het_filter_params, " \
						+ "there is not pop het filter string."
			raise Exception( s_msg )
		#end if no string

		i_num_fields_expected=len( mycl.HET_FILTER_ATTR_NAMES_IN_ORDER )
		ls_filter_params=self.input.het_filter.split( \
										mycl.POP_HET_FILTER_STRING_DELIM )
		i_num_param_values=len( ls_filter_params )

		if i_num_fields_expected != i_num_param_values:
			s_msg="In PGOpSimuPop instance, " \
					+ "def __set_het_filter_params, " \
					+ "the program expects " \
					+ str( i_num_fields_expected ) \
					+ "parameters for the heterozygosity " \
					+ "filter, but received " \
					+ str( i_num_param_values ) + "."
			raise Exception( s_msg )
		#end if values number other than expected 

		for idx in range(  len( ls_filter_params ) ):
			s_value=ls_filter_params[ idx ]
			v_value_typed=mycl.HET_FILTER_PARAM_TYPES_IN_ORDER[idx]( s_value )
			setattr( self, mycl.HET_FILTER_ATTR_NAMES_IN_ORDER[ idx ], v_value_typed )
		#end for each param

		#This file will record the cycle number and heterozygosity value
		#for each recorded pop:

		s_het_filter_info_file_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "het_filter_info" ]
		self.__file_for_het_filter=open( self.output.basename + s_het_filter_info_file_ext, 'w' )
		#counter used to compare to the last attribute
		#passed in the het filter string (total pops to save):
		self.total_filtered_pops_saved=0

		return
	#end __set_het_filter_params

	def prepareOp( self, s_tag_out="" ):
		
		try:
			'''
			2018_05_16. This new attribute, __max_tries_at_tolerance, 
			is provided by  the input object, which stores the value
			as a string, (because the main GUI uses a combobox to 
			limit the values available). Hence we must convert in order
			to use it in def __restrictedGenerator:
			'''
			self.__max_tries_at_tolerance=int( self.input.tolerance_tries )

			'''
			2017_03_08.  This call converts the list
			of cycle range and rate entries in the 
			list attribite nbadjustment into a list
			of per-cycle rate adjustments, used by
			this objects def __harvest.
			'''

			self.__nb_and_census_adjustment_by_cycle=self.input.makePerCycleNbAdjustmentList()




			'''
			2018_05_27.  We have added a new input parameter, loci_file_name, which
			if not the NO_LOCI_FILE value (i.e. "None"), then should be a file with
			lines that give 3 comma-delimited fields, loci_name, chromosome, position.
			Here we check whether a file name is present,  If present, we validate the file
			and set the flag that tells this def to use the __createGenomeFromLociFile 
			instead of the original def __createGenomeFromSNPAndMSatTotals.
			
			2018_06_04.  Bugfix, by adding the use_loci_file flag to the test as to whether 
			we should create a PGSimupopLociInfo object.  Note that after that object is 
			made, then the test as to whether we initialize a genome using a loci file 
			is to test that this PGOpSimuPop's attribute __user_supplied_loci_info is 
			not None.
			'''
			if self.input.use_loci_file==True \
					and ( self.input.loci_file_name.lower() != NO_LOCI_FILE.lower() ):
				'''
				This call will throw an exception if
				the file fails any of its validation
				tests:
				'''
				pgsimloci.PGSimupopLociInfoFileManager.validateFile( 
												self.input.loci_file_name )
				'''
				This object supplies the loc info in lists and a dict
				'''
				self.__user_supplied_loci_info=pgsimloci.PGSimupopLociInfo( \
														self.input.loci_file_name )
			#end if we are using a loci info file, validate it, and make a loci info object.

			self.__createSinglePop()

			if self.__user_supplied_loci_info is not None:
				'''
				2018_07_27. With the addition of an option to add
				per-loci allele frequencies to the user-supplied loci info file,
				we now intialize the genome differently, depending on whether
				or not the user-supplied file info includes allele frequencies. 
				Note that we know there are user-supplied loci if the
				new data member of this class __user_supplied_allele_frequencies,
				is non-None, as created and assigned in the def __createSinglePop
				'''
				if self.__user_supplied_allele_frequencies is None:
					self.__createGenomeFromUserSuppliedLociInfo()
				else:
					self.__createGenomeFromUserSuppliedLociInfoWithAlleleFrequencies()
				#end if no user-supplied allele frequencies, else use them
			else:
				self.__createGenomeFromSNPAndMSatTotals()
			#end if we are using a loci info file,
			#else no such file

			self.__createAge()	
			
			s_basename_without_replicate_number=self.output.basename	
			
			if VERY_VERBOSE==True:
				print( "resetting output basename with tag: " + s_tag_out )
			#end if VERY_VERBOSE

			self.output.basename=s_basename_without_replicate_number + s_tag_out

			'''
			2018_04_01.  This if block was moved here from the __init__ def,
			so that the sim_nb_estimates and age_counts file name will include
			the replicate number.  Formerly, because these files were meant only to be
			recorded on replicate 1, we put no replicate number in their names.  Now,
			in case we want to write these for each replicate, we want to name and 
			open them after having appended the replicate s_tag_out to the output file 
			base name.
			'''
			if self.__write_once_only_files:
				s_nb_values_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "sim_nb_estimates" ]
				s_age_counts_file_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "age_counts" ]

				self.__file_for_nb_records=open( self.output.basename + s_nb_values_ext, 'w' )
				self.__file_for_age_counts=open( self.output.basename + s_age_counts_file_ext, 'w' )

				s_header="\t".join( [ "generation" ] \
							+ [ "age" + str( idx ) for idx \
								in range( 1, self.__total_ages_for_age_file + 1 ) ] )

				self.__file_for_age_counts.write( s_header + "\n" )
			#end if we are to write age counts and pwop nb values to file


			if self.__output_mode == PGOpSimuPop.OUTPUT_ORIG:
				self.output.openOut()
				self.output.openErr()
				self.output.openMegaDB()
			elif self.__output_mode == PGOpSimuPop.OUTPUT_GENEPOP_ONLY:

				self.__setup_genepop_file()

				if self.input.do_het_filter == True:
					self.__set_het_filter_params()
				#end if het filter is to be applied

			elif self.__output_mode == PGOpSimuPop.OUTPUT_ORIG \
									and self.do_het_filter == True:
				s_msg="In PGOpSimuPop instance, " \
						+ "def prepareOp, " \
						+ "the output mode is for original output, " \
						+ "and the het filter flag is set to True.  " \
						+ "This is currently not an implemented output state."
				raise Exception( s_msg )
			else:
				s_msg="In PGOpSimuPop instance, " \
						+ "def prepareOp, " \
						+ "unknown value for output mode: " \
						+ str( self.__output_mode ) + "."
				raise Exception( s_msg )
			#end if orig out, else gp only, else error.

			'''
			2018_04_25. We write the new output file that LDNe2 will use
			to apply chromosome/loci associations.
			2018_04_27. We won't write the table if user has specified
			zero chromosomes (i.e. default, original scenario)
			2018_06_02. Add a test for a chrom loci file.  If we
			have one, we write the chrom loci table for LDNe2:
			'''
			if self.input.numChroms > 0 \
					or ( self.__user_supplied_loci_info is not None ):	
				self.__write_chromosome_loci_table( self.__pop )
			#end if user specified non-zero chromosome total, write table

			'''
			2017_02_07
			We are revising to try to use a targeted Nb, but instead of NbVar being a fixed int, 
			we want to use a float f, 0.0 <= f <= 1.0.  We want to warn users when we've loaded
			an NbVar from the original configuration files, that uses an integer, for the original
			tolerance test that simply took the abs(diff) between the calc'd Nb and the target 
			Nb - NbVar.  Thus some config files may load inappropriatly large NbVar values:

			2018_01_09
			This check and warning was moved from the pginputsimupop.py module, def get_config(),
			which was formerly issued on loading the param from a conf file, even though
			the actual value used in the simulation may be a revised value, one entered by 
			the user into the GUI, or revised as an optional arg to pgdrivesimupop.py.
			'''
			if self.input.NbVar > 1.0:
				s_msg="Warning:  in PGOpSimuPop instance, def prepareOp, " \
												+ "the Nb tolerance value looks high at " \
												+ str( self.input.NbVar ) + ".  " \
												+ "This will allow populations with " \
												+ "Nb values varying substantially " \
												+ "(i.e by at or more than the target Nb value)." 

				sys.stderr.write( s_msg + "\n" )
			# end if NbVar > 1

			self.__createSim()
			
			self.__is_prepared=True

		except Exception as oex:

			o_traceback=sys.exc_info()[ 2 ]
			s_err_info=pgut.get_traceback_info_about_offending_code( o_traceback )
			s_traceback_msg="In PGOpSimupop instance, an exception was raised with message: " \
							+ str( oex ) + "\nThe error origin info is:\n" + s_err_info

			if self.__guierr is not None:
				self.__guierr( None, str( oex ) + " " + s_traceback_msg )
			#end if using gui messaging

			raise Exception( "Exception message: " \
								+ str( oex ) \
								+ "Traceback: " \
								+ s_traceback_msg )
		#end try...except

		return
	#end prepareOp

	def doOp( self ):
		try:
			if self.__is_prepared:

				#if client has not indicated otherwise,
				#we write the current param set to
				#write the configutation file on which
				#this run is based:
				if self.__write_input_as_config_file:
					self.output.openConf()
					self.input.writeInputParamsToFileObject( self.output.conf ) 
					self.output.conf.close()
				#end if client wants this run to include
				#a configuration file (if many replicates,
				#this may be set to False for all but first)

				#now we do the sim

				self.__evolveSim()

				'''
				We close the ages and nb-values file object, if it exists.  This
				necessitated by python3, which otherwise produced emtpy files. Note
				that a None value will simply return false for the hasattr test.
				'''
				for v_this in [ self.__file_for_nb_records, self.__file_for_age_counts, self.__file_for_het_filter ]:
					if hasattr( v_this, "close" ):
						v_this.close()
					#end if a closable object, close it
				#for each of the test file attributes
				
				if self.__output_mode == PGOpSimuPop.OUTPUT_ORIG:
					self.output.out.close()
					self.output.err.close()
					self.output.megaDB.close()

					#note as of 2016_08_23, we don't compress the config file
					if self.__compress_output:
						s_conf_file=self.output.confname
						s_genepop_file=self.output.genepopname
						self.output.bz2CompressAllFiles( \
									ls_files_to_skip=[ s_genepop_file,  s_conf_file ] )
					#end if compress

					self.__write_genepop_file()

					if self.__remove_db_gen_sim_files:
						#note that this call removes both compressed
						#and uncompressed versions of these files
						#(see PGOutputSimuPop code and comments)
						for s_extension in [ "sim", "gen", "db" ]:
							self.output.removeOutputFileByExt( s_extension )
						#end for output files *sim, *gen, *db
					#end if we are to remove the non-genepop files (gen, sim, db)

				elif self.__output_mode == PGOpSimuPop.OUTPUT_GENEPOP_ONLY:

					self.output.genepop.close()

					if self.__compress_output:
						'''
						Note that when PGOpSimuPop is in genepop-only
						output mode, the *gen, *sim, *db files do
						not exist.  If called without excluding them
						the def bz2CompressAllFiles will throw an error.
						'''
						self.output.bz2CompressAllFiles( \
									ls_files_to_skip=[ self.output.genname,
														self.output.simname,
														self.output.dbname,
														self.output.confname ] )
					#end if compress
				#end if orig output mode, else genepop output mode
			else:
				raise Exception( "PGOpSimuPop object not prepared to operate (see def prepareOp)." )
			#end  if prepared, do op else exception
		except Exception as oex:
			o_traceback=sys.exc_info()[ 2 ]
			s_err_info=pgut.get_traceback_info_about_offending_code( o_traceback )
			s_msg="In PGOpSimupop instance, an exception was raised with message: " \
							+ str( oex ) + "\nThe error origin info is:\n" + s_err_info
			if self.__guierr is not None:
				self.__guierr( None, s_msg )
			#end if using gui messaging
			raise Exception( "Exception raised with message, " \
												+ str ( oex ) \
												+ "and traceback: " \
												+ s_msg )
		#end try...except

		return
	#end doOp

	def __write_genepop_file( self ):


		'''
		2018_07_30.
		With the addition of an option for users to supply loci information 
		in a file, we for now deprecate this def, which was created to leave
		open the option to output the pops in the original format used by
		Tiago Anteo in the AgeStructureNe code.  Because we have been, and
		expect all future users to, use the GENEPOP output, we'll disable
		this, instead of updating the way it fetches loci and loci totals:
		'''

		s_msg = "In PGOpSimuPop instance, def __write_genepopfile, " \
					+ "this def has been deprecated in favor of the " \
					+ "standard GENEPOP output format writer.  Please " \
					+ "set the pgopsimupop.py module __output_mode member " \
					+ "to its constant, mod-level value, \"OUTPUT_GENEPOP_ONLY\"" 
		
		raise Exception( s_msg )

#		if self.__output_mode == PGOpSimuPop.OUTPUT_ORIG:
#			i_num_msats=0
#			i_num_snps=0
#			
#			if hasattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS ):
#				i_num_msats=getattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS )
#			#end if input has num msats
#
#			if hasattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_SNPS ):
#				i_num_snps=getattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_SNPS )
#			#end if input has number of snps
#
#			i_total_loci=None 
#
#			if self.__user_supplied_loci_info is None
#
#				i_total_loci=i_num_msats+i_num_snps
#			else:
#				i_total_loci=self.__user_supplied_loci_info.total_loci
#			#####
#
#			if i_total_loci == 0:
#				s_msg= "In %s instance, cannot write genepop file.  MSats and SNPs total zero."  \
#						% type( self ).__name__ 
#				sys.stderr.write( s_msg + "\n" )
#			else:
#				#writes all loci values 
#				'''
#				2017_05_30.  To accomodate new module pgdrivesimulation.py, which
#				reads in a conf and does not require a life table, we default an
#				NbNe value to zero if the conf file does not supply it.  Note that
#				this parameter (Nb/Ne ratio) is not (currently) required for the 
#				simulation, but is passed along in the genepop file header to allow 
#				for an Nb bias adjustment as read-in and calculated by the 
#				pgdriveneestimator.py module.
#				'''
#				f_this_nbne=0.0
#
#				if hasattr( self.input, "NbNe" ):
#					f_this_nbne=self.input.NbNe
#				#end if we have an NbNe value, use it.
#
#				self.output.gen2Genepop( 1, 
#							i_total_loci, 
#							b_pop_per_gen=True,
#							b_do_compress=False,
#							f_nbne_ratio=f_this_nbne )
#			#end if no loci reported
#		else:
#			s_msg="In PGOpSimuPop instance, def __write_genepop_file, " \
#						+ "this def was called but he output mode was " \
#						+ "not for the original mode."
#			raise Exception( s_msg )
#		#end if output mode is orig else not
		return
	#end __write_genepop_file

	def deliverResults( self ):
		return
	#end deliverResults

	def __createGenomeFromUserSuppliedLociInfo( self ):

		'''
		This def is an alternative to __createGenomeFromSNPAndMSatTotals
		2018_05_27.  Currently we always create only
		biallelic SNPs from the user supplied loci.
		'''
		
		FLOAT_TOL=1e-32

		initOps = []
		preOps = []

		i_num_snps=self.__user_supplied_loci_info.total_loci

		i_snp_count=-1

		lf_random_freqs=None

		'''
		2018_06_13.  If user specifies 0.0 for SNP het initialization,
		we don't want to use the random distribution, but rather
		to simmply init all snps di-alleles at frequencies zero and 1.0:
		'''
		if abs( self.input.het_init_snp - 0.0 ) <= FLOAT_TOL:
			lf_random_freqs=[ 0.0 for idx in range( i_num_snps ) ]
		else:

			if SNP_ALLELE_FREQ_DISTRIBUTION=="fixed_uniform":
					f_allele_frequency= \
								pgut.get_allele_freq_from_quadratic_root_of_het_value( \
																	self.input.het_init_snp )
					lf_random_freqs=[ f_allele_frequency for idx in range( i_num_snps ) ]	
			else:

				'''
				2018_07_09. Revised the def in pgutilitities to allow caller to specify
				a distribution, so, for now, as we search for a better solution, we
				specity the truncnorm, which looks to have to narrow a distribution.
				'''
				lf_random_freqs=\
						pgut.get_snp_allele_freqs_from_het_value_using_random_dist( \
																f_this_het_value=self.input.het_init_snp,
																i_num_freqs=i_num_snps,
																lf_tolerances=SNP_HET_INIT_TOLERANCES,
																s_distribution=SNP_ALLELE_FREQ_DISTRIBUTION )
			#end fi uniform else use random distribution

		#end if user has set init snp freq to zero, else use distribution

		for f_random_freq in lf_random_freqs:		

			i_snp_count+=1

			initOps.append(
					sp.InitGenotype(
					#Position 0 is coded as 0, not good for genepop
					freq=[0.0, f_random_freq, 1 - f_random_freq ],
					loci=i_snp_count ))

		#end for each snp frequency, initialize a loci

		self.__genInitOps=initOps
		self.__genPreOps=preOps

		return
	#end __createGenomeFromUserSuppliedLociInfo

	'''
	2018_07_27
	This is a new method created when we added the option
	for users to supply allele frequencies when they have
	a loci/chrom/pos file.

	'''
	def __createGenomeFromUserSuppliedLociInfoWithAlleleFrequencies( self ):

		'''
		This def expects a list of floats assigned to member 
		self.__user_supplied_allele_frequencies, in the order
		such that the ith of the freqs corresponds to the ith
		loci as entered into the initializatioin in def __createSinglePop.
		'''
		

		initOps = []
		preOps = []

		i_num_snps=self.__user_supplied_loci_info.total_loci

		assert i_num_snps == len( self.__user_supplied_allele_frequencies )

		i_snp_count=-1
	
		
		for f_freq in self.__user_supplied_allele_frequencies:		

			i_snp_count+=1

			initOps.append(
					sp.InitGenotype(
					#Position 0 is coded as 0, not good for genepop
					freq=[0.0, f_freq, 1 - f_freq ],
					loci=i_snp_count ))

		#end for each snp frequency, initialize a loci

		self.__genInitOps=initOps
		self.__genPreOps=preOps


		return
	#end __createGenomeFromUserSuppliedLociInfoWithAlleleFrequencies

	'''
	2018_07_30.  We rename this def from __createGenome to
	__createGenomeFromSNPAndMSatTotals
	'''
	def __createGenomeFromSNPAndMSatTotals( self ):

		size = self.input.popSize
		numMSats = self.input.numMSats
		numSNPs = self.input.numSNPs

		maxAlleleN = 100

		FLOAT_TOL=1e-32

		#print "Mutation model is most probably not correct", numMSats, numSNPs
		loci = (numMSats + numSNPs) * [1]
		initOps = []
	
		'''
		2018_02_18.  We are adding a new parameter "het_init_msat",
		which allows the user to enter a value in (0.0,0.85]
		which will be used to compute a set of allele frequencies 
		totaling the value in startAlleles, and whose expected
		heterozygosity is within a tolerance (0.001 as of now)
		of the parameter.

		The new pgutilities def get_dirichlet_allele_dist_for_expected_het,
		uses a heuristic set of alpha values, applied according to the desired
		het value, to repeatedly try to extract a set of dirichlet distributed
		freqs that achieve the target het.
		'''

		for msat in range(numMSats):
			'''
			Old call to get dirichlet on 1.0 alpha now replaced by call
			to achieve an expected het:
			'''
			#diri = numpy.random.mtrand.dirichlet([1.0] * self.input.startAlleles)
			diri = pgut.get_dirichlet_allele_dist_for_expected_het( \
														self.input.het_init_msat,
														self.input.startAlleles,
														f_tolerance=MSAT_INIT_HET_PRECISION )

			'''
			Check added 2018_02_18, to make sure our heurisitic
			returned a set of allele freqs:
			'''
			if diri is None:
				s_msg="In PGOpSimuPop instance, def __createGenomeFromSNPAndMSatTotals, " \
							+ "The program did not produce a set of allele frequencies " \
							+ "for thecould"
				raise Exception( s_msg )
			#end if no


			if type(diri[0]) == float:
				diriList = diri
			else:
				diriList = list(diri)
			#end if type

			initOps.append(
					sp.InitGenotype(freq=[0.0] * ((maxAlleleN + 1 - 8) // 2) +
					diriList + [0.0] * ((maxAlleleN + 1 - 8) // 2),
					loci=msat))
		#end for msat

	
		if numSNPs > 0:
			'''
			2018_05_24. We now generate a list of allele frequencies 
			randomly drawn from a truncated ([0.0,1.0]) normal distribution
			with the mean set to the allele frequency given by our 
			intial snp expected heterozygosity value. See the pgutilities.py
			module, defs related to obtaining frequencies using the trunc 
			normal distribution.
			'''
			i_snp_count=-1

			lf_random_freqs=None

			'''
			2018_06_13.  We do not use the random number gen if the
			client wants an init het value of 0.0, but instead initialize
			all SNPs ad di-allele frequencies zero and 1.1
			'''
			if abs( self.input.het_init_snp - 0.0 ) <= FLOAT_TOL:
				lf_random_freqs=[ 0.0 for idx in range( self.input.numSNPs ) ]	
			else:

				if SNP_ALLELE_FREQ_DISTRIBUTION == "fixed_uniform":
					f_allele_frequency=\
							pgut.get_allele_freq_from_quadratic_root_of_het_value( \
																self.input.het_init_snp )				

					lf_random_freqs=[ f_allele_frequency for idx in range( self.input.numSNPs ) ]
				else:

					lf_random_freqs=\
							pgut.get_snp_allele_freqs_from_het_value_using_random_dist( \
																f_this_het_value=self.input.het_init_snp,
																i_num_freqs=self.input.numSNPs,
																lf_tolerances=SNP_HET_INIT_TOLERANCES,
																s_distribution=SNP_ALLELE_FREQ_DISTRIBUTION )
				#end if user wants 0.0 as init freq, else fixed uniform, else use random distribution
				#named in SNP_ALLELE_FREQ_DISTRIBUTION

			for f_random_freq in lf_random_freqs:		

				i_snp_count+=1

				initOps.append(
						sp.InitGenotype(
						#Position 0 is coded as 0, not good for genepop
						freq=[0.0, f_random_freq, 1 - f_random_freq ],
						loci=numMSats + i_snp_count))

			#end for each snp frequency, initialize a loci
		#end if we want at least one SNP

		preOps = []

		if self.input.mutFreq > 0:
			preOps.append(sp.StepwiseMutator(rates=self.input.mutFreq,
					loci=list(range(numMSats))))
		#end if mufreq > 0

		self.__loci=loci
		self.__genInitOps=initOps
		self.__genPreOps=preOps

		return
	#end __createGenomeFromSNPAndMSatTotals

	def __get_dict_chromosome_number_by_loci_number_evenly_distributed ( self,
																			i_number_of_loci, 
																			i_number_of_chromosomes ):

		'''
		2018_04_18. We're adding chromosome/loci
		associations in order to leverage LDNe2's
		feature that computes Ne using chromosome/loci
		information.  Note that the easy, default way
		to get simupop to evenly  assign, say, 30 loci 
		to 5 chromosomes, "loci=[10,10,10],
		chromtypes=[Autosome]*5", means that if our user
		is using both q Msats and r snps, and since we always
		assign the first q loci to be msats and the last r
		to be snps, the default chrom assignments will tend to
		bunch the msats together on the same (few) first 
		chromosomes and the snps on the last.  We thus
		will distribute them using the addLoci and addChrom
		methods of the pop struct (see __createSinglePop).
		In order to hold these assignments
		steady among replicates, we, rather than using any 
		random assignment, we assign N loci 0,1,2...N-1 to 
		M chromosomes 0,1,2...M-1, in order, i=1,2,3...N, 
		assigning loci i to chromsome i mod M, which puts 
		an additional loci on each of the first T chromosomes 
		where T = N mod M. 

		Note: if the number of chromosomes exceeds the number
		of loci, we trim the number of chromosomes to equal
		the number of loci.

		2018_05_22.  Testing using Genepop's linkage diseq 
		test shows that despite assigning loci using the 
		alternating-chromosome method described above, alleles 
		are treated as physically linked according
		to the scheme, for N loci and M chromosomes, that the first
		N/M loci are assigned to a single chromosome, the second
		N/M loci assigned to another, etc.  Therefor we change the
		loci assignment scheme so that the program will output
		a chromsome/loci file that agrees with the way alleles
		are linked in the program.
		'''

		di_chromosome_number_by_loci_number={}

		if i_number_of_loci < i_number_of_chromosomes:
			i_number_of_chromosomes=i_number_of_loci
		#end if more chromosomes thatn loci, get rid of excess
		#chromosomes

		i_partition_size=int( i_number_of_loci / i_number_of_chromosomes )

		i_remainder=i_number_of_loci % i_number_of_chromosomes

		i_loci_count=0

		for i_chr in range( i_number_of_chromosomes ):
			for i_part_idx in range( i_partition_size ):
				di_chromosome_number_by_loci_number[ i_loci_count ]=i_chr
				i_loci_count += 1
			#end for each partition index

			#If we have remainder, add one loci to the current chromosome
			if i_remainder > 0:
				di_chromosome_number_by_loci_number[ i_loci_count ]=i_chr
				i_loci_count += 1
				i_remainder-=1
			#end if remainder, add loci
		#end for each chrom

		return di_chromosome_number_by_loci_number
	#end __get_dict_chromosome_number_by_loci_number_evenly_distributed

	def __get_loci_positions_by_loci_number( self, di_chromosome_number_by_loci_number ):

		'''
		2018_04_18.  This def is added to assist in assigning chromosomes
		to loci. The loci position on the chrom, per simuPOP, is a unitless
		value, left to the user's discretion and use.  For now we simply
		use floats between 0 and 1.0, and space the loci evenly across the
		chromosome.

		This def assumes that the lists given by list( mydict.keys() ) and 
		list( mydict.values() ) have indices such that mydict.values()[i] 
		always equals mydict[ mydict.keys()[i] ].

		2018_05_22. We've changed the position scheme to place loci evenly
		across chromosome with 100 units istead of 1.0.  This is meant to
		emulate cM units along a 100 cM chromosome.
		'''

		di_loci_position_by_loci_number={}
		
		li_loci_numbers=list( di_chromosome_number_by_loci_number.keys() )
		li_chromosome_numbers=list( di_chromosome_number_by_loci_number.values() )

		set_chromosome_numbers=set( li_chromosome_numbers )

		array_chromosome_numbers=numpy.array( li_chromosome_numbers )

		for i_chromosome_number in set_chromosome_numbers:

			array_idx_this_chrom_number=\
					( numpy.where( array_chromosome_numbers == i_chromosome_number ) )[0]

			i_total_loci_on_this_chrom=len( array_idx_this_chrom_number )

			'''
			2018_05_22. We change the position values to mimic loci
			evenly spaced over a 100 cM chromosome.
			'''
			
			f_position_increment=100.0/float( i_total_loci_on_this_chrom )
			
			f_current_position=0.0

			for idx in array_idx_this_chrom_number: 	

					di_loci_position_by_loci_number[ li_loci_numbers[ idx ] ]=f_current_position

					f_current_position+=f_position_increment
			#end for each index in the chrom number list
		#end for each i_chromosome_number

		return di_loci_position_by_loci_number

	#end __get_loci_positions_by_loci_number

	def __add_loci_and_chromosomes_to_pop( self, 
											pop, 
											i_number_of_loci, 
											i_number_of_chromosomes, 
											li_chrom_type_list  ):
		'''
		2018_04_18. We now associate a chromosome with each loci.
		For more details, see comments heading def,  
		__get_dict_chromosome_number_by_loci_number_evenly_distributed, 
		and the simuPOP manual page at 
		http://simupop.sourceforge.net/manual_svn/build/userGuide_ch4_sec3.html
		'''
		di_chromosome_number_by_loci_number=\
					self.__get_dict_chromosome_number_by_loci_number_evenly_distributed( \
																		i_number_of_loci,
																		i_number_of_chromosomes )
	
		'''
		One chromosome already exists?
		'''
		i_tot_chroms_already_created=1

		'''
		These position floats, for no particular reason
		representing N even pieces of each chrom as proportion of
		[0.0,1.0], with N = max(number-of-loci).  These parameters
		are required when using the addLoci and addChrom methods
		of the Population object. Further, one can't assign the same
		postiion to two loci,  Even further, we may in the future want 
		to use loci positional information within chromosomes
		
		2018_05_22.  Note that our positions are now given as proportions
		of a chrom [0.0, 100.0], to better mimic cM units. Note, too
		that testing shows that simuPOP will disallow any two positions
		that differ by less than 1e-13.

		'''

		di_loci_position_by_loci_number= \
				self.__get_loci_positions_by_loci_number( \
										di_chromosome_number_by_loci_number )
		
		li_sorted_loci_numbers=sorted( list( di_chromosome_number_by_loci_number.keys() ) )

		for i_loci_number in li_sorted_loci_numbers:

			i_chromosome_number=di_chromosome_number_by_loci_number[ i_loci_number ] 
			
			'''
			Zero indexing of chrom numbers means if we've created N chromosomes,
			then the last chrom created was number N-1

			'''
			if i_chromosome_number >= i_tot_chroms_already_created:

				'''
				Chromomsome not yet created, create.
				'''	
				pop.addChrom( lociPos=[], chromType=li_chrom_type_list[ i_chromosome_number ]  )

				i_tot_chroms_already_created+=1

			#end if chromosome not yet created
			
			'''
			Note we name the N loci using l0, l1, l2...l(N-1). They will then 
			correctly correspond to the current Genpopfile Header loci names, 
			as written in the pgooutputsimupop.py 
			def writeGenepopFileHeaderAndLociList.
			'''
			pop.addLoci( i_chromosome_number, 
							pos=di_loci_position_by_loci_number[ i_loci_number ],
							lociNames= "l" + str( i_loci_number ))

		#end for each loci number

		return
	#end __add_loci_and_chromosomes_to_pop

	def __write_chromosome_loci_table( self, o_simupop_population ):
		'''
		2018_05_09.  As currently coded, for any set of replicates
		the loci/chromosome assignments are identical.  Hence, to 
		avoid potential output file clutter, we only write the
		chrom/loci file for replicate one only (as determined by
		the client's use of param b_write_the_once_only_files in
		the __init__ def.  This is the same policy used for the 
		age-class and pwop nb file:
		'''
		if self.__write_once_only_files:
			self.output.writeLociChromTable( o_simupop_population )
		#end if we'er writing the age count and nb files, write the chrom file too
		return
	#end __write_chromosome_loci_table

	def __createSinglePop( self ):

		popSize=self.input.popSize
		nLoci=self.input.numMSats + self.input.numSNPs
		startLambda=self.input.startLambda
		lbd=self.input.lbd
		
		ldef_init_sex=[]

		'''
		This 2-cull-method selection for intializing sex ratios
		was added 2017_01_05.  When the user selects
		"equal_sex_ratio" in the interface (PGGuiSimuPop), we 
		initialize always using "maleProp=0.5".  When the user
		chooses the "survivial_rates" option, then the configuration
		file param "maleProb" is accessed (its value also may have been 
		reset in the interface), and the sex ratio is determined using 
		Tiago's original assignment, "maleFreq=input.maleProb".

		Note that as of 2018_05_07, our actual name for the cull method
		formerly called "equal_sex_ratio" is now "maintain_distribution"
		We leave the constants and variable names unchanged.
		'''
		if self.input.cull_method == \
					pgin.PGInputSimuPop.CONST_CULL_METHOD_EQUAL_SEX_RATIOS:

			ldef_init_sex=[sp.InitSex(maleProp=0.5)]

		elif self.input.cull_method == \
					pgin.PGInputSimuPop.CONST_CULL_METHOD_SURVIVIAL_RATES:
			ldef_init_sex=[ sp.InitSex(maleFreq=self.input.maleProb) ]
		else:
			s_msg="In PGOpSimuPop instance, def __createSinglePop, "  \
						+ "there is an unknown value for the cull_method " \
						+ "parameter: " + str( self.input.cull_method ) + "."
			raise Exception( s_msg )
		#end if equal sex ratio else

		initOps=ldef_init_sex 

		'''
		2017_05_31. Note that after we implemented the __harvest def in
		pgopsimupop.py, we were no longer using lambda to adjust the N0
		in def __calcDemo (see).  However, this use of the lambda (i.e. ldb),
		was not deleted.  It was set to be hidden in the resources/simupop.param.names,
		but was still getting used in the ResizeSubPops operator with a default
		value of 1.0.  I am now checking for either the IGNORE in startLambda or
		a lambda value very close to 1.0. 
		'''
		f_insig_diff=1e-64
		f_this_diff=abs( lbd - pgin.LAMBDA_IGNORE )
		if startLambda < pgin.START_LAMBDA_IGNORE \
				and f_this_diff > f_insig_diff:
			
			s_msg="Warning: In PGOpSimuPop instance, def __createSinglePop, " \
					+ "the non-unity lambda parameter found in your configuration file, "  \
					+ "with value, " + str( lbd ) + ", will be ignored.  "  \
					+ "Per cycle population reductions are currently not done using lambda, " \
					+ "but instead using the Nb and census adjustment parameter \"nbadjustment\"."
				
			sys.stderr.write( s_msg + "\n" )
			
			if self.__guiinfo is not None:
				if self.__is_first_replicate:
					self.__guiinfo( None, s_msg )
				#end if this is the first replicate
			#end if using gui messaging

			#####2017_05_31 rem out, currently not used.
			#preOps = [sp.ResizeSubPops(proportions=(float(lbd), ),
			#					begin=startLambda)]
			#####

			preOps = []
				
		else:

			preOps = []

		#end if lambda < VALUE_NO_LAMBA

		postOps = []
		
		'''
		2018_04_19. We now assign loci to chromosomes, and, in 
		order not to put all M mstats (always the first M loci)
		on just a few chromosomes, and similarly with S SNPs (the
		last S loci created, we're creating chromosomes and loci
		using the simuPOP.addChrom and simuPOP.addLoci (see def
		__add_loci_and_chromosome_to_pop.  We rem out the original
		pop creation, and replace with stripped down initialization,
		then assign loci and chroms after:
		
		2018_04_27.  Revise the chrom-total handlingrevert to 
		the original pop creation statement when number of chromsomes 
		is zero.  Note, too, that when this total is zero, we will 
		not write a chrom/loci table.

		2018_05_27.  We have added the ability of the user to supply
		loci info (read in from a file), and so we now intialize 
		the Population by testing first to see if the PGSimupopLociInfo
		(as created in prepareOp, when a valid file name is supplied),
		exists.  If so we init the Pop using its loci quants, else
		we initialize as before (testing whether we have > 0 chroms
		in our input chrom total, and using out numMSats and numSNPs
		totals).

		"pop" to be assigned according to method:
		'''
		pop=None

		if self.__user_supplied_loci_info is not None:
			dsi_loci_totals_by_chrom= \
					self.__user_supplied_loci_info.loci_totals_by_chromosome
			'''
			This call gets the list of postions by chromosome,
			and solves the problem of loci at identical positions
			by incrementing one of such a pair by the minimum
			"postion" value (currently trials show 1e-13), 
			to which simupop is sensitive, and will allow the 
			pair to be intialized as different loci.  

			Note that now (2018_07_03) this call returns,
			in addition to the dict of position lists by chrom,
			a per-chrom list of loci names whose names match
			the positions read in from the loci file, as
			given by the loc_pos_by_chrom dict.  Loci with 
			"jiggled" positions will be listed in the order 
			in which they were given in the input loci,chrom,pos
			file.
			'''
			dsf_loci_pos_by_chrom, dsf_loci_names_by_chrom = \
					self.__user_supplied_loci_info\
								.getPositionsUsingSmallOffsetForNonUniquePositions()

			ls_chrom_names=list( dsi_loci_totals_by_chrom.keys() )

			'''
			2018_07_05. Decided to use natsort, since often chromosome
			names are either numbers or a combination of alpha and number:
			'''
			ls_sorted_chrom_names = natsort.realsorted( ls_chrom_names )


			li_loci_totals=[]
			lf_positions=[]

			'''
			2018_07_03. In order to use the user supplied loci names,
			we now get them from our loci info object, instead of
			using out default "l<num>" naming convention.
			'''
			ls_loci_names=[]

			'''
			2018_07_27. We now give the user the option to provide
			allele frequencies in a 4th column of a loci, chrom, postion, freq
			file.  We also retain the former format, loci, chrom, postiion
			as valid
			'''
			b_have_user_supplied_allele_frequencies=\
					self.__user_supplied_loci_info\
						.allele_frequenies_by_chrom_and_locus_name is not None

			lf_loci_allele_frequencies=[] if b_have_user_supplied_allele_frequencies else None

			for s_chrom in ls_sorted_chrom_names:

				lf_positions+=dsf_loci_pos_by_chrom[ s_chrom ]
				li_loci_totals.append( dsi_loci_totals_by_chrom[ s_chrom ] )
				ls_loci_names+=dsf_loci_names_by_chrom[ s_chrom ]
			
				if b_have_user_supplied_allele_frequencies:
					df_allele_frequencies_by_loci_name=\
							self.__user_supplied_loci_info.allele_frequenies_by_chrom_and_locus_name[ s_chrom ]
					
			
					
					lf_loci_allele_frequencies+=[ df_allele_frequencies_by_loci_name[ s_name ] \
											for s_name in dsf_loci_names_by_chrom[ s_chrom ] ]
				#end if
			#end for each chrom	

			pop=sp.Population(popSize, ploidy=2, loci=li_loci_totals,
						lociPos=lf_positions, lociNames=ls_loci_names,
						chromTypes=[sp.AUTOSOME] * len( li_loci_totals ),
						infoFields=["ind_id", "father_id", "mother_id",
						"age", "breed", "rep_succ",
						"mate", "force_skip"])

			if b_have_user_supplied_allele_frequencies:
				self.__user_supplied_allele_frequencies=lf_loci_allele_frequencies
			#end if the user also supplied alelle frequencies.

		else:

			if self.input.numChroms==0:
				'''
				So that we can access total loci using the lociNames pop attribute, even
				when we've used our generic, automated loci inititalization. In cases
				in which the user supplies a loci/chrom file, or sets numChroms to 
				non-zero, the loci names are incorporated durint the pop init.
				'''
				ls_loci_names=[ "l" + str( idx ) for idx in range( nLoci ) ]

				pop = sp.Population( popSize, ploidy=2, loci=[1] * nLoci,
							lociNames=ls_loci_names, chromTypes=[sp.AUTOSOME] * nLoci,
							infoFields=["ind_id", "father_id", "mother_id",
							"age", "breed", "rep_succ",
							"mate", "force_skip"] )
			else:

				pop = sp.Population( popSize, ploidy=2, 					
										infoFields=["ind_id", "father_id", "mother_id",
															"age", "breed", "rep_succ",
																	"mate", "force_skip"])
				
				li_chrom_types=[ sp.AUTOSOME for i in range( self.input.numChroms ) ]

				self.__add_loci_and_chromosomes_to_pop( pop, nLoci, 
															self.input.numChroms, 
															li_chrom_types  )
			#end if user specifies zero chroms, else divvy up loci among some N>0 chromosomes
		#end if the user supplied loci info, else we use our chrom/snp/msat totals

		for ind in pop.individuals():
			ind.breed = -1000
		#end for ind in pop

		oExpr = ('"%s/samp/%f/%%d/%%d/smp-%d-%%d-%%d.txt" %% ' +
						'(numIndivs, numLoci, gen, rep)') % (
						 self.input.dataDir, self.input.mutFreq, popSize)
		
		self.__pop=pop
		self.__popInitOps=initOps
		self.__popPreOps=preOps
		self.__popPostOps=postOps
		self.__oExpr=oExpr

		return 
	#end __createSinglePop

	def __createSim( self ):
		self.__sim = sp.Simulator(self.__pop, rep=self.input.reps)
		return 
	#endd __createSim

	def __evolveSim(self):

		sim=self.__sim
		gens=self.input.gens
		mateOp=self.__mateOp
		genInitOps=self.__genInitOps
		genPreOps=self.__genPreOps
		popInitOps=self.__popInitOps
		ageInitOps=self.__ageInitOps
		popPreOps=self.__popPreOps
		agePreOps=self.__agePreOps
		popPostOps=self.__popPostOps
		agePostOps=self.__agePostOps
		reportOps=self.__reportOps
		oExpr=self.__oExpr

		##### rem out to add stopOp option 2017_08_07
#		sim.evolve( initOps=genInitOps + popInitOps + ageInitOps,
#					preOps=popPreOps + genPreOps + agePreOps,
#					postOps=popPostOps + reportOps + agePostOps,
#					matingScheme=mateOp,
#					gen=gens)


		stopOp=[]

		if self.input.do_het_filter:
			stopOp=[ sp.PyOperator( func=self.__keep_collecting_filtered_pops  ) ]
		#end if we are writing het-value-filtered pops, then we stop after the user-supplied limit
		#is reached.

		sim.evolve( initOps=genInitOps + popInitOps + ageInitOps,
					preOps=popPreOps + genPreOps + agePreOps,
					postOps=popPostOps + reportOps + agePostOps + stopOp,
					matingScheme=mateOp,
					gen=gens)
		##### end rem out and revise the evole op set by adding a stop when filtering pops by het value.

	#end __evolveSim

	def __keep_collecting_filtered_pops( self, pop ):
		'''
		This pyOperator is used when the output mode is OUTPUT_GENEPOP_ONLY
		'''

		b_filtered_total_not_reached= \
				self.total_filtered_pops_saved < self.total_filtered_pops_to_save

		b_filter_min_het_still_below_pop_het=\
				not( self.min_het_filter_greater_than_current_pop_het )

		#As of 2018_02_24 non-zero mutation frequencies apply only to msats.
		b_pop_het_can_increase=self.input.numMSats > 0 and self.input.mutFreq > 0		

		b_filter_range_still_achievable=b_filter_min_het_still_below_pop_het \
														or b_pop_het_can_increase
		
		#For the case when the pop hets will no
		#longer be able to meet the filter,
		#we want to notify the user:
		if not ( b_filter_range_still_achievable ):
			s_pop_number=str( pop.dvars().gen ) 
			
			'''
			2018_04_01. Added to let user know what the
			mean het value was, to compare with their
			filter minimum.
			'''
			f_mean_expected_het=self.__get_mean_heterozygosity_over_all_loci( pop )

			s_msg="The simulation's current pop, number " \
					+ s_pop_number \
					+ ", has an expected " \
					+ "heterozygosity less than the minimum, " \
					+ str( f_mean_expected_het )  \
					+ ", as set in the heterozygosity filter.  " \
					+ "With no mutation rate and/or no microsats, " \
					+ "the program currently stops the simulation, " \
					+ "under the assumption that mean " \
					+ "expected heterozygisity will only decrease " \
					+ "as the simulation evolves further, and cannot " \
					+ "produce a pop whose mean het meets the filter " \
					+ "criteria."

			self.__write_interruption_file( s_msg )
		#end if het can't meed filter criteria

		return  b_filtered_total_not_reached and b_filter_range_still_achievable

	#end keep_collecting_filtered_pops

	def __calcDemo( self, gen, pop ):

		v_return_value=None	
		myAges = []
		for age in range(self.input.ages - 2):
			myAges.append(age + 1)
		#end for age in range

		curr = 0

		for i in pop.individuals():
			if i.age in myAges:
				curr += 1
		#end for i in pop

		#todo apply NB change here!!

		'''
		2017_02_25.  We are now using a harvest rate
		instead of the old input.lbd lambda.  In this
		new scenario, we only adjust the number of newborns
		created if our harvest rate is above 1.0, the only
		case in which our new attribute __lambda_for_newborns
		should be non-None.  See def __make_harvest_list. 

		2017_03_02. We are now applying the newborns increase
		(a "negative" lambda,i.e., harvest rate greater than 1.0)
		in the def, __harvest, and so have deleted code that 
		tests-for and applies the attribute,__lambda_for_newborns.
		'''
		v_return_value = self.__current_N0 + curr

		if VERBOSE:
			print( "in __calcDemo, with args, %s %s %s %s, returning %s "
					% ( "gen: ", str( gen ), "pop", str( pop ), str( v_return_value ) ) )
		#end if verbose

		return v_return_value

	#end __calcDemo

	def __getRandomPos( self, arr ):

		sumVal = sum(arr)
		rnd = random.random()
		acu = 0.0
		v_return_value=None

		for i in range(len(arr)):
			acu += arr[i]
			if acu >= rnd * sumVal:
				 v_return_value=i
				 break
			#end if acu . . .
		#end for i in range...

		return v_return_value
	#end __getRandomPos

	def __litterSkipGenerator( self, pop, subPop ):

		if VERY_VERY_VERBOSE:
			print( "In __litterSkipGenerator on gen: " + str( pop.dvars().gen ) )
		#end if very very verbose

		fecms = self.input.fecundityMale
		fecfs = self.input.fecundityFemale

		nextFemales = []
		malesAge = {}
		femalesAge = {}
		availOfs = {}
		gen = pop.dvars().gen
		nLitter = None

		if self.input.litter and self.input.litter[0] < 0:
			nLitter = - self.input.litter[0]
		#end if litter and litter[0] < 0

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				malesAge.setdefault(int(ind.age), []).append(ind)
			else:
				if nLitter is not None:
					availOfs[ind] = nLitter
				#end if nLitter not none

				diff = int(gen - ind.breed)

				#Thu Jun 23 14:00:42 MDT 2016
				#because we want to represent an emtpy
				#skip list as "None" in the interface
				#we test its value in the input object,
				#considet a skip==None to imply that
				#len( skip ) == 0:
				i_len_skip=0 if self.input.skip is None \
									else len( self.input.skip )
				if diff > i_len_skip:
					available = True
				else:
					prob = random.random() * 100
					assert self.input.skip is not None, \
							"Expecting self.input.skip to be list."
					#print prob, self.input.skip, diff
					if prob > self.input.skip[diff - 1]:
						available = True
					else:
						available = False
					#end if prob > skip else not
				#end if diff > len else not

				#print ind, available

				if available:
					femalesAge.setdefault(int(ind.age), []).append(ind)
				#end if available

			#end if ind.sex() == 1
		#end for ind in pop...

		maleFec = []
		for i in range(len(fecms)):
			maleFec.append(fecms[i] * len(malesAge.get(i + 1, [])))
		#end for i in range...

		femaleFec = []
		for i in range(len(fecfs)):

			if self.input.forceSkip > 0 and random.random() < self.input.forceSkip:
				femaleFec.append(0.0)
			else:
				 femaleFec.append(fecfs[i] * len(femalesAge.get(i + 1, [])))
			#end if forceSkip . . . else
		#end for i in range

		while True:

			female = None

			if len(nextFemales) > 0:
				female = nextFemales.pop()
			#end if len( next....

			while not female:
				age = self.__getRandomPos(femaleFec) + 1
				if len(femalesAge.get(age, [])) > 0:

					female = random.choice(femalesAge[age])

					if nLitter is not None:
						if availOfs[female] == 0:
							female = None
						else:
							availOfs[female] -= 1
						#end if availOfs, else not
					elif self.input.litter:
						lSize = self.__getRandomPos(self.input.litter) + 1
						if lSize > 1:
							nextFemales = [female] * (lSize - 1)
						#end if size>1

						femalesAge[age].remove(female)
					#end if nLitter is not none elif litter
				#end if len( femalsage . . . 
			#end while not female

			male = None

			if self.input.isMonog:
				if female.mate > -1:
					male = pop.indByID(female.mate)
				#end if female.mate 
			#end if isMonog

			while male is None:
				age = self.__getRandomPos(maleFec) + 1
				if len(malesAge.get(age, [])) > 0:
					male = random.choice(malesAge[age])
				#end if len malesage

				if self.input.isMonog:
					if male.mate > -1:
						male = None
					else:
						male.mate = female.ind_id
					#end if male.mate > -1
				#end if isMonog
			#end while male is None...

			female.breed = gen

			if self.input.isMonog:
				female.mate = male.ind_id
			#end if is monog

			if VERY_VERY_VERBOSE:
				print( "in __litterSkipGenerator, yielding with  " \
						+ "male: %s, female: %s"
						% ( str( male ), str( female ) ) )
			#end if verbose

			yield male, female

		#end while True
	#end __litterSkipGenerator

	def __calcNb( self, pop, pair ):
		
		'''
		2017_03_02 This float tolerance is added
		in order to test the kbar value before using 
		it as a divisor (below).  This to control
		the error messaging when our new __harvest
		def creates a population that causes a 
		zero value for kbar.
		'''
		reltol=1e-90

		fecms = self.input.fecundityMale
		fecfs = self.input.fecundityFemale
		cofs = []

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				fecs = fecms
				pos = 0
			else:
				pos = 1
				fecs = fecfs
			#end if sex==1 else not
			
			if fecs[int(ind.age) - 1] > 0:
				nofs = len([x for x in pair if x[pos] == ind])
				cofs.append(nofs)
			#end if fecs
		#end for ind in pop

		if len( cofs ) == 0:
			s_msg="In PGOpSimuPop instance, " \
					 + "def __calcNb, " \
					 + "the program can't calculate " \
					 + "a PWoP Nb value for the current population, " \
					 + "because it found  no fecund pairs."
			if self.__guierr is not None:
				self.__guierr( None, s_msg )
			#end if gui error, then show

			raise Exception( s_msg )
		#end if no pairs of fecund indivs found
							
		kbar = 2.0 * self.__current_N0 / len(cofs)

		Vk = numpy.var(cofs)

		if kbar <= reltol:
			s_msg="In PGOpSimuPop instance, def __calcNb, " \
								+ "divisor, kbar, is too close to zero (kbar = " \
								+ str( kbar ) + ")."
			if self.__guierr is not None:
				self.__guierr( None, s_msg )
			#end if gui err, show

			raise Exception( s_msg )
		#end if kbar close to zero

		nb = old_div((kbar * len(cofs) - 2), (kbar - 1 + old_div(Vk, kbar)))
		#print len(pair), kbar, Vk, (kbar * len(cofs) - 2) / (kbar - 1 + Vk / kbar)
	
		return nb
	#end __calcNb

	def __restrictedGenerator( self, pop, subPop ):

		if VERY_VERBOSE:
			print( "----------------" )
			print( "in restrictedGenerator with gen: " + str( pop.dvars().gen ) )
			print( "in restrictedGenerator with target: " + str( self.__targetNb ) )
			print( "in restrictedGenerator with tolerance " + str( self.__toleranceNb ) )
		#end if very verbose

		"""No monogamy, skip or litter"""
		nbOK = False
		nb = None
		attempts = 0
		
		if VERY_VERBOSE:

			print ( "in __restrictedGenerator with " \
					+ "args, pop: %s, subpop: %s"
							% ( str( pop ), str( subPop ) ) )
		#end if VERBOSE

		while not nbOK:

			pair = []
			'''
			2018_03_13.  Change, now using this attribute,
			__generator_called_by_restricted_generator,
			set in def __createAge, so that we now are either 
			calling the (default) __litterSkipGenerator, or,
			if the input includes doNegBinom and gamma lists, 
			then, this call is assigned to the __fitnessGenerator

			'''
			#gen = self.__litterSkipGenerator(pop, subPop)
			gen=self.__generator_called_by_restricted_generator( pop, subPop )

			#print 1, pop.dvars().gen, nb

			'''
			2017_02_06
			Now testing with goal of using this generator 
			for all sims.  Need to cast __current_N0 as 
			an int for this arg.
			'''

			for i in range( int( round( self.__current_N0 ) ) ):
				pair.append( next(gen) )
			#end for i in range

			'''
			2017_03_24.  Since this def is now always used
			to get the next gen, we change the gen 
			number after which we apply our nb test, to the 
			gen post burn in. 

			Recall that startLambda is now set by the user 
			to give the number burnin cycles, that is, generations
			for which no nb tolerance test will be applied.
			
			'''

			i_last_burnin_cycle = 0 \
					if self.input.startLambda >= PGOpSimuPop.VALUE_TO_IGNORE \
					else self.input.startLambda

			'''
			Note: We are trying to let the user always see
			one-indexed gens,, given that the user enters
			one-indexed values for burn-in and start save.
			So we are trying to apply our tests to reflect 
			that indexing instead of simuPOP's zero-based 
			indexing: 
			'''
			i_one_indexed_gen_number = pop.dvars().gen + 1

			if i_one_indexed_gen_number <= i_last_burnin_cycle:
				break
			#end if gen number is less than our burn-in threshold.

			nb = self.__calcNb(pop, pair)

			'''
			2017_02_06
			After meeting with Robin Waples, we now default
			to using this generator, and have added attributes
			to this PGOpSimuPop object to supply the target Nb
			and its tolerance value (rather than using the
			original input.* attributes (see def createAge
			for the initializatio of these values).
			'''
			#### Remm'd out.  This is from the original code using the original param values:
			#if abs(nb - self.input.Nb_orig_from_pop_section ) <= self.input.NbVar:

			if abs(nb - self.__targetNb ) <= self.__toleranceNb:
				
				nbOK = True

				if VERY_VERBOSE:
					print( "in restrictedGenerator, selecting pop with Nb at: " + str( nb ) )
				#end if very verbose	
			else:
				for male, female in pair:
					female.breed -= 1
				#end for male, female

				attempts += 1

			#end for abs( nb ... else not

			if attempts > self.__max_tries_at_tolerance:
				s_msg="In PGOpSimuPop instance, " \
							+ "def __restrictedGenerator, " \
							+ "for generation, " + str( pop.dvars().gen ) \
							+ ", after " + str( self.__max_tries_at_tolerance ) \
							+ " tries, the simulation did not generate a " \
							+ "population with an Nb value inside " \
							+ "the tolerance.  Target Nb: " \
							+ str( self.__targetNb ) \
							+ ", and tolerance at +/- " \
							+ str( self.__toleranceNb ) + "."

				'''
				If we are using gui messaging, 
				we need to show this here, otherwise,
				because SimuPop is calling this def,
				the exception won't propogate to
				doOp, where other exceptions will
				be shown.
				'''
				if self.__guierr is not None:					
					self.__guierr( None, s_msg )
				#end if using gui messaging
				
				'''
				2017_06_11.  Request from Brian H. to delete the output files
				after an Nb-tolerance test fail.
				'''
				self.__cleanup_on_failure()

				raise Exception( s_msg )

				##### Remm'd out. 
				#We are now using the above exception instead 
				#of this message.  
				#print( "out", pop.dvars().gen )
				#sys.exit(-1)

			#end if attempts > self.__max_tries_at_tolerance

		#end while not nbOK

		'''
		For comparing Nb values as calculated
		(and accepted) on the pops as generated by simuPop, 
		to those created downstream by NeEstimator.

		Note 2018_04_01.  The if block that was here and
		tested the __write_once_only_files flag, 
		and if true writes the pwop nb to file has been 
		moved to __outputAge, so now we simply record it:
		The move reduced the number of these values written
		by restricting them to those pops also being written
		to output in the genepop file.

		Note 2018_04_17.  We've moved the writing of pwop
		Nb's back to this def, because, in the case that
		the user wants a pwop for gen 0 (i.e. the user sets
		the start save param to one), the sim calls outputAge 
		before the pwop calc for gen 0 is performed. So we must
		write it here.
		'''	

		if self.__write_once_only_files:

			'''
			2018_04_16.  To make output consistent
			with user input in the GUI, we increment
			the gen number by one, to reflect 1-indexed
			cycle numbers, rather than the zero-indexed
			"gen" series:
			'''

			i_one_indexed_gen_number=pop.dvars().gen + 1

			#We only record pwop nb values associated with
			#pops being saved to output:
			if i_one_indexed_gen_number >= self.input.startSave:

				s_thisgen=str( i_one_indexed_gen_number ) 
				s_thisnb=str( nb )

				self.__file_for_nb_records.write( \
						"\t".join( [ s_thisgen, s_thisnb ] ) \
						+ "\n" )
				'''
				Added 2017_08_24 to allow constantly updated plotting
				in PGGuiSimuPop instances.
				'''
				self.__file_for_nb_records.flush()
			#end if this gen is to be recorded, write the Nb
		#end if we are to write the nb value file

		for male, female in pair:
			yield male, female
		#end for male, female
	
	#end __restrictedGenerator

	def __fitnessGenerator( self, pop, subPop ):

		fecms = self.input.fecundityMale
		fecfs = self.input.fecundityFemale

		totFecMales = 0.0
		totFecFemales = 0.0
		availableFemales = []
		perAgeMaleNorm = {}
		perAgeFemaleNorm = {}
		gen = pop.dvars().gen
		ageCntMale = {}
		ageCntFemale = {}

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				a = self.input.gammaAMale[int(ind.age) - 1]
				b = self.input.gammaBMale[int(ind.age) - 1]
				if a:
					gamma = numpy.random.gamma(a, b)
					ind.rep_succ = gamma
					#ind.rep_succ = numpy.random.poisson(gamma)
				else:
					ind.rep_succ = 1
				#end if a else not

				perAgeMaleNorm[int(ind.age) - 1] = perAgeMaleNorm.get( 
								int(ind.age) - 1, 0.0) + ind.rep_succ

				ageCntMale[int(ind.age) - 1] = ageCntMale.get(
								int(ind.age) - 1, 0.0) + 1
			else:
				#if ind.age == 0: totFecFemales +=0
				a = self.input.gammaAFemale[int(ind.age) - 1]
				b = self.input.gammaBFemale[int(ind.age) - 1]
				if a:
					gamma = numpy.random.gamma(a, b)
					ind.rep_succ = gamma
					#ind.rep_succ = numpy.random.poisson(gamma)
				else:
					ind.rep_succ = 1
				#end if a else not

				perAgeFemaleNorm[int(ind.age) - 1] = perAgeFemaleNorm.get(
								int(ind.age) - 1, 0.0) + ind.rep_succ
				
				ageCntFemale[int(ind.age) - 1] = ageCntFemale.get(
								int(ind.age) - 1, 0.0) + 1

				availableFemales.append(ind.ind_id)
			#end if ind.sex == 1 else not
		#end for ind in pop.individuals

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				if perAgeMaleNorm[int(ind.age) - 1] == 0.0:
					ind.rep_succ = 0.0
				else:
					ind.rep_succ = ageCntMale[int(ind.age) - 1] * fecms[
								int(ind.age) - 1] * ind.rep_succ / perAgeMaleNorm[
								int(ind.age) - 1]
				#end if perAgeMaleNorm ... else not
				totFecMales += ind.rep_succ
			else:
				if ind.ind_id not in availableFemales:
					continue
				#end if ind,ind_id not ...

				if perAgeFemaleNorm[int(ind.age) - 1] == 0.0:
					ind.rep_succ = 0.0
				else:
					ind.rep_succ = ageCntFemale[int(ind.age) - 1] * fecfs[
								int(ind.age) - 1] * ind.rep_succ / perAgeFemaleNorm[
								int(ind.age) - 1]
				#end if perAgeFemaleNorm ... else not

				totFecFemales += ind.rep_succ
		#end for ind in pop

		nextFemales = []
		while True:

			mVal = random.random() * totFecMales
			fVal = random.random() * totFecFemales
			runMale = 0.0
			runFemale = 0.0
			male = False
			female = False

			if len(nextFemales) > 0:
				female = nextFemales.pop()
				female.breed = gen
			#end iflen( nextFemales ...

			inds = list(pop.individuals())
			random.shuffle(inds)

			for ind in inds:
				if ind.age == 0:
					continue
				#end if ind.age == 0

				if ind.sex() == 1 and not male:  # male
					runMale += ind.rep_succ
					if runMale > mVal:
						male = ind
					#end if runMale

				elif ind.sex() == 2 and not female:
					if ind.ind_id not in availableFemales:
						continue
					#end if ind.ind_id not in avail...

					runFemale += ind.rep_succ

					if runFemale > fVal:
						female = ind
						female.breed = gen
					#end if runFemale
				#end if ind.sex == 1 else ==2 

				if male and female:
					break
				#end if male and female
			#end for ind in inds

			if VERY_VERBOSE:
				s_msg="yielding from __fitnessGenerator with: " \
						+ "%s and %s" \
						% ( str( male ), str( female ) )
				print ( s_msg )
			#end if very verbose

			yield male, female
		#end while True
	#end __fitnessGenerator 

	def __cull( self, pop ):

		kills = []
		for i in pop.individuals():
			if i.age > 0 and i.age < self.input.ages - 1:
				if i.sex() == 1:
					cut = self.input.survivalMale[int(i.age) - 1]
				else:
					cut = self.input.survivalFemale[int(i.age) - 1]
				#end i i.sex==1 else not
				
				if random.random() > cut:
					kills.append(i.ind_id)
				#end if random.random...
			#endif age>0 andage<.....
		#end for i in pop

		pop.removeIndividuals(IDs=kills)

		return True
	#end __cull

	##Brian Trethewey addition for the immediate culling of a proportion of the adult population
	def __equalSexCull(self, pop):

		kills = []
		cohortDict = {}
		for i in pop.individuals():
			indAge = i.age

			if not indAge in cohortDict:
				cohortDict[indAge] = []
			cohortDict[indAge].append(i)


		for cohortKey in cohortDict:
			## !! Cohort 0 does not get culled!!
			if cohortKey == 0.0:
				continue

			cohortKills = []

			#setup data and seperate males and females
			cohort = cohortDict[cohortKey]

			cohortTotal = len(cohort)
			cohortMales = [x for x in cohort if x.sex()==1]
			maleCount = len(cohortMales)
			cohortFemales = [x for x in cohort if x.sex() == 2]
			femaleCount = len(cohortFemales)

			if VERBOSE:
				print(cohortKey)
				print(cohortTotal)
				print(maleCount)
				print(femaleCount)
				print("\n")
			#end if verbose

					##!! Cohort 0 does not get culled!!
			if cohortKey == 0.0:
				continue

			cohortKills = []

			'''
			2017_02_26. Adding int() because round returns a float,
			which results in a type error in call to random.sample below.

			'''
			maleCull = int(numpy.floor(maleCount *(1- self.input.survivalMale[int(cohortKey) - 1])))
			femaleCull = int(numpy.floor(femaleCount *(1- self.input.survivalFemale[int(cohortKey) - 1])))
			maleChance = maleCount *(1- self.input.survivalMale[int(cohortKey) - 1]) - maleCull
			femaleChance = femaleCount *(1- self.input.survivalFemale[int(cohortKey) - 1]) - femaleCull
			maleRand = random.random()
			femaleRand = random.random()
			if maleChance>maleRand:
				maleCull+=1
				#print ("extra Male")
			if femaleChance>femaleRand:
				femaleCull+=1
				#print ("extraFemale")


			if PRINT_CULL_TOTALS:
				print ("cohort: " + str(cohortKey))
				print ("maleCount: " + str(maleCount))
				print ("femaleCount: " + str(femaleCount))
				print ("maleCull: " + str(maleCull))
				print ("femaleCull: " + str(femaleCull))
				print ("\n\n")
			# end if PRINT_CULL_TOTALS

			# choose which sex to kill first
			# flag is one and 0 for easy switching
			# killChoiceFlag = round(random.random())
			# if femaleCount > maleCount:
			# 	killChoiceFlag = 0
			# if maleCount > femaleCount:
			# 	killChoiceFlag = 1

			'''
			2017_02_26 Correction to the following two lines.  I think numpy.sample is
			supposed to be random.sample
			'''
			# sample  harvest
			maleHarvestList = random.sample(cohortMales, maleCull)
			femaleHarvestList = random.sample(cohortFemales, femaleCull)

			for ind in maleHarvestList:
				#				print "Dead " + str(ind.ind_id)
				kills.append(ind.ind_id)
			for ind in femaleHarvestList:
				#				print "Dead " + str(ind.ind_id)
				kills.append(ind.ind_id)

			# kills.extend(cohortKills)
			# endif age>0 andage<.....
			# end for i in pop


			#kills.extend(cohortKills)
			# endif age>0 andage<.....
		# end for i in pop
		if VERBOSE:
			print(kills)
		#end if VERBOSE

		pop.removeIndividuals(IDs=kills)
		return True

	#end __equalSexCull

	def __harvest(self, pop):

		f_reltol=float( 1e-90 )

		gen = pop.dvars().gen

		if VERY_VERBOSE:
			print( "-----------------" )
			print( "in harvest with:" )
			print( "    gen num: " + str( gen ) )
		#end if very verbose

		if self.__nb_and_census_adjustment_by_cycle is None \
					or self.__nb_and_census_adjustment_by_cycle[ gen ] < f_reltol:
			if VERY_VERBOSE:
				print( "leaving harvest without harvesting pop or augmenting N0." )
			#end if very verbose
			return True
		#end if no harvest needed

		if VERY_VERBOSE:
			print ("    current Nb: " + str( self.__targetNb ) )
		#end if very verbose

		#determine harvest rate for this generation
		harvestRate = self.__nb_and_census_adjustment_by_cycle[ gen ]

		#reduce expected NB by 1-harvest rate, except when using an increase-for-newborns,
		#which, though user-entered as a rate > 1.0, is literally a negative harvest rate, 
		#and will proportionally increase the Nb:
		self.__targetNb =self.__targetNb *(1-harvestRate) if harvestRate < 1.0 \
						else self.__targetNb * harvestRate

		#Reset the toleracne to make it proportional to our new targetNb:
		self.__set_nb_tolerance()
		
		if VERY_VERBOSE:
			print ("    harvest rate: " + str( harvestRate ) )
		#end if very verbose

		'''
		2017_02_26.  No explicit call to a recalc fx is needed.  The assignment 
		of the Nb to the input object, and the subsequent assignment that gets the N0
		from the input object will result in the input object recalculating N0 using its 
		just-updated Nb value, before delivering it to this objects current_N0 attribute.
		'''
		#reduce N0
		# TODO self.__current_N0 = recalcN0(self.__targetNb)
		self.input.Nb=self.__targetNb
		self.__current_N0=self.input.N0

		if VERY_VERBOSE:
			print ("    new targetNb: " + str( self.__targetNb ) )
			print ("    new current N0: " + str( self.__current_N0 ) )
		#end if very verbose

		#If we did the newborn N0 adjustment, we do not harvest.
		if harvestRate >= 1.0:
			if VERY_VERBOSE:
				print ("returning after adjusting newborn N0" )
			#end if very verbose

			return True
		#end if this simulatiuon only adjusts N0 for newborns

		# change rate to correct for nb/bc differenece
#		harvestRate = harvestRate/self.input.NbNc

		kills = []
		cohortDict = {}

		'''
		2017_02_27.  This counter allows
		a check, before culling, that
		the resulting pop size will not be
		zero, which will result in an error condition
		at next call to evolve().  See exception
		test below.
		'''
		i_current_pop_size=0
		for i in pop.individuals():

			i_current_pop_size+=1

			indAge = i.age

			if not indAge in cohortDict:
				cohortDict[indAge] = []
			cohortDict[indAge].append(i)
		#end for each individual
	
		if VERY_VERBOSE:
			print( "    current pop size: " + str( i_current_pop_size ) )
		#end if very verbose

		for cohortKey in cohortDict:
			## !! Cohort 0 does not get culled!!
			# if cohortKey == 0.0:
			#	continue

			cohortKills = []

			# setup data and seperate males and females
			cohort = cohortDict[cohortKey]
			cohortTotal = len(cohort)
			cohortMales = [x for x in cohort if x.sex() == 1]
			maleCount = len(cohortMales)
			cohortFemales = [x for x in cohort if x.sex() == 2]
			femaleCount = len(cohortFemales)

			'''
			2017_02_26. Adding int() because round returns a float,
			which results in a type error in call to random.sample below.
			'''
			maleHarvest = int( numpy.floor(maleCount * harvestRate) )
			femaleHarvest = int( numpy.floor(femaleCount * harvestRate) )

			maleChance = (maleCount * harvestRate) - maleHarvest
			femaleChance = (femaleCount * harvestRate) - femaleHarvest
			maleRand = random.random()
			femaleRand = random.random()
			if maleChance>maleRand:
				maleHarvest+=1
				#print ("extra MaleHarvest")
			if femaleChance>femaleRand:
				femaleHarvest+=1
				#print ("extraFemaleHarvest")

			if VERY_VERY_VERBOSE:
				print ("cohort: " + str( cohortKey ) )
				print ("maleCount: " + str( maleCount ) )
				print ("femaleCount: " + str( femaleCount ) )
				print ("maleHarvest: " + str(maleHarvest) )
				print ("femaleHarvest: " + str(femaleHarvest) )
				print("\n\n")
			#end if very verbose

			# choose which sex to kill first
			# flag is one and 0 for easy switching
			# killChoiceFlag = round(random.random())
			# if femaleCount > maleCount:
			# 	killChoiceFlag = 0
			# if maleCount > femaleCount:
			# 	killChoiceFlag = 1

			'''
			2017_02_26 Correction to the following two lines.  I think numpy.sample is
			supposed to be random.sample
			'''
			#sample  harvest
			maleHarvestList = random.sample(cohortMales,maleHarvest)
			femaleHarvestList = random.sample(cohortFemales,femaleHarvest)

			for ind in maleHarvestList:
#				print "Dead " + str(ind.ind_id)
				kills.append(ind.ind_id)
			for ind in femaleHarvestList:
#				print "Dead " + str(ind.ind_id)
				kills.append(ind.ind_id)

				# kills.extend(cohortKills)
				# endif age>0 andage<.....
		# end for i in pop

		if VERY_VERBOSE:	
			print( "-----------------" )
			print( "in __harvest, removing " \
							+ str( len( kills ) ) \
							+ " individuals " )
		#end if very_verbose

		if len( kills ) == i_current_pop_size: 	
			s_msg="In PGOpSimuPop instance, def __harvest, " \
						+ "Error: harvest will cull the entire " \
						+ "current population."
			raise Exception( s_msg )
		#end if  kill list is entire pop

		pop.removeIndividuals(IDs=kills)
		
		return True
	# end __harvest

	def __zeroC( self, v ):
		a = str(v)
		while len(a) < 3:
			a = "0" + a
		#end while len(a) < 3
		return a
	#end __zeroC

	def __get_mean_heterozygosity_over_all_loci( self, pop ):

		lf_hetvals=[]

		tup_loci_names=pop.lociNames()

		i_num_loci=len( tup_loci_names )

		for idx in range( i_num_loci ):

			sp.stat(pop, alleleFreq=[idx])

			lf_hetvals.append( 1 - sum([x*x for x in pop.dvars().alleleFreq[idx].values()]) )

		#end for each loci

		return numpy.mean( lf_hetvals )
	#end __get_mean_heterozygosity_over_all_loci

	def __outputAge( self, pop ):
		try:

			gen = pop.dvars().gen

			if DUMP_POPS==True:
				print ("-----------------")
				print ("for run with basename: " + self.output.basename )
				print ("pop dump for cycle " + str( gen ) )
				sp.dump( pop )
			#end if DUMP_POPS


			'''
			2017_04_05.  Now using startSave, which was
			formerly suppressed and always set to zero.
			Since the GUI offers it and users excpect
			a 1-based count of cycles, we subtract
			one from the value to get the proper cycle
			as the start.

			2018_04_16.  Adjusting for one-indexed cycles.
			'''

			i_one_indexed_gen=gen+1

			if i_one_indexed_gen < ( self.input.startSave ):
				return True
			#end if gen < startSave

			rep = pop.dvars().rep

			'''
			Testing age counts per gen
			'''
			totals_by_age={}

			if self.__output_mode==PGOpSimuPop.OUTPUT_GENEPOP_ONLY:

				if self.input.do_het_filter == False:

					self.output.genepop.write( "pop\n" )

				else:

					f_mean_het=self.__get_mean_heterozygosity_over_all_loci( pop )

					if f_mean_het >= self.min_mean_heterozygosity \
								and f_mean_het <= self.max_mean_heterozygosity:
						self.output.genepop.write( "pop\n" )
						self.total_filtered_pops_saved += 1
						'''
						2018_04_16.  We now increment the pop number,
						to make all output pop-number records consistent
						with 1-indexed series, instead of simuPOP's zero
						indexed pop numbers:L
						'''
						i_one_indexed_pop_number=gen+1
						self.__file_for_het_filter.write( str( i_one_indexed_pop_number ) + "\t" \
														+ str( f_mean_het ) + "\n" )
					elif f_mean_het < self.min_mean_heterozygosity:	
					
						'''
						This flag will be tested in the stopOp
						call to def __keep_collecting_filtered_pops
						'''
						self.min_het_filter_greater_than_current_pop_het=True
						
						return True

					else:
						return True
					#end if het in range, else if pop's het less than filter's min, else return.
				#end if not het filter in effect, else test
			#end if output mode is genepop only, check whether het filter

			for i in pop.individuals():
				'''
				2017_08_04. I'm adding a new output mode, to 
				output genepop file only.  So, first, we check
				mode, then, if original, we do the code from
				the original.
				'''
				if self.__output_mode==PGOpSimuPop.OUTPUT_ORIG:
					self.output.out.write("%d %d %d %d %d %d %d\n" % (gen, rep, i.ind_id, i.sex(),
										i.father_id, i.mother_id, i.age))

					'''
					As of 2016_08_24:
					Change to Tiago's code to facilitate converting the *gen file 
					(i.e. the file whose handle is output.err), 
					to a genepop file (see def __write_genepop file, 
					we simply write indiv ID and alleles for all individuals
					in this pop to the *gen file, instead of those only for the 
					newborns -- hence we comment out the if statement, and de-indent 
					it's body

					As of 2016_08_31, reverted to the original code, so that
					as before the genepop file will be written with newborns
					only past the first cycle.  This is for the purposes of Congen
					conference, to do Nb estimates on the newborn cohort. Once
					genepop subsampling by individal demographics is implemented,
					we'll once again write the genpop to include all individuals,
					(then do subsampling on the full genepop) but will also include the 
					parentage and age (and other?) info as part of the individual 
					ID (using both the *gen (output.err) and *sim (output.err) files to 
					create the genepop.  It may be that we'll just keep this original 
					filter on the gen, and create the genepop using the indiv list to 
					get the individual ids, and this gen output to lookup genotypes.
					

					As of 2016_09_01, combining the age, sex, and parantage info into the indiv id
					for the first (indiv id) field in the *gen file.  Note above that this info
					is also written to the *sim file.  Putting it in the gen file will allow
					the gen file to be the sole source for writing  gen2genepop conversion
					in instances of type PGOutputSimuPop.  Also, we will again eliminate
					the filter used in writing the gen file indivs/cycle, and to 
					apply age or other filter conditions downstream from this output (using
					instances of class objects in new module genepopindividualid.py). Hence,
					once again we rem out the original filter on age for the gen-file indiv/generation
					'''
		#			if i.age == 1 or gen == 0:

					s_id_fields=PGOpSimuPop.DELIMITER_INDIV_ID.join( [ \
								str( i.ind_id ), str( i.sex() ), str( i.father_id ),
								str( i.mother_id ), str( i.age ) ] )

					self.output.err.write("%s %d " % (s_id_fields, gen))

					for pos in range(len(i.genotype(0))):
						a1 = self.__zeroC(i.allele(pos, 0))
						a2 = self.__zeroC(i.allele(pos, 1))
						self.output.err.write(a1 + a2 + " ")
					#end for pos in range

					self.output.err.write("\n")
					
					#end if age == 1 or gen == 0

					'''
					End of change to Tiago's code.
					'''
				elif self.__output_mode == PGOpSimuPop.OUTPUT_GENEPOP_ONLY:

					s_id_fields=PGOpSimuPop.DELIMITER_INDIV_ID.join( [ \
								str( i.ind_id ), str( i.sex() ), str( i.father_id ),
								str( i.mother_id ), str( i.age ) ] )

					self.output.genepop.write( "%s" % (s_id_fields + ", " ) )

					for pos in range(len(i.genotype(0))):
						a1 = self.__zeroC(i.allele(pos, 0))
						a2 = self.__zeroC(i.allele(pos, 1))
						self.output.genepop.write(a1 + a2 + " ")
					#end for pos in range

					self.output.genepop.write( "\n" )

				#end if output mode original, else genepop only 

				'''
				2017_02_07.  We are recording effects on the age 
				structure of using the culls __equalSexCull 
				and __harvest.
				'''
				if int( i.age ) in totals_by_age:
					totals_by_age[ int(i.age) ] += 1
				else:
					totals_by_age[ int( i.age ) ] = 1
				# end if age already recorded, else new age

			#end for i in pop

			'''
			2017_02_07.  To record age structure per gen.
			'''
			if self.__write_once_only_files:
				'''
				2018_04_16. For consistency with user
				pop (cycle) range entries in the GUI,
				we output the gen number + 1, using 
				1-indexed cycle numbers instead of the 
				zero-indexed series used by simuPOP.
				'''
				i_one_indexed_pop_number=gen+1
				ls_entry=[ str( i_one_indexed_pop_number ) ]
				
				for idx in range( self.__total_ages_for_age_file ):
					i_thisage=idx+1
					if i_thisage in totals_by_age: 
						s_this_val=str( totals_by_age[ i_thisage ]  )
					else:
						s_this_val=str(0)
					#end if age has a total

					ls_entry.append( s_this_val )

				#end for each possible age

				s_entry="\t".join( ls_entry )

				self.__file_for_age_counts.write(  s_entry + "\n" )
			#end if we are to write the age counts file

			'''
			2018_06_08. We add the ability to sample LD values
			if the flags are set as indicated (see beginning of
			Module for constant settings).
			'''
			if LD_WRITE_SAMPLE==True:
				if len( LD_CYCLES_LIST ) == 0 \
							or ( gen+1 ) in LD_CYCLES_LIST:

					self.__write_ld_on_sample( pop, gen+1, 
								i_num_loci_pairs_to_sample=LD_NUM_PAIRS,
								s_outfile=self.output.basename + ".ld.sample",
								b_sample_linked=LD_SAMPLE_LOCI_LINKED, 
								b_sample_unlinked=LD_SAMPLE_LOCI_UNLINKED,
								s_method=LD_METHOD )

				#end if this cycle should be sampled of LD
			#end if we are to sample LD

		except  Exception as oex:
			raise oex
		#end try...except
		return True
	#end __outputAge

	def __outputMega( self, pop ):
		gen = pop.dvars().gen
		'''
		2017_04_05.  Now using startSave, which was
		formerly suppressed and always set to zero.
		Since the GUI offers it and users excpect
		a 1-based count of cycles, we subtract
		one from the value to get the proper cycle
		as the start.
		'''
		if gen < ( self.input.startSave - 1 ):
			return True
		#end if gen < startSave

		'''
		We write the db info only if we're in orignial output mode:
		'''
		if self.__output_mode == PGOpSimuPop.OUTPUT_ORIG:

			for i in pop.individuals():
				if i.age == 0:
					self.output.megaDB.write("%d %d %d %d %d\n" % (gen, i.ind_id, i.sex(),
									i.father_id, i.mother_id))
				#end if age == 0
			#end for i in pop
		#end if output mode is original	

		return True
	#end __outputMega

	def __setAge( self, pop ):

		probMale = [1.0]

		for sv in self.input.survivalMale:
			probMale.append(probMale[-1] * sv)
		#end for sv in survivalMale

		totMale = sum(probMale)
		probFemale = [1.0]

		for sv in self.input.survivalFemale:
			probFemale.append(probFemale[-1] * sv)
		#end for sv in survivalFemale

		totFemale = sum(probFemale)

		for ind in pop.individuals():
			if ind.sex() == 1:
				prob = probMale
				tot = totMale
			else:
				prob = probFemale
				tot = totFemale
			#end if sex == 1 else not

			cut = tot * random.random()
			acu = 0

			for i in range(len(prob)):

				acu += prob[i]
				if acu > cut:
					age = i
					break
				#end if acu>cut
			#end for i in range

			ind.age = age
		return True
	#end __setAge

	def __set_nb_tolerance( self ):
		'''
		2017_04_03. This def was added after noting
		that the tolerance needed to be computed not only
		initially in __createAge, but also updated after 
		changes to targetNb in def __harvest.
		'''

		f_nbvar=PGInputSimuPop.DEFAULT_NB_VAR if self.input.NbVar is None \
															else self.input.NbVar 

		self.__toleranceNb=self.__targetNb * f_nbvar

		return
	# end __set_nb_tolerance	

	def __createAge( self ):

		pop=self.__pop

		ageInitOps = [
					#InitInfo(lambda: random.randint(0, self.input.ages-2), infoFields='age'),
					sp.IdTagger(),
					#PyOperator(func=self.__outputAge,at=[0]),
					sp.PyOperator(func=self.__setAge, at=[0]),
					]

		

		agePreOps = [
					sp.InfoExec("age += 1"),
					sp.InfoExec("mate = -1"),
					sp.InfoExec("force_skip = 0"),
					sp.PyOperator(func=self.__outputAge),
					]
		
		mySubPops = []

		for age in range(self.input.ages - 2):
			mySubPops.append((0, age + 1))
		#end for age in range

		'''
		2017_02_06
		After meeting with Robin Waples, we decided to make the
		Nb-tolerance used in the __restrictedGenerator part of
		all simulations.  To that end we now use the Nb available
		as part of the N0 caluclation, and call the restrictedGenerator.

		We apply our own tolerance value, currently hidden from the user.
		We'll create new attributes for our self object, and intitialize
		a target Nb with the input objects Nb property, with will 
		usually be the Nb used in the N0 caluclation, unless there is no
		"effective size" section in the config file (hence no Nb/Nc and its
		related Nb), so that the only source of an Nb is the "pop" section 
		of the configuration file (see property "Nb" in the PGInputSimuPop 
		object).
		'''

		self.__targetNb=self.input.Nb

		self.__set_nb_tolerance()	

		self.__selected_generator=None
		'''
		Added 2018_03_13, so that if using NegBinom
		(and gamma list), and also have a target
		Nb, we can havce the restrictedGenerator
		call the fitnessGenerator, which computes using
		gammas.
		'''
		self.__generator_called_by_restricted_generator=None

		'''
		Select a generator based on the input parameters,
		and whether we have a target Nb:
		'''
		if( self.input.doNegBinom ):
			'''
			Changed 2018_03_13, see above.
			'''
			if self.__targetNb is not None:
				self.__selected_generator=self.__restrictedGenerator
				self.__generator_called_by_restricted_generator=self.__fitnessGenerator
				pass
			else:
				self.__selected_generator = self.__fitnessGenerator
			#end use the retricted if target Nb, else don't
		elif self.__targetNb is not None:
			self.__selected_generator = self.__restrictedGenerator
			'''
			Added 2018_03_13, to specify our default litterSkip
			generator, so that as above we can also allow use of the 
			fitness generator as part of the restricted generator's
			tolerance testingm  if the user
			wants a neg binom based fecundity calc and also wants
			to use tolerance testing (see above).
			'''
			self.__generator_called_by_restricted_generator=self.__litterSkipGenerator
		else:
			self.__selected_generator = self.__litterSkipGenerator 
		#end if we want fitness gen,else restricted, else litter skip
		
		'''
		2018_05_17. We add the ability of users to input a recombination intensity.
		So we now create the op list outside the call to HeteroMating, so we can
		add the Recombinator if the user has input a non-zero value. Note that
		the simuPOP docs say:
			"The generic genotype transmitters do not handle genetic recombination. 
			A genotype transmitter Recombinator is provided for such purposes, and 
			can be used with RandomMating and SelfMating (replace 
			MendelianGenoTransmitter and SelfingGenoTransmitter used in these 
			mating schemes)"
		
		2018_08_16.  Note that we have suppressed the recombination controls in the GUI, and
		now run only the recomb. intensity set to zero, i.e. running the MendelianGenoTransmitter
		as the only inheritance simulator, as was the original call used by Tiago.
		'''

		lo_offspring_generator_ops=None

		if self.input.recombination_intensity > 0.0:

			'''
			2018_08_16. A guard against an unforseen execution path to this option, 
			since we want to deactivate recombination.
			'''

			s_msg="Error in initializing the mating scheme mechanism. " \
					+ "The program should not see a non-zero recombination " \
					+ "intensity, but the current value is, " \
					+ str( self.input.recombination_intensity ) \
					+ "." 
			
			raise Exception( s_msg )
			##### rem out, as part of the deactivation of recombination 
#			lo_offspring_generator_ops=[ sp.Recombinator( intensity=self.input.recombination_intensity ), 
#											sp.IdTagger(),
#											sp.PedigreeTagger()]
		else:

			lo_offspring_generator_ops=[ sp.MendelianGenoTransmitter(), sp.IdTagger(),
											sp.PedigreeTagger()]
		#end if we have a recombination intensity, else not	

		mateOp = sp.HeteroMating( [ sp.HomoMating(
									sp.PyParentsChooser( self.__selected_generator ),
									sp.OffspringGenerator(numOffspring=1, 
									ops=lo_offspring_generator_ops,
									sexMode=(sp.PROB_OF_MALES, self.input.maleProb)), weight=1),
									sp.CloneMating(subPops=mySubPops, weight=-1) ],
									subPopSize=self.__calcDemo )

		##### Code Remm'd out
		'''
		2017_02_06
		This is the origial assignment of mateOP before changing the code used to select
		the generator def.
		'''
#		mateOp = sp.HeteroMating( [ 
#					sp.HomoMating(
#					sp.PyParentsChooser(self.__fitnessGenerator if self.input.doNegBinom
#					else (self.__litterSkipGenerator if self.input.Nb_orig_from_pop_section is None else
#					self.__restrictedGenerator)),
#					sp.OffspringGenerator(numOffspring=1, ops=[
#					sp.MendelianGenoTransmitter(), sp.IdTagger(),
#					sp.PedigreeTagger()],
#					sexMode=(sp.PROB_OF_MALES, self.input.maleProb)), weight=1),
#					sp.CloneMating(subPops=mySubPops, weight=-1)],
#					subPopSize=self.__calcDemo )
		##### end temp rem out original

		#Code added 2016_11_01, with new input value "cull_method", we
		#choose our culling def ref accordingly
		def_for_culling=None

		if self.input.cull_method == pgin.PGInputSimuPop.CONST_CULL_METHOD_SURVIVIAL_RATES:
			def_for_culling=self.__cull
		elif self.input.cull_method == pgin.PGInputSimuPop.CONST_CULL_METHOD_EQUAL_SEX_RATIOS:
			def_for_culling=self.__equalSexCull
		else:
			s_msg="In PGOpSimuPop instance, def __createAge, " \
						+ "input object's value for cull_method " \
						+ "is unknown: " + self.input.cull_method \
						+ "."
			raise Exception( s_msg )
		#end if cull method survival rates, equal sex,  else unkown

		#Code revised 2016_11_01 to use the above def_for_culling
		#reference, to assign user-input method:

		##### temp rem out original agePostOps assignment
		'''
		2017_02_07.  We're adding the def __harvest as a post op.

		'''
#		agePostOps = [ sp.PyOperator( func=self.__outputMega ), 
#					sp.PyOperator( func=def_for_culling ) ]
		
		agePostOps = [ sp.PyOperator( func=self.__outputMega ), 
							sp.PyOperator( func=def_for_culling ),
							sp.PyOperator( func=self.__harvest ) ]


		pop.setVirtualSplitter(sp.InfoSplitter(field='age',
			   cutoff=list(range(1, self.input.ages))))

		self.__ageInitOps=ageInitOps
		self.__agePreOps=agePreOps
		self.__mateOp=mateOp
		self.__agePostOps=agePostOps

		return
	#end __createAge

	def __write_interruption_file( self, s_fail_notice ):

		ERR_NOTICE_FILE_EXT="sim.interruption.msg"

		if hasattr( self.output, "basename" ):
			s_err_file_name=self.output.basename + "." + ERR_NOTICE_FILE_EXT
			try:
				o_err_file=open( s_err_file_name, 'w' )
				o_err_file.write( s_fail_notice + "\n" )
				o_err_file.close()
			except IOError as oei:

				'''
				We don't want to rase an exception, since this 
				def is meant to be called before throwing an exception,
				so we know there is a more pertinent error to be thrown
				by the caller.
				'''
				
				s_msg="Warning, in PGOpSimuPop instance, def __cleanup_on_failure, " \
							+ "failed to write file, "  + s_err_file_name \
							+ ", with message: " + s_fail_notice + "." 

				sys.stderr.write( s_msg + "\n" )
			#end try...except IO error
		else:
			s_msg="Warning, in PGOpSimuPop instance, def __write_interruption_file, " \
							+ "failed to find output file basename, to write message: " \
							+ " s_fail_notice." 

			sys.stderr.write( s_msg + "\n" )

		#end if basename exists, else warning

		return
	#end __write_interruption_file

	def __cleanup_on_failure( self, s_reason="Nb tolerance test failure."  ):
		'''
		2017_06_11.  This def was added on request from 
		Brian H. to delete the output files when
		the Nb tolerance test fails.
		'''

		ERR_NOTICE_FILE_EXT="sim.interruption.msg"

		s_fail_notice="\nError:  output interrupted due to " + s_reason + "\n"

		self.__write_interruption_file( s_fail_notice )

		if self.output:
			for s_outfile in [ "out", "err", "megaDB", "genepop" ]:	
				if hasattr( self.output, s_outfile ):
					o_file=getattr( self.output, s_outfile )
					if hasattr( o_file, "close" ):
						o_file.close()
					#end if closable, close
				#end if output has the outfile
			#end close output files, preperatory to removing
		
			for s_outfile_attr in [ "simname", "genname", "dbname", "genepopname" ]:
				if hasattr( self.output, s_outfile_attr ):
					s_outfile_name=getattr( self.output, s_outfile_attr )
					#This utility def only removes a file (files) if it exists:
					pgut.remove_files( [ s_outfile_name ] )
				#end if file name available, close it if exists
			#end for each of the sim output files (except conf and age/pwop records)
		#end if we have an output object
			
		if self.__file_for_nb_records is not None:
			if hasattr( self.__file_for_nb_records, "write" ):
				self.__file_for_nb_records.write( s_fail_notice  )
				self.__file_for_nb_records.close()
			#end if we have a writable nb recores item
		#end if we have a nb records file
				
		if self.__file_for_age_counts is not None:
			if hasattr( self.__file_for_age_counts, "write" ):
				self.__file_for_age_counts.write( s_fail_notice )
				self.__file_for_age_counts.close()
			#end if we have a writable age counts item
		#end if we have an age counts file

		if self.__file_for_het_filter is not None:
			if hasattr( self.__file_for_het_filter, "write" ):
				self.__file_for_het_filter.write( s_fail_notice )
				self.__file_for_het_filter.close()
			#end if we have a writable age counts item
		#end if we have an age counts file

		return
	#end __cleanup_on_failure

	def __write_ld_on_sample( self, o_pop, 
								i_cycle_number, 
								i_num_loci_pairs_to_sample, 
								s_outfile, 
								b_sample_linked, 
								b_sample_unlinked,
								s_method ):
		'''
		2018_06_08. Currently only for testing, as the file written is not
		part of the cleanup routine, nor managed as a member of this class

		If, after filtering linked or unlinked, loci pairs total less than
		the value for i_num_loci_pairs_to_sample, the def samples all available.
		'''
		import itertools

		i_num_loci=len( o_pop.lociNames() )

		ltup_all_pairs=None

		if not( b_sample_linked and b_sample_unlinked ):
			print( "In pgopsimupop instance, def __write_ld_on_sample, " \
						+ "warning, the LD report filter flags, b_sample_linked " \
						+ "and b_sample_unlinked are not yet implemented. "\
						+ "the sampled pairs will be selected without regard to " \
						+ "physical linkage." )
		#end if user has set b_sample_linked or b_sample_unlinked

		ltup_all_pairs=list( itertools.combinations( range( i_num_loci ), 2 ) )

		i_total_pairs_available=len( ltup_all_pairs )

		if i_total_pairs_available < i_num_loci_pairs_to_sample:

			i_num_loci_pairs_to_sample=i_total_pairs_available		

		#end if sample size < population

		ltup_sampled_loci_pairs=random.sample( ltup_all_pairs, i_num_loci_pairs_to_sample )

		lli_sampled_loci_pairs=[ list( thistup ) for thistup in ltup_sampled_loci_pairs ]

		sp.stat( o_pop, LD=lli_sampled_loci_pairs, vars=[ s_method ] )

		o_file=open( s_outfile, 'a' )
	
		ddd_allvars=o_pop.vars()

		dd_ldvals=ddd_allvars[ s_method ]

		for i_first_loci in dd_ldvals:

			for i_second_loci in dd_ldvals[ i_first_loci ]:

				f_ld_value=dd_ldvals[ i_first_loci ][ i_second_loci ]

				i_pos_1=o_pop.locusPos( i_first_loci )
				i_pos_2=o_pop.locusPos( i_second_loci )

				i_chrom_loc_1=o_pop.chromLocusPair( i_first_loci )[0]
				i_chrom_loc_2=o_pop.chromLocusPair( i_second_loci )[0]

				f_distance="inf"

				if i_chrom_loc_1==i_chrom_loc_2:
					f_distance = abs( i_pos_2 - i_pos_1 )
				#end if same chrom

				o_file.write( str( i_cycle_number ) \
						+ "\t" \
						+ "l"  \
						+ str( i_first_loci ) \
						+  "\t" \
						+ "l" \
						+ str( i_second_loci ) \
						+ "\t"  \
						+ str( f_distance ) \
						+ "\t" \
						+ str( f_ld_value ) \
						+ "\n" )

			#end for each second loci
		#end for each first loci	

		o_file.close()
		
		return
	#end __write_ld_on_sample

#end class PGOpSimuPop

if __name__ == "__main__":

	try:
		import agestrucne.pginputsimupop as pgin
		import agestrucne.pgoutputsimupop as pgout
		import agestrucne.pgsimupopresources as pgrec
		import agestrucne.pgparamset as pgps
		import agestrucne.pgutilities as pgut
	except ImportError as ie:
		s_my_mod_path=os.path.abspath( __file__ )
		sys.path.append( s_my_mod_path )
		import agestrucne.pginputsimupop as pgin
		import agestrucne.pgoutputsimupop as pgout
		import agestrucne.pgsimupopresources as pgrec
		import agestrucne.pgparamset as pgps
		import agestucne.pgutilities as pgut
	#end try to get pgmods

	import time
	import argparse	as ap

	LS_ARGS_SHORT=[ "-l", "-c" , "-p" , "-o"  ]
	LS_ARGS_LONG=[ "--lifetable" , "--configfile", "--paramnamesfile", "--outputbase" ]
	LS_ARGS_HELP=[ "life table file",
						"configuration file",
						"param names file (usually: resources/simupop.param.names)",
						"output files base name" ]

	LS_OPTIONAL_ARGS_SHORT=[ "-s" ]
	LS_OPTIONAL_ARGS_LONG=[ "--paramresets" ]
	LS_OPTIONAL_ARGS_HELP=[ "string, comma-delimted list of param name=value pairs, used to reset paramater values"]

	DELIMIT_RESETS=","
	DELIMIT_NAME_VAL_PAIRS="="
	o_parser=ap.ArgumentParser()

	o_arglist=o_parser.add_argument_group( "args" )

	i_total_nonopt=len( LS_ARGS_SHORT )
	i_total_opt=len( LS_OPTIONAL_ARGS_SHORT )

	for idx in range( i_total_nonopt ):
		o_arglist.add_argument( \
				LS_ARGS_SHORT[ idx ],
				LS_ARGS_LONG[ idx ],
				help=LS_ARGS_HELP[ idx ],
				required=True )
	#end for each required argument

	for idx in range( i_total_opt ):
		o_arglist.add_argument( \
				LS_OPTIONAL_ARGS_SHORT[ idx ],
				LS_OPTIONAL_ARGS_LONG[ idx ],
				help=LS_OPTIONAL_ARGS_HELP[ idx ],
				required=False )
	#end for each required argument

	o_args=o_parser.parse_args()

	s_lifetable_file=o_args.lifetable	
	s_conf_file=o_args.configfile
	s_outbase=o_args.outputbase
	PARAM_NAMES_FILE=o_args.paramnamesfile

	o_param_names=pgps.PGParamSet( PARAM_NAMES_FILE )
	o_resources=pgrec.PGSimuPopResources([ s_lifetable_file ] )
	o_input=pgin.PGInputSimuPop(  s_conf_file, o_resources, o_param_names )
	o_output=pgout.PGOutputSimuPop( s_outbase  )
	
	o_input.makeInputConfig()

	if o_args.paramresets:
		ls_resets=o_args.paramresets.split( DELIMIT_RESETS )
		for s_reset in ls_resets:
			ls_name_val=s_reset.split( DELIMIT_NAME_VAL_PAIRS )
			s_param_name=ls_name_val[ 0 ]
			v_val=eval( ls_name_val[ 1 ] )
			setattr( o_input, s_param_name, v_val )
		#end for each param reset
	#end if caller has param resets

	o_op=PGOpSimuPop( o_input, o_output, b_remove_db_gen_sim_files=True )

	o_op.prepareOp()
	o_op.doOp()

#end if

