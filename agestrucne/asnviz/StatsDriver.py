from __future__ import print_function
import glob
import os
import sys
import ntpath

import configparser

import LineRegress


def getFiles(pattern):
    files =glob.glob(pattern)
    return files

if __name__ == "__main__":
    # how many cycles to use from the first value reported
    cycle_array = [5,7,10]
    # what p value to use for significance
    p_val_array = [0.1,0.05,0.15]

    neFiles = sys.argv[1:len(sys.argv)-1]
    configName = sys.argv[-1]
    print(configName)
    config = configparser.ConfigParser()
    config.read(configName)
    configFile = "current.cfg"
    for neFile in neFiles:

        base_path, base_filename_full = ntpath.split(neFile)
        base_filename = base_filename_full.split(".")[0]
        print(base_filename)

        for cycle_val in cycle_array:
            config.set("data","endCollect",str(cycle_val))
            for p_val in p_val_array:
                config.set("confidence","alpha", str(p_val))
                stat_filename = base_path+'/'+base_filename+'_'+str(cycle_val)+'cyc'+'_'+str(p_val)+'P.stats.txt'
                config.set("confidence","outputFilename",stat_filename)
                config.write(open(configFile, "w"))

                if os.path.isfile(neFile):
                    LineRegress.neRun(neFile,configFile)
                else:
                    print("Ne Datatable File not Found")
