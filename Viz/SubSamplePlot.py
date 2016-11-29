import csv

import matplotlib.pyplot as plt



def createBoxPlot(table,title = None, xlab = None, yLab= None, dest = "show", sortCrit = "pop"):

    flatData = [val for sublist in table for val in table[sublist]]

    plotData = []

    unzippedX = [x[0] for x in flatData if x[0]]
    print unzippedX
    setX = set(unzippedX)
    listX = list(setX)
    print listX
    if sortCrit == "pop":
        listX = sorted(listX,key=lambda tup: (tup[0],tup[1]))
    else:
        listX = sorted(listX,key=lambda tup: (tup[1],tup[0]))
        print listX
    for x in listX:
        ySet = [datum[1] for datum in flatData if datum[0] == x]
        plotData.append(ySet)
        # plotData = unzippedy
    plotData.append([])
    listX.append("$(Pop,Loci)$")
    plt.boxplot(plotData, labels= listX)
    plt.xticks(rotation=45)
    if title:
        plt.title(title)
    if xlab:
        plt.xlabel(xlab)
    if yLab:
        plt.ylabel(yLab)
    plt.subplots_adjust(bottom = 0.25)
    plt.margins(0.15,0.15)

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
        if not popSample in dataDict[sourceName]:
            dataDict[sourceName][popSample] = {}
            popDict[sourceName][popSample] = {}
        if not lociSample in dataDict[sourceName][popSample]:
            dataDict[sourceName][popSample][lociSample] = []
            popDict[sourceName][popSample][lociSample] = []
        dataDict[sourceName][popSample][lociSample].append(neEst)
        popDict[sourceName][popSample][lociSample].append(individualCount)
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
                print popKey
                print lociKey
                replicateVctr.append((popKey,lociKey,replicateDict[popKey][lociKey]))
                individualCountVctr.append((popKey,lociKey,individualCountDict[popKey][lociKey]))
        resultTable[replicate] = replicateVctr
        individualCountTable[replicate] = individualCountVctr
        print resultTable
    return resultTable,individualCountTable


def groupBy(table,groupIdentifier = "pop"):
    sortedDict = {}
    for key in table.keys():
        keyData = table[key]
        newKeyVctr = []
        if groupIdentifier == "pop":
            data = sorted(keyData, key=lambda tup: (tup[0],tup[1]) )
        else:
            data = sorted(keyData, key=lambda tup: (tup[1], tup[0]))
            print keyData
        for touple in data:
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
        sortedTable = groupBy(table,"loci")
        if len(table.keys()) ==1:
            createBoxPlot(sortedTable,sortCrit = "loci")

        else:
            for key in table.keys():
                tempTable = {key:table[key]}

                createBoxPlot(tempTable)

if __name__ == "__main__":
    subSamplePlotter("test.tsv")
