import ConfigParser
import re

import LineRegress

from neLineRegress import resultScraper


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
    simReps = [1000]

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

    if config.has_section("analysis"):
        if config.has_option("analysis", "types"):
            paramTemp = config.get("analysis", "types")
            paramList = re.split(delimiters.paramTemp)
            simReps = [value for value in paramList]

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
                 "simulationReps":simReps}

def runSimulation(species,outFolder,simReps,lambdaVal,startPop,N0,microSats,alleleCount,SNPs,mutationRate):
    neFile = ""
    #create folder for simupop run
    #run simupop
    #convert output files to TSV

    return outputFiles

def runNeEst(files,locisampling,popsampling,regressConfig):
    outputFile = ""
    #create output folder
    #run neEstimator
    neFile = ""
    #run lineregress
    statsFile =  LineRegress.neStats(neFile, regressConfig)
    return statsFile

def gatherNe(files):
    for filename in files:
        results, temp = resultScraper.scrapeNE(filename)


def gatherPower(filename):
    powerData = resultScraper.scrapePower(filename)
    return powerData

def gatherSlopesO(filename):
    slopeData = resultScraper.scrapeSlopes(filename)
    return slopeData

def batch(configFile,operations):
    configs  = readconfig(configFile)


