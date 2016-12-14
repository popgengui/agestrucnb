import csv

import matplotlib.pyplot as plt

from Viz.FileIO import configRead


def createBoxPlot(table,title = None, xlab = None, yLab= None, dest = "show", sortCrit = "pop"):

    flatData = [val for sublist in table for val in table[sublist]]

    plotData = []

    unzippedX = [x[0] for x in flatData if x[0]]
    setX = set(unzippedX)
    listX = list(setX)
    print listX
    if sortCrit == "pop":
        listX = sorted(listX,key=lambda tup: (tup[0],tup[1]))
    else:
        listX = sorted(listX,key=lambda tup: (tup[1],tup[0]))
    for x in listX:
        ySet = [datum[1] for datum in flatData if datum[0] == x]
        plotData.append(ySet)
        # plotData = unzippedy
    plotData.append([])
    listX.append("$(Pop,Loci)$")
    plt.boxplot(plotData, labels= listX,sym='')
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

    def createOneDimBoxPlot(table, title=None, xlab=None, yLab=None, dest="show", groupCrit="pop"):

        flatData = [val for sublist in table for val in table[sublist]]

        plotData = []
        goupBy(table,groupCrit)

        unzippedX = [x[0] for x in flatData if x[0]]
        print unzippedX
        setX = set(unzippedX)
        listX = list(setX)
        listX.sort()
        for x in listX:
            ySet = [datum[1] for datum in flatData if datum[0] == x]
            plotData.append(ySet)
            # plotData = unzippedy
        plotData.append([])
        listX.append("$(Pop,Loci)$")
        plt.boxplot(plotData, labels=listX)
        plt.xticks(rotation=45)
        if title:
            plt.title(title)
        if xlab:
            plt.xlabel(xlab)
        if yLab:
            plt.ylabel(yLab)
        plt.subplots_adjust(bottom=0.25)
        plt.margins(0.15, 0.15)

        if dest == "show":
            plt.show()
        else:
            plt.savefig(dest, bbox_inches='tight')
        plt.close()
        plt.clf()

#reads in data fron neEst file outputs

'''
Ted added 2016_12_05, to allow for
non-float values in the x-axis tuples.
'''
def return_float_or_string( v_val ):
    f_val=None
    v_return_val=None
    try:
        v_return_val=float( v_val )
    except ValueError:
        v_return_val=v_val
    #end try to cast as float
    return v_return_val
#end return_float_if_convertable_else_string


def neFileRead(filename, firstVal = 0):
    fileBuffer = open(filename, "rb")
    replicateData = csv.DictReader(fileBuffer, delimiter="\t", quotechar="\"")
    dataDict = {}
    popDict={}
    popSample = 0
    for item in replicateData:
        sourceName = item['original_file']
        cohort = int(item["pop"])


        sourceName = (sourceName, cohort)
        pop =  item['sample_value']

        '''
        Ted revised 2016_12_05, to allow
        non-float (string) pop sample values.
        '''
        popSample = return_float_or_string(pop)
        #popSample = float(pop)

        #popSample = pop
        loci = item['loci_sample_value']

        '''
        Ted revosed 2016_12_05, to allow
        non-float (string) loci sample values.
        '''
        lociSample = return_float_or_string(loci)
        #lociSample = float(loci)

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


def sortBy(table, sortIdentifier ="pop"):
    sortedDict = {}
    for key in table.keys():
        keyData = table[key]
        newKeyVctr = []
        if sortIdentifier == "pop":
            data = sorted(keyData, key=lambda tup: (tup[0],tup[1]) )
        else:
            data = sorted(keyData, key=lambda tup: (tup[1], tup[0]))
            print keyData
        for touple in data:
            newTouple = ((touple[0],touple[1]),touple[2])
            newKeyVctr.append(newTouple)

        sortedDict[key] = newKeyVctr
    return sortedDict

def goupBy(table, groupIdentifier):
    newTable = {}
    for key in table.keys():
        keyData = table[key]
        newKeyVctr = []
        #set index of item to bin by
        if groupIdentifier == "pop":
            binIdx = 0
        else:
            binIdx = 1
        #bin and extend all arrays by the desired item in touple
        binDict = {}
        for item in keyData:
            if item[binIdx] not in binDict:
                binDict[item[binIdx]] = []
            binDict[item[binIdx]].extend(item[2])
        newKeyVctr = [(binVal,binDict[binVal])for binVal in binDict.keys()]
        newTable[key] = newKeyVctr
    return newTable





def subSamplePlotter(neFile, configFile = None):
    if configFile == None:
        table, popTable = neFileRead(neFile)
        sortedTable = sortBy(table, "pop")
        if len(table.keys()) ==1:
            createBoxPlot(sortedTable,sortCrit = "pop")

        else:
            for key in table.keys():
                tempTable = {key:sortedTable[key]}
                print tempTable
                createBoxPlot(tempTable,)
    else:
        configs = configRead(configFile)
        table, popTable = neFileRead(neFile)
        sortedTable = sortBy(table, configs["sortBy"])
        if len(table.keys()) == 1:
            ''' 
            2016_12_13, Ted replaced the configs[ "dest" ] reference to the new config option loaded with key "whisker".
            '''
            createBoxPlot(sortedTable, title=configs["title"],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["whisker"], sortCrit =configs["sortBy"])
        else:
            for key in sortedTable.keys():
                tempTable = {key: sortedTable[key]}
                '''
                2016_12_13, revised by Ted.  See similar replacement above, note configs[ "whisper" ] replaces configs[ "dest" ]
                '''
                createBoxPlot(tempTable,title=configs["title"],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["whisker"], sortCrit =configs["sortBy"])

if __name__ == "__main__":
    subSamplePlotter("subTest.tsv")
