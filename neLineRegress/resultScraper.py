import re


def scrapeResults(fileName):
    statFile  = open(fileName)
    powerRegex = re.compile('Positive Slopes:\s+(?P<positive>\d*)\s+Neutral Slopes:\s+(?P<neutral>\d*)\s+Negative Slopes:\s+(?P<negative>\d*)')
    fileText = statFile.read()
    matches= powerRegex.search(fileText)
    #print matches.groups()
    results = {"positive":int(matches.group("positive")),"neutral":int(matches.group("neutral")),"negative":int(matches.group("negative"))}
    #print results
    return results



file  = "neStatsOut.txt"

scrapeResults(file)