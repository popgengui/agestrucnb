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
	'''
	MAX_TRIES_AT_NB=100

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
									b_write_nb_and_ages_files=False,
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
			b_write_nb_and_ages_files.  This param was added 20150407
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
		self.__write_nb_and_age_count_files=b_write_nb_and_ages_files
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

		
		if self.__write_nb_and_age_count_files:
			s_nb_values_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "sim_nb_estimates" ]
			s_age_counts_file_ext=pgout.PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "age_counts" ]

			self.__file_for_nb_records=open( self.output.basename + s_nb_values_ext, 'w' )
			self.__file_for_age_counts=open( self.output.basename + s_age_counts_file_ext, 'w' )

			s_header="\t".join( [ "generation" ] \
						+ [ "age" + str( idx ) for idx \
							in range( 1, self.__total_ages_for_age_file + 1 ) ] )

			self.__file_for_age_counts.write( s_header + "\n" )
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

		i_total_loci=self.input.numMSats + self.input.numSNPs

		self.output.writeGenepopFileHeaderAndLociList( \
												self.output.genepop,
												i_total_loci,
												f_this_nbne,
												b_do_compress=False )
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
		'''
		2017_03_08.  This call converts the list
		of cycle range and rate entries in the 
		list attribite nbadjustment into a list
		of per-cycle rate adjustments, used by
		this objects def __harvest.
		'''
		try:
			self.__nb_and_census_adjustment_by_cycle=self.input.makePerCycleNbAdjustmentList()
			self.__createSinglePop()
			self.__createGenome()
			self.__createAge()	
			
			s_basename_without_replicate_number=self.output.basename	
			
			if VERY_VERBOSE==True:
				print( "resetting output basename with tag: " + s_tag_out )
			#end if VERY_VERBOSE

			self.output.basename=s_basename_without_replicate_number + s_tag_out

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
			if self.__guierr is not None:
				self.__guierr( None, str( oex ) )
			#end if using gui messaging
			raise oex
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
			raise oex
		#end try...except

		return
	#end doOp

	def __write_genepop_file( self ):

		if self.__output_mode == PGOpSimuPop.OUTPUT_ORIG:
			i_num_msats=0
			i_num_snps=0
			
			if hasattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS ):
				i_num_msats=getattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS )
			#end if input has num msats

			if hasattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_SNPS ):
				i_num_snps=getattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_SNPS )
			#end if input has number of snps

			i_total_loci=i_num_msats+i_num_snps

			if i_total_loci == 0:
				s_msg= "In %s instance, cannot write genepop file.  MSats and SNPs total zero."  \
						% type( self ).__name__ 
				sys.stderr.write( s_msg + "\n" )
			else:
				#writes all loci values 
				'''
				2017_05_30.  To accomodate new module pgdrivesimulation.py, which
				reads in a conf and does not require a life table, we default an
				NbNe value to zero if the conf file does not supply it.  Note that
				this parameter (Nb/Ne ratio) is not (currently) required for the 
				simulation, but is passed along in the genepop file header to allow 
				for an Nb bias adjustment as read-in and calculated by the 
				pgdriveneestimator.py module.
				'''
				f_this_nbne=0.0

				if hasattr( self.input, "NbNe" ):
					f_this_nbne=self.input.NbNe
				#end if we have an NbNe value, use it.

				self.output.gen2Genepop( 1, 
							i_total_loci, 
							b_pop_per_gen=True,
							b_do_compress=False,
							f_nbne_ratio=f_this_nbne )
			#end if no loci reported
		else:
			s_msg="In PGOpSimuPop instance, def __write_genepop_file, " \
						+ "this def was called but he output mode was " \
						+ "not for the original mode."
			raise Exception( s_msg )
		#end if output mode is orig else not
		return
	#end __write_genepop_file

	def deliverResults( self ):
		return
	#end deliverResults

	def __createGenome( self ):

		size = self.input.popSize
		numMSats = self.input.numMSats
		numSNPs = self.input.numSNPs

		maxAlleleN = 100

		#print "Mutation model is most probably not correct", numMSats, numSNPs
		loci = (numMSats + numSNPs) * [1]
		initOps = []
	
		'''
		2018_02_18.  We are adding a new parameter "het_init_msat",
		which allows the user to enter a value in (0.0,0.85]
		which will be used to compute a set off	allele frequencies 
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
														self.input.startAlleles )

			'''
			Check added 2018_02_18, to make sure our heurisitic
			returned a set of allele freqs:
			'''
			if diri is None:
				s_msg="In PGOpSimuPop instance, def __createGenome, " \
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

		'''
		2018_02_08.  We are adding a new parameter "het_init_snp",
		which allows the user to enter a value in [0.0,0.5]
		which will be used to compute a pair of (diallelic)
		allele frequencies assigned instead of the former 
		hard-coded 0.5 (which is still the default.)
		The call to the new pgutilities def get_roots_quadratic,
		uses coefficients derived from solving for He in the
		expected Het calculation for a loci:
			He = 1 - [ freq_allele_1 ^ 2 + freq_allele_2 ^ 2 ]
		where freq_allele_2 = 1 - freq_allele_1, to get

		-freq^2 + freq - He/2 = 0

		'''

		if self.input.het_init_snp < 0.0 or self.input.het_init_snp > 0.5:
			s_msg="In PGOpSimuPop instance, def __createGenome, " \
						+ "The value for heterozygosity initialization " \
						+ "for SNPs is invalid at " \
						+ str( self.input.het_init_snp )  \
						+ ".  Values are valid in [0.0,0.5]"
			
			raise Exception ( s_msg )
		#end if invalid snp het init value

		lf_roots=pgut.get_roots_quadratic( -1, 1, -1*(self.input.het_init_snp)/2 )

		f_init_snp_freq=None
		
		'''
		We can use either root, since 
		one root gives the freq for one
		allele, whose diallelic partner
		will be the 2nd root and their sum
		will be one.  (Note that for the special
		case of He=0.5, then we'll have one root
		equal to -0.5 and the other to 0.5.  Hence
		we test for a positive root.
		'''
		for f_root in lf_roots:
			if f_root >= 0.0 and f_root <= 0.5:
				f_init_snp_freq=f_root
				break
			#end if positive root
		#end for each root	

		if f_init_snp_freq is None:
			s_msg="In pgOpSimuPop instance, def __createGenome, " \
					+ "the program failed to get an initial allele " \
					+ "frequence for the initial expected heterozygosity " \
					+ "value set at, " + str ( self.input.het_init_snp ) + "."

			raise Exception( s_msg )
		#end if no init frequency

		for snp in range(numSNPs):
			freq = f_init_snp_freq
			initOps.append(
					sp.InitGenotype(
					#Position 0 is coded as 0, not good for genepop
					freq=[0.0, freq, 1 - freq],
					loci=numMSats + snp))
		#end for snp

		preOps = []

		if self.input.mutFreq > 0:
			preOps.append(sp.StepwiseMutator(rates=self.input.mutFreq,
					loci=list(range(numMSats))))
		#end if mufreq > 0

		self.__loci=loci
		self.__genInitOps=initOps
		self.__genPreOps=preOps

		return
	#end __createGenome

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

		pop = sp.Population(popSize, ploidy=2, loci=[1] * nLoci,
					chromTypes=[sp.AUTOSOME] * nLoci,
					infoFields=["ind_id", "father_id", "mother_id",
					"age", "breed", "rep_succ",
					"mate", "force_skip"])

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

			s_msg="The simulation's current pop, number " \
					+ s_pop_number \
					+ ", has an expected " \
					+ "heterozygosity less than the minimum, " \
					+ str( self.min_mean_heterozygosity )  \
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
		#end if very erbose
			

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
			gen post burn in
			'''
			first_gen_to_include = 0 \
					if self.input.startLambda >= PGOpSimuPop.VALUE_TO_IGNORE \
					else self.input.startLambda

			if pop.dvars().gen < first_gen_to_include:
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

				'''
				For comparing Nb values as calculated
				(and accepted) on the pops as generated by simuPop, 
				to those created downstream by NeEstimator.
				'''
				if self.__write_nb_and_age_count_files:
					s_thisNb=str( nb )
					s_thisgen=str( pop.dvars().gen ) 
					self.__file_for_nb_records.write( \
							"\t".join( [ s_thisgen, s_thisNb ] ) \
							+ "\n" )
					'''
					Added 2017_08_24 to allow constantly updated plotting
					in PGGuiSimuPop instances.
					'''
					self.__file_for_nb_records.flush()
				#end if we are to write the nb value file

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

			if attempts > PGOpSimuPop.MAX_TRIES_AT_NB:
				s_msg="In PGOpSimuPop instance, " \
							+ "def __restrictedGenerator, " \
							+ "for generation, " + str( pop.dvars().gen ) \
							+ ", after " + str( PGOpSimuPop.MAX_TRIES_AT_NB ) \
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

			#end if attempts > MAX_TRIES_AT_NB

		#end while not nbOK

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
		for idx in range( self.input.numSNPs + self.input.numMSats ):
			sp.stat(pop, alleleFreq=[idx])
			lf_hetvals.append( 1 - sum([x*x for x in pop.dvars().alleleFreq[idx].values()]) )
		#end for each loci

		return numpy.mean( lf_hetvals )
	#end __get_mean_heterozygosity_over_all_loci

	def __outputAge( self, pop ):
		try:

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
						self.__file_for_het_filter.write( str( gen ) + "\t" \
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
			if self.__write_nb_and_age_count_files:
				ls_entry=[ str( gen ) ]
				
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

		mateOp = sp.HeteroMating( [ sp.HomoMating(
									sp.PyParentsChooser( self.__selected_generator ),
									sp.OffspringGenerator(numOffspring=1, 
									ops=[ sp.MendelianGenoTransmitter(), sp.IdTagger(),
										sp.PedigreeTagger()],
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
		import pgutilities	 as pgut
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

