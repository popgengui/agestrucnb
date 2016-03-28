'''
Description
Implements abstract class AGPOperation for simuPop simulations,
as coded by Tiago Antao's sim.py modlule.  See class description.
'''
__filename__ = "pgopsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import apgoperation as modop
from simuOpt import simuOptions
simuOptions["Quiet"] = True
import simuPOP as sp
import sys
import random
import numpy

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

	def __init__(self, o_input, o_output ): 

		super( PGOpSimuPop, self ).__init__()

		self.__input=o_input
		self.__output=o_output
		self.__lSizes = [0, 0, 0, 0, 0, 0]
		self.__reportOps = [ sp.Stat(popSize=True),
		    #PyEval(r'"gen %d\n" % gen', reps=0),
		    #PyEval(r'"size %s\n" % subPopSize', reps=0), 
		    ]

		self.__is_prepared=False

	#end __init__

	def prepareOp( self ):
		self.__createSinglePop()
		self.__createGenome()
		self.__createAge()	
		self.__output.openOut()
		self.__output.openErr()
		self.__output.openMegaDB()
		self.__createSim()
		self.__is_prepared=True
		return
	#end prepareOp

	def doOp( self ):
		if self.__is_prepared:

			self.__evolveSim()
			self.__output.out.close()
			self.__output.err.close()
			self.__output.megaDB.close()

		else:
			raise Exception( "PGOpSimuPop object not prepared to operate (see def prepareOp)." )

		#end  if prepared, do op else exception

		return
	#end doOp

	def deliverResults( self ):
		return
	#end deliverResults

	@property
	def input( self ):
		return self.__input
	#end input

	@input.setter
	def input( self, o_input_object ):
		self.__input=o_input_object
		return
	#end setter

	@input.deleter
	def input( self ):
		del self.__input
		return
	#end delete

	def __createGenome( self ):

	    size = self.__input.popSize
	    numMSats = self.__input.numMSats
	    numSNPs = self.__input.numSNPs

	    maxAlleleN = 100
	    #print "Mutation model is most probably not correct", numMSats, numSNPs
	    loci = (numMSats + numSNPs) * [1]
	    initOps = []

	    for msat in range(numMSats):
		diri = numpy.random.mtrand.dirichlet([1.0] * self.__input.startAlleles)
		if type(diri[0]) == float:
		    diriList = diri
		else:
		    diriList = list(diri)

		initOps.append(
		    sp.InitGenotype(freq=[0.0] * ((maxAlleleN + 1 - 8) // 2) +
				    diriList + [0.0] * ((maxAlleleN + 1 - 8) // 2),
				    loci=msat))

	    for snp in range(numSNPs):
		freq = 0.5
		initOps.append(
		    sp.InitGenotype(
			#Position 0 is coded as 0, not good for genepop
			freq=[0.0, freq, 1 - freq],
			loci=numMSats + snp))

	    preOps = []
	    if self.__input.mutFreq > 0:
		preOps.append(sp.StepwiseMutator(rates=self.__input.mutFreq,
			      loci=range(numMSats)))
	    self.__loci=loci
	    self.__genInitOps=initOps
	    self.__genPreOps=preOps

	    return

	#end __createGenome

	def __createSinglePop( self ):
	    popSize=self.__input.popSize
	    nLoci=self.__input.numMSats + self.__input.numSNPs
	    startLambda=self.__input.startLambda
	    lbd=self.__input.lbd
	    initOps = [sp.InitSex(maleFreq=self.__input.maleProb)]
	    if startLambda < 99999:
		preOps = [sp.ResizeSubPops(proportions=(float(lbd), ),
					   begin=startLambda)]
	    else:
		preOps = []
	    postOps = []
	    pop = sp.Population(popSize, ploidy=2, loci=[1] * nLoci,
				chromTypes=[sp.AUTOSOME] * nLoci,
				infoFields=["ind_id", "father_id", "mother_id",
					    "age", "breed", "rep_succ",
					    "mate", "force_skip"])
	    for ind in pop.individuals():
		ind.breed = -1000
	    oExpr = ('"%s/samp/%f/%%d/%%d/smp-%d-%%d-%%d.txt" %% ' +
		     '(numIndivs, numLoci, gen, rep)') % (
			 self.__input.dataDir, self.__input.mutFreq, popSize)
	    
	    self.__pop=pop
	    self.__popInitOps=initOps
	    self.__popPreOps=preOps
	    self.__popPostOps=postOps
	    self.__oExpr=oExpr

	    return 

	#end __createSinglePop

	
	def __createSim( self ):
	    self.__sim = sp.Simulator(self.__pop, rep=self.__input.reps)
	    return 
    	#end __createSim

	def __evolveSim(self):

	    sim=self.__sim
	    gens=self.__input.gens
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

	    sim.evolve(
		initOps=genInitOps + popInitOps + ageInitOps,
		preOps=popPreOps + genPreOps + agePreOps,
		postOps=popPostOps + reportOps + agePostOps,
		matingScheme=mateOp,
		gen=gens)
	   #end __evolveSim

	def __calcDemo( self, gen, pop ):
	    myAges = []
	    for age in range(self.__input.ages - 2):
		myAges.append(age + 1)
	    curr = 0
	    for i in pop.individuals():
		if i.age in myAges:
		    curr += 1
	    if gen >= self.__input.startLambda:
		self.__input.N0 = self.__input.N0 * self.__input.lbd
	    return self.__input.N0 + curr
	#end __calcDemo

	def __getRandomPos( self, arr ):
	    sumVal = sum(arr)
	    rnd = random.random()
	    acu = 0.0
	    for i in range(len(arr)):
		acu += arr[i]
		if acu >= rnd * sumVal:
		    return i
	        #end if acu . . .
	    #end for i in range...
	#end __getRandomPos


	def __litterSkipGenerator( self, pop, subPop ):

	    fecms = self.__input.fecundityMale
	    fecfs = self.__input.fecundityFemale
	    nextFemales = []
	    malesAge = {}
	    femalesAge = {}
	    availOfs = {}
	    gen = pop.dvars().gen
	    nLitter = None

	    if self.__input.litter and self.__input.litter[0] < 0:
		nLitter = - self.__input.litter[0]
	    for ind in pop.individuals():
		if ind.sex() == 1:  # male
		    malesAge.setdefault(int(ind.age), []).append(ind)
		else:
		    if nLitter is not None:
			availOfs[ind] = nLitter
		    diff = int(gen - ind.breed)
		    if diff > len(self.__input.skip):
			available = True
			#print diff, len(self.__input.skip), gen, ind.breed
		    else:
			prob = random.random() * 100
			#print prob, self.__input.skip, diff
			if prob > self.__input.skip[diff - 1]:
			    available = True
			else:
			    available = False
		    #print ind, available
		    if available:
			femalesAge.setdefault(int(ind.age), []).append(ind)
	     #end for ind in pop...
	    maleFec = []
	    for i in range(len(fecms)):
		maleFec.append(fecms[i] * len(malesAge.get(i + 1, [])))
	    #end for i in range...

	    femaleFec = []
	    for i in range(len(fecfs)):
		if self.__input.forceSkip > 0 and random.random() < self.__input.forceSkip:
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
			elif self.__input.litter:
			    lSize = self.__getRandomPos(self.__input.litter) + 1
			    self.__lSizes[lSize] += 1
			    if lSize > 1:
				nextFemales = [female] * (lSize - 1)
			    #end if size>1

			    femalesAge[age].remove(female)
			#end if nLitter not None
		    #end if len( femalsage . . . 
		#end while not femail
	    #end while True
	

		male = None

		if self.__input.isMonog:
		    if female.mate > -1:
			male = pop.indByID(female.mate)
		    #end if female
		#end if isMonog

		while male is None:
		    age = self.__getRandomPos(maleFec) + 1
		    if len(malesAge.get(age, [])) > 0:
			male = random.choice(malesAge[age])
		    if self.__input.isMonog:
			if male.mate > -1:
			    male = None
			else:
			    male.mate = female.ind_id
			#end if male.mate
		    #end if isMonog
		#end while male..

		female.breed = gen
		if self.__input.isMonog:
		    female.mate = male.ind_id
		yield male, female

	#end __litterSkipGenerator

	def __calcNb( self, pop, pair ):
	    fecms = self.__input.fecundityMale
	    fecfs = self.__input.fecundityFemale
	    cofs = []
	    for ind in pop.individuals():
		if ind.sex() == 1:  # male
		    fecs = fecms
		    pos = 0
		else:
		    pos = 1
		    fecs = fecfs
		if fecs[int(ind.age) - 1] > 0:
		    nofs = len([x for x in pair if x[pos] == ind])
		    cofs.append(nofs)
	    kbar = 2.0 * self.__input.N0 / len(cofs)
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
	    while not nbOK:
		pair = []
		gen = self.__litterSkipGenerator(pop, subPop)
		#print 1, pop.dvars().gen, nb
		for i in range(self.__input.N0):
		    pair.append(gen.next())
		if pop.dvars().gen < 10:
		    break
		nb = self.__calcNb(pop, pair)
		if abs(nb - self.__input.Nb) <= self.__input.NbVar:
		    nbOK = True
		else:
		    for male, female in pair:
			female.breed -= 1
		    attempts += 1
		if attempts > 100:
		    print "out", pop.dvars().gen
		    sys.exit(-1)
	    for male, female in pair:
		yield male, female
	#end __restrictedGenerator

	def __fitnessGenerator( self, pop, subPop ):
	    fecms = self.__input.fecundityMale
	    fecfs = self.__input.fecundityFemale
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
		    a = self.__input.gammaAMale[int(ind.age) - 1]
		    b = self.__input.gammaBMale[int(ind.age) - 1]
		    if a:
			gamma = numpy.random.gamma(a, b)
			ind.rep_succ = gamma
			#ind.rep_succ = numpy.random.poisson(gamma)
		    else:
			ind.rep_succ = 1
		    perAgeMaleNorm[int(ind.age) - 1] = perAgeMaleNorm.get(
			int(ind.age) - 1, 0.0) + ind.rep_succ
		    ageCntMale[int(ind.age) - 1] = ageCntMale.get(
			int(ind.age) - 1, 0.0) + 1
		else:
		    #if ind.age == 0: totFecFemales +=0
		    a = self.__input.gammaAFemale[int(ind.age) - 1]
		    b = self.__input.gammaBFemale[int(ind.age) - 1]
		    if a:
			gamma = numpy.random.gamma(a, b)
			ind.rep_succ = gamma
			#ind.rep_succ = numpy.random.poisson(gamma)
		    else:
			ind.rep_succ = 1
		    perAgeFemaleNorm[int(ind.age) - 1] = perAgeFemaleNorm.get(
			int(ind.age) - 1, 0.0) + ind.rep_succ
		    ageCntFemale[int(ind.age) - 1] = ageCntFemale.get(
			int(ind.age) - 1, 0.0) + 1
		    availableFemales.append(ind.ind_id)

	    for ind in pop.individuals():
		if ind.sex() == 1:  # male
		    if perAgeMaleNorm[int(ind.age) - 1] == 0.0:
			ind.rep_succ = 0.0
		    else:
			ind.rep_succ = ageCntMale[int(ind.age) - 1] * fecms[
			    int(ind.age) - 1] * ind.rep_succ / perAgeMaleNorm[
				int(ind.age) - 1]
		    totFecMales += ind.rep_succ
		else:
		    if ind.ind_id not in availableFemales:
			continue
		    if perAgeFemaleNorm[int(ind.age) - 1] == 0.0:
			ind.rep_succ = 0.0
		    else:
			ind.rep_succ = ageCntFemale[int(ind.age) - 1] * fecfs[
			    int(ind.age) - 1] * ind.rep_succ / perAgeFemaleNorm[
				int(ind.age) - 1]
		    totFecFemales += ind.rep_succ

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
		inds = list(pop.individuals())
		random.shuffle(inds)
		for ind in inds:
		    if ind.age == 0:
			continue
		    if ind.sex() == 1 and not male:  # male
			runMale += ind.rep_succ
			if runMale > mVal:
			    male = ind
		    elif ind.sex() == 2 and not female:
			if ind.ind_id not in availableFemales:
			    continue
			runFemale += ind.rep_succ
			if runFemale > fVal:
			    female = ind
			    female.breed = gen
		    if male and female:
			break
		yield male, female
	#end __fitnessGenerator 

	def __cull( self, pop ):
	    kills = []
	    for i in pop.individuals():
		if i.age > 0 and i.age < self.__input.ages - 1:
		    if i.sex() == 1:
			cut = self.__input.survivalMale[int(i.age) - 1]
		    else:
			cut = self.__input.survivalFemale[int(i.age) - 1]
		    if random.random() > cut:
			kills.append(i.ind_id)
	    pop.removeIndividuals(IDs=kills)
	    return True
	#end __cull

	def __zeroC( self, v ):
	    a = str(v)
	    while len(a) < 3:
		a = "0" + a
	    return a
    	#end __zeroC


	def __outputAge( self, pop ):
	    gen = pop.dvars().gen
	    if gen < self.__input.startSave:
		return True
	    rep = pop.dvars().rep
	    for i in pop.individuals():
		self.__output.out.write("%d %d %d %d %d %d %d\n" % (gen, rep, i.ind_id, i.sex(),
						      i.father_id, i.mother_id, i.age))
		if i.age == 1 or gen == 0:
		    self.__output.err.write("%d %d " % (i.ind_id, gen))
		    for pos in range(len(i.genotype(0))):
			a1 = self.__zeroC(i.allele(pos, 0))
			a2 = self.__zeroC(i.allele(pos, 1))
			self.__output.err.write(a1 + a2 + " ")
		    self.__output.err.write("\n")
	    return True
    	#end __outputAge


	def __outputMega( self, pop ):
	    gen = pop.dvars().gen
	    if gen < self.__input.startSave:
		return True
	    for i in pop.individuals():
		if i.age == 0:
		    self.__output.megaDB.write("%d %d %d %d %d\n" % (gen, i.ind_id, i.sex(),
						       i.father_id, i.mother_id))
	    return True
    	#end __outputMega


	def __setAge( self, pop ):
	    probMale = [1.0]
	    for sv in self.__input.survivalMale:
		probMale.append(probMale[-1] * sv)
	    totMale = sum(probMale)
	    probFemale = [1.0]
	    for sv in self.__input.survivalFemale:
		probFemale.append(probFemale[-1] * sv)
	    totFemale = sum(probFemale)
	    for ind in pop.individuals():
		if ind.sex() == 1:
		    prob = probMale
		    tot = totMale
		else:
		    prob = probFemale
		    tot = totFemale
		cut = tot * random.random()
		acu = 0
		for i in range(len(prob)):
		    acu += prob[i]
		    if acu > cut:
			age = i
			break
		ind.age = age

	    return True
	#end __setAge

	def __createAge( self ):
	    pop=self.__pop

	    ageInitOps = [
		#InitInfo(lambda: random.randint(0, self.__input.ages-2), infoFields='age'),
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
	    for age in range(self.__input.ages - 2):
		mySubPops.append((0, age + 1))
	    mateOp = sp.HeteroMating([
		sp.HomoMating(
		    sp.PyParentsChooser(self.__fitnessGenerator if self.__input.doNegBinom
				     else (self.__litterSkipGenerator if self.__input.Nb is None else
					   self.__restrictedGenerator)),
		    sp.OffspringGenerator(numOffspring=1, ops=[
			sp.MendelianGenoTransmitter(), sp.IdTagger(),
			sp.PedigreeTagger()],
			sexMode=(sp.PROB_OF_MALES, self.__input.maleProb)), weight=1),
		sp.CloneMating(subPops=mySubPops, weight=-1)],
		subPopSize=self.__calcDemo)
	    agePostOps = [
		sp.PyOperator(func=self.__outputMega),
		sp.PyOperator(func=self.__cull),
	    ]
	    pop.setVirtualSplitter(sp.InfoSplitter(field='age',
						   cutoff=range(1, self.__input.ages)))

	    self.__ageInitOps=ageInitOps
	    self.__agePreOps=agePreOps
	    self.__mateOp=mateOp
	    self.__agePostOps=agePostOps

	    return
    #end __createAge
#end class PGOpSimuPop

