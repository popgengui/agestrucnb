'''
Description
Implements abstract class AGPOperation for simuPop simulations,
as coded by Tiago Antao's sim.py modlule.  See class description.
'''
__filename__ = "pgopsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE_CONSOLE=False
VERY_VERBOSE_CONSOLE=False
#if True, then invokes ncurses debugger
DO_PUDB=False

if DO_PUDB:
	from pudb import set_trace; set_trace()
#end if do pudb

import apgoperation as modop
import pgutilities as pgut
#for the lambda-ignore constant:
import pginputsimupop as pgin
from simuOpt import simuOptions
simuOptions["Quiet"] = True
import simuPOP as sp
import sys
import random
import numpy
import copy
import os

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

	def __init__(self, o_input, o_output, b_compress_output=True ):  

		super( PGOpSimuPop, self ).__init__( o_input, o_output )

		self.__lSizes = [0, 0, 0, 0, 0, 0]
		self.__reportOps = [ sp.Stat(popSize=True) ]
		self.__is_prepared=False
		self.__compress_output=b_compress_output

		#if this object is created in one of multiple
		#python so-called "Processes" objects from class
		#"multiprocessing", all pops in their separate "process"
		#will have identical individuals (same number/genotypes) 
		#unless we reseed the numpy random number generator 
		#for each "process:"
		numpy.random.seed()
		
		return
	#end __init__

	def prepareOp( self, s_tag_out="" ):

		self.__createSinglePop()
		self.__createGenome()
		self.__createAge()	
		
		s_basename_without_replicate_number=self.output.basename	
		
		if VERY_VERBOSE_CONSOLE==True:
			print( "resetting output basename with tag: " + s_tag_out )
		#end if VERY_VERBOSE_CONSOLE

		self.output.basename=s_basename_without_replicate_number + s_tag_out

		self.output.openOut()
		self.output.openErr()
		self.output.openMegaDB()
		self.output.openConf()

		self.__createSim()
		self.__is_prepared=True

		return
	#end prepareOp

	def doOp( self ):
		if self.__is_prepared:
			#we write the current param set to
			#write the configutation file on which
			#this run is based:
			self.input.writeInputParamsToFileObject( self.output.conf ) 
			self.output.conf.close()

			#now we do the sim
			self.__evolveSim()
			self.output.out.close()
			self.output.err.close()
			self.output.megaDB.close()

			if self.__compress_output:
				self.output.bz2CompressAllFiles()
			#end if compress

			self.__write_genepop_file()
		else:
			raise Exception( "PGOpSimuPop object not prepared to operate (see def prepareOp)." )
		#end  if prepared, do op else exception

		return
	#end doOp

	def __write_genepop_file( self ):
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
			self.output.gen2Genepop( 1, 
					i_total_loci, 
					b_pop_per_gen=True,
					b_do_compress=False )
		#end if no loci reported
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

		for msat in range(numMSats):
			diri = numpy.random.mtrand.dirichlet([1.0] * self.input.startAlleles)
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

		for snp in range(numSNPs):
			freq = 0.5
			initOps.append(
					sp.InitGenotype(
					#Position 0 is coded as 0, not good for genepop
					freq=[0.0, freq, 1 - freq],
					loci=numMSats + snp))
		#end for snp

		preOps = []

		if self.input.mutFreq > 0:
			preOps.append(sp.StepwiseMutator(rates=self.input.mutFreq,
					loci=range(numMSats)))
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
		initOps = [sp.InitSex(maleFreq=self.input.maleProb)]
		if startLambda < pgin.START_LAMBDA_IGNORE:
			preOps = [sp.ResizeSubPops(proportions=(float(lbd), ),
								begin=startLambda)]
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

		sim.evolve( initOps=genInitOps + popInitOps + ageInitOps,
					preOps=popPreOps + genPreOps + agePreOps,
					postOps=popPostOps + reportOps + agePostOps,
					matingScheme=mateOp,
					gen=gens)

	#end __evolveSim

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

		if gen >= self.input.startLambda:
			self.input.N0 = self.input.N0 * self.input.lbd
		#endif gen >= start lambda

		v_return_value = self.input.N0 + curr

		if VERBOSE_CONSOLE:
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
						self.__lSizes[lSize] += 1
						if lSize > 1:
							nextFemales = [female] * (lSize - 1)
						#end if size>1

						femalesAge[age].remove(female)
					#end if nLitter is not nonem elif litter
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

			if VERY_VERBOSE_CONSOLE:
				print( "in __litterSkipGenerator, yielding with  " \
						+ "male: %s, female: %s"
						% ( str( male ), str( female ) ) )
			#end if verbose

			yield male, female

		#end while True
	#end __litterSkipGenerator

	def __calcNb( self, pop, pair ):

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

		kbar = 2.0 * self.input.N0 / len(cofs)
		Vk = numpy.var(cofs)
		nb = (kbar * len(cofs) - 2) / (kbar - 1 + Vk / kbar)
		#print len(pair), kbar, Vk, (kbar * len(cofs) - 2) / (kbar - 1 + Vk / kbar)
		return nb
	#end __calcNb

	def __restrictedGenerator( self, pop, subPop ):
		
		"""No monogamy, skip or litter"""
		nbOK = False
		nb = None
		attempts = 0


		if VERY_VERBOSE_CONSOLE:

			print ( "in __restrictedGenerator with " \
					+ "args, pop: %s, subpop: %s"
							% ( str( pop ), sr( subPop ) ) )
		#end if VERBOSE_CONSOLE

		while not nbOK:
			pair = []
			gen = self.__litterSkipGenerator(pop, subPop)
			#print 1, pop.dvars().gen, nb

			for i in range(self.input.N0):
				pair.append(gen.next())
			#end for i in range

			if pop.dvars().gen < 10:
				break
			#end if pop.dvars

			nb = self.__calcNb(pop, pair)

			if abs(nb - self.input.Nb) <= self.input.NbVar:
				nbOK = True
			else:
				for male, female in pair:
					female.breed -= 1
				#end for male, female

				attempts += 1

			#end for abs( nb ... else not

			if attempts > 100:
				print( "out", pop.dvars().gen )
				sys.exit(-1)
			#end if attempts > 100
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

			if VERY_VERBOSE_CONSOLE:
				s_msg="yielding from __fitnessGenerator with: " \
						+ "%s and %s" \
						% ( str( male ), str( female ) )
				print ( s_msg )
			#end if VERBOSE_CONSOLE

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

	def __zeroC( self, v ):
		a = str(v)
		while len(a) < 3:
			a = "0" + a
		#end while len(a) < 3
		return a
	#end __zeroC

	def __outputAge( self, pop ):
		gen = pop.dvars().gen
		if gen < self.input.startSave:
			return True
		#end if gen < startSave

		rep = pop.dvars().rep

		for i in pop.individuals():
			self.output.out.write("%d %d %d %d %d %d %d\n" % (gen, rep, i.ind_id, i.sex(),
								i.father_id, i.mother_id, i.age))

			if i.age == 1 or gen == 0:
				self.output.err.write("%d %d " % (i.ind_id, gen))
				for pos in range(len(i.genotype(0))):
					a1 = self.__zeroC(i.allele(pos, 0))
					a2 = self.__zeroC(i.allele(pos, 1))
					self.output.err.write(a1 + a2 + " ")
				#end for pos in range
				self.output.err.write("\n")
			#end if age == 1 or gen == 0
		#end for i in pop

		return True
	#end __outputAge

	def __outputMega( self, pop ):
		gen = pop.dvars().gen
		if gen < self.input.startSave:
			return True
		#end if gen < startSave

		for i in pop.individuals():
			if i.age == 0:
				self.output.megaDB.write("%d %d %d %d %d\n" % (gen, i.ind_id, i.sex(),
								i.father_id, i.mother_id))
			#end if age == 0
		#end for i in pop

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

		mateOp = sp.HeteroMating( [ 
					sp.HomoMating(
					sp.PyParentsChooser(self.__fitnessGenerator if self.input.doNegBinom
					else (self.__litterSkipGenerator if self.input.Nb is None else
					self.__restrictedGenerator)),
					sp.OffspringGenerator(numOffspring=1, ops=[
					sp.MendelianGenoTransmitter(), sp.IdTagger(),
					sp.PedigreeTagger()],
					sexMode=(sp.PROB_OF_MALES, self.input.maleProb)), weight=1),
					sp.CloneMating(subPops=mySubPops, weight=-1)],
					subPopSize=self.__calcDemo )

		agePostOps = [ sp.PyOperator(func=self.__outputMega), 
					sp.PyOperator(func=self.__cull) ]

		pop.setVirtualSplitter(sp.InfoSplitter(field='age',
			   cutoff=range(1, self.input.ages)))

		self.__ageInitOps=ageInitOps
		self.__agePreOps=agePreOps
		self.__mateOp=mateOp
		self.__agePostOps=agePostOps

		return
	#end __createAge
	
#end class PGOpSimuPop

if __name__ == "__main__":

	import pginputsimupop as pgin
	import pgoutputsimupop as pgout
	import pgsimupopresources as pgrec
	import pgparamset as pgps
	import pgutilities	 as pgut
	import time

	ls_args=[ "lifetable file", "configuration file", "output base" ]

	s_usage=pgut.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	s_lifetable_file=sys.argv[ 1 ]
	s_conf_file=sys.argv[ 2 ]
	s_outbase=sys.argv[ 3 ]
	PARAM_NAMES_FILE="resources/simupop.param.names"

	o_param_names=pgps.PGParamSet( PARAM_NAMES_FILE )
	o_resources=pgrec.PGSimuPopResources([ s_lifetable_file ] )
	o_input=pgin.PGInputSimuPop(  s_conf_file, o_resources, o_param_names )
	o_output=pgout.PGOutputSimuPop( s_outbase  )
	
	o_input.makeInputConfig()

	o_op=PGOpSimuPop( o_input, o_output )
	o_op.prepareOp()
	o_op.doOp()
#end if

