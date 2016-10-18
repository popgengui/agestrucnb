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
    return resultDict

def scrapeNe(filename, firstVal):
    fileBuffer = open(filename, "rb")
    replicateData = csv.DictReader(fileBuffer, delimiter="\t", quotechar="\"")
    dataDict = {}
    popDict = {}
    popNum = 0
    for item in replicateData:
        sourceName = item['original_file']
        pop = item['pop']
        popNum = int(pop)
        individualCount = int(item["indiv_count"])
        neEst = float(item['est_ne'])
        maxError = float(item['95ci_high'])
        minError = float(item['95ci_low'])
        # if neEst == "NaN":
        #    neEst = sys.maxint
        if not sourceName in dataDict:
            dataDict[sourceName] = {}
            popDict[sourceName] = {}
        dataDict[sourceName][popNum] = neEst
        popDict[sourceName][popNum] = individualCount
    replicateKeys = dataDict.keys()
    resultTable = {}
    individualCountTable = {}
    for replicate in replicateKeys:
        replicateVctr = []
        individualCountVctr = []
        replicateDict = dataDict[replicate]
        individualCountDict = popDict[replicate]
        popKeys = replicateDict.keys()
        popKeys.sort()
        for popKey in popKeys:
            if popKey >= firstVal:
                # print popKey
                replicateVctr.append((popKey, replicateDict[popKey]))
                individualCountVctr.append((popKey, individualCountDict[popKey]))
        resultTable[replicate] = replicateVctr
        individualCountTable[replicate] = individualCountVctr
    return resultTable, individualCountTable

file  = "neStatsOut.txt"

scrapePower(file)
scrapeSlopes(file)