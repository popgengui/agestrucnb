import ConfigParser
import csv
import re


def scrapePower(fileName):
    statFile  = open(fileName)
    powerRegex = re.compile('Positive Slopes:\s+(?P<positive>\d*)\s+Neutral Slopes:\s+(?P<neutral>\d*)\s+Negative Slopes:\s+(?P<negative>\d*)')
    fileText = statFile.read()
    matches= powerRegex.search(fileText)
    #print matches.groups()
    powerResults = {"positive":int(matches.group("positive")),"neutral":int(matches.group("neutral")),"negative":int(matches.group("negative"))}
    #print results
    return powerResults


def scrapeSlopes(fileName):
    statFile  = open(fileName)
    slopeRegex = re.compile('^([+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)\s*([+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)\s*(\(([+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?),\s([+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)\))',re.MULTILINE)
    fileText = statFile.read()
    matches = slopeRegex.findall(fileText)
    slopeResults = []
    for match in  matches:
        matchDict ={}
        print match
        matchDict['slope'] = float(match[0])
        matchDict['intercept'] = float(match[1])
        matchDict['lowerCI'] = float(match[3])
        matchDict['upperCI'] = float(match[4])
        slopeResults.append(matchDict)
        print matchDict
    slopeArray = [dict['slope'] for dict in slopeResults]
    interceptArray = [dict['intercept'] for dict in slopeResults]
    lowerCIArray=[dict['lowerCI']for dict in slopeResults]
    upperCIArray = [dict['upperCI'] for dict in slopeResults]
    resultDict = {"slope":slopeArray,"intercept":interceptArray,"lowerCI":lowerCIArray,"upperCI":upperCIArray}
    print resultDict
    return slopeResults, resultDict

def scrapeNE(filename, firstVal=0):
    fileBuffer = open(filename, "rb")
    replicateData = csv.DictReader(fileBuffer, delimiter="\t", quotechar="\"")
    dataDict = {}
    popDict = {}
    maxDict = {}
    minDict ={}
    popNum = 0
    for item in replicateData:
        sourceName = item['original_file']
        pop = item['pop']
        popNum = int(pop)
        individualCount = int(item["census"])
        neEst = float(item['est_ne'])
        maxError = float(item['95ci_high'])
        minError = float(item['95ci_low'])
        # if neEst == "NaN":
        #    neEst = sys.maxint
        if not sourceName in dataDict:
            dataDict[sourceName] = {}
            popDict[sourceName] = {}
            maxDict[sourceName] = {}
            minDict[sourceName] = {}

        dataDict[sourceName][popNum] = neEst
        popDict[sourceName][popNum] = individualCount
        maxDict[sourceName][popNum] = maxError
        minDict[sourceName][popNum] = minError
    replicateKeys = dataDict.keys()
    resultTable = {}
    individualCountTable = {}
    errorTable = {}
    for replicate in replicateKeys:
        replicateVctr = []
        individualCountVctr = []
        errorVctr = []
        replicateDict = dataDict[replicate]
        individualCountDict = popDict[replicate]
        minRepDict = minDict[replicate]
        maxRepDict = maxDict[replicate]

        popKeys = replicateDict.keys()
        popKeys.sort()
        for popKey in popKeys:
            if popKey >= firstVal:
                # print popKey
                replicateVctr.append((popKey, replicateDict[popKey]))
                individualCountVctr.append((popKey, individualCountDict[popKey]))
                errorVctr.append((popKey,minRepDict[popKey],maxRepDict[popKey]))
        resultTable[replicate] = replicateVctr
        individualCountTable[replicate] = individualCountVctr
        errorTable[replicate] = errorVctr
    return resultTable,individualCountTable, errorTable

#Method to read in a graph config file and return a dictionary of
def configRead(filename):
    configDict = {}
    title =  None
    xLab = None
    yLab = None
    setExpected = None
    boxplotDest = "show"
    destType = "show"
    regressionDest = "show"
    scatterDest = "show"
    xLims =None
    yLims = None
    autoFlag = False
    startDataCollect = 0
    alphaVal = 0.05
    statFileOut = "neStats.out"
    sigSlope = 0
    fileOrder = None
    groupBy = "pop"

    config = ConfigParser.ConfigParser()
    config.readfp(open(filename))
    if config.has_section("labels"):
        if config.has_option("labels", "title"):
            title = config.get("labels", "title")
        if config.has_option("labels", "xLab"):
            xLab = config.get("labels", "xLab")
        if config.has_option("labels", "yLab"):
            yLab = config.get("labels", "yLab")
    if config.has_section("destination"):
        if config.has_option("destination", "desttype"):
            destType = config.get("destination","desttype")

        if destType=="none":
            destType = "none"
            regressionDest = "none"
            boxplotDest = "none"
            scatterDest = "none"
        if config.has_option("destination","regressionfile"):
            regressionDest = config.get("destination","regressionfile")
        if config.has_option("destination", "boxplotfile"):
            boxplotDest = config.get("destination","boxplotfile")
        if config.has_option("destination", "scatterfile"):
            scatterDest = config.get("destination","scatterfile")
    if config.has_section("comparison"):
        valueFlag = True
        setExpected = None
        if config.has_option("comparison", "type"):
            comparisonType = config.get("comparison", "type")
            if comparisonType == "auto"  or comparisonType == "Auto"or comparisonType == "pop" or comparisonType == "Pop":
                setExpected = comparisonType
                valueFlag = False
            elif comparisonType == "None" or comparisonType == "none":
                valueFlag = False
        if  valueFlag:
            if config.has_option("comparison", "lambda"):
                lambdaValue = config.getfloat("comparison", "lambda")
                setExpected = lambdaValue-1
            if config.has_option("comparison", "expectedSlope"):
                expectedSlope = config.getfloat("comparison", "expectedSlope")
                setExpected =  expectedSlope

    if config.has_section("limits"):
        if config.has_option("limits", "xMin") and config.has_option("limits", "xMax"):
            xMin = config.getfloat("limits", "xMin")
            xMax = config.getfloat("limits", "xMax")
            xLims = (xMin, xMax)
        if config.has_option("limits", "yMin")and config.has_option("limits", "yMax"):
            yMin = config.getfloat("limits", "yMin")
            yMax = config.getfloat("limits", "yMax")
            yLims = (yMin, yMax)
    if config.has_section("confidence"):
        if config.has_option("confidence","alpha"):
            alphaVal = config.getfloat("confidence", "alpha")
        if config.has_option("confidence","outputFilename"):
            statFileOut = config.get("confidence","outputFilename")
        if config.has_option("confidence", "significantSlope"):
            sigSlope = config.getfloat("confidence", "significantSlope")

    if config.has_section("data"):
        if config.has_option("data","startCollect"):
            startDataCollect = config.getint("data","startCollect")

    if config.has_section("SubSample"):
        if config.has_option("SubSample", "GroupBy"):
            groupBy = config.get("SubSample", "GroupBy")



    configDict["title"]=title
    configDict["xLab"] = xLab
    configDict["yLab"] = yLab
    configDict["expected"] = setExpected
    configDict["dest"] = regressionDest
    configDict["boxplot"] = boxplotDest
    configDict["scatter"] = scatterDest
    configDict["xLims"] = xLims
    configDict["yLims"] = yLims
    configDict["alpha"] = alphaVal
    configDict["startData"] = startDataCollect
    configDict["statsFilename"] = statFileOut
    configDict["sigSlope"] = sigSlope
    configDict["groupBy"] = groupBy
    configDict["fileOrding"] = fileOrder
    return configDict


file  = "neStatsOut.txt"

scrapePower(file)
scrapeSlopes(file)