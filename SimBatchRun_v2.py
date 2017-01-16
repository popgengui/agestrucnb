import ConfigParser
import os
import re
from itertools import product

'''
Not sure about current import language for plotting
'''

try:
    import Viz.LineRegress
except Exception as oex:
    print( "Warning, unable to import Viz.LineRegress: "  \
            +  "error: " + str( oex ) + "." )
#end try ... except

try:
    import Viz.ResultScraper
except Exception as oex:
    print( "Warning, unable to import Viz.ResultScraper: "  \
            +  "error: " + str( oex ) + "." )
#end try...except

#Ted added  2016_10_23, for making uniq file names.
import random 
import uuid

'''
-----Run constants-----
Ted added these 2017_01_15 as constants for the 
Simulation and NeEstimation run.  The only constant
related to simulations is the number of processes
used, as used in def runOneSimulationRep. 

In this version (2017_01_15), in place of calling def "batch,"
when this script is called as the __main__ script, then, for each
set of params as given by the batch config, a string call to def
"run" is added to a list of calls.   Each of these then are used
in calls to "run" using independant python processes (see def 
runDefCallsInSeparateProcesses). The command line -t value tells 
the script how many such run calls to run in parallel.

The NUM_PROCS constants can be reset using the optional params
in the current, optional command line flags -s and -n. The 
default values are 1, assuming that many calls to run will be made.

run this script with -h to see the help notes on these.
'''
NUM_PROCS_FOR_SIM_REPS=2
NUM_PROCS_FOR_NE_EST=2
'''
The followingare parameters Other parameters used 
in the call to pgdriveneestimator.py. To see 
other options and the param list, execute
"python pgdriveneestimator.py -h", 
for help with the parameter list.
'''

'''
Default values
put no limit on pop size, nor on the
range of pops to be evaluated by
NeEstimator:
'''
MINPOPSIZE="1"
MAXPOPSIZE="99999"
POPRANGE="1-99990"
'''
Default minimum allele frequence
for NeEstimator:
'''
MINALLELEFREQ="0.01"
'''
Default number of replicates for
Populatioin subsampling:
'''
REPLICATES=1

'''
Default loci subsampling scheme is "percent."
'''
LOCISCHEME="percent"

'''
Default is to use all of the loci.
Set these to require at least locimin
and at most locimax. Loci subsets are
randomly selected when locimax is less 
than the total available.
'''
LOCIMIN="1"
LOCIMAX="99999"

'''
Default uses all loci.  To use a range of 
the mth to the nth, as ordered in the 
genepop file, set this as "m-n"
'''
LOCIRANGE="1-99999"

'''
Default uses only 1 replicate for each loci subsample value.
'''
LOCIREPLICATES="1"

'''
Default mode uses python multiprocessing (even if only 
1 process is requested), and removes intermediate files.
'''
MODE="no_debug"

'''----- end NeEstimation run constants.'''

def readconfig(filename):

    ## SETS DEFaULTS
    #all defaults must be in a list even if only one value
    speciesFile = ""

    #Ted added 2016_10_18, additional files
    #needed to run sim
    lifeTableFile=""

    #File with param names
    #and associated properties
    #of simulation parameters.
    simparamset=""

    outFolder = ""
    lineRegressConfig = ""
    lambdas = [1.0]

    '''
    Ted added (2016_10_25), list of integers parameter.  
    Each givea as the number of repro cycles to burn in
    before staring to apply lambda.  This may be best
    used as a single number for all sim reps(?)
    '''
    startLambdas=[ 99999 ]

    startPopulations = []#TODO need default
    N0s = []#TODO need default
    microsats = []#TODO need default
    alleleCount = []#TODO needs default
    SNPs = []#TODO need default
    mutationRate = [0]
    lociSampling = [1.0]
    populationSampling = [1.0]
    simReps = [100]
    '''
    Ted added 2016_10_23.  These paramaters
    are required by pgdriveneestimator, to
    run an Ne estimation.  They create a default 
    genepop sampling of individuals, to extract
    only one year olds from each population.
    They assume the individual ID format being output
    by the pgopsimupop.py code is as indicated:
    '''
    popSamplingScheme="cohortsperc"
    popSamplingParams="id;sex;father;mother;age,float;int;float;float;float,1"

    ##SET FILE DELIMITERS
    delimiters = ',|\||\n|;'

    #open files
    config = ConfigParser.ConfigParser()
    config.readfp(open(filename))

    #read in output filename
    if config.has_section("outFolder"):
        if config.has_option("outFolder", "name"):
            outFolder = config.get("outFolder", "name")

    ##read species input file
    if config.has_section("species"):
        if config.has_option("species", "name"):
            speciesFile = config.get("species", "name")

    '''
    Ted added five config entries (2016_10_18),
    -->1 integer to give total burn-in repro cycles
    before applying lambda, 
    -->2 additional files need to run simulation
    -->2 params to specify genepop indiv pop 
    sampling type and parameters.  Note that these
    sampling params have default values entered 
    above to cover 1-year-old cohort sampling using
    the output format current to pgopsimupop.py, using
    the version that includes demography in the genepop
    id fields.
    '''
    if config.has_section("startLambdas"):
        if config.has_option( "startLambdas", "values" ):
            paramTemp = config.get("startLambdas", "values")
            paramList = re.split(delimiters,paramTemp)
            startLambdas = [int(value) for value in paramList]


    if config.has_section("lifetable"):
        if config.has_option("lifetable", "name"):
            lifeTableFile = config.get("lifetable", "name")

    if config.has_section("simparamset"):
        if config.has_option("simparamset", "name"):
            simparamset = config.get("simparamset", "name")

    if config.has_section("popSamplingScheme"):
        if config.has_option("popSamplingScheme", "name"):
            popSamplingScheme = config.get("popSamplingScheme", "name")

    if config.has_section("popSamplingParams"):
        if config.has_option("popSamplingParams", "name"):
            popSamplingParams = config.get("popSamplingParams", "name")
    # end Ted-added config entries

    ##read lineRegress input file
    if config.has_section("lineRegress"):
        if config.has_option("lineRegress", "name"):
            lineRegressConfig = config.get("lineRegress", "name")

    ##read Lambda
    if config.has_section("lambda"):
        if config.has_option("lambda", "values"):
            paramTemp = config.get("lambda", "values")
            paramList = re.split(delimiters,paramTemp)
            lambdas = [float(value) for value in paramList]

    ##read starting population
    if config.has_section("startPop"):
        if config.has_option("startPop", "values"):
            paramTemp = config.get("startPop", "values")
            paramList = re.split(delimiters,paramTemp)
            startPopulations = [int(value) for value in paramList]

    '''
    Not used, and not sure if it is synonymous with N0,
    which is used and is the number of newborns.
    '''
    ##read starting newborns (N0)
    if config.has_section("startNewborns"):
        if config.has_option("startNewborns", "values"):
            paramTemp = config.get("startNewborns", "values")
            paramList = re.split(delimiters,paramTemp)
            N0s = [int(value) for value in paramList]

    ##read starting newborns (N0)
    '''
    This value is used.
    '''
    if config.has_section("N0"):
        if config.has_option("N0", "values"):
            paramTemp = config.get("N0", "values")
            paramList = re.split(delimiters,paramTemp)
            N0s = [int(value) for value in paramList]

    ##read Number of Microsats
    if config.has_section("Microsats"):
        if config.has_option("Microsats", "values"):
            paramTemp = config.get("Microsats", "values")
            paramList = re.split(delimiters,paramTemp)
            microsats = [int(value) for value in paramList]

    ## read number of alleles per microsat
    if config.has_section("alleleCount"):
        if config.has_option("alleleCount", "values"):
            paramTemp = config.get("alleleCount", "values")
            paramList = re.split(delimiters,paramTemp)
            alleleCount = [int(value) for value in paramList]

    ##read in number of SNPs
    if config.has_section("SNPs"):
        if config.has_option("SNPs", "values"):
            paramTemp = config.get("SNPs", "values")
            paramList = re.split(delimiters,paramTemp)
            SNPs = [int(value) for value in paramList]

    ##read in mutation Rate
    if config.has_section("mutationRate"):
        if config.has_option("mutationRate", "values"):
            paramTemp = config.get("mutationRate", "values")
            paramList = re.split(delimiters,paramTemp)
            mutationRate = [float(value) for value in paramList]


    if config.has_section("lociSampleRate"):
        if config.has_option("lociSampleRate", "values"):
            paramTemp = config.get("lociSampleRate", "values")
            paramList = re.split(delimiters,paramTemp)
            #Ted changed type int to float for this param.
            #From default it looks like it was meant to be a proportion
            #and so a float.
            lociSampling = [float(value) for value in paramList]


    if config.has_section("individualSamplRate"):
        if config.has_option("individualSamplRate", "values"):
            paramTemp = config.get("individualSamplRate", "values")
            paramList = re.split(delimiters,paramTemp)
            #Ted changed type int to float for this param. See above
            #for lociSampling.
            populationSampling = [float(value) for value in paramList]

    if config.has_section("simReps"):
        if config.has_option("simReps", "values"):
            paramTemp = config.get("simReps", "values")
            paramList = re.split(delimiters,paramTemp)
            simReps = [int(value) for value in paramList]




    ##create parameter dictionary for return
    paramDict = {"species":speciesFile,
                #Ted added following two entries 2016_10_18
                 "lifetable":lifeTableFile,
                 "simparamset":simparamset,
                 "outputFolder":outFolder,
                 "regressConfig":lineRegressConfig,
                 "lambdas":lambdas,
                 "startLambdas":startLambdas,
                 "startPops":startPopulations,
                 "N0":N0s,
                 "microsats":microsats,
                 "alleleCount":alleleCount,
                 "SNPs":SNPs,
                 "mutationRate":mutationRate,
                 "lociSampling":lociSampling,
                 "popSampling":populationSampling,
                 #Ted added following two entries 2016_10_23:
                 "popSamplingScheme":popSamplingScheme,
                 "popSamplingParams":popSamplingParams,
                 "simReps":simReps}
    return paramDict

#Ted added 2016_10_18, for easier revision.

def getUniqFileName(lengthLimit=None):
    '''
    As of 2016_10_18, provisional code,
    that names the sim output files with
    long random strings. This may need to change,
    as names more human-understandable
    may be needed.
    '''


    uniqStrAsList=list( str( uuid.uuid4() ).replace( "-", "x" ) )

    lenUniqStr=len( uniqStrAsList )

    baseNameLen=lenUniqStr

    if lengthLimit is not None:
        baseNameLen=min( [ lengthLimit, lenUniqStr ] )
    #end if we have a limit on length

    uniqNameAsList=uniqStrAsList

    if  baseNameLen < lenUniqStr:
        uniqNameAsList=random.sample( uniqStrAsList, baseNameLen )    
    #end if we can't use the whole uniq string

    uniqName="".join( uniqNameAsList )    

    return uniqName
#end getUniqFileName

def getSimOutfileBasename(runFolder, replicateNumber):

    uniqName=getUniqFileName( lengthLimit=10 )

    baseName=runFolder + os.sep + uniqName + "_r_" + str( replicateNumber )

    return baseName
#end getSimOutfileBasename

#Ted added 2016_10_18.
def resetSimInputParams(o_simInput, lambdaVal, startLambda, startPop,N0,microSats,alleleCount,SNPs,mutationRate):
    '''
    Since the o_simInput object will have
    parameter values as set in the config
    file, and new values are needed,   
    this def updates values as given
    by the def parameters.  It changes the 
    caller's value for param, o_simInput object, 
    in place, and so returns None.
    '''
    o_simInput.lbd=lambdaVal
    o_simInput.startLambda=startLambda
    o_simInput.popSize=startPop
    o_simInput.startAlleles=alleleCount
    o_simInput.mutFreq=mutationRate 

    '''
    N0 assignment may fail if the life table
    has an "effective_size" section.  In this case
    the input object diallows direct setting of
    N0. We want to know if a fail is on this
    param in particular.
    '''
    try:
        o_simInput.N0=int( N0 )
    except Exception as oex:
        s_msg="In mod SimBatchRun.py, " \
                + "def resetSimInputParams, " \
                + "can't assign an N0 value. " \
                + "Assignment value attempted was, " \
                + str( N0 ) + ".  Exception raised: " \
                + str( oex ) + "."
        raise Exception( oex )
    #end try . . . except
    return
#end resetSimInputParams

#Ted added 2016_10_18 to ease revision
def setupPyCommandForPopen( defName, defArgSequence ):
    '''
    This def creates a string to be used in
    a subprocess POpen call, such that it
    is the stringified def call arg for the
    python terminal -p parameter, preceeded
    by an import statement (importing this module).
    '''
    AQUOTE="'"

    callAsString=""

    stringifiedArgs=[]    

    for anArg in defArgSequence:
        argAsString=str(anArg)

        #String args not recognized unless quoted
        if type( anArg ) == str:
            argAsString = AQUOTE + anArg + AQUOTE
        #end if string, then enclose
        stringifiedArgs.append( argAsString )
    #end for each arg, stringify

    argsAsOneString=",".join( stringifiedArgs )
    
    currentModFilename=__file__
    modName=None
    '''
    If this is for a nested Popen call
    then the mod's file name will have a *.pyc extension.
    If its the first Popen call after execution,
    then it will have extension *.py
    '''
    
    if currentModFilename.endswith( ".py" ):
        modName=currentModFilename.replace( ".py", "" )
    else:
        modName=currentModFilename.replace( ".pyc", "" )
    #end if py mod else pyc mod

    modName=os.path.basename( modName )
    callAsString="import " +  modName + " as mymod;" \
            + "mymod." + defName  + "(" + argsAsOneString + ")"

    return callAsString
#end setupPyCommandForPopen

'''
    2016_10_18 Ted added the following def to do 1 of N sim reps, 
    as called from runSimulation.  The  params are identical to 
    those for runSimulation except:
    --simRepNumber is int i in (1,2,3...N) of
    N replicates (instead of simReps=N, in the runSimulation param list).
    --outFileBaseName is the path and base name to the outfile location
    to which the Sim will write it's *conf and *genepop files (instead of
    the original value passed too runSimulation, the "outFolder", which 
    is likely now part of the outfile base namei).
'''
def runOneSimulationRep( species, lifetable, simparamset, outFileBaseName,simRepNumber,lambdaVal,startLambda, startPop,N0,microSats,alleleCount,SNPs,mutationRate ):
    '''
    Run one simulation. Amenable to being in 
    a new python subprocess
    '''

    import pgparamset as pgparams
    import pgsimupopresources as pgres
    import pginputsimupop as pgin
    import pgoutputsimupop as pgout
    import pgopsimupop as pgop

    o_paramInfo=pgparams.PGParamSet( simparamset )
    o_lifeTableInfo=pgres.PGSimuPopResources( [ lifetable ] )
    o_simInput=pgin.PGInputSimuPop( species, o_lifeTableInfo, o_paramInfo )
    o_simInput.makeInputConfig()

    o_simOutput=pgout.PGOutputSimuPop( outFileBaseName )

    resetSimInputParams( o_simInput, lambdaVal, startLambda, startPop, N0, microSats, alleleCount, SNPs, mutationRate )

    o_simOp=pgop.PGOpSimuPop( o_simInput, o_simOutput, b_remove_db_gen_sim_files=True, b_write_input_as_config_file=True )

    o_simOp.prepareOp()
    o_simOp.doOp()

    return
#end runOneSimulationRep
    
# Ted added 2016_10_18  new param "lifetable" and "process" 
def runDefCallsInSeparateProcesses( defName, defArgSets, processorCount=1, pyExeName="python" ):
    '''
    Input Params:
        defName, string naming a def in this module.
        defArgSets, a list of sequences, each of which
            is an arg set that correctly gives the
            params to the def    
        processorCount, optional, the total processes to
            run in parallel.
        pyExeName, the python executable to invoke 
            through Popen.

    Ouput: None.  Currently the return val of each def
        is not available.

    Runs python subprocesses using POpen, one process for
    each arg set, adding new processes as others finish,
    to try to keep max <= processorCount running in 
    parallel.
    '''

    import time
    import subprocess
    from pgutilityclasses import IndependantSubprocessGroup

    SLEEPINSECONDS=0.05

    subProcesses=IndependantSubprocessGroup()

    defCallStartedCount=0

    defCallCount=len( defArgSets )

    while defCallStartedCount < defCallCount:

        subprocessCount=subProcesses.getTotalAlive()

        availableProcessCount=processorCount-subprocessCount

        remainingCallCount=defCallCount-defCallStartedCount

        numSubprocessToStart=min( availableProcessCount, remainingCallCount )

        for idx in range( numSubprocessToStart ):
            #Zero-indexed list of arg sets accessed before
            #we increment our 1-based count of started def calls:

            pyCommandForPopen=setupPyCommandForPopen( defName, defArgSets[ defCallStartedCount ] )

            #####temp
            print( "command: " + pyCommandForPopen )
            #####
            defCallStartedCount += 1
    
            newSubprocess=subprocess.Popen( [ pyExeName, "-c",  pyCommandForPopen ] )

            subProcesses.addSubprocess( newSubprocess )

        #end for each arg set

        time.sleep( SLEEPINSECONDS )
    #end while there are calls yet to start
        
    #With no calls left to invoke, we 
    #wait until all in processes are  done:
    while subProcesses.getTotalAlive() > 0:
        time.sleep( SLEEPINSECONDS )
    #end while processes still alive

    return
#end runDefCallsInSeparateProcesses

# Ted added 2016_10_18  new params "lifetable" and "process" 
# and code to hook up with simulation-runs
def runSimulation(species, lifetable, simparamset, outFolder,simReps,lambdaVal, startLambda, startPop,N0,microSats,alleleCount,SNPs,mutationRate, processorCount=NUM_PROCS_FOR_SIM_REPS ):

    SINGLE_SIM_DEF_NAME="runOneSimulationRep"

    argSets=[]
    
    outputFiles = []

    '''
    Make arg sets in order to
    call the simulation in separate
    processes.  
    ''' 
    for repNumber in range( simReps ):
        outfileBasename=getSimOutfileBasename( outFolder, replicateNumber=repNumber )
        anArgSet=(species, lifetable, simparamset, outfileBasename, repNumber, 
                lambdaVal,startLambda, startPop,N0,microSats,alleleCount,SNPs,mutationRate )
        argSets.append( anArgSet )
        outputFiles.append( outfileBasename + ".genepop" )
    #end for each rep, make an arg set

    '''
    This may be run most often with just. processorCount=1, especially
    if the parallelized factor is to be the number of sims run with 
    different parameters. In the single proccess case running the 
    sims via this call consume about the same time and resources
    as would calling runOneSimulationRep in the main process: 
    '''
    runDefCallsInSeparateProcesses( SINGLE_SIM_DEF_NAME, argSets, processorCount=processorCount )

    return outputFiles
#end runSimulation

#Ted added (2016_10_23) these support defs for runNeEst
def getGenepopFile( files, runFolder ):
    '''
    Not sure what the files variable will contain.
    For now, 2016_10_23, we assume "files" is a string
    giveing the genepop file name.  If the folder is
    not part of the genepop file name, then add it.

    This def likely will need revising after I more 
    clearly see how folders are created.
    '''
    s_genepopfile=files

    if runFolder not in files:
        s_genepopfile=runFolder + os.sep + files
    #end if folder not already part of file name    
    return s_genepopfile

#end getGenepopFile

def  getNeOutfileBaseName( runFolder ):
    '''
    Return the basename that will prefix 
    the *.tsv file name and *.msgs
    files that will be written by
    pgdriveneestimator.py.
    '''
    s_basePrefix=getUniqFileName( lengthLimit=20 )

    s_baseName=runFolder + os.sep + s_basePrefix 

    return s_baseName 
#end getNeOutfileBaseName


def doNeEstimation( genepopFiles, runFolder, locisampling, popsampling, popSamplingScheme, popSamplingParams, processorCount ):

    '''
    These are the command line args (as of 2017_01_15).  We're calling the module 
    in the alternative method, by importing pgdriveneestimator and then calling 
    its "mymain" def, with the args values listed in sequence:

          usage: pgdriveneestimator.py [-h] -f GPFILES -s SCHEME -p PARAMS -m MINPOPSIZE
                             -a MAXPOPSIZE -r POPRANGE -e MINALLELEFREQ -c
                             REPLICATES -l LOCISCHEME -i LOCISCHEMEPARAMS -n
                             MINTOTALLOCI -x MAXTOTALLOCI -g LOCIRANGE -q
                             LOCIREPLICATES [-o PROCESSES] [-d MODE] 

    Since we're using the mymain call method instead of the terminal command, we
    also add the output file objects that are used instead of stdout and stderr.
    Finally, we add a None value for the MultiprocessingEvent argument, which is
    only used in the setting of the GUI.  To till out the arg values, we set
    the following as constants:
    '''
    import pgdriveneestimator as pgdrive

    
    MULTIPROCEVENT=None

    '''
    In the usual case the popsampling value (assumed to be a float giving a proportion),
    will be appended to the default value of popSamplingParams, which specify the fields
    and the "max_age" criteria (default age is 1, see above def readconfig). In this scenario 
    the parameter string ends with the percent value appended to the max_age value with a 
    semi-colon delimiter.  As of now, 2016_10_23, we are assuming that any non-empty string 
    for the sampling params value will be correctly passed to pgdriveneestimator by appending 
    the proportion as a percent value.
    '''
    
    popsamplingAsArg=str( popsampling )

    if popsampling>=0.0 and popsampling<=1.0:
        popsamplingAsArg = str(  popsampling * 100.0 )
    #end if popsampling is a proportion, make a percentage

    locisamplingArg=str( locisampling )
    if locisampling>=0.0 and locisampling <= 1.0:
        locisamplingArg=str( locisampling * 100.0 )
    #end if locisampling is a proportion, make a percentage

    popSamplingParams=popsamplingAsArg if popSamplingParams=="" else popSamplingParams + ";" + popsamplingAsArg

    neOutfileBaseName=getNeOutfileBaseName( runFolder )

    mainTableFile=neOutfileBaseName + ".tsv"
    msgsFile=neOutfileBaseName + ".msgs"

    objMainTableFile=open( mainTableFile, 'w' )
    objMsgsFile=open( msgsFile, 'w' )

    pgDriveArgs=( str(  genepopFiles  ), popSamplingScheme, popSamplingParams, 
                            MINPOPSIZE, MAXPOPSIZE, POPRANGE, MINALLELEFREQ, 
                            REPLICATES, LOCISCHEME, locisamplingArg, LOCIMIN, LOCIMAX,
                            LOCIRANGE, LOCIREPLICATES,  processorCount, MODE, objMainTableFile, 
                            objMsgsFile, MULTIPROCEVENT )
    
    pgdrive.mymain( *pgDriveArgs ) 

    return mainTableFile
#end doNeEstimation

'''
Ted added 2 params on 2016_10_23 to specify pop sampling scheme, 
and added code to call pgdriveneestimator.py.
Note that the "processorCount" parameter refers to the number 
of processes to run in parallel
'''
def runNeEst(files,runFolder,locisampling, popsampling, popSamplingScheme, popSamplingParams, regressConfig, processorCount = NUM_PROCS_FOR_NE_EST ):
    statsFile = ""
    #create output folder

    #run neEstimator
    neFile = doNeEstimation( files, runFolder, locisampling, popsampling, popSamplingScheme, popSamplingParams, processorCount  )

    ##### temp rem out plotting calls
    #run lineregress
#    configVals = Viz.LineRegress.neConfigRead(regressConfig)
#    statsFile =  Viz.LineRegress._neStatsHelper(neFile, configVals["alpha"], outFileName=statsFile,significantValue=configVals["sigSlope"],firstVal=configVals["startData"])
#    return statsFile
    #just a place holder as the call to this def
    #asks for 2 items
    return None, None
    ##### end temp


def gatherNe(fileName,firstVal):
    results, temp = ResultScraper.scrapeNE(fileName,firstVal)
    return results

def gatherPower(filename):
    powerData = ResultScraper.scrapePower(filename)
    return powerData

def gatherSlopes(filename):
    slopeData = ResultScraper.scrapeSlopes(filename)
    return slopeData


def createIdentifier(species, outFolder, simReps, lambdaVal, startPop, N0, microSats, alleleCount, SNPs, mutationRate, locisampling, popsampling, regressConfig):
    identifier = "l"+str(lambdaVal) \
    +"p" + str(startPop)\
    + "N0" + str(N0) \
    + "m" + str(microSats)\
    + "ac" + str(alleleCount)\
    + "SNPs" + str(SNPs)\
    + "mr" + str(mutationRate)\
    + "ls" + str(locisampling)\
    + "ps" + str(popsampling)
    return identifier


def parseIdentifier(identifier):
    re.compile('l(?P<lambda>[\d.\.]*)p(?P<startPop>[\d*])N0(?P<N0>[\d]*)m(?P<microsats>[\d]*)ac(?P<allelecount>[\d]*)SNPs(?P<SNPs>[\d]*)mr(?P<mutations>[\d\.]*)ls(?P<locisampling>[\d\.]*)ps(?P<popsampling>[\d\.]*)')





def nameRunFolder(species,outFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate,locisampling,popsampling,regressConfig):
    runFolder = createIdentifier(species,outFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate,locisampling,popsampling,regressConfig)
    print runFolder
    #Ted changed os.sys to os.path:
    runFolder = os.path.join(outFolder, runFolder)
    if os.path.isdir(runFolder):
        return None
    return runFolder

#Ted added params "lifetable", "simparamset" 2016_10_18, and params popSamplingScheme and popSamplingParams on 2016_10_23, 
#and param startLambda on 2016_10_25
def run(species,lifetable,simparamset,outFolder,simReps,lambdaVal,startLambda,startPop,N0,microSats,alleleCount,SNPs,mutationRate,locisampling,popsampling, popSamplingScheme, popSamplingParams, regressConfig):
    runFolder = nameRunFolder(species,outFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate,locisampling,popsampling,regressConfig)

    if  not runFolder:
        return

    os.makedirs(runFolder)
    simFiles = runSimulation(species,lifetable,simparamset,runFolder,simReps,lambdaVal,startLambda,startPop,N0,microSats,alleleCount,SNPs,mutationRate)
    neFile, statsFile = runNeEst(simFiles,runFolder,locisampling,popsampling,popSamplingScheme, popSamplingParams, regressConfig)

    return neFile, statsFile

def runSamplingOnly(files,runFolder,locisampling,popsampling,regressConfig):
    neFile, statsFile = runNeEst(files,runFolder,locisampling,popsampling,popSamplingScheme, popSamplingParams, regressConfig)
    return neFile,statsFile

def collectStatsData(neDict, statsDict, outFolder,firstVal):
    slopesName = "slopes.csv"
    powerName = "power.csv"
    neName = "Ne.csv"

    for identifier in neDict:
        neFile = neDict[identifier]
        neData = gatherNe(neFile, firstVal)
        nePath = os.path.join(outFolder, neName)
        neOut = open(nePath, "w")
        neOut.write("parameters,replicate,Reproductive Cycle,Ne\n")
        for datapoint in neData:
            print datapoint
            data = neData[datapoint]
            print data
            for point in data:
                neOut.write(str(identifier) + "," + str(datapoint) + "," + str(point[0]) + "," + str(point[1]) + "\n")
    neOut.close()

    for identifier in statsDict:
        statsFile = statsDict[identifier]
        slopePath =os.path.join(outFolder, slopesName)
        powerPath = os.path.join(outFolder, powerName)
        powerOut = open(powerPath,"w")
        slopeOut = open(slopePath,"w")






def batch(configFile,threads = 1):
    configs  = readconfig(configFile)
    speciesFile = configs["species"]
    outFolder = configs["outputFolder"]
    incriment = 1
    while os.path.isdir(outFolder):
        #Ted cast var "incriment" assigned above,
        #as string so the concat op would work:
        outFolder = outFolder+"("+str(incriment)+")"
        incriment+=1
    #Ted,  changed "mkdirs" to makedirs 2016_10_24
    #(assuming that's the def intended)
    os.makedirs(outFolder)

    runParams = product(configs["species"],configs["lifetable"],configs["simparamset"],[outFolder],configs["simReps"],configs["lambdas"],configs["startLambda"],configs["startPops"],configs["N0"],configs["microsats"],configs["alleleCount"],configs["SNPs"],configs["mutationRate"],configs["lociSampling"],configs["popSampling"],configs["popSamplingScheme"], configs["popSamplingParams" ], configs["regressConfig"])

    if len(configs["simReps"])==1 and len(configs["startPops"])==1 and len(configs["N0"])==1 and len(configs["microsats"])==1 and len(configs["alleleCount"])==1 and len(configs["SNPs"])==1 and len(configs["mutationRate"])==1:
        if threads == 1:
            neFiles = []
            simFiles = runSimulation(runParams[0],runParams[1],runParams[2],runParams[3],runParams[4],runParams[5],runParams[6],runParams[7],runParams[8],runParams[9])
            neDict = {}
            statsDict ={}
            for paramset in runParams:
                runFolder = nameRunFolder(*runParams)
                if not runFolder:
                    continue
                ident = createIdentifier(*runParams)
                neFile, statsFile = run(*runParams)
                neDict[ident] = neFile
                statsDict[ident] = statsFile
    else:
        if threads ==1:
            neDict = {}
            statsDict ={}
            for paramset in runParams:
                ident = createIdentifier(*runParams)
                neFile, statsFile = run(*runParams)
                neDict[ident] = neFile
                statsDict[ident] = statsFile

'''
Ted added 2016_10_24, for testing.
'''
if __name__ == "__main__":

    import argparse as ap

    REQUIRED_SHORT=[ "-c", "-r" ] 
    OPTIONAL_SHORT=["-s", "-n"  ]

    REQUIRED_LONG=["--configfile", "--runthreads" ] 
    OPTIONAL_LONG=[ "--simthreads", "--nethreads" ]

    s_chelp="configuration file"
    s_rhelp="Processes to run in parallel for calls to run.  " \
                    + "Use available cores if you have lots of " \
                    + "values in lists in your batch config file."
    s_shelp="Optional, default is 1.  Processes to run in parallel for simulations.  " \
                    + "For each process used according to  the -r value, this many will " \
                    + "be allocated, one for each simulation replicate.  " \
                    + "If run calls are few, and number of sim replicates " \
                    + "are many, use one core for -r, and a higher number here."
    s_nhelp="Optional, default is 1. Process to run in parallel for Ne estimations.  " \
                    + "For each process used according to  the -r value, this many will " \
                    + "be allocated for Ne estimation runs.  "  \
                    + "If run calls are few, and total populations in the genepop " \
                    + "files is many, use one core for -r, and a higher number here."

    REQUIRED_HELP=[ s_chelp, s_rhelp ]
    OPTIONAL_HELP=[ s_shelp, s_nhelp ] 

    o_parser=ap.ArgumentParser()
    o_arglist=o_parser.add_argument_group( "args" )

    i_total_nonopt=len( REQUIRED_SHORT )

    for idx in range( i_total_nonopt ):
        o_arglist.add_argument( \
                REQUIRED_SHORT[ idx ],
                REQUIRED_LONG[ idx ],
                help=REQUIRED_HELP[ idx ],
                required=True )
    #end for each arg

    i_total_opt=len( OPTIONAL_SHORT )

    for idx in range( i_total_opt ):
        o_parser.add_argument( \
                OPTIONAL_SHORT[ idx ],
                OPTIONAL_LONG[ idx ],
                help=OPTIONAL_HELP[ idx ],
                required=False )


    o_args=o_parser.parse_args()

    s_configfile=o_args.configfile
    i_run_threads=int( o_args.runthreads )

    if o_args.simthreads is not None:
        NUM_PROCS_FOR_SIM_REPS=o_args.simthreads    
    #end if we have optional simthreads

    if o_args.nethreads is not None:
        NUM_PROCS_FOR_NE_EST=o_args.nethreads
    #end if we have optional nethreads 

    configs  = readconfig(s_configfile)
    speciesFile = configs["species"]
    outFolder = configs["outputFolder"]

    list_of_arg_sets=[]

    for idx_n0 in range( len( configs[ "N0" ] ) ):
        for idx_lambda in range( len ( configs[ "lambdas" ] ) ):
            #sub in our chosen-for-testing single-list 
            args_for_this_run=(configs["species"],configs["lifetable"],configs["simparamset"],
                        [outFolder],configs["simReps"],configs["lambdas"][idx_lambda],configs["startLambdas"],
                        configs["startPops"], configs["N0"][idx_n0],configs["microsats"],configs["alleleCount"],
                        configs["SNPs"], configs["mutationRate"],configs["lociSampling"],configs["popSampling"],
                        configs["popSamplingScheme"], configs["popSamplingParams" ], configs["regressConfig"] )

            #As for any other listed items, we'll just pass along the first val:
            args_for_this_run=[ v_val if type( v_val ) != list  else v_val[ 0 ] for v_val in args_for_this_run ]
            list_of_arg_sets.append( args_for_this_run )
        #end for each lambda
    #end for each N0 value

    runDefCallsInSeparateProcesses( defName="run", defArgSets=list_of_arg_sets, processorCount=i_run_threads )


#end if name is main

