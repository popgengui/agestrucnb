'''
Description

Retrieves and prepares data needed to run simuPop.  See class description.

'''
__filename__ = "pginputsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from ConfigParser import ConfigParser
from ConfigParser import NoSectionError

class PGInputSimuPop( object ):
	'''
	Object meant to fetch parameter values and prepare them for 
	use in a simuPop simulation.  

	Object to be passed to a PGOpSimuPop object, which is, in turn,
	passed to a PGGuiSimuPop object, so that the widgets can then access
	defs in this input object, in order to, for example, show or allow
	changes in parameter values for users before they run the simulation.
	'''

	def __init__( self, s_config_file = None, s_resources_file = None ):
	
		self.config_file=s_config_file
		self.resources_file=s_resources_file
		
		if self.config_file is not None \
			and self.resources_file is not None:
			self.__get_config()
		#end if we have 2 file names

		return
	#end def __init__

	def __find_resources( self, s_config_file_value, o_resources_parser ):
		'''
		if eval works, then the values are in the original conf file.
		else if eval call raises NameError, then it names a value 
		the conf file gave in form dict[ species ], one of the 
		dictionaries hard-coded into tiago's myUtils file, 
		so we find it in our resources file
		'''
		v_value=None

		try: 
			v_value=eval (s_config_file_value )

		except NameError, ne:
			
			ls_dict_item_split=s_config_file_value.split( "[" )
			s_dict_name=( ls_dict_item_split[ 0 ] ).strip()
			s_gamma_list_key=ls_dict_item_split[ len( ls_dict_item_split ) - 1 ]
			s_gamma_list_key=s_gamma_list_key.replace( "]", "" )

			#resoures configuration file, writteh using the dictinaries in tiagos
			#myUtils file, has a main section 'resources' for 
			#values that tiago coded dict[ species ]=value, where value is a list
			#or int, but also has dictionary values (gammaAMale has
			#dictionary value), which require the dict name to be a section name
			#so that the key or keys can be used for the key=value portion
			try: 
				v_value=o_resources_parser.get( s_dict_name, s_gamma_list_key )
			except NoSectionError, ns:
				v_value=o_resources_parser.get( 'resources', s_dict_name )
			#end try to use dict name as section, else use 'resources' except

			v_value=eval( v_value )

		#end try  to evaluate the string, excpet, go to resources

		return v_value
	#end __find_resources

	def __get_config( self ):

	    config = ConfigParser()
	    config.read(self.config_file)

	    o_resources_parser=ConfigParser()
	    o_resources_parser.read( self.resources_file )

	    self.N0 = config.getint("pop", "N0")
	    self.popSize = config.getint("pop", "popSize")
	    self.ages = self.__find_resources( config.get("pop", "ages"), o_resources_parser )

	    if config.has_option("pop", "isMonog"):
		self.isMonog = config.getboolean("pop", "isMonog")
	    else:
		self.isMonog = False
	    if config.has_option("pop", "forceSkip"):
		self.forceSkip = config.getfloat("pop", "forceSkip") / 100
	    else:
		self.forceSkip = 0
	    if config.has_option("pop", "skip"):
		self.skip = self.__find_resources( config.get("pop", "skip"), o_resources_parser )
	    else:
		self.skip = []
	    if config.has_option("pop", "litter"):
		self.litter = self.__find_resources( config.get("pop", "litter"), o_resources_parser )
	    else:
		self.litter = None
	    #end if config has litter

	    if config.has_option("pop", "male.probability"):
		self.maleProb = config.getfloat("pop", "male.probability")
	    else:
		self.maleProb = 0.5
	    if config.has_option("pop", "gamma.b.male"):
		self.doNegBinom = True
		self.gammaAMale = self.__find_resources( config.get("pop", "gamma.a.male"), o_resources_parser )
		self.gammaBMale = self.__find_resources( config.get("pop", "gamma.b.male"), o_resources_parser )
		self.gammaAFemale = self.__find_resources( config.get("pop", "gamma.a.female"), o_resources_parser )
		self.gammaBFemale = self.__find_resources( config.get("pop", "gamma.b.female"), o_resources_parser )
	    else:
		self.doNegBinom = False
	    #end if config.has gamma b mail, then get all gammas


	    if config.has_option("pop", "survival"):
		self.survivalMale = self.__find_resources( config.get("pop", "survival"), o_resources_parser )
		self.survivalFemale = self.__find_resources( config.get("pop", "survival"), o_resources_parser )
	    else:
		self.survivalMale = self.__find_resources( config.get("pop", "survival.male"), o_resources_parser )
		self.survivalFemale = self.__find_resources( config.get("pop", "survival.female"), o_resources_parser )
	    self.fecundityMale = self.__find_resources( config.get("pop", "fecundity.male"), o_resources_parser )
	    self.fecundityFemale = self.__find_resources( config.get("pop", "fecundity.female"), o_resources_parser )
	    if config.has_option("pop", "startLambda"):
		self.startLambda = config.getint("pop", "startLambda")
		self.lbd = config.getfloat("pop", "lambda")
		#self.lbd = mp.mpf(config.get("pop", "lambda"))
	    else:
		self.startLambda = 99999
		#self.lbd = mp.mpf(1.0)
		self.lbd = 1.0
	    if config.has_option("pop", "Nb"):
		self.Nb = config.getint("pop", "Nb")
		self.NbVar = config.getfloat("pop", "NbVar")
	    else:
		self.Nb = None
		self.NbVar = None

	    self.startAlleles = config.getint("genome", "startAlleles")
	    self.mutFreq = config.getfloat("genome", "mutFreq")
	    self.numMSats = config.getint("genome", "numMSats")
	    if config.has_option("genome", "numSNPs"):
		self.numSNPs = config.getint("genome", "numSNPs")
	    else:
		self.numSNPs = 0

	    self.reps = config.getint("sim", "reps")
	    if config.has_option("sim", "startSave"):
		self.startSave = config.getint("sim", "startSave")
	    else:
		self.startSave = 0
	    self.gens = config.getint("sim", "gens")
	    self.dataDir = config.get("sim", "dataDir")

	#end getConfig

#end class

