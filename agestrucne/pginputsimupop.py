'''
Description

Retrieves and prepares data needed to run simuPop.  See class description.

'''
from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object
from past.utils import old_div
__filename__ = "pginputsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

START_LAMBDA_IGNORE=99999
LAMBDA_IGNORE=1.0
DEFAULT_NB_VAR=0.05
DEFAULT_SNP_HET_INIT=0.5
DEFAULT_MSAT_HET_INIT=0.8

import sys
import os
from configparser import ConfigParser
from agestrucne.pgutilityclasses import NbAdjustmentRangeAndRate

class PGInputSimuPop( object ):

	'''
	Object meant to fetch parameter values and prepare them for 
	use in a simuPop simulation.  

	Object to be passed to a PGOpSimuPop object, which is, in turn,
	passed to a PGGuiSimuPop object, so that the widgets can then access
	defs in this input object, in order to, for example, show or allow
	changes in parameter values for users before they run the simulation.
	'''
	
	#Add prefix "CONST" so pgguisimupop instances
	#can ignore these as non-parameterized attributes
	CONST_CULL_METHOD_SURVIVIAL_RATES="survival_rates"
	CONST_CULL_METHOD_EQUAL_SEX_RATIOS="equal_sex_ratio"

	def __init__( self, s_config_file = None, o_model_resources = None, o_param_names=None ):
		'''
		param s_config_file, parseable by ConfigParser, params for 
			running simuPop, or references into the resources
			object.  Note that this config file must have a
			section called "model" with a "name" option, which
			should match a name key in the PGModelResources objects
			dictionary.

		param o_model_resources, object of type PGModelResources,
			whose member dictionary has the sub-dictionaries
			that have the param values not given in the config file,
			such as fecundity and reproductive values, and exposed
			via calls to is getValue def.

		param o_param_names, object ot type PGParamSet,
			that gives a shortname (attribute name)
			and a longname (readable text), for each 
			param in the simpupop configuration attribute 
			list
		'''
		self.__config_parser=None
		self.__resources=o_model_resources
		self.__param_names=o_param_names

		#for writing current param values to a new config file,
		#and updated as attributes are created either by reading
		#in the orig config file in def get_config, or by adding the parameter
		#in def addParameter:
		self.__config_file_option_name_by_attribute_name={}		

		self.__config_file_section_name_by_attribute_name={}
		if s_config_file is not None:
			self.__full_config_file_name=s_config_file
			self.config_file=os.path.basename( s_config_file )
			self.__make_config_parser( s_config_file )
		#end if we have a conf file
	
		return
	#end def __init__
  
	def __find_resources( self, s_model_name, s_config_file_value ):
		'''
		if eval works, then the values are in the original conf file.
		else if eval call raises NameError, then it names a value 
		the conf file gave in form dict[ species ], one of the 
		dictionaries that should be available in the PGModelResources 
		member instance.
		'''
		v_value=None

		try: 

			v_value=eval (s_config_file_value )

		except NameError as ne:

			if self.__resources is not None:
				
				ls_dict_item_split=s_config_file_value.split( "[" )
				s_dict_name=( ls_dict_item_split[ 0 ] ).strip()
				s_gamma_list_key=ls_dict_item_split[ len( ls_dict_item_split ) - 1 ]
				s_gamma_list_key=s_gamma_list_key.replace( "]", "" )

				#resoures configuration file, written using the dictinaries in tiagos
				#myUtils file, has a main section 'resources' for 
				#values that tiago coded dict[ species ]=value, where value is a list
				#or int, but also has dictionary values (gammaAMale has
				#dictionary value), which require the dict name to be a section name
				#so that the key or keys can be used for the key=value portion
				v_value=self.__resources.getLifeTableValue( s_model_name, s_dict_name, s_gamma_list_key )

				if v_value is None:
					v_value=self.__resources.getLifeTableValue( s_model_name, 'resources', s_dict_name )
				#end if we got none returned when we tried to name the section, then  use 'resources'
			else:
				raise Exception ( "input object for PGInputSimuPop has no resources, " \
						"but the value in the configuration file parser , " \
						+ s_config_file_value + " can't be resolved by eval(): " \
						+ str( ne ) )
			#end if we have a resources file to deal
			#with the NameError value, else not
		#end try  to evaluate the string, excpet, go to resources

		return v_value

	#end __find_resources

	def __make_config_parser( self, s_resources_file_name ):
		self.__config_parser = ConfigParser()
		self.__config_parser.read(s_resources_file_name )
	#end __maake_config_parser

	def __update_attribute_config_file_info( self, s_attribute_name, s_section_name, s_option_name ):
		'''
		updates the member dictionaries that tie attribute names to
		config file sections and option names, to facilitate
		writing the current attribute set back to a configuration file
		'''

		self.__config_file_section_name_by_attribute_name[ s_attribute_name ]=s_section_name
		self.__config_file_option_name_by_attribute_name[ s_attribute_name ]=s_option_name
		return
	#end __update_attribute_config_file_info

	def makePerCycleNbAdjustmentList( self ):
		'''
		2017_03_09. This def converts the input param list of range strings 
		of form min-max:rate, into a list of floats, such that list indexes 
		that range from min-1 to max-1 have value rate.  The latter list is
		returned.

		This def is called from class PGOpSimuPop object instances
		in their prepareOp def, for use in their def __harvest.
		'''

		lf_rates=None

		try:
			lf_rates=[ 0.0 for idx in range( self.gens ) ]
			
			for s_rate_and_range in self.nbadjustment:

				o_raterange=NbAdjustmentRangeAndRate( 2, self.gens, s_rate_and_range )

				#we use the list indexes and cycle number minus 1	
				#note that the effects of harvest are such that
				#the nth cycle's pop and Nb are changed at the end
				#of cycle n-1.  Also note that simupop orders cycles
				#on zero-indexed values:
				i_start_cycle=o_raterange.start_cycle-2 \
							if o_raterange.start_cycle > 1 else 0

				i_end_cycle=o_raterange.end_cycle - 1 \
							if o_raterange.end_cycle > 1 else 0

				for idx in range( i_start_cycle, i_end_cycle ):
					lf_rates[ idx ] = o_raterange.rate
				#end for each idx in range
			#end for each range and rate setting

		except Exception as oex:

			s_msg="In PGInputSimuPop instance, def " \
						+ "__update_attribute_nb_adjustement_by_cycle, " \
						+ "an exception was raised evaluating the nbadjustment " \
						+ "list: " + str( self.nbadjustment ) \
						+ "\nException message: " + str( oex )

			raise Exception( s_msg )

		#end try ... except

		return  lf_rates
	#end makePerCycleNbAdjustmentList
			
	def __get_effective_size_info_if_avail( self ):

		o_parser=self.__config_parser

		dv_values={ "Nb":None, "NbNc":None, "NbNe":None }
		do_types_by_name={ "Nb":int, "NbNc":float, "NbNe":float }

		for s_this_option in dv_values:

			s_this_value=None
			v_this_value=None

			if o_parser.has_option( "effective_size", s_this_option ):
				s_this_value=o_parser.get( "effective_size", s_this_option )
			else:
				if self.__resources is not None:
					#Returns None is no such section/options in the life table config 
					#parser
					s_this_value=self.__resources.getLifeTableValue( \
												self.model_name, "effective_size", s_this_option )
				#end if we have life tables, check
			#end if not in config file, check life table

			if s_this_value is not None:
				try:
					v_this_value=do_types_by_name[ s_this_option ] ( s_this_value )
				except Exception as oex:
					s_msg="In PGInputSimuPop instance, def __get_effective_size_info_if_avail, " \
							+ "there was an error converting the value, " \
							+ str( s_this_value  ) + ", for " + s_this_option \
							+ ", into its proper type, " + str( do_types_by_name[ s_this_option ] ) \
							+ "."
					raise Exception( s_msg )
				#end try...except
			#end if value not None
			
			dv_values[ s_this_option ] = v_this_value
		#end for each option in effective size section
		return ( dv_values[ "Nb" ], dv_values[ "NbNc" ], dv_values[ "NbNe" ] )
	#end __get_effective_size_info_if_avail

	def __get_config( self ):

		DEFAULT_CULL_METHOD="survival_rates"

		config=self.__config_parser

		s_model_name=config.get( "model", "name" )

		self.model_name=s_model_name
		
		self.__update_attribute_config_file_info( "model_name", "model", "name" )

		self.__N0_from_pop_section = config.getint("pop", "N0")

		self.popSize = config.getint("pop", "popSize")
		self.__update_attribute_config_file_info( "popSize", "pop", "popSize" )

		self.ages = self.__find_resources( s_model_name,  config.get("pop", "ages"))
		self.__update_attribute_config_file_info( "ages", "pop", "ages" )

		if config.has_option("pop", "isMonog"):
			self.isMonog = config.getboolean("pop", "isMonog")
		else:
			self.isMonog = False
		#end if isMonog else not
		self.__update_attribute_config_file_info( "isMonog", "pop", "isMonog" )

		if config.has_option("pop", "forceSkip"):	
			'''
			2017_05_19.  Orignially this probability value was read 
			in as a percentage (only present in 2 of the 100emperor
			config files, and set to 21) and then divided by 100.  
			However, because the GUI will store the assigned value, 
			it is simplest to avoid any manipulation of the value 
			when it is read in.  We simply require a value in [0.0,1.0].
			'''

			self.forceSkip = config.getfloat( "pop", "forceSkip" )

			if self.forceSkip < 0.0 or self.forceSkip > 1.0:
				s_msg="In PGInputSimuPop instance, def __get_config, " \
							+ "the configuration file's value for forceSkip, " \
							+ str( self.forceSkip ) + ", " \
							+ "is not valid.  It should be a float in the range, " \
							+ "0.0 <= float <= 1.0."  
				
				raise Exception( s_msg )
			#end if forceSkip not a valid value
		else:
			self.forceSkip = 0.0
		#end if forceSkip, else not
		self.__update_attribute_config_file_info( "forceSkip", "pop", "forceSkip" )

		if config.has_option("pop", "skip"):
			self.skip = self.__find_resources( s_model_name,  config.get("pop", "skip"))
		else:
			self.skip = None
		#end if skip, else not
		self.__update_attribute_config_file_info( "skip", "pop", "skip" )

		if config.has_option("pop", "litter"):
			self.litter = self.__find_resources( s_model_name,  config.get("pop", "litter"))
		else:
			self.litter = None
	    #end if config has litter
		self.__update_attribute_config_file_info( "litter", "pop", "litter" )

		if config.has_option("pop", "male.probability"):
			self.maleProb = config.getfloat("pop", "male.probability")
		else:
			self.maleProb = 0.5
		#end if male.prob, else not
		self.__update_attribute_config_file_info( "maleProb", "pop", "male.probability" )

		if config.has_option("pop", "gamma.b.male"):
			self.doNegBinom = True
			self.gammaAMale = self.__find_resources( s_model_name,  config.get("pop", "gamma.a.male"))
			self.gammaBMale = self.__find_resources( s_model_name,  config.get("pop", "gamma.b.male"))
			self.gammaAFemale = self.__find_resources( s_model_name,  config.get("pop", "gamma.a.female"))
			self.gammaBFemale = self.__find_resources( s_model_name,  config.get("pop", "gamma.b.female"))
			self.__update_attribute_config_file_info( "gammaAMale", "pop", "gamma.a.male" )
			self.__update_attribute_config_file_info( "gammaAFemale", "pop", "gamma.a.female" )
			self.__update_attribute_config_file_info( "gammaBMale", "pop", "gamma.b.male" )
			self.__update_attribute_config_file_info( "gammaBFemale", "pop", "gamma.b.female" )
		else:
			self.doNegBinom = False
	    #end if config.has gamma.b.male, then get all gammas
		#note that this def (sourced from Tiago's code) does not check for "doNegBinom",
		#but it is inferred from presence/absense of the gamma.b.male (as are all gamma{A,B} params)
		#but should be no harm in adding it to a written config file, where if won't be read
		#by this def:
		self.__update_attribute_config_file_info( "doNegBinom", "pop", "doNegBinom" )

		if config.has_option("pop", "survival"):
			self.survivalMale = self.__find_resources( s_model_name,  config.get("pop", "survival"))
			self.survivalFemale = self.__find_resources( s_model_name,  config.get("pop", "survival"))
		else:
			self.survivalMale = self.__find_resources( s_model_name,  config.get("pop", "survival.male"))
			self.survivalFemale = self.__find_resources( s_model_name,  config.get("pop", "survival.female"))
		#end if pop survival else not
		self.__update_attribute_config_file_info( "survivalMale", "pop", "survival.male" )
		self.__update_attribute_config_file_info( "survivalFemale", "pop", "survival.female" )


		self.fecundityMale = self.__find_resources( s_model_name,  config.get("pop", "fecundity.male"))
		self.__update_attribute_config_file_info( "fecundityMale", "pop", "fecundity.male" )
		self.fecundityFemale = self.__find_resources( s_model_name,  config.get("pop", "fecundity.female"))
		self.__update_attribute_config_file_info( "fecundityFemale", "pop", "fecundity.female" )

		if config.has_option("pop", "startLambda"):
			self.startLambda = config.getint("pop", "startLambda")
			self.lbd = config.getfloat("pop", "lambda")
			#self.lbd = mp.mpf(config.get("pop", "lambda"))
		else:
			'''
			2018_01_09. We change the default so that if the conf file has no startLambda 
			(i.e.  total burn-in cycles), instead of setting it to START_LAMBDA_IGNORE, 
			we'll set it equal to to the number of age classes, the usually appropriate
			value for this param. This change depends on the self.ages attribute being 
			already read-in and/or set earlier in this def (see also 
			def __reset_start_lambda_using_ages).
			'''
			#self.startLambda = START_LAMBDA_IGNORE
			self.startLambda=None
			self.__reset_start_lambda_using_ages()
			#self.lbd = mp.mpf(1.0)
			self.lbd = LAMBDA_IGNORE
		#end if startLambda, else not
		self.__update_attribute_config_file_info( "startLambda", "pop", "startLambda" )
		self.__update_attribute_config_file_info( "lbd", "pop", "lambda" )

		if config.has_option("pop", "Nb"):
			''''
			minimal change to Tiagos code so we can read in a "None" value
			for Nb, if such has been entered in config file. (Allows
			regularization of writing config files based on an input objects
			set of parameters)
			'''
			v_nb_val=eval( config.get( "pop", "Nb" ) ) 

			'''
			As of 2016_10_14, we don't want to accept on-None values
			for nb in the pop section, as we now only use a given Nb
			as supplied in an (optional) "effective_size" section
			(section can be in config file (checked first) or
			life table (see below).
			'''
			if v_nb_val is not None:
				s_msg="In PGInputSimuPop instance, def get_config, " \
						+ "the config file's \"pop\" section has a " \
						+ "non None value for parameter \"Nb\".  As " \
						+ "of 2016_10_14, the simulation operation "\
						+ "ignores Nb values (and NbVar values given "\
						+ "the config file \"pop\" section.  " \
					 	+ "It is now only used when supplied "\
						+ "in an \"effective_size\" section.  Nb is now " \
						+ "used only to compute N0 when Nb and Nb/Nc are supplied " \
						+ "(if no Nb and Nb/Nc is supplied, an N0 value should be " \
						+ "supplied in the config files \"pop\" section."
				raise Exception( s_msg )
			#end if an Nb val was found in the pop section, error

			self.__Nb_from_pop_section = None if v_nb_val is None else config.getint("pop", "Nb")

		else:
			self.__Nb_from_pop_section = None
		#end if config has Nb, else not


		if config.has_option( "pop", "NbVar" ):
			v_nbvar=eval( config.get( "pop", "NbVar" ) )

			self.NbVar=DEFAULT_NB_VAR if v_nbvar is None else config.getfloat( "pop", "NbVar" )		
		else:
			self.NbVar=DEFAULT_NB_VAR
		#end if NbVar present, else use default

		self.__update_attribute_config_file_info( "_PGInputSimuPop__Nb_from_pop_section", "pop", "Nb" )
		self.__update_attribute_config_file_info( "NbVar", "pop", "NbVar" )

		self.startAlleles = config.getint("genome", "startAlleles")
		self.__update_attribute_config_file_info( "startAlleles", "genome", "startAlleles" )

		self.mutFreq = config.getfloat("genome", "mutFreq")
		self.__update_attribute_config_file_info( "mutFreq", "genome", "mutFreq" )

		self.numMSats = config.getint("genome", "numMSats")
		self.__update_attribute_config_file_info( "numMSats", "genome", "numMSats" )

		if config.has_option("genome", "numSNPs"):
			self.numSNPs = config.getint("genome", "numSNPs")
		else:
			self.numSNPs = 0
		#end if config has numSNps else not

		self.__update_attribute_config_file_info( "numSNPs", "genome", "numSNPs" )

		self.reps = config.getint("sim", "reps")
		self.__update_attribute_config_file_info( "reps", "sim", "reps" )
		if config.has_option("sim", "startSave"):
			self.startSave = config.getint("sim", "startSave")
			'''
			2017_04_05.  This is a correction for old configuration
			files that were using the old default startSave value 
			of 0 (now default is 1).
			'''
			if self.startSave==0:
				self.startSave=1
			#end if startsave is zero

		else:
			'''
			2017_04_05.  As we re-activate the startSave feature,
			with a control on the GUI interface, we now use 1-indexed
			cycle numbers, so that the code during the simulation will 
			(before writing results) check whether the gen number equals 
			the startSave - 1.  Thus, the default startSave, to record all 
			cycles, is now 1 instead of zero.
			'''
			self.startSave = 1
		#end if config has startSave

		self.__update_attribute_config_file_info( "startSave", "sim", "startSave" )

		self.gens = config.getint("sim", "gens")
		self.__update_attribute_config_file_info( "gens", "sim", "gens" )

		self.dataDir = config.get("sim", "dataDir")
		self.__update_attribute_config_file_info( "dataDir", "sim", "dataDir" )

		#See the getter property def "N0".  If available, Nb and NbNc, 
		#from a life table or config file section "effective_size",
		#will be used to calculate N0.  Otherwise the NO from the "pop" section
		#will be used.
		i_nb_from_eff_size_info, f_nbnc_ratio_from_eff_size_info, f_nbne_from_eff_size_info= \
								self.__get_effective_size_info_if_avail()
		
		if i_nb_from_eff_size_info is not None \
					and f_nbnc_ratio_from_eff_size_info is not None:
			#Note that this value may exist along with Nb
			#from the config file "pop" section:

			self.__Nb_from_eff_size_info=i_nb_from_eff_size_info

			self.NbNc=f_nbnc_ratio_from_eff_size_info
			self.__update_attribute_config_file_info( \
					"_PGInputSimuPop__Nb_from_eff_size_info", 
												"effective_size", "Nb" )
			self.__update_attribute_config_file_info( "NbNc", "effective_size", "NbNc" )
		#end if we compute N0, else use given 	

		if f_nbne_from_eff_size_info is not None:
			self.NbNe=f_nbne_from_eff_size_info
			self.__update_attribute_config_file_info( "NbNe", "effective_size", "NbNe" )
		#end if we have an nb/ne ratio value

		self.__update_attribute_config_file_info( "N0", "pop", "N0" )

		if config.has_option("sim", "cull_method"):
			self.cull_method = config.get("sim", "cull_method")
		else:
			self.cull_method = DEFAULT_CULL_METHOD
		#end if config has sim, cull_method
		self.__update_attribute_config_file_info( "cull_method", "sim", "cull_method" )

		'''
		2017_03_07.  Adding list of strings of form m-n:r, that gives a range of
		cycles, m to n, for eacho f which to use pgopsimupop def __harvest to
		adjust Nb and Nc (the census) by proportion r.
		'''
		if config.has_option( "sim", "nbadjustment" ):
			'''
			We expect a config entry that will eval as a list of strings.
			'''
			self.nbadjustment=eval( config.get( "sim", "nbadjustment" ) )
			'''
			2017_04_05.  After changing the implementation of the nb adjustment 
			parameter to better sync with cycle numbers, we set the minimum 
			possible cycle number at 2 instead of 1 (which would have no effect, 
			since the harvest, which makes the population and Nb adjustments,
			needs an existing pop, i.e., can operate only after at least one
			pop has been created).  We correct any nb adjustment list that was
			saved before this change.
			'''

			self.__correct_min_cycle_in_nb_adjustment_list()
		else:

			s_msg="In PGInputSimuPop instance, " \
					+ "def __get_config, " \
					+ "the program cannot find the attribute \"gens\", " \
					+ "giving the total cycles to be simulated."
			assert self.gens, s_msg

			'''
			2017_05_16.  We change the default setting of the nbadjustment.
			Instead of the range "2-" + str(self.gens), we'll intialize as 2-2:0.0. 
			This is better, because the user can change the number of cycles
			int the PGGuiSimuPop instance, and, unless ages is then lower than 2,
			the value here is consistent, and won't cause an error to be raised 
			when the sim's "run" button is clicked,the error from the consistency check
			between the number of cycles value and the entries for nbadjustment.
			Note, too that the 0.0 rate means no adjustment will be made.
			'''
			self.nbadjustment=[ "2-2:0.0" ]
		#end if the config file has an nbadjustment list else make one

		self.__update_attribute_config_file_info( "nbadjustment", "sim" , "nbadjustment" )

		'''
		These two params are added 2017_08_08, to allow the gui to pass 
		an output mode of type PGOpSimuPop.OUTPUT_GENEPOP_HET_FILTERED
		and a set of parameters to produce output restricted to 
		pop sections with mean expected heterozygosity within a range,
		and to stop saving such filtered pops after a total have been
		recorded.
		'''
		if config.has_option("sim", "do_het_filter" ):
			self.do_het_filter = config.getboolean("sim", "do_het_filter")
		else:
			self.do_het_filter=False
		#end if config has sim, cull_method
		self.__update_attribute_config_file_info( "do_het_filter", "sim", "do_het_filter" )

		if config.has_option("sim", "het_filter" ):
			self.het_filter = config.get("sim", "het_filter")
		else:
			self.het_filter="0.00,1.00,99999"
		#end if config has sim, cull_method
		self.__update_attribute_config_file_info( "het_filter", "sim", "het_filter" )

		'''
		2018_02_08.  We are adding a parameter, "het_init_snp", which will 
		then determine the initial SNP allele frequencies. (See pgopsimupop.py,
		def??)
		'''
		if config.has_option( "sim", "het_init_snp" ):
			self.het_init_snp=config.getfloat("sim", "het_init_snp")
		else:
			self.het_init_snp=DEFAULT_SNP_HET_INIT
		#end if we have an initial expected het
		self.__update_attribute_config_file_info( "het_init_snp", "sim", "het_init_snp" )

		'''
		2018_02_18.  We also adding a parameter, "het_init_msat", which will 
		then determine the initial Msat allele frequencies. 
		'''
		if config.has_option( "sim", "het_init_msat" ):
			self.het_init_msat=config.getfloat("sim", "het_init_msat")
		else:
			self.het_init_msat=DEFAULT_MSAT_HET_INIT
		#end if we have an initial expected het

		self.__update_attribute_config_file_info( "het_init_msat", "sim", "het_init_msat" )

		return
	#end __get_config

	def __correct_min_cycle_in_nb_adjustment_list( self ):
		for idx in range( len(  self.nbadjustment ) ):
			s_entry=self.nbadjustment[ idx ]
			if s_entry.startswith( "1-" ):
				s_new_entry="2-" + s_entry[ 2: ]
				self.nbadjustment[ idx ] = s_new_entry 
			#end if entry has start cycle 1, should be 2
		#end for each entry
		return
	#end __correct_min_cycle_in_nb_adjustment_list

	def __reset_start_lambda_using_ages( self ):
		'''
		Added 2017_02_25, to enable a default start lambda 
		(the burn-in cycles total) that is compatible with
		the new default use of the PGOpSimuPop __restrictedGenerator,
		which applies a test for an Nb tolerance.  Any reasonable
		tolerance will not be reached in the pre-burnin cycles, so that
		the default of 0 burnin cycles (startLambda=99999) is now
		likely to make the simulation fail due to being unable to
		reach an Nb within target, in the pre-burn-in cycles.  Using
		the total age classes as the total burn-in cycles should
		allow the Nb to stabalize within a reasonable tolerance before
		the tolerance test is applied.

		This def is called by def self.makeInputConfig 
	
		2018_01_09.  This call created a bug, since the GUI and the
		pgdrivesimulation.py module both allow users to set the burn-in
		(i.e. startLambda) parameter, but this call was resetting it to
		the number of age classes.  We revise it now to only set it to
		the number of age classes if its current value is None.
		'''

		if self.startLambda is None:
			s_errmsg="In PGInputSimuPop instance " \
							+ "def __reset_start_lambda_using_ages, " \
							+ "a reset of the start lambda (burn-in setting) " \
							+ "failed.  No \"ages\" parameter was found."
			assert self.ages, s_errmsg 

			self.startLambda=self.ages
		#end if no startLambda, set it to total ages
				 
		return
	#end __reset_start_lambda_using_ages

	def __compute_n0_from_eff_size_info( self ):

		'''
		2016_11_04
		Revising by incorporating Brian Trethway's new calc method 
		(adapted from his module Sample_testing.py, which he pushed to
		our github repo a few days ago).
		'''

		i_n0=None
		
		#First make sure we have the parmeters in our input object:
		ls_required_params=[ "NbNc", "_PGInputSimuPop__Nb_from_eff_size_info", "survivalFemale",
							"survivalMale", "maleProb" ]
		
		ls_missing_params=[]

		for s_param_name in ls_required_params:
			if not hasattr( self, s_param_name ):
				ls_missing_params.append( s_param_name )
			#end if our input object does not have the attribute
		#end for each param

		if len( ls_missing_params ) != 0:
			s_msg="In PGInputSimuPop instance, def __compute_n0_from_eff_size_info, " \
						+ "Unable to caluclate N0 due to missing parameter(s): " \
						+ ", ".join( ls_missing_params ) + "."
			raise Exception( s_msg )
		#end if one or more params missing

		f_female_ratio = 1-self.maleProb

		if self.NbNc < 0.0:
			s_msg=" In PGInputSimuPop instance, def __compute_n0_from_eff_size_info, " \
									+ "N0 calculation requires an NbNc ratio " \
									+ "greater than or equal to zero, current value: " \
									+ str( self.NbNc ) + "."

			raise Exception( s_msg )

		#end if NbNc is zero raise error

		if self.NbNc != 0:

			f_Nc = old_div(float( self.__Nb_from_eff_size_info ), float( self.NbNc ))
		else:
			f_Nc=0

			s_msg="Warning:  in PGInputSimuPop instance, def __compute_n0_from_eff_size_info, " \
					"NbNc value is zero, so Nc value is set to zero."
			sys.stderr.write( s_msg + "\n" )
		#end if NbNc is zero, then nc=nb/nbnc, else nc is zero

		f_current_male_prop=self.maleProb
		f_current_female_prop=f_female_ratio
		f_cum_pop_porp = 1

		#Assumes male and female survivals have same length
		for i_age in range(len(self.survivalMale)):
			#calcualte new male Ratio
			f_current_male_prop = f_current_male_prop * self.survivalMale[i_age]
			#calculate new female ratio
			f_current_female_prop = f_current_female_prop * self.survivalFemale[i_age]
			#add to cumulative
			f_cum_pop_porp+=f_current_male_prop
			f_cum_pop_porp+=f_current_female_prop
		#end for each age in male survival list

		#calulate N0
		if f_cum_pop_porp <= 0.0:
			s_msg=" In PGInputSimuPop instance, def __compute_n0_from_eff_size_info, " \
									+ "variable cum_pop_proportion expected to be " \
									+ "greater than zero.  The current value: " \
									+ str( f_cum_pop_porp ) + "." 

			raise Exception( s_msg )
		#end if invalid value for f_cum_pop_porp

		i_n0 = int( round ( old_div(f_Nc,f_cum_pop_porp) ) )
		
		return i_n0
	#end __compute_n0_from_eff_size_info

	def setupConfigParser( self, s_config_file_name ):
		self.config_file=os.path.basename( s_config_file_name )
		self.__make_config_parser( s_config_file_name )
		return
	#end setupResources  
	
	def getConfigParserOption( self, s_section_name, s_option_name ):
		s_val=None
		if self.__config_parser is not None:
			if self.__config_parser.has_section( s_section_name ):
				if self.__config_parser.has_option( s_section_name, s_option_name ):
					s_val = self.__config_parser.get( s_section_name, s_option_name )
				#end if has option
			#end if has section
		#end if parser
		return s_val
	#end getConfigOption

	def addParameter( self, s_attribute_name, v_attribute_value, 
			s_config_file_option_name, 
			s_config_file_section_name ):
		'''
		If user wants to add a parameter not in the current set of params as read
		in from the config file source of this instance, this def will both add the 
		param and value, plus update the member dictionaries that facilitate
		writing a new config file that includes this parameter.  Note that the
		arg s_config_file_option_name is necessitated by Tiago's standards in 
		his config files, as he often uses an attribute name different
		from the option name that gives the value.
		'''
		setattr( self, s_attribute_name, v_attribute_value )
		self.__update_attribute_config_file_info( s_attribute_name, s_config_file_section_name, 
				s_config_file_option_name )
		return
	#end addParameter

	def __get_configparser_input_params( self ):

		'''
		make a ConfigParser object using the current set of input parmater 
		attribute values, using the param_names member attribute to 
		to find the attribute names for the parameters used in the simupop
		simulation run
		'''

		if self.__param_names is None:
			s_msg="In PGInputSimuPop instance, can't write config file" \
					+ ": missing the required PGParamSet object."
			raise Exception( s_msg )
		#end if no parma set object

		o_parser=ConfigParser()
		o_parser.optionxform=str

		ls_attribute_names=list(self.__config_file_section_name_by_attribute_name.keys())

		for s_attribute in ls_attribute_names:

			s_section_name=self.__config_file_section_name_by_attribute_name[ s_attribute ]
			s_option_name=self.__config_file_option_name_by_attribute_name[ s_attribute ]

			if s_section_name not in o_parser.sections():
				o_parser.add_section( s_section_name )
			#end if new section

			o_parser.set( s_section_name, s_option_name, str( getattr( self, s_attribute ) ) ) 
		#end for each attribue

		return o_parser
	#end __get_configparser_input_params

	def getDictParamValuesByAttributeName( self ):
		'''
		Note that this algorithm simply skips
		over paramters with names in the PGParamSet
		object, but without a corresponding attribute
		in this (self) instance.
		'''
		dv_param_values_by_name={}

		if self.__param_names is None:
			s_msg="In PGInputSimuPop instance, can't get dict of param/values" \
					+ ": missing the required PGParamSet object."
			raise Exception( s_msg )
		#end if no parma set object

		ls_attribute_names=self.param_names.shortnames

		for s_name in ls_attribute_names:
			if hasattr( self, s_name ):
				dv_param_values_by_name[ s_name ]=getattr( self, s_name )
			#end if hasattr
		#end for each param name
		
		return dv_param_values_by_name
	#end getDictParamValuesByAttributeName

	def writeInputParamsToFileObject( self, o_file ):

		o_parser=self.__get_configparser_input_params()
		o_parser.write( o_file )

		return
	#end writeInputParamsToFileObject

	def writeInputParamsAsConfigFile( self, s_outfile_name ):
		o_parser=self.__get_configparser_input_params()
		
		if os.path.isfile( s_outfile_name ):
			s_msg="In PGInputSimuPop instance, " \
						+ "can't write to file "  \
						+ s_outfile_name \
						+ ": file exists."
			raise Exception( s_msg  )
		#end if file exists

		o_file=open( s_outfile_name, 'w' )
		o_parser.write( o_file )
		o_file.close()
		return
	#end writeInputParamsAsConfigFile

	def makeInputConfig( self ):
		self.__get_config()
		self.__make_params_whose_values_are_lists_have_uniform_item_types()
		'''
		Added 2017_02_25, to enable a default start lambda 
		(the burn-in cycles total) that is compatible with
		the new default use of the PGOpSimuPop __restrictedGenerator.

		2018_01_09. In resolving the bug that this caused, i.e. that
		resetting the value of startLambda in the GUI or the pgdrivesimulation.py
		module was not taking effect (rather, the call below was resetting
		it to the number of age classes), we've changed the reset def (see) 
		to keep any non-None value for startLambda, and only revert to ages
		if startLambda is currently python's None value.
		'''
		self.__reset_start_lambda_using_ages()
		return
	#end makeInputConfig

	@property 
	def param_names( self ):
		return self.__param_names
	#end def paramnames

	@param_names.setter
	def param_names( self, o_param_names ):
		self.__param_names=o_param_names
		return
	#end paramnames

	def copyMe( self ):
		o_copy=PGInputSimuPop( self.__full_config_file_name,
				self.__resources,
				self.__param_names )

		#update input object with any param values
		#changed after reading in the config file
		#(for example, changed in the gui interface):
		dv_param_vals_by_name=self.getDictParamValuesByAttributeName()
		for s_param_name in dv_param_vals_by_name:
			setattr( o_copy, s_param_name, dv_param_vals_by_name[ s_param_name ] )
		#end for each param name

		return o_copy
	#end copyMe

	def __make_params_whose_values_are_lists_have_uniform_item_types( self ):

		'''
		Some lists as given in configuraion files have "0" entered as one item, 
		which the python's "eval" call evaluates as an int, while other items 
		in the lists have decimals, such as "32.2", which is evaluated as a float 
		type.  In these cases, in order to manage input by users, when
		this object is tied to a GUI, we want uniform types, and so will promote
		these ints to floats.  Note that as of 2016_09_20, we only correct his case.
		If we find paramaters (as given by our member PGParamSet object) with list
		as value, also having multi-types among its items, we will throw an exception.
		'''

		dv_param_vals_by_name=self.getDictParamValuesByAttributeName()

		for s_param_name in dv_param_vals_by_name:
			v_val=dv_param_vals_by_name[ s_param_name ]
			if type( v_val ) == list:

				di_types={ type( this_val ).__name__:1 for this_val in v_val }
				
				ls_types=list( di_types.keys() )
				ls_types.sort()
				if len( ls_types ) > 1:
					if ls_types==[ 'float','int' ]:
						setattr( self, s_param_name, [ float( i ) for i in v_val ] )
					else:
						s_msg="In PGInputSimuPop instance, " \
								+ "def __make_params_whose_values" \
								+ "_are_lists_have_uniform_item_types" \
								+ "the parameter " + s_param_name \
								+ "has more than one type.  The only valid " \
								+ "case of such lists is those with int and float " \
								+ "items.  This list, " + str( v_val ) \
								+ " , with types, " + str( ls_types ) + "."
						raise Exception( s_msg )
					#end if list is mix of ints and floats, make all floats, else error
				#end if non-uniqe types in list
			#end of attribute is a list
		#end for each param name
		return
	#end __make_params_whose_values_are_lists_have_uniform_item_types

	def __get_nb_attribute_derivation( self ):

		'''
		Older versions of life tables lack an Nb and Nb/Nc ratio.  All life tables have an N0,
		and some older versions have an Nb given by config file "pop" section.  For instances 
		of this calss that use older life tables, we simply return the self.__N0 attribute.  
		Otherwise we compute it from Nb and NbNc.
		'''

		s_attribute_derivation=None

		b_has_pop_N0=hasattr( self, "_PGInputSimuPop__N0_from_pop_section" )
		b_has_pop_Nb=hasattr( self, "_PGInputSimuPop__Nb_from_pop_section" )
		b_has_NbNc=hasattr( self, "NbNc" ) 
		b_has_eff_size_Nb=hasattr( self, "_PGInputSimuPop__Nb_from_eff_size_info" )

		if b_has_pop_N0 and b_has_pop_Nb and ( not( b_has_NbNc ) ):
			s_attribute_derivation = "pop_section"
		elif b_has_eff_size_Nb and b_has_NbNc:
			s_attribute_derivation = "effective_size_section"
		else:
			s_msg="In PGInputSimuPop instance, def __get_nb_attribute_derivation, " \
					+ "could not evaluate source of Nb. It did not occur either (i) " \
					+ "only in the \"pop\" section of the configuration file, or (ii) "\
					+ "in an \"effective_size\" section of the life table or config file " \
					+ "along with an NbNc value (Nb/Nc ratio)."
			raise Exception( s_msg )
		#end if pop section only, or effective size params are both present
		
		return s_attribute_derivation
	#end __get_nb_attribute_derivation

	def N0IsCalculatedFromEffectiveSizeInfo( self ):
		s_nb_attribute_source=self.__get_nb_attribute_derivation()

		return s_nb_attribute_source=="effective_size_section"
	#end NbIsCalculatedFromEffectiveSizeInfo

	@property
	def N0( self ):
		'''
		Older versions of life tables lack an Nb and Nb/Nc ratio.  All life tables have an N0,
		and some older versions have an Nb given by config file "pop" section.  For instances 
		of this calss that use older life tables, we simply return the self.__N0 attribute.  
		Otherwise we compute it from Nb and NbNc.
		'''

		s_nb_source=self.__get_nb_attribute_derivation()

		if s_nb_source=="pop_section":
			'''
			2017_02_25.  With further revisions to PGOpSimuPop,
			we no longer allow N0 to be taken from the
			\"pop\" section.
			'''
			s_msg="In PGInputSimuPop instance, property N0.getter, " \
						+ "the program no longer allows the N0 value " \
						+ "to be derived from the original setting in " \
						+ "the \"pop\" section of the configuration " \
						+ "file."
			raise Exception( s_msg )
		elif s_nb_source=="effective_size_section":			
			return self.__compute_n0_from_eff_size_info()
		else:
			s_msg="In PGInputSimuPop instance, property N0, " \
					+ "cannot find N0 value, neither from config file \"pop\"" \
					+ " nor as computable from Nb and NbNc attributes."
			raise Exception( s_msg )
		#end if Nb only from single val, else compute from Nb and NbNc, else error
	#end property N0

	@N0.setter
	def N0( self, v_value ):
		s_nb_source=self.__get_nb_attribute_derivation()	

		if s_nb_source=="pop_section":
			s_msg="In PGInputSimuPop instance, property N0.setter, " \
						+ "the program no longer allows the N0 value " \
						+ "to be derived from the original setting in " \
						+ "the \"pop\" section of the configuration " \
						+ "file."
			raise Exception( s_msg )

		elif s_nb_source=="effective_size_section":
			''' 
			If we have effective size info, and the 
			client assigns an N0 value via this setter,
			we assume the client intends to set N0 without
			calculating from Nb and Nb/Nc, which is currently
			not allowed:
			'''
			s_msg="In PGInputSimuPop instance, property N0.setter, " \
							+ "The N0 value passed, " + str( v_value ) \
							+ ", cannot be assigned, " \
							+ "because this input object has Nb and Nb/Nc " \
							+ "values which are used to calculate N0."
			Exception( s_msg )
		else:
			s_msg="In PGInputSimuPop instance, property N0.setter, " \
						+ "unknown string value returned from " \
						+ "call to __get_nb_attribute_derivation."
			raise Exception( s_msg )
		#end if N0 in pop section else effective size, else other
		return
	#end setter N0

	@property 
	def Nb( self ):
		s_nb_source=self.__get_nb_attribute_derivation()

		if s_nb_source=="pop_section":
			s_msg="In PGInputSimuPop instance, property Nb.getter, " \
						+ "the program no longer allows the Nb value " \
						+ "to be derived from the original setting in " \
						+ "the \"pop\" section of the configuration " \
						+ "file."
			raise Exception( s_msg )
			return self.__Nb_from_pop_section
		elif s_nb_source=="effective_size_section": 			
			return self.__Nb_from_eff_size_info
		else:
			s_msg="In PGInputSimuPop instance, property Nb, " \
						+ "unknown string value returned from " \
						+ "call to __get_nb_attribute_derivation."
			raise Exception( s_msg )
		#end if pop_section else if "effective_size_section"	
		#else error
	#end property Nb

	@Nb.setter
	def Nb( self, v_value ):

		s_nb_source=self.__get_nb_attribute_derivation()

		if s_nb_source=="pop_section":
			'''
			2017_02_25.  With further revisions in
			PGOpSimuPop, this Nb value, from the
			original pop sections in Tiago's original,
			is now obsolete, since Nb is now a value
			correlated with the Nb/Nc and Nb/Ne ratios
			in our new "effective size" sections in the
			life tables.
			'''
			s_msg="In PGInputSimuPop instance, property Nb.setter, " \
						+ "the program no longer allows the Nb value " \
						+ "to be derived from the original settings int " \
						+ "the \"pop\" section of the configuration " \
						+ "file."
			raise Exception( s_msg )
		elif s_nb_source=="effective_size_section":
			self.__Nb_from_eff_size_info=v_value
		else:
			s_msg="In PGInputSimuPop instance, property Nb.setter, " \
						+ "unknown string value returned from " \
						+ "call to __get_nb_attribute_derivation."
			raise Exception( s_msg )
		#end if source is pop section else if effective_size_section
		#else error
	#end Nb setter

	@property
	def Nb_orig_from_pop_section( self ):
		'''
		This Nb val is the original value
		(originally the sole "Nb" attribute
		in the input object), that Tiago 
		uses in his code that chooses
		which generator to use (see "mateOp="
		assignment in the createAge def in
		mod pgopsimupop.py).  With our
		addition of Nb and Nb/Nc  paramters,
		in an "effective_size" section in life tables
		(or config files), and used to caluclate the N0 (aka, N1),
		we need to check for the Nb attribute sources, when
		the original code requests the Nb for use in a generator.
		If we've used an effective_size-derived Nb in an N0 calc, 
		and the pop section Nb is supplied as non "None",
		then we throw an error.  If, however, there is only one
		Nb value supplied, and it is in the pop section, we 
		then supply is to the sim op to be used in the generator
		choice.
		'''
		i_returnval=None
		s_nb_source=self.__get_nb_attribute_derivation()
		if s_nb_source=="pop_section":
			i_returnval=self.__Nb_from_pop_section
		elif s_nb_source=="effective_size_section":
			if self.__Nb_from_pop_section is not None:
				s_msg="In PGInputSimuPop instance, property Nb_orig_from_pop_section, " \
						+ "Nb was derived from an \"effective_size\" section, " \
						+ "found in the life table or config file, " \
						+ "but there is also an Nb value in the \"pop\" section " \
						+ "that is not \"None\".  Currently the simkulation cannot use " \
						+ "a pop section derived Nb, when there is another present in " \
						+ "an effective_size section."
				raise Exception( s_msg )
			#end if we have a non-None value in pop section, error
			i_returnval=self.__Nb_from_pop_section
		else:
			s_msg="In PGInputSimuPop instance, property Nb_orig_from_pop_section, " \
					+ "unknown string value returned form call to __get_nb_attribute_derivation." 
			raise Exception( s_msg )
		#end if pop-section Nb, else effective size, else unknown
		return i_returnval
	#end properby Nb_orig_from_pop_section


	'''
	This def helps clients to, for example,
	give users GUI message needs
	that the current conig no effective size info,
	so that N0 will be set manually by the user,
	instead of calculated using an Nb/Nc and Nb.
	'''
	def has_effective_size_info( self ):
		b_returnval=False
		s_nb_source=self.__get_nb_attribute_derivation()
		if s_nb_source=="effective_size_section":
			b_returnval=True
		#end if nb is from effective_size_section
		return b_returnval
	#end has_effective_size_info

	def __check_for_consistent_age_related_params( self ):
		'''
		2017_04_05.  This def checks that the parameters
		related to the total ages of the model species are
		consistent.  
		'''
		b_return_value=True

		s_msg="In PGInputSimuPop instance, " \
					+ "def __check_for_consistent_age_related_params, " \
					+ "the following inconsistencies were found:"

		if not( hasattr( self, "ages" ) ) or self.ages is None:
			s_msg+="\n\n No value was found for the ages parameter.\n\n"
			b_return_value=False
		#end if no ages	

		if not( hasattr( self, "fecundityFemale" ) ) \
							or self.fecundityFemale is None:
			s_msg+="\n\n No value was found for the female fecundity parameter.\n\n"
			b_return_value=False
		#end if no femail fecundity

		if not( hasattr( self, "fecundityMale" ) ) or self.fecundityMale is None:
			s_msg+="\n\n No value was found for the male fecundity parameter.\n\n"
			b_return_value=False
		#end if no male fecundity

		if not( hasattr( self, "survivalFemale" ) ) or self.survivalFemale is None:
			s_msg+="\n\n No value was found for the female survival parameter.\n\n"
			b_return_vale=False
		#end if no female survival 

		if not( hasattr( self, "survivalMale" ) ) or self.survivalMale is None:
			s_msg+="\n\n No value was found for the male survival parameter.\n\n"
			b_return_value=False
		#end if no female surviva

		i_num_ages=self.ages
		i_num_female_fecundity_values=len( self.fecundityFemale )
		i_num_male_fecundity_values=len( self.fecundityMale )
		i_num_female_survival_values=len( self.survivalFemale )
		i_num_male_survival_values=len( self.survivalMale )

		
		if i_num_female_fecundity_values != i_num_ages-1 \
				or i_num_male_fecundity_values != i_num_ages-1:
			s_msg+="\n\n There are inconsistent age/fecundity values.  " \
						+ "The number of female and/or male fecundity values " \
						+ " should equal the number of ages minus one.\n\n"
			b_return_value=False
		#end if inconsistent fecundity list length

		'''
		2018_03_07.  Although all the rest of our provided configuration
		files have survival entries totalling 2 less than the ages total,
		We have two configuration files, for the bighorn (100 and 200), 
		in which the number of survial entries is equal to the number of fecundity 
		entries, hence only 1 less than the ages value, so we change our test:

		2018_03_16.  We changed our minds, and will not allow a diff of 1 in the
		ages total minus survival.  Instead we are removing the last entry in 
		the survival list for the bighorn (value is 0.0), to bring it into
		line with the other conf files, so that ages minus num-survival-vals.
		is 2.
		'''
#		if i_num_female_survival_values != i_num_ages - 2 \
#			 or i_num_male_survival_values != i_num_ages - 2: 
		i_ages_minus_female_survival_entries=i_num_ages-i_num_female_survival_values	
		i_ages_minus_male_survival_entries=i_num_ages-i_num_male_survival_values	
		b_male_survival_in_range=( i_ages_minus_male_survival_entries  in [ 2 ] )
		b_female_survival_in_range=( i_ages_minus_female_survival_entries in [ 2 ] )

		if not( b_male_survival_in_range and b_female_survival_in_range ):
			 
			s_msg+="\n\n There are inconsistent age/survival values, " \
						+ "The number of female and/or male survival values " \
						+ " should equal the number of ages minus two.\n\n"
			b_return_value=False

		#end if inconsistent survival list length

		return b_return_value, s_msg
	#end def __check_for_consistent_age_related_params 

	def __check_for_consistent_cycle_related_values( self ):
		'''
		2017_04_05.  This def checks on parameters that depend 
		on the number of reproductive cycles (named "gens"
		in this input object).  These include
		the burn-in value, as well as the startSave value,
		and the ranges in the nb-adjustment list.
		'''
		b_return_value=True
		b_have_gens_value=True	

		s_msg="In PGInputSimuPop instance, " \
				+ "def, __check_for_consistent_cycle_related_values, " \
				+ "the following inconsistancies were found:" 


		if not( hasattr( self, "gens" ) ) or self.gens is None:
			s_msg+="\n\n Parameter gens (giving total reproductive cycles) " \
					+ "is missing.\n\n"
			b_have_gens_value=False	
			b_return_value=False
		#end if no gens param

		#The startSave value should be at least 1 and no more than gens:
		if not( hasattr( self, "startSave" ) ) or self.startSave is None:
			s_msg+= "\n\n Parameter startSave is missing.\n\n"
			b_return_value=False
		elif b_have_gens_value:
			if self.startSave < 1 or self.startSave > self.gens:
				s_msg+="\n\n The startSave value (cycle at which to start recording) " \
							+ "has an invalid value: " + str( self.startSave ) \
							+ ".  It should be at least 1 and no greater than the " \
							+ "number of gens (reproductive cycles), " \
							+ str( self.gens ) + ".\n\n"

				b_return_value=False
		#end if no startSave parameter	

		try:
			lf_rates=self.makePerCycleNbAdjustmentList()	
		except Exception as oex:
			s_msg += "\n\n" + str( oex ) + "\n\n"
			b_return_value=False
		#end try...except


		return b_return_value, s_msg

	#end __check_for_consistent_cycle_related_values
			
	def valuesAreConsistent(self):
		'''
		2017_04_05. This def added so that 
		when the PGGuiSimuPop instance's 
		runSimulation def is called, it
		can check for consistencies in the input
		before proceeding to the simulation proper.

		Increasing interdependancies among the 
		current set of allowed input user settings
		means that the per-control valideity tests
		are not sufficient guarantors of valid input
		values.
		'''
		s_msg="Messages from consistency checks: " 

		b_ages_look_consistent, s_ages_msgs= \
					self.__check_for_consistent_age_related_params()
		b_cycles_look_consistent, s_cycles_msg=\
					self.__check_for_consistent_cycle_related_values()

		if not b_ages_look_consistent:
			s_msg+="\n\n" + s_ages_msgs
		#end if inconsistent ages values 

		if not b_cycles_look_consistent:
			s_msg+="\n\n" + s_cycles_msg
		#end if  inconsistent cycles values

		b_return_value=( b_ages_look_consistent and b_cycles_look_consistent )

		return b_return_value, s_msg
	#end def valuesAreConsistent
		
#end class PGInputSimuPop

if __name__ == "__main__":
	import agestrucne.pgutilities as pgut
	import agestrucne.pgparamset as pgps
	import agestrucne.pgsimupopresources as pgsr	
	ls_args=[ "config file", "life-table file", "paramset file", "outfile_name" ]

	s_usage=pgut.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	s_configfile=sys.argv[1]
	s_lifetable=sys.argv[2]
	s_paramset=sys.argv[3]
	s_outfile=sys.argv[4]

	o_paramset=pgps.PGParamSet( s_paramset )
	o_lifetable=pgsr.PGSimuPopResources( [s_lifetable] )
	o_input=PGInputSimuPop( s_configfile, o_lifetable, o_paramset )
	o_input.makeInputConfig()
	o_input.writeInputParamsAsConfigFile( s_outfile )

#end if main

