from __future__ import print_function
import csv
import os

import matplotlib.pyplot as plt

from agestrucne.asnviz.FileIO import configRead, makeOutlierDict, writeOutliers


def createBoxPlot(table,title = None, subTitle = None,  xlab = None, yLab= None, dest = "show", sortCrit = "pop",):

    flatData = [val for sublist in table for val in table[sublist]]

    plotData = []

    unzippedX = [x[0] for x in flatData if x[0]]
    setX = set(unzippedX)
    listX = list(setX)
    print(listX)
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
    boxpoints = plt.boxplot(plotData, labels= listX)
    if len(boxpoints["fliers"]) >0:
        outliers =  makeOutlierDict(boxpoints["fliers"])
    plt.clf()
    plt.boxplot(plotData, labels=listX, sym = "")
    print("outiers")
    print(boxpoints["fliers"])
    plt.xticks(rotation=45)
    if title:
        plt.suptitle(title)
    if subTitle:
        plt.title(subTitle, fontsize = 8)
    if xlab:
        plt.xlabel(xlab)
    if yLab:
        plt.ylabel(yLab)
    plt.subplots_adjust(bottom = 0.25)
    plt.margins(0.15,0.15)

    

    if dest == "show":
        plt.show()
        plt.close()
    else:
        plt.savefig(dest, bbox_inches='tight')
        plt.close()
        plt.clf()
    return  outliers

    def createOneDimBoxPlot(table, title=None, xlab=None, yLab=None, dest="show", groupCrit="pop"):

        flatData = [val for sublist in table for val in table[sublist]]

        plotData = []
        goupBy(table,groupCrit)

        unzippedX = [x[0] for x in flatData if x[0]]
        print(unzippedX)
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
    '''
    2017_04_28. Revised by Ted, for python3, csv reader
    requres that the file buffer deliver strings, but 'rb' delivers
    bytes type objects in py3.  We open the file with 'r'
    instead of 'rb'.
    '''

    fileBuffer = open(filename, "r")
    replicateData = csv.DictReader(fileBuffer, delimiter="\t", quotechar="\"")
    dataDict = {}
    popDict={}
    popSample = 0
    for item in replicateData:
        sourceName = item['original_file']
        sourceName = os.path.basename(sourceName)
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
        neEst = float(item['ne_est_adj'])
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
    replicateKeys = list(dataDict.keys())
    resultTable = {}
    individualCountTable = {}
    for replicate in replicateKeys:
        replicateVctr = []
        individualCountVctr = []
        replicateDict = dataDict[replicate]
        individualCountDict = popDict[replicate]
        popKeys = list(replicateDict.keys())
        popKeys.sort()
        for popKey in popKeys:
            lociKeys = list(replicateDict[popKey].keys())
            lociKeys.sort()
            for lociKey in lociKeys:
                #print popKey
                print(popKey)
                print(lociKey)
                replicateVctr.append((popKey,lociKey,replicateDict[popKey][lociKey]))
                individualCountVctr.append((popKey,lociKey,individualCountDict[popKey][lociKey]))
        resultTable[replicate] = replicateVctr
        individualCountTable[replicate] = individualCountVctr
        print(resultTable)
    return resultTable,individualCountTable


def sortBy(table, sortIdentifier ="pop"):
    sortedDict = {}
    for key in list(table.keys()):
        keyData = table[key]
        newKeyVctr = []
        if sortIdentifier == "pop":
            data = sorted(keyData, key=lambda tup: (tup[0],tup[1]) )
        else:
            data = sorted(keyData, key=lambda tup: (tup[1], tup[0]))
            print(keyData)
        for touple in data:
            newTouple = ((touple[0],touple[1]),touple[2])
            newKeyVctr.append(newTouple)

        sortedDict[key] = newKeyVctr
    return sortedDict

def goupBy(table, groupIdentifier):
    newTable = {}
    for key in list(table.keys()):
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
        newKeyVctr = [(binVal,binDict[binVal])for binVal in list(binDict.keys())]
        newTable[key] = newKeyVctr
    return newTable



def subSamplePlotter(neFile, configFile = None):
    outliers ={}
    if configFile == None:
        table, popTable = neFileRead(neFile)
        sortedTable = sortBy(table, "pop")
        if len(list(table.keys())) ==1:
            outliers = {"":createBoxPlot(sortedTable,sortCrit = "pop")}

        else:
            for key in list(table.keys()):
                tempTable = {key:sortedTable[key]}
                print(tempTable)
                outliers[key] = createBoxPlot(tempTable,subTitle=key)
        writeOutliers(outliers, "outliers.txt")
    else:
        configs = configRead(configFile)
        table, popTable = neFileRead(neFile)
        sortedTable = sortBy(table, configs["sortBy"])
        if len(list(table.keys())) == 1:
            ''' 
            2016_12_13, Ted replaced the configs[ "dest" ] reference to the new config option loaded with key "whisker".
            '''
            outliers = {"": createBoxPlot(sortedTable, title=configs["title"],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["whisker"], sortCrit =configs["sortBy"])}
        else:
            destCounter = 1
            for key in list(sortedTable.keys()):
                tempTable = {key: sortedTable[key]}
                '''
                2016_12_13, revised by Ted.  See similar replacement above, note configs[ "whisper" ] replaces configs[ "dest" ]
                '''
                dest = configs["whisker"]

                if dest!="show" and dest!=None:
                    #dest= dest+"_"+str(destCounter)
                    dest=add_number_to_file_name( dest, destCounter )
                    destCounter+=1
                outliers[key] = createBoxPlot(tempTable,title=configs["title"], subTitle=key,xlab=configs["xLab"],yLab=configs["yLab"],dest=dest, sortCrit =configs["sortBy"])
        writeOutliers(outliers,configs["statsFilename"])

def add_number_to_file_name( s_name, i_number ):
    '''
    Added 2017_05_12 by Ted.
    If the name (file, usually with path) has no 
    legit graphics extension, we can simply
    append the number to the name.  Otherwise,
    we insert the number between the file name
    and extension.
    '''

    NUM_CHARS_EXT=4
    LEGIT_TYPES=[ ".png", ".pdf" ]
    
    #A default return value, changed
    #only if the name meets criteria.
    s_name_with_number=s_name + "_" + str( i_number )

    s_file_name_only=os.path.basename( s_name )
    i_len_file_name=len( s_file_name_only )

    #Can be a valid graphics file name if it has
    #one of the extensions plus at least one character.
    if i_len_file_name >= ( NUM_CHARS_EXT + 1 ):
        s_ext_chars=s_file_name_only[ i_len_file_name-NUM_CHARS_EXT: i_len_file_name ]
        if s_ext_chars in LEGIT_TYPES:
            #For the unaltered part of our path and name
            #we need to index the righmost match of our ext chars:
            idx_extension=s_name.rfind( s_ext_chars  )
            s_pre_extension_part=s_name[ 0:idx_extension ]
            s_insert="_" + str( i_number )
            s_name_with_number=s_pre_extension_part \
                        + s_insert + s_ext_chars
        #end if our extension is legit
    #end if the file name is long enough to have an extension

    return s_name_with_number
#end def add_number_to_file_name

if __name__ == "__main__":
    subSamplePlotter("subTest.tsv")
