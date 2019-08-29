from __future__ import print_function
import glob
import os
import sys

import neLineRegress.LineRegress as LineRegress


def getFiles(pattern):
    files =glob.glob(pattern)
    return files

if __name__ == "__main__":
    neFile = sys.argv[1]
    configFile = None
    if len(sys.argv) ==3:
        configName = sys.argv[2]
        if not os.path.isfile(configName):
            print(configName +"does not exist, using defaults")
        else:
            configFile = configName
    if os.path.isfile(neFile):
        LineRegress.neGrapher(neFile,configFile)
        LineRegress.neStats(neFile,configFile)
    else:
        print("Ne Datatable File not Found")
