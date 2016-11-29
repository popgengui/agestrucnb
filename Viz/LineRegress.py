#created by Brian Trethewey
#
#neGrapher is primary interface for graphing data
#neStats is primary interface for creating statistics output file for a dataset


import ConfigParser

from numpy import array, math
from scipy import stats, random
import matplotlib.pyplot as plt
from numpy import mean, median, isnan
import csv
import sys
import os
from  ResultScraper import scrapeNE

#function to perform the linear regression and store the results in a dictionary
def lineRegress(linePoints):
    xArray, yArray = _pointsToVectors(linePoints)
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
    xVctr , yVctr = zip(*points)
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
        minError = errorData[errorIdx][1]
        maxError = errorData[errorIdx][2]
        dataVal = flatData[errorIdx][1]
        print minError, maxError, dataVal
        print "\n\n"
        minDelta = abs(dataVal - minError)
        maxDelta = abs(maxError - dataVal)

        minErrorVctr.append(minDelta)
        maxErrorVctr.append(maxDelta)
    errorArray = [minErrorVctr,maxErrorVctr]
    print errorArray
    unzippedX, unzippedY = zip(*flatData)
    plt.errorbar(unzippedX, unzippedY,errorArray, fmt = "o")
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

 #method to create a boxplot of the outputNEs
def createBoxPlot(table,title = None, xlab = None, yLab= None, dest = "show"):
    if dest == "none":
        return
    plt.figure("box")
    flatData = [val for sublist in table for val in table[sublist]]

    plotData = []

    unzippedX, unzippedy = zip(*flatData)
    setX = set(unzippedX)
    listX = list(setX)
    listX.sort()
    for x in listX:
        ySet = [datum[1] for datum in flatData if datum[0] == x]
        errorSet = [datum[1] for datum in flatData if datum[0] == x]
        plotData.append(ySet)
        # plotData = unzippedy
    plt.boxplot(plotData)
    #set xAxis
    plt.xticks(range(len(listX)), listX)
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

#method to get teh confidence interval around the Slope of the regression
#uses the formula t((1-alpha/2):DoF)(s(b1))
#alpha: desired probability
#linePoints: list of touples defining the x and y coordinates of a point
#returns 3 variables, the slope of the regression, the intercept of the regression, and a touple containing the upper and lower bounds of the confidence interval of the slope
def slopeConfidence(alpha, linePoints):
    if len(linePoints)<=2:
        return "Error: not enough points for calculation"
    #if len(linePoints)==2:
    #    regression = lineRegress(linePoints)
    #    return regression["slope"], regression["intercept"],(regression["slope"],regression["slope"])
    #get linear regression for points
    regression = lineRegress(linePoints)
    #get Tscore
    tScore = stats.t.ppf((1-alpha/2), len(linePoints)-2)


    #get s(b1)  == (MSE)/sum(xi-mean(x))^2)
    xVctr, yVctr = _pointsToVectors(linePoints)
    MSE = _MSE(regression["slope"], regression["intercept"],linePoints)
    xMean = mean(xVctr)
    xMeanDiffArray = []
    for x in xVctr:
        xDiff = x - xMean
        xDiffSq = xDiff *xDiff
        xMeanDiffArray.append(xDiffSq)
    xDiffSum = sum(xMeanDiffArray)
    sSqVal = MSE/xDiffSum
    sVal = math.sqrt(sSqVal)
    deltaConfidence = tScore*sVal
    confidenceInterval = (regression["slope"]-deltaConfidence,regression["slope"]+deltaConfidence)
    return regression["slope"], regression["intercept"], confidenceInterval


#get MSE of a regression
#slope: slope of calculated regression
#intercept: intercept of calculated regression
#yPoints: An array of the points used to create the regression
#xVctr: an array of the values
#returns MSE
def _MSE(slope, intercept,linePoints):
    errorArray = []

    #get  sigma error squared
    for point in linePoints:
        xVal = point[0]
        yVal = point[1]
        expectedY = slope * xVal + intercept
        difference  = yVal - expectedY
        squareDifference  = difference*difference
        errorArray.append(squareDifference)
    errorSum = sum(errorArray)

    #devide by DoF (n-2)
    MSE = errorSum/(len(linePoints)-2)
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
    for line in dataVctrs.values():
        data = lineRegress(line)
        LineStats.append(data)
    #flatten the array
    allpoints = [val for sublist in dataVctrs.values()  for val in sublist]
    #unzip to obtain x and y value vectors for all points
    xVals, yVals = zip(*allpoints)

    minX = min(xVals)
    maxX = max(xVals)
    xVctr = list(set(allpoints))
    if maxX - minX>1:

        xVctr = range(minX,maxX)

    lineVctrs =[]
    colorVctr = []
    styleVctr = []

    #creates expected slope line for comparisons
    if expectedSlope:
        expectedPoints = []
        if expectedSlope == "pop":
            if popTable:
                averagePopPoints = []
                allpoints = [val for sublist in popTable for val in popTable[sublist]]
                xVals, yVals = zip(*allpoints)
                xSet = set(xVals)
                for x in xSet:
                    pointYSet = [point[1] for point in allpoints if point[0] == x]
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


#Method to read in a graph config file and return a dictionary of
def neConfigRead(filename):
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
    return configDict

#master function to create a graph from neEstimation data.
#neFile: filepath for the neEstimation output file desired.
#configFile filepath to configureation file containting parameteres for the graph (see example.cfg and example1.cfg,
#   this parameter and all feilds in the file are optional with what i considered the most relevant/base defaults)
def neGrapher(neFile, configFile):

    if not configFile:
        table , countsTable, errorTable= scrapeNE(neFile)
        neGraphMaker(table)
        createBoxPlot(table)
        createScatterPlot(table)
        return True
    configs = neConfigRead(configFile)
    table,countsTable, errorTable = scrapeNE(neFile,configs["startData"])
    print table
    neGraphMaker(table,expectedSlope=configs["expected"],title= configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["dest"],xLim=configs["xLims"],yLim=configs["yLims"], countTable = countsTable)
    createBoxPlot(table,title =  configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["boxplot"])
    createScatterPlot(table, errorTable, title =  configs['title'],xlab=configs["xLab"],yLab=configs["yLab"],dest=configs["scatter"])


#master function for creating a table of confidence intervals form neEstimation data
#neFile: filepath of neEstimation output file
#confidenceAlpha: level of confidence desired should be <0.5, most common are 0.05 and 0,1 for 95% and 90% respectivly
#outFileName: resulting file location for file results, will overwrite existing file.
#significantValue: value of comparison w/ regards to slope. should be 0 for every test, but can be changed if needed.
#testFlag: flag that disables file write and prints stats to console instead, used for test functions
def _neStatsHelper(neFile,confidenceAlpha, outFileName = "neStatsOut.txt", significantValue = 0, firstVal = 0,testFlag = False):
    tableFormat = "{:<30}{:<30}{:<50}{:<80}\n"
    confPercent = (1 - confidenceAlpha)*100
    tableString =tableFormat.format("Slope","Intercept","Confidence Interval("+str(confPercent)+"%)","Source File")
    table, countsTable, errorTable = scrapeNE(neFile,firstVal)
    slopeVctr = []
    confidenceVctr = []

    Uncountable = 0
    for recordKey in table.keys():
        record = table[recordKey]
        slope, intercept, confidence  = slopeConfidence(confidenceAlpha,record)
        tableString+=tableFormat.format(slope,intercept,confidence,recordKey)
        if isnan(slope):
            Uncountable +=1
        else:
            slopeVctr.append(slope) 
            confidenceVctr.append(confidence)
    maxSlope = max(slopeVctr)
    minSlope = min(slopeVctr)
    meanSlope = mean(slopeVctr)
    medSlope = median(slopeVctr)
    negativeCount=0
    zeroCount=0
    positiveCount=0
    for cI in confidenceVctr:
        if cI[0]>significantValue:
            positiveCount+=1
        elif cI[1]<significantValue:
            negativeCount+=1
        else:
            zeroCount+=1
    if testFlag:
        print slopeVctr
        print confidenceVctr

        print positiveCount
        print zeroCount
        print negativeCount
        return
    outFile = open(outFileName,"w")
    outFile.write("File:"+neFile+"\n")
    outFile.write("\n")
    outFile.write("Max Regression Slope:\t\t"+str(maxSlope)+"\n")
    outFile.write("Min Regression Slope:\t\t"+str(minSlope)+"\n")
    outFile.write("Mean Regression Slope:\t\t"+str(meanSlope)+"\n")
    outFile.write("Meadian Regression Slope:\t"+str(medSlope)+"\n")
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
        return _neStatsHelper(neFile,0.05)

    configVals = neConfigRead(configFile)
    return _neStatsHelper(neFile,configVals["alpha"], outFileName=configVals["statsFilename"],significantValue=configVals["sigSlope"],firstVal=configVals["startData"], testFlag= testFlag)


if __name__ == "__main__":
    #Tests

    #Test Linear Regression
    print"lineRegress Tests"
    #Perfect Positive Regression
    xVct = range(10)
    yVct  = range(10)
    table = zip(xVct,yVct)
    result = lineRegress(table)
    assert result["slope"] == 1.0
    assert result["intercept"] == 0.0
    assert result["r_val"] ==1.0
    yVct = range(0,20,2)
    table = zip(xVct,yVct)
    result = lineRegress(table)
    assert result["slope"] == 2.0
    assert result["intercept"] == 0.0
    assert result["r_val"] == 1.0
    yVct = range(10,20,1)
    table = zip(xVct,yVct)
    result = lineRegress(table)
    assert result["slope"] == 1.0
    assert result["intercept"] == 10.0
    assert result["r_val"] ==1.0
    print "Perfect Positive regression passed"

    # Perfect Negative Regression
    xVct = range(10)
    yVct  = range(10,0,-1)
    table = zip(xVct,yVct)
    result = lineRegress(table)
    assert result["slope"] == -1.0
    assert result["intercept"] == 10.0
    assert result["r_val"] == -1.0
    yVct = range(20,0,-2)
    table = zip(xVct,yVct)
    result = lineRegress(table)
    assert result["slope"] == -2.0
    assert result["intercept"] == 20.0
    assert result["r_val"] ==-1.0
    yVct = range(0,-10,-1)
    table = zip(xVct,yVct)
    result = lineRegress(table)
    assert result["slope"] == -1.0
    assert result["intercept"] == 0.0
    assert result["r_val"] ==-1.0
    print "Perfect Negative regression passed"





    print "lineRegress Tests Passed"

    print "Confidence Tests "
    xVct = range(5)
    yVct  = range(5)
    table = zip(xVct,yVct)
    print slopeConfidence(0.05,table)
    xVct = range(5)
    yVct  = range(5)
    yVct[0]-=1
    table = zip(xVct,yVct)
    print slopeConfidence(0.01,table)
    print slopeConfidence(0.05, table)
    print slopeConfidence(0.1,table)
    xVct = range(10)
    yVct  = range(10)
    yVct[0]-=1
    table = zip(xVct,yVct)
    print slopeConfidence(0.01,table)
    print slopeConfidence(0.05, table)
    print slopeConfidence(0.1,table)
    print "Confidence Tests passed"

    print"getLineGraph Tests"
    xVct = range(10)

    assert _getGraphLine(0.0, 0.0, xVct) == [(0,0.0), (1,0.0),(2, 0.0), (3,0.0), (4,0.0), (5,0.0), (6,0.0), (7,0.0), (8,0.0), (9,0.0)]
    print "slope 0 test passed"
    assert _getGraphLine(0.0, 6.0, xVct) == [(0,6.0), (1,6.0),(2, 6.0), (3,6.0), (4,6.0), (5,6.0), (6,6.0), (7,6.0), (8,6.0), (9,6.0)]
    print "slope 0 intercept !=0 test passed"
    assert _getGraphLine(1.0, 0.0, xVct) == [(0,0.0), (1,1.0), (2,2.0), (3,3.0), (4,4.0), (5,5.0), (6,6.0), (7,7.0), (8,8.0), (9,9.0)]
    print"x=y case pass"
    assert _getGraphLine(1.0, 1.0, xVct) == [(0,1.0),(1, 2.0), (2,3.0), (3,4.0), (4,5.0), (5,6.0), (6,7.0), (7,8.0), (8,9.0), (9,10.0)]
    print "intercept != 0 test passed"
    assert _getGraphLine(4.0, 1.0, xVct) == [(0,1.0), (1,5.0), (2,9.0), (3,13.0), (4,17.0), (5,21.0), (6,25.0), (7,29.0), (8,33.0), (9,37.0)]
    print "slope 4 intercept 1 test passed"
    assert _getGraphLine(-1.0, 0.0, xVct) == [(0,0.0), (1,-1.0), (2,-2.0), (3,-3.0), (4,-4.0), (5,-5.0), (6,-6.0), (7,-7.0), (8,-8.0), (9,-9.0)]
    print "negative slope test passed"
    assert _getGraphLine(-2.0, 3.0, xVct) == [(0,3.0), (1,1.0), (2,-1.0 ), (3,-3.0), (4,-5.0), (5,-7.0), (6,-9.0), (7,-11.0), (8,-13.0), (9,-15.0)]
    print "negative slope intercept !=0 test passed"
    assert _getGraphLine(2.0, -3.0, xVct) == [(0,-3.0), (1,-1.0), (2,1.0 ), (3,3.0), (4,5.0), (5,7.0), (6,9.0), (7,11.0), (8,13.0), (9,15.0)]
    print "negative intercept !=0 test passed"


    xVct = range(3,13,1)
    assert _getGraphLine(1.0, 0.0, xVct) == [(3,3.0), (4,4.0), (5,5.0), (6,6.0), (7,7.0), (8,8.0), (9,9.0), (10,10.0), (11,11.0), (12,12.0)]
    print "non 0 positive x start passed"
    xVct = range(3,13,1)
    yVct = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    assert _getGraphLine(1.0, -3.0, xVct) == zip(xVct,yVct)
    print "non 0 x start non 0 intercept passed"

    xVct = range(10,0,-1)
    yVct = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    assert _getGraphLine(1.0, 0.0, xVct) == zip(xVct,yVct)
    print "negative step x axis passed"

    xVct = range(0, -10, -1)
    yVct = [0.0, -1.0, -2.0, -3.0, -4.0, -5.0, -6.0, -7.0, -8.0, -9.0]
    assert _getGraphLine(1.0, 0.0, xVct) == zip(xVct, yVct)
    print "negative step x axis passed"

    xVct = range(-7,3,1)
    yVct = [-7.0, -6.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0]
    assert _getGraphLine(1.0, 0.0, xVct) == zip(xVct, yVct)
    print "negative start x axis passed"

    xVct = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    yVct = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    assert _getGraphLine(1.0, 0.0, xVct) == zip(xVct, yVct)
    print "non integer x axis passed"

    print "getGraphLine Passed"


    xVct = range(0,20,2)
    table = []
    table.append(_getGraphLine(-0.1, 0, xVct))
    table.append(_getGraphLine(-0.005, 0, xVct))
    table.append(_getGraphLine(-0.15, 10, xVct))
    table.append(_getGraphLine(0.25, 10, xVct))


    print "createGraph Test"
    colorStyles = ["", ""]
    lineStyles = ["", ""]
    title = "testTitle"
    x = "TestX"
    y = "TestY"
    createGraph(table,colorVctr=colorStyles, styleVctr=lineStyles, title=title, xlab=x, yLab=y)


    print "NeRegressionGraphMaker"

    testYs = [[0,0,0,0,0],[1,2,3,4,5],[-1,-2,-3,-4,-5],[1,3,1,3,1]]
    testX = [1,2,3,4,5]
    testTable =[]
    for yVct in testYs:
        testTable.append(zip(testX,yVct))
    id = 0
    testDict = {}
    for data in testTable:
        testDict[id] = data
        id+=1

    lines, color, styles = _NeRegressionGraphCalc(testDict)

    createGraph(lines,colorVctr=color,styleVctr=styles)

    testYs = [[0,0,0,0,0],[1,2,3,4,5],[-1,-2,-3,-4,-5],[1,3,0,2,-1]]
    for yVct in testYs:
        testTable.append(zip(testX,yVct))
    testDict = {}
    for data in testTable:
        testDict[id] = data
        id += 1
    lines, color, styles = _NeRegressionGraphCalc(testDict, -0.333)

    createGraph(lines,colorVctr=color,styleVctr=styles)

    testArray = [2,5,3,6,1,4]
    testArray.sort()
    print  testArray

    table, countsTable, errorTable = scrapeNE("testData.txt")

    print table
    print countsTable
    print errorTable



    neGraphMaker(table)

    configwrite= ConfigParser.ConfigParser()
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

    print neConfigRead("example1.cfg")
    print "test master methods"
    neGrapher("testData.txt","example1.cfg")
    _neStatsHelper("testData.txt",0.1,testFlag=True)
    _neStatsHelper("testData.txt",0.05)
