from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import configparser
import os
import re
from itertools import product
import LineRegress
import ResultScraper



def readconfig(filename):

    ## SETS DEFaULTS
    #all defaults must be in a list even if only one value
    speciesFile = ""
    outFolder = ""
    lineRegressConfig = ""
    lambdas = [1.0]
    startPopulations = []#TODO need default
    N0s = []#TODO need default
    microsats = []#TODO need default
    alleleCount = []#TODO needs default
    SNPs = []#TODO need default
    mutationRate = [0]
    lociSampling = [1.0]
    populationSampling = [1.0]
    simReps = [100]

    ##SET FILE DELIMITERS
    delimiters = ',|\||\n|;'

    #open files
    config = configparser.ConfigParser()
    config.readfp(open(filename))

    #read in output filename
    if config.has_section("outFolder"):
        if config.has_option("outFolder", "name"):
            outFolder = config.get("outFolder", "name")

    ##read species input file
    if config.has_section("species"):
        if config.has_option("species", "name"):
            speciesFile = config.get("species", "name")

    ##read lineRegress input file
    if config.has_section("lineRegress"):
        if config.has_option("lineRegress", "name"):
            lineRegressConfig = config.get("lineRegress", "name")

    ##read Lambda
    if config.has_section("lambda"):
        if config.has_option("lambda", "values"):
            paramTemp = config.get("lambda", "values")
            paramList = re.split(delimiters.paramTemp)
            lambdas = [float(value) for value in paramList]

    ##read starting population
    if config.has_section("startPop"):
        if config.has_option("startPop", "values"):
            paramTemp = config.get("startPop", "values")
            paramList = re.split(delimiters.paramTemp)
            startPopulations = [int(value) for value in paramList]

    ##read starting newborns (N0)
    if config.has_section("startNewborns"):
        if config.has_option("startNewborns", "values"):
            paramTemp = config.get("startNewborns", "values")
            paramList = re.split(delimiters.paramTemp)
            N0s = [int(value) for value in paramList]

    ##read starting newborns (N0)
    if config.has_section("N0"):
        if config.has_option("N0", "values"):
            paramTemp = config.get("N0", "values")
            paramList = re.split(delimiters.paramTemp)
            N0s = [int(value) for value in paramList]

    ##read Number of Microsats
    if config.has_section("Microsats"):
        if config.has_option("Microsats", "values"):
            paramTemp = config.get("Microsats", "values")
            paramList = re.split(delimiters.paramTemp)
            microsats = [int(value) for value in paramList]

    ## read number of alleles per microsat
    if config.has_section("alleleCount"):
        if config.has_option("alleleCount", "values"):
            paramTemp = config.get("alleleCount", "values")
            paramList = re.split(delimiters.paramTemp)
            alleleCount = [int(value) for value in paramList]

    ##read in number of SNPs
    if config.has_section("SNPs"):
        if config.has_option("SNPs", "values"):
            paramTemp = config.get("SNPs", "values")
            paramList = re.split(delimiters.paramTemp)
            SNPs = [int(value) for value in paramList]

    ##read in mutation Rate
    if config.has_section("mutationRate"):
        if config.has_option("mutationRate", "values"):
            paramTemp = config.get("mutationRate", "values")
            paramList = re.split(delimiters.paramTemp)
            mutationRate = [float(value) for value in paramList]


    if config.has_section("lociSampleRate"):
        if config.has_option("lociSampleRate", "values"):
            paramTemp = config.get("lociSampleRate", "values")
            paramList = re.split(delimiters.paramTemp)
            lociSampling = [int(value) for value in paramList]


    if config.has_section("individualSamplRate"):
        if config.has_option("individualSamplRate", "values"):
            paramTemp = config.get("individualSamplRate", "values")
            paramList = re.split(delimiters.paramTemp)
            populationSampling = [int(value) for value in paramList]

    if config.has_section("simReps"):
        if config.has_option("simReps", "values"):
            paramTemp = config.get("simReps", "values")
            paramList = re.split(delimiters.paramTemp)
            simReps = [int(value) for value in paramList]


    ##create parameter dictionary for return
    paramDict = {"species":speciesFile,
                 "outputFolder":outFolder,
                 "regressConfig":lineRegressConfig,
                 "lambdas":lambdas,
                 "startPops":startPopulations,
                 "N0":N0s,
                 "microsats":microsats,
                 "alleleCount":alleleCount,
                 "SNPs":SNPs,
                 "mutationRate":mutationRate,
                 "lociSampling":lociSampling,
                 "popSampling":populationSampling,
                 "simReps":simReps}
    return paramDict

def runSimulation(species,outFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate):
    outputFiles = []
    #create folder for simupop run
    #run simupop

    return outputFiles

def runNeEst(files,runFolder,locisampling,popsampling,regressConfig):
    statsFile = ""
    #create output folder
    #run neEstimator
    neFile = ""
    #run lineregress
    configVals = ResultScraper.configRead(regressConfig)
    statsFile =  LineRegress._neStatsHelper(neFile, configVals["alpha"], outFileName=statsFile,significantValue=configVals["sigSlope"],firstVal=configVals["startData"])
    return statsFile

def gatherNe(fileName,firstVal):
    results, temp = ResultScraper.scrapeNE(fileName,firstVal)
    return results

def gatherPower(filename):
    powerData = ResultScraper.scrapePower(filename)
    return powerData

def gatherSlopes(filename):
    instanceArray, arrayDict = ResultScraper.scrapeSlopes(filename)
    return instanceArray



def createIdentifier(species, outFolder, simReps, lambdaVal, startPop, N0, microSats, alleleCount, SNPs, mutationRate, locisampling, popsampling, regressConfig):
    identifier = "l"+str(lambdaVal)
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
    print(runFolder)
    runFolder = os.sys.join(outFolder, runFolder)
    if os.path.isdir(runFolder):
        return None
    return runFolder

def run(species,outFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate,locisampling,popsampling,regressConfig):
    runFolder = nameRunFolder(species,outFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate,locisampling,popsampling,regressConfig)
    if  not runFolder:
        return
    os.makedirs(runFolder)
    simFiles = runSimulation(species,runFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate)
    neFile, statsFile = runNeEst(simFiles,runFolder,locisampling,popsampling,regressConfig)

    return neFile, statsFile

def runSamplingOnly(files,runFolder,locisampling,popsampling,regressConfig):
    neFile, statsFile = runNeEst(files,runFolder,locisampling,popsampling,regressConfig)
    return neFile,statsFile

def collectStatsData(neDict, statsDict, outFolder,regressConfig):
    slopesName = "slopes.csv"
    powerName = "power.csv"
    neName = "Ne.csv"
    statConfig = ResultScraper.configRead(regressConfig)

    nePath = os.path.join(outFolder, neName)
    neOut = open(nePath, "w")
    neOut.write("parameters,replicate,Reproductive Cycle,Ne\n")
    for identifier in neDict:
        neFile = neDict[identifier]
        neData = gatherNe(neFile, statConfig["startData"])
        for datapoint in neData:
            print(datapoint)
            data = neData[datapoint]
            print(data)
            for point in data:
                neOut.write(str(identifier) + "," + str(datapoint) + "," + str(point[0]) + "," + str(point[1]) + "\n")
    neOut.close()

    #compile stats file
    slopePath = os.path.join(outFolder, slopesName)
    powerPath = os.path.join(outFolder, powerName)
    powerOut = open(powerPath, "w")
    powerOut.write("parameters,Positive Slopes,Neutral Slopes, Negative Slopes, Total\n")
    slopeOut = open(slopePath, "w")
    slopeOut.write("parameters,Slope,Intercept,CI Slope Min,CI Slope Max\n")
    for identifier in statsDict:
        statsFile = statsDict[identifier]
        power = gatherPower(statsFile)
        slopes = gatherSlopes(statsFile)
        sumPower = sum(power.values())
        powerOut.write(str(identifier)+ "," +str(power["positive"])+ "," +str(power["neutral"])+ "," +str(power["negative"])+ "," +str(sumPower)+"\n")
        for dataPoint in slopes:
            slopeOut.write(str(identifier)+ "," +dataPoint["slope"]+ "," +dataPoint["intercept"]+ "," +dataPoint["lowerCI"]+ "," +dataPoint["upperCI"]+"\n")
    powerOut.close()
    slopeOut.close()



def batch(configFile,threads = 1):
    configs  = readconfig(configFile)
    speciesFile = configs["species"]
    outFolder = configs["outputFolder"]
    incriment = 1
    while os.path.isdir(outFolder):
        outFolder = outFolder+"("+incriment+")"
        incriment+=1
    os.mkdirs(outFolder)
    runParams = product(configs["species"],[outFolder],configs["simReps"],configs["lambdas"],configs["startPops"],configs["N0"],configs["microsats"],configs["alleleCount"],configs["SNPs"],configs["mutationRate"],configs["lociSampling"],configs["popSampling"],configs["regressConfig"])

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

    collectStatsData(neDict, statsDict, outFolder, configs["regressConfig"])





