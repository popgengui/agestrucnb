from __future__ import division
from __future__ import print_function
#created by Brian Trethewey
#
#neGrapher is primary interface for graphing data
#neStats is primary interface for creating statistics output file for a dataset


from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object
from past.utils import old_div
import configparser

from numpy import array, math
from scipy import stats, random
import matplotlib.pyplot as plt
from numpy import mean, median, isnan
import csv
import sys
import os
'''
Location moved to agestrucne.asnviz:
'''
#from Viz.FileIO import scrapeNE, configRead, readFileOrder, makeOutlierDict, writeOutliers
from agestrucne.asnviz.FileIO import scrapeNE, configRead, readFileOrder, makeOutlierDict, writeOutliers


#function to perform the linear regression and store the results in a dictionary
def line_regress(line_points):
    xArray, yArray = _pointsToVectors(line_points)
    slope, intercept, r_value, p_value, std_err = stats.linregress(xArray, yArray)
    result  = {}
    result["slope"] = slope
    result["intercept"] = intercept
    result["r_val"] = r_value
    result["p_val"] = p_value
    result["std_err"] = std_err
    return result

#helper function to create lines from slope, intercept data
def _getGraphLine(slope, intercept, xVctr):
    pointVctr = []
    for x in xVctr:
        pointVctr.append((x,slope*x + intercept))
    return pointVctr


def _pointsToVectors(points):
    #zip with a * preforms the inverse
    xVctr , yVctr = list(zip(*points))
    return xVctr, yVctr


#function that implements the matplotlib and creates the graph object, also shows or saves the object to file
#dest parameter:  if show graph is printed to screen using .show() otherwise expects a filename with extension and saves the file in that format as per .savefig()
def createGraph(lineArray, title = None, xlab = None, yLab= None, colorVctr = None, styleVctr = None, dest = "show", xLim = None, yLim = None):
    if dest != "none":
        lineCount = len(lineArray)
        if colorVctr and len(colorVctr) < lineCount:
            difference = lineCount-len(colorVctr)
            for  x in range(difference):
                colorVctr.append(colorVctr[len(colorVctr)-1])
        if styleVctr and len(styleVctr) < lineCount:
            difference = lineCount-len(styleVctr)
            for  x in range(difference):
                styleVctr.append(styleVctr[len(styleVctr)-1])

        colorFlag = ""
        styleFlag = ""
        for yVctrIdx in range(lineCount):
            if colorVctr:
                colorFlag = colorVctr[yVctrIdx]
            if styleVctr:
                styleFlag = styleVctr[yVctrIdx]
            argFlag = colorFlag+styleFlag
            xvctr, yvctr = _pointsToVectors(lineArray[yVctrIdx])

            xVctr = array(xvctr)
            yVctr = array(yvctr)
            plt.plot(xVctr,yVctr,argFlag)
        if title:
            plt.title(title)
        if xlab:
            plt.xlabel(xlab)
        if yLab:
            plt.ylabel(yLab)
        if xLim:
            plt.xlim(xLim)
        if yLim:
            plt.ylim(yLim)

        if dest == "show":
            plt.show()
        else:
            plt.savefig(dest, bbox_inches='tight')
            plt.close()

# method to create a scatterPlot of the outputNEs
def createScatterPlot(table,errorTable, title=None, xlab=None, yLab=None, dest="show"):
    if dest =="none":
        return
    plt.figure("scatter")
    flatData = [val for sublist in table for val in table[sublist]]
    errorData = [val for sublist in errorTable for val in errorTable[sublist]]

    minErrorVctr = []
    maxErrorVctr = []
    for errorIdx in range(len(errorData)):
        minError = errorData[errorIdx][1][0]
        maxError = errorData[errorIdx][1][1]
        dataVal = flatData[errorIdx][1]
        minDelta = abs(dataVal - minError)
        maxDelta = abs(maxError - dataVal)

        minErrorVctr.append(minDelta)
        maxErrorVctr.append(maxDelta)
    errorArray = [minErrorVctr,maxErrorVctr]
    unzippedX, unzippedY = list(zip(*flatData))
    #plt.errorbar(unzippedX, unzippedY,errorArray, fmt = "o")
    plt.scatter(unzippedX,unzippedY)
    plt.margins(0.15,0.15)
    if title:
        plt.title(title)
    if xlab:
        plt.xlabel(xlab)
    if yLab:
        plt.ylabel(yLab)

    if dest == "show":
        plt.show("scatter")
    else:
        plt.savefig(dest, bbox_inches='tight')
        plt.close()

def createHzLinePlot(table, title=None, xlab="Heterozygosity", yLab=None, dest="show"):
    if dest == "none":
        return
    plt.figure("Hz")
    for key in list(table.keys()):
        pass

    # plt.errorbar(unzippedX, unzippedY,errorArray, fmt = "o")
    #plt.plot(unzippedX, unzippedY)
    plt.margins(0.15, 0.15)
    if title:
        plt.title(title)
    if xlab:
        plt.xlabel(xlab)
    if yLab:
        plt.ylabel(yLab)

    if dest == "show":
        plt.show("hz")
    else:
        plt.savefig(dest, bbox_inches='tight')
        plt.close()


 #method to create a boxplot of the outputNEs
def createBoxPlot(table,title = None, xlab = None, yLab= None, dest = "show", outlierFile = "outliers.txt"):
    if dest == "none":
        return
    plt.figure("box")
    flatData = [val for sublist in table for val in table[sublist]]

    plotData = []

    unzippedX, unzippedy = list(zip(*flatData))
    setX = set(unzippedX)
    listX = list(setX)
    listX.sort()
    for x in listX:
        ySet = [datum[1] for datum in flatData if datum[0] == x]
        errorSet = [datum[1] for datum in flatData if datum[0] == x]
        plotData.append(ySet)
        # plotData = unzippedy
    plotstats = plt.boxplot(plotData,labels=listX)
    if len(plotstats["fliers"])>0:
        outliers = {"":makeOutlierDict(plotstats["fliers"])}
    plt.clf()
    plt.figure("box")
    plt.boxplot(plotData, labels=listX, sym = "")
    if title:
        plt.title(title)
    if xlab:
        plt.xlabel(xlab)
    if yLab:
        plt.ylabel(yLab)

    if dest == "show":
        plt.show("box")
    else:
        plt.savefig(dest, bbox_inches='tight')
        plt.close()
    writeOutliers(outliers,outlierFile)
    return


    # get s(b1)  == (MSE)/sum(xi-mean(x))^2)
    # this estimates the variation of the system
def calculate_s_score(linePoints):
    regression = line_regress(linePoints)
    xVctr, yVctr = _pointsToVectors(linePoints)
    MSE = _MSE(regression["slope"], regression["intercept"], linePoints)
    xMean = mean(xVctr)
    xMeanDiffArray = []
    for x in xVctr:
        xDiff = x - xMean
        xDiffSq = xDiff * xDiff
        xMeanDiffArray.append(xDiffSq)
    xDiffSum = sum(xMeanDiffArray)
    sSqVal = old_div(MSE, xDiffSum)
    sVal = math.sqrt(sSqVal)
    return  sVal
    

#method to get teh confidence interval around the Slope of the regression
#uses the formula t((1-alpha/2):DoF)(s(b1))
#alpha: desired probability
#linePoints: list of touples defining the x and y coordinates of a point
#returns 3 variables, the slope of the regression, the intercept of the regression, and a touple containing the upper and lower bounds of the confidence interval of the slope
def slope_confidence(alpha, line_points):
    if len(line_points)<=2:
        return "Error: not enough points for calculation"
    #if len(linePoints)==2:
    #    regression = lineRegress(linePoints)
    #    return regression["slope"], regression["intercept"],(regression["slope"],regression["slope"])
    #get linear regression for points
    regression = line_regress(line_points)
    #get Tscore
    t_score = stats.t.ppf((1-old_div(alpha,2)), len(line_points) - 2)


    #get s(b1)  == (MSE)/sum(xi-mean(x))^2)

    s_val = calculate_s_score(line_points)
    deltaConfidence = t_score*s_val
    confidence_interval = (regression["slope"]-deltaConfidence,regression["slope"]+deltaConfidence)
    return regression["slope"], regression["intercept"], confidence_interval

    #confidence test for null hypothesis **only works for 0 right now**
#alpha: desired probability
#linePoints: list of touples defining the x and y coordinates of a point
#hypothesis_slope: slope  defined by null hypothesis, assumed to be 0  and doesnt work right now, here for extensibility
def alpha_test(alpha, linePoints, hypothesis_slope = 0):
    alpha_result= 0
    regression = line_regress(linePoints)
    #get t_ test score
    t_score = stats.t.ppf((1-old_div(alpha,2)), len(linePoints)-2)
    s_val = calculate_s_score(linePoints)
    t_star = abs(old_div(regression['slope'],s_val))
    if t_star > t_score:
        alpha_result  = 1
    return alpha_result

#calculate beta error given a known expected slope assumes null mean value is 0
#alpha: desired probability
#linePoints: list of touples defining the x and y coordinates of a point
# #expected: the expected slope of the system
#null_mean: the mean defined by the null hypothesis  currently assumed to be 0
def beta_test(alpha, linePoints, expected, null_mean = 0):
    beta_value =0
    #get regression data
    regression = line_regress(linePoints)
    #get T score
    t_score = stats.t.ppf((1-old_div(alpha,2)), len(linePoints)-2)
    #get sVAL 
    s_val = calculate_s_score(linePoints)
    # just for completion
    #print(expected)
    hypothesis_mean_offset = abs(null_mean - expected)
    delta = old_div(hypothesis_mean_offset,s_val)
    t_offset =t_score- delta
    beta_value = stats.t.cdf(t_offset,len(linePoints)-2)
    return beta_value




    
#get MSE of a regression
#slope: slope of calculated regression
#intercept: intercept of calculated regression
#yPoints: An array of the points used to create the regression
#xVctr: an array of the values
#returns MSE
def _MSE(slope, intercept, line_points):
    error_array = []

    #get sigma error squared
    for point in line_points:
        x_val = point[0]
        y_val = point[1]
        expected_y = slope * x_val + intercept
        difference  = y_val - expected_y
        squareDifference  = difference*difference
        error_array.append(squareDifference)
    error_sum = sum(error_array)

    #devide by DoF (n-2)
    MSE = old_div(error_sum, (len(line_points) - 2))
    return MSE





#helper function to get line slopes, extracted in case changes or medians are wanted instead
def _getExpectedLineSlope(vctr):
    result = mean(vctr)
    return result

def _getExpectedLineStats(slopes, intercepts, xVctr,expectedSlope = None):
    xMean = mean(xVctr)
    if expectedSlope =="auto":
        expectedSlope = _getExpectedLineSlope(slopes)

    midpoints = []
    for lineIdx in range(len(slopes)):
        slope = slopes[lineIdx]
        intercept = intercepts[lineIdx]
        midpoints.append(slope*xMean+intercept)
    midpoint = mean(midpoints)
    expectedIntercept = float(midpoint)-float(expectedSlope*xMean)
    return expectedSlope, expectedIntercept


# xVctr:        List/Array of values representing the X axis(will be shared between all YPoints arrays)
# yPoints:      List/Array of Arrays composed of the Y values at each value in xVctr for each datastream
# expectedSlope:Optional Value for the slope of any Control or Expected line to compare to,
#       if None(default) no line produced
#       if value creates a line with that slope in red
#       if "auto" creates a line with slope =  average slope of all lines
def _NeRegressionGraphCalc(dataVctrs, expectedSlope = None, popTable = None):
    #get linear regression stats for all datasets
    LineStats = []
    for line in list(dataVctrs.values()):
        data = line_regress(line)
        LineStats.append(data)
    #flatten the array
    all_points = [val for sublist in list(dataVctrs.values())  for val in sublist]
    #unzip to obtain x and y value vectors for all points
    xVals, yVals = list(zip(*all_points))

    minX = min(xVals)
    maxX = max(xVals)+1
    xVctr = list(set(all_points))
    if maxX - minX>1:

        xVctr = list(range(int(math.floor(minX)),int(math.ceil(maxX))))

    lineVctrs =[]
    colorVctr = []
    styleVctr = []

    #creates expected slope line for comparisons
    if expectedSlope:
        expectedPoints = []
        if expectedSlope == "pop":
            if popTable:
                averagePopPoints = []
                all_points = [val for sublist in popTable for val in popTable[sublist]]
                xVals, yVals = list(zip(*all_points))
                xSet = set(xVals)
                for x in xSet:
                    pointYSet = [point[1] for point in all_points if point[0] == x]
                    averageY = mean(pointYSet)
                    averagePopPoints.append((x,averageY))
            expectedPoints = averagePopPoints
        else:
            #get all slope and intercept values to get means
            slopes = []
            intercepts = []
            for statDict in LineStats:
                slopes.append(statDict["slope"])
                intercepts.append(statDict["intercept"])

            #get expected line Stats
            expectedSlope,expectedIntercept = _getExpectedLineStats(slopes, intercepts, xVctr,expectedSlope)
            expectedPoints = _getGraphLine(expectedSlope, expectedIntercept, xVctr)


        #make expected line for plotting
        if len(expectedPoints)>0:
            lineVctrs.append(expectedPoints)
            colorVctr.append("r")
            styleVctr.append("-")

    for statDict in LineStats:
        slope = statDict["slope"]
        intercept = statDict["intercept"]
        if not isnan(slope):
            linePoints  = _getGraphLine(slope, intercept, xVctr)
            lineVctrs.append(linePoints)
            colorVctr.append("b")
            styleVctr.append("--")
    return lineVctrs, colorVctr,styleVctr

#combines linear regression and create graph into one function
def neGraphMaker(pointsVctrs, expectedSlope = None,title = None, xlab = None, yLab= None, dest = "show", xLim = None, yLim = None, countTable = None):
    lines, colors, styles = _NeRegressionGraphCalc(pointsVctrs, expectedSlope,countTable)
    createGraph(lines, colorVctr=colors, styleVctr=styles, title=title, xlab=xlab,yLab=yLab, dest=dest, xLim = xLim, yLim = yLim)

# #reads in data fron neEst file outputs
# def neFileRead(filename, firstVal = 0):
#     fileBuffer = open(filename, "rb")
#     replicateData = csv.DictReader(fileBuffer, delimiter="\t", quotechar="\"")
#     dataDict = {}
#     popDict={}
#     popNum = 0
#     for item in replicateData:
#         sourceName = item['original_file']
#         sourceName = os.path.basename(sourceName)
#
#         pop =  item['pop']
#         popNum = int(pop)
#         individualCount = int(item["census"])
#         neEst = float(item['est_ne'])
#         #if neEst == "NaN":
#         #    neEst = sys.maxint
#         if  not sourceName in dataDict:
#             dataDict[sourceName] = {}
#             popDict[sourceName] = {}
#         dataDict[sourceName][popNum] = neEst
#         popDict[sourceName][popNum]=individualCount
#     replicateKeys = dataDict.keys()
#     resultTable = {}
#     individualCountTable = {}
#     for replicate in replicateKeys:
#         replicateVctr = []
#         individualCountVctr = []
#         replicateDict = dataDict[replicate]
#         individualCountDict = popDict[replicate]
#         popKeys = replicateDict.keys()
#         popKeys.sort()
#         for popKey in popKeys:
#             if popKey >=firstVal:
#                 #print popKey
#                 replicateVctr.append((popKey-firstVal,replicateDict[popKey]))
#                 individualCountVctr.append((popKey-firstVal,individualCountDict[popKey]))
#         resultTable[replicate] = replicateVctr
#         individualCountTable[replicate] = individualCountVctr
#     return resultTable,individualCountTable




#master function to create a graph from neEstimation data.
#neFile: filepath for the neEstimation output file desired.
#configFile filepath to configureation file containting parameteres for the graph (see example.cfg and example1.cfg,
#   this parameter and all feilds in the file are optional with what i considered the most relevant/base defaults)
def neGrapher(neFile, configFile=None):

    if not configFile:
        table , countsTable, errorTable= scrapeNE(neFile)
        neGraphMaker(table)
        createBoxPlot(table)
        createScatterPlot(table)
        return True
    configs = configRead(configFile)
    table,countsTable, errorTable = scrapeNE(neFile,configs["startData"])
    if configs["ordering"]:
        orderingTable = readFileOrder(configs["ordering"])
        table = orderFiles(table,orderingTable,configs["orderingGen"])
        errorTable = orderFiles(errorTable,orderingTable,configs["orderingGen"])
    outlierFile = configs["statsFilename"]
    outlierpath, outlierext =os.path.splitext(outlierFile)
    outlierFile = outlierpath+".outliers"+outlierext
    #TODO this is where converting the x values to a enviromental variable should occur.
    #table = _enviromentalFactor(table, envFactors)
    neGraphMaker(table,expectedSlope=configs["expected"],title= configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["dest"],xLim=configs["xLims"],yLim=configs["yLims"], countTable = countsTable)
    outlierFlag = createBoxPlot(table,title =  configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["boxplot"],outlierFile=outlierFile)
    createScatterPlot(table, errorTable, title =  configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["scatter"])
    return outlierFlag

def _enviromentalFactor(table, factorTable):
    pass

#master function for creating a table of confidence intervals form neEstimation data
#neFile: filepath of neEstimation output file
#confidenceAlpha: level of confidence desired should be <0.5, most common are 0.05 and 0,1 for 95% and 90% respectivly
#outFileName: resulting file location for file results, will overwrite existing file.
#significantValue: value of comparison w/ regards to slope. should be 0 for every test, but can be changed if needed.
#testFlag: flag that disables file write and prints stats to console instead, used for test functions
def _neStatsHelper(table,neFile,confidenceAlpha, outFileName = "neStatsOut.txt", significantValue = 0, firstVal = 0,expected = 0,testFlag = False):

    tableFormat = "{:<20}{:<20}{:<50}{:<20}{:<80}\n"
    confPercent = (1 - confidenceAlpha)*100
    tableString =tableFormat.format("Slope","Intercept","Confidence Interval("+str(confPercent)+"%)","P value", "Source File")
    slopeVctr = []
    confidenceVctr = []
    alpha_vctr =[]
    s_score_vctr= []

    Uncountable = 0
    for recordKey in list(table.keys()):

        record = table[recordKey]
        slope, intercept, confidence  = slope_confidence(confidenceAlpha, record)


        # perform alpha test
        alpha_result = alpha_test(confidenceAlpha, record)
        if alpha_result == 0:
            alpha_vctr.append(0)
        elif slope > 0:
            alpha_vctr.append(1)
        else:
            alpha_vctr.append(-1)

        #get std dev estimate
        s_val = calculate_s_score(record)
        s_score_vctr.append(s_val)
        t_star = old_div(slope,s_val)
        #calculate p value DF = num points-2
        p_score = stats.t.sf(t_star,len(record)-2)

        #Ted edit 2017_05_12. For python3, we have to cast the confidence tuple 
        #as a string. Looks like py3 provides no tuple handling in the format 
        #method for the string.
        tableString+=tableFormat.format(slope,  intercept ,  str( confidence ) ,p_score,  recordKey[0]+"\n")
        if isnan(slope):
            Uncountable +=1
        else:
            slopeVctr.append(slope)
            confidenceVctr.append(confidence)
    maxSlope = max(slopeVctr)
    minSlope = min(slopeVctr)
    meanSlope = mean(slopeVctr)
    medSlope = median(slopeVctr)
    averageSscore = mean(s_score_vctr)
    negativeCount=0
    zeroCount=0
    positiveCount=0

    #change for alpha test
    for value in alpha_vctr:
        if value>0:
            positiveCount+=1
        elif value<0:
            negativeCount+=1
        else:
            zeroCount+=1
    # for cI in confidenceVctr:
    #     if cI[0] > significantValue:
    #            positiveCount += 1
    #     elif cI[1] < significantValue:
    #         negativeCount += 1
    #     else:
    #         zeroCount += 1
    if testFlag:
        print(slopeVctr)
        print(confidenceVctr)

        print(positiveCount)
        print(zeroCount)
        print(negativeCount)
        return
    outFile = open(outFileName,"w")
    outFile.write("File:"+neFile+"\n")
    outFile.write("\n")
    outFile.write("Max Regression Slope:\t\t\t"+str(maxSlope)+"\n")
    outFile.write("Min Regression Slope:\t\t\t"+str(minSlope)+"\n")
    outFile.write("Mean Regression Slope:\t\t\t"+str(meanSlope)+"\n")
    outFile.write("Meadian Regression Slope:\t\t"+str(medSlope)+"\n")
    outFile.write("Mean Variance Estimate:\t\t\t"+str(averageSscore)+"\n")
    outFile.write("\n")
    outFile.write("Comparison to a slope of: "+str(significantValue)+"  at alpha =  "+str(confidenceAlpha)+"\n")
    outFile.write("Positive Slopes:\t"+str(positiveCount)+"\t\tNeutral Slopes:\t"+str(zeroCount)+"\t\tNegative Slopes:\t"+str(negativeCount)+"\n")
    outFile.write("Non-Number Slopes:\t"+str(Uncountable))
    outFile.write("\n\n")
    outFile.write(tableString)
    outFile.close()
    return outFileName



def neStats(neFile, configFile = None, testFlag = False):
    if not  configFile:
        table, countsTable, errorTable = scrapeNE(neFile,)
        return _neStatsHelper(table,neFile,0.05)

    configVals = configRead(configFile)
    neTable,countsTable, errorTable = scrapeNE(neFile,configVals["startData"],lastVal=configVals["endData"])
    if configVals["ordering"]:

        orderingTable = readFileOrder(configVals["ordering"])
        neTable = orderFiles(neTable,orderingTable,configVals["orderingGen"])

    return _neStatsHelper(neTable,neFile,configVals["alpha"], outFileName=configVals["statsFilename"],significantValue=configVals["sigSlope"],firstVal=configVals["startData"], testFlag= testFlag)

#gets thh minumum of the maximum of the number of subpops for the table
def _getSubpopLimit(table,itemList=None):
    identTuples = list(table.keys())
    maxDict = {}
    for ident in identTuples:
        if not itemList or ident in itemList:
            if ident[0] not in maxDict:
                maxDict[ident[0]] = 0
            maxDict[ident[0]] = max(maxDict[ident[0]],ident[1])
    return maxDict


def _geLociVal(table):

    identTuples = list(table.keys())
    lociCounter ={}
    for ident in identTuples:
        if ident[2] not in lociCounter:
            #initilize counter
            lociCounter[ident[2]] = 0
        lociCounter[ident[2]]+=1
    sortedLociList = list(lociCounter.keys())
    sortedLociList.sort()
    lociSum = sum(lociCounter.values())
    chanceList = [0]*len(sortedLociList)
    chanceSum=0
    for i in range(len(sortedLociList)):
        lociChance  = old_div(lociCounter[sortedLociList[i]],lociSum)
        chanceSum+=lociChance
        chanceList[i]=chanceSum
    randVal = random.rand()
    i=0
    while chanceList[i]<randVal and i< len(chanceList):
        i+=1
    selected = sortedLociList[i]
    return selected



def orderFiles(table, orderDict,genNum = 1):
    orderedTable = {}
    #get count of suppops
    subpopLimits = _getSubpopLimit(table)
    #get leastvalue
    subpopLimit = min(subpopLimits.values())
    # get loci value for key

    lociVal = _geLociVal(table)

    #create randomized lists  for each file to

    for ordering in list(orderDict.keys()):
        for ident in list(subpopLimits.keys()):
            SelectRandom.createOrdering((ident,ordering), subpopLimits, subpopLimit)

        for subpopNumber in range(int(subpopLimit)-1):
            orderedTable[(ordering,subpopNumber)]=[]
            for entry in orderDict[ordering]:
                entryNum = SelectRandom.getOrderingVal((entry[1],ordering),subpopNumber)
                entryList = table[(entry[1],entryNum,lociVal)]
                foundGen = None
                for point in entryList:
                    if point[0] == genNum:
                        foundGen = point[1]
                        break
                if not foundGen:
                    print("desired gen not found in")
                    print(entry[1])
                    raise Exception("desired gen number "+str(genNum)+" not found in "+str(entry))
                orderedTable[(ordering,subpopNumber)].append((entry[0], foundGen))
    return orderedTable

class SelectRandom(object):
    orderingDict = {}

    @staticmethod
    def createOrdering(identifier,subpopLimits,selectedCount):
        #print identifier
        #print subpopLimits
        #print selectedCount
        if not identifier in SelectRandom.orderingDict:
            SelectRandom.orderingDict[identifier] = SelectRandom._createorderArray(subpopLimits[identifier[0]],int(selectedCount))
            print("New Entry")
        else:
            print("existing entry found")

    @staticmethod
    def clearOrdering():
        SelectRandom.orderingDict = {}
    @staticmethod
    def _createorderArray(totalCount, selectedCount):
        ordering  = random.choice(list(range(1,int(totalCount+1))) , selectedCount)
        return ordering

    @staticmethod
    def getOrderingVal(identifier,index):
        return SelectRandom.orderingDict[identifier][index]


def neRun(neFile,configFile):

    if not configFile:
        table , countsTable, errorTable= scrapeNE(neFile)
        neGraphMaker(table)
        createBoxPlot(table)
        createScatterPlot(table)
        _neStatsHelper(table,0.5)
        return True
    configs = configRead(configFile)

    ##### temp
    print( "-------------" )
    print( "got back dictfrom configread: " + str( configs ) )
    ##### end temp

    table,countsTable, errorTable = scrapeNE(neFile,configs["startData"],lastVal=configs["endData"])
    if configs["ordering"]:
        SelectRandom()
        orderingTable = readFileOrder(configs["ordering"])
        table = orderFiles(table,orderingTable,configs["orderingGen"])
        errorTable = orderFiles(errorTable,orderingTable,configs["orderingGen"])
    outlierFile = configs["statsFilename"]
    outlierpath, outlierext =os.path.splitext(outlierFile)
    outlierFile = outlierpath+".outliers"+outlierext

    neGraphMaker(table,expectedSlope=configs["expected"],title= configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["dest"],xLim=configs["xLims"],yLim=configs["yLims"], countTable = countsTable)
    createBoxPlot(table,title =  configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["boxplot"],outlierFile=outlierFile)
    createScatterPlot(table, errorTable, title =  configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["scatter"])
    _neStatsHelper(table,neFile,configs["alpha"], outFileName=configs["statsFilename"],significantValue=configs["sigSlope"],firstVal=configs["startData"],expected=configs["expected"])
    return createBoxPlot(table, title=configs['title'], xlab=configs["xLab"], yLab=configs["yLab"], dest=configs["boxplot"],
                  outlierFile=outlierFile)

if __name__ == "__main__":
    #Tests

    #Test Linear Regression
    print("lineRegress Tests")
    #Perfect Positive Regression
    xVct = list(range(10))
    yVct  = list(range(10))
    table = list(zip(xVct,yVct))
    result = line_regress(table)
    assert result["slope"] == 1.0
    assert result["intercept"] == 0.0
    assert result["r_val"] ==1.0
    yVct = list(range(0,20,2))
    table = list(zip(xVct,yVct))
    result = line_regress(table)
    assert result["slope"] == 2.0
    assert result["intercept"] == 0.0
    assert result["r_val"] == 1.0
    yVct = list(range(10,20,1))
    table = list(zip(xVct,yVct))
    result = line_regress(table)
    assert result["slope"] == 1.0
    assert result["intercept"] == 10.0
    assert result["r_val"] ==1.0
    print("Perfect Positive regression passed")

    # Perfect Negative Regression
    xVct = list(range(10))
    yVct  = list(range(10,0,-1))
    table = list(zip(xVct,yVct))
    result = line_regress(table)
    assert result["slope"] == -1.0
    assert result["intercept"] == 10.0
    assert result["r_val"] == -1.0
    yVct = list(range(20,0,-2))
    table = list(zip(xVct,yVct))
    result = line_regress(table)
    assert result["slope"] == -2.0
    assert result["intercept"] == 20.0
    assert result["r_val"] ==-1.0
    yVct = list(range(0,-10,-1))
    table = list(zip(xVct,yVct))
    result = line_regress(table)
    assert result["slope"] == -1.0
    assert result["intercept"] == 0.0
    assert result["r_val"] ==-1.0
    print("Perfect Negative regression passed")





    print("lineRegress Tests Passed")

    print("Confidence Tests ")
    xVct = list(range(5))
    yVct  = list(range(5))
    table = list(zip(xVct,yVct))
    print(slope_confidence(0.05, table))
    xVct = list(range(5))
    yVct  = list(range(5))
    yVct[0]-=1
    table = list(zip(xVct,yVct))
    print(slope_confidence(0.01, table))
    print(slope_confidence(0.05, table))
    print(slope_confidence(0.1, table))
    xVct = list(range(10))
    yVct  = list(range(10))
    yVct[0]-=1
    table = list(zip(xVct,yVct))
    print(slope_confidence(0.01, table))
    print(slope_confidence(0.05, table))
    print(slope_confidence(0.1, table))
    print("Confidence Tests passed")

    print("getLineGraph Tests")
    xVct = list(range(10))

    assert _getGraphLine(0.0, 0.0, xVct) == [(0,0.0), (1,0.0),(2, 0.0), (3,0.0), (4,0.0), (5,0.0), (6,0.0), (7,0.0), (8,0.0), (9,0.0)]
    print("slope 0 test passed")
    assert _getGraphLine(0.0, 6.0, xVct) == [(0,6.0), (1,6.0),(2, 6.0), (3,6.0), (4,6.0), (5,6.0), (6,6.0), (7,6.0), (8,6.0), (9,6.0)]
    print("slope 0 intercept !=0 test passed")
    assert _getGraphLine(1.0, 0.0, xVct) == [(0,0.0), (1,1.0), (2,2.0), (3,3.0), (4,4.0), (5,5.0), (6,6.0), (7,7.0), (8,8.0), (9,9.0)]
    print("x=y case pass")
    assert _getGraphLine(1.0, 1.0, xVct) == [(0,1.0),(1, 2.0), (2,3.0), (3,4.0), (4,5.0), (5,6.0), (6,7.0), (7,8.0), (8,9.0), (9,10.0)]
    print("intercept != 0 test passed")
    assert _getGraphLine(4.0, 1.0, xVct) == [(0,1.0), (1,5.0), (2,9.0), (3,13.0), (4,17.0), (5,21.0), (6,25.0), (7,29.0), (8,33.0), (9,37.0)]
    print("slope 4 intercept 1 test passed")
    assert _getGraphLine(-1.0, 0.0, xVct) == [(0,0.0), (1,-1.0), (2,-2.0), (3,-3.0), (4,-4.0), (5,-5.0), (6,-6.0), (7,-7.0), (8,-8.0), (9,-9.0)]
    print("negative slope test passed")
    assert _getGraphLine(-2.0, 3.0, xVct) == [(0,3.0), (1,1.0), (2,-1.0 ), (3,-3.0), (4,-5.0), (5,-7.0), (6,-9.0), (7,-11.0), (8,-13.0), (9,-15.0)]
    print("negative slope intercept !=0 test passed")
    assert _getGraphLine(2.0, -3.0, xVct) == [(0,-3.0), (1,-1.0), (2,1.0 ), (3,3.0), (4,5.0), (5,7.0), (6,9.0), (7,11.0), (8,13.0), (9,15.0)]
    print("negative intercept !=0 test passed")


    xVct = list(range(3,13,1))
    assert _getGraphLine(1.0, 0.0, xVct) == [(3,3.0), (4,4.0), (5,5.0), (6,6.0), (7,7.0), (8,8.0), (9,9.0), (10,10.0), (11,11.0), (12,12.0)]
    print("non 0 positive x start passed")
    xVct = list(range(3,13,1))
    yVct = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    assert _getGraphLine(1.0, -3.0, xVct) == list(zip(xVct,yVct))
    print("non 0 x start non 0 intercept passed")

    xVct = list(range(10,0,-1))
    yVct = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    assert _getGraphLine(1.0, 0.0, xVct) == list(zip(xVct,yVct))
    print("negative step x axis passed")

    xVct = list(range(0, -10, -1))
    yVct = [0.0, -1.0, -2.0, -3.0, -4.0, -5.0, -6.0, -7.0, -8.0, -9.0]
    assert _getGraphLine(1.0, 0.0, xVct) == list(zip(xVct, yVct))
    print("negative step x axis passed")

    xVct = list(range(-7,3,1))
    yVct = [-7.0, -6.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0]
    assert _getGraphLine(1.0, 0.0, xVct) == list(zip(xVct, yVct))
    print("negative start x axis passed")

    xVct = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    yVct = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    assert _getGraphLine(1.0, 0.0, xVct) == list(zip(xVct, yVct))
    print("non integer x axis passed")

    print("getGraphLine Passed")


    xVct = list(range(0,20,2))
    table = []
    table.append(_getGraphLine(-0.1, 0, xVct))
    table.append(_getGraphLine(-0.005, 0, xVct))
    table.append(_getGraphLine(-0.15, 10, xVct))
    table.append(_getGraphLine(0.25, 10, xVct))


    print("createGraph Test")
    colorStyles = ["", ""]
    lineStyles = ["", ""]
    title = "testTitle"
    x = "TestX"
    y = "TestY"
    createGraph(table,colorVctr=colorStyles, styleVctr=lineStyles, title=title, xlab=x, yLab=y)


    print("NeRegressionGraphMaker")

    testYs = [[0,0,0,0,0],[1,2,3,4,5],[-1,-2,-3,-4,-5],[1,3,1,3,1]]
    testX = [1,2,3,4,5]
    testTable =[]
    for yVct in testYs:
        testTable.append(list(zip(testX,yVct)))
    id = 0
    testDict = {}
    for data in testTable:
        testDict[id] = data
        id+=1

    lines, color, styles = _NeRegressionGraphCalc(testDict)

    createGraph(lines,colorVctr=color,styleVctr=styles)

    testYs = [[0,0,0,0,0],[1,2,3,4,5],[-1,-2,-3,-4,-5],[1,3,0,2,-1]]
    for yVct in testYs:
        testTable.append(list(zip(testX,yVct)))
    testDict = {}
    for data in testTable:
        testDict[id] = data
        id += 1
    lines, color, styles = _NeRegressionGraphCalc(testDict, -0.333)

    createGraph(lines,colorVctr=color,styleVctr=styles)

    testArray = [2,5,3,6,1,4]
    testArray.sort()
    print(testArray)

    table, countsTable, errorTable = scrapeNE("testData.txt")

    print(table)
    print(countsTable)
    print(errorTable)



    neGraphMaker(table)

    configwrite= configparser.ConfigParser()
    configwrite.add_section("labels")
    configwrite.set("labels","title", "titletext")
    configwrite.set("labels", "xLab", "xLabel")
    configwrite.set("labels", "yLab", "yLabel")
    configwrite.add_section("destination")
    configwrite.set("destination","desttype", "show")
    configwrite.set("destination","regressionfile", "test.png")
    configwrite.set("destination","boxplotfile", "box.pdf")
    configwrite.set("destination","scatterfile", "show")
    configwrite.add_section("comparison")
    configwrite.set("comparison", "type", "pop")
    configwrite.set("comparison", "expectedSlope", -0.1)
    configwrite.add_section("data")
    configwrite.set("data", "startCollect",11)
    configwrite.add_section("confidence")
    configwrite.set("confidence","alpha",0.05)
    configwrite.write(open("example1.cfg","w"))

    print(configRead("example1.cfg"))
    print("test master methods")
    neGrapher("testData.txt","example1.cfg")
    table, countsTable, errorTable = scrapeNE("testData.txt")
    _neStatsHelper(table,"testData",0.1,testFlag=True)
    _neStatsHelper(table,"testData",0.05)

    orderDict = {"foo":[(0,"biz"),(1,"baz"),(2,"bar")],"Flop":[(0,"biz"),(5,"boz")]}

    orderTable ={("biz",1):[(1,5),(3,33)],("biz",2):[(1,10),(6,67)],("baz",1):[(1,10),(4,33)],("baz",2):[(1,20),(4,88)],("baz",3):[(1,30),(4,99)],("bar",1):[(1,15),(5,33)],("boz",1):[(1,25),(2,33)]}

    print(orderFiles(orderTable,orderDict))
    ordered = orderFiles(orderTable,orderDict)
    ordered2 = orderFiles(orderTable,orderDict)
    print(ordered)
    print(ordered2)
    print(ordered == ordered2)
    neGraphMaker(ordered)

    try:
        orderFiles(orderTable, orderDict, 3)
    except Exception as e:
        print(e.message)
        print("exception check passed")
