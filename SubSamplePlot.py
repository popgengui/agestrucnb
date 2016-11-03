import csv

import matplotlib.pyplot as plt



def createBoxPlot(table,title = None, xlab = None, yLab= None, dest = "show"):

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
    popNum = 0
    for item in replicateData:
        sourceName = item['original_file']
        pop =  item['sample_value']
        popNum = float(pop)
        individualCount = int(item["indiv_count"])
        neEst = float(item['est_ne'])
        #if neEst == "NaN":
        #    neEst = sys.maxint
        if  not sourceName in dataDict:
            dataDict[sourceName] = {}
            popDict[sourceName] = {}
        dataDict[sourceName][popNum] = neEst
        popDict[sourceName][popNum]=individualCount
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
            if popKey >=firstVal:
                #print popKey
                replicateVctr.append((popKey,replicateDict[popKey]))
                individualCountVctr.append((popKey,individualCountDict[popKey]))
        resultTable[replicate] = replicateVctr
        individualCountTable[replicate] = individualCountVctr
    return resultTable,individualCountTable
