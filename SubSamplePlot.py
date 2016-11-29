import csv

import matplotlib.pyplot as plt



def createBoxPlot(table,title = None, xlab = None, yLab= None, dest = "show", sortCrit = "pop"):

    flatData = [val for sublist in table for val in table[sublist]]

    plotData = []

    unzippedX, unzippedy = zip(*flatData)
    setX = set(unzippedX)
    listX = list(setX)
    if sortCrit == "pop":
        sorted(listX,key=lambda tup: (tup[0],tup[1]))
    else:
        sorted(listX,key=lambda tup: (tup[1],tup[0]))
    for x in listX:
        ySet = [datum[1] for datum in flatData if datum[0] == x]
        plotData.append(ySet)
        # plotData = unzippedy
    plt.boxplot(plotData)
    #set v axis
    plt.xticks(range(len(listX)),listX)
    if title:
        plt.title(title)
    if xlab:
        plt.xlabel(xlab)
    if yLab:
        plt.ylabel(yLab)

    if dest == "show":
        plt.show()
    else:
        plt.savefig(dest, bbox_inches='tight')
    plt.close()
    plt.clf()

#reads in data fron neEst file outputs
def neFileRead(filename, firstVal = 0):
    fileBuffer = open(filename, "rb")
    replicateData = csv.DictReader(fileBuffer, delimiter="\t", quotechar="\"")
    dataDict = {}
    popDict={}
    popSample = 0
    for item in replicateData:
        sourceName = item['original_file']
        pop =  item['sample_value']
        popSample = float(pop)
        loci = item['loci_sample_value']
        lociSample = float(loci)
        individualCount = int(item["indiv_count"])
        neEst = float(item['est_ne'])
        #if neEst == "NaN":
        #    neEst = sys.maxint
        if  not sourceName in dataDict:
            dataDict[sourceName] = {}
            popDict[sourceName] = {}
        dataDict[sourceName][popSample][lociSample] = neEst
        popDict[sourceName][popSample][lociSample]=individualCount
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
            lociKeys = replicateDict[popKey].keys()
            lociKeys.sort()
            for lociKey in lociKeys:
                #print popKey
                replicateVctr.append((popKey,lociKey,replicateDict[popKey][lociKey]))
                individualCountVctr.append((popKey,lociKey,individualCountDict[popKey][lociKey]))
        resultTable[replicate] = replicateVctr
        individualCountTable[replicate] = individualCountVctr
    return resultTable,individualCountTable


def groupBy(table,groupIdentifier = "pop"):
    sortedDict = {}
    for key in table.keys():
        keyData = table[key]
        newKeyVctr = []
        if groupIdentifier == "pop":
            sorted(keyData, key=lambda tup: (tup[0],tup[1]) )
        if groupIdentifier == "loci":
            sorted(keyData, key=lambda tup: (tup[1], tup[0]))
        for touple in keyData:
            newTouple = ((touple[0],touple[1]),touple[2])
            newKeyVctr.append(newTouple)

        sortedDict[key] = newKeyVctr
    return sortedDict



def createErrorPlot(table,errorTable, title = None, xlab = None, yLab= None, dest = "show"):

    flatData = [val for sublist in table for val in table[sublist]]

    plotData = []

    unzippedX, unzippedy = zip(*flatData)
    setX = set(unzippedX)
    listX = list(setX)
    listX.sort()
    for x in listX:
        ySet = [datum[1] for datum in flatData if datum[0] == x]
        plotData.append(ySet)
        # plotData = unzippedy

#def create3Dplot

def subSamplePlotter(neFile, configFile = None):
    if configFile == None:
        table, popTable = neFileRead(neFile)
        if len(table.keys()) ==1:
            createBoxPlot(table,"loci")
        else:
            for key in table.keys():
                tempTable = {key:table[key]}
                createBoxPlot(tempTable)

if __name__ == "__main__":
    subSamplePlotter("test.tsv")

