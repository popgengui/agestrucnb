# negui

We plan to make a front end for ease of use, and incorporate the population genetics functions provided by Tiago Antao's python program at https://github.com/tiagoantao/AgeStructureNe.git.  

Current implemenation is for python 2.7.

Thu Jan 28 18:05:47 MST 2016

We plan on an iterative implementation of the several analyses performed by Tiago's code.  As we begin, I've committed skeletal source files to begin a tkinter framework.  Even this approach may change.  The basic class structure includes a gui class that contains an popgen (PG) operation.  This is seen in the file, preliminary_uml_classes.png.  The current strucure of the program can be seen via descriptions of classes and relationships by loading doxydoc/html/index.html into a browser. 

Sun Jul 17 23:00:41 MDT 2016

Current python version:
	python 2.7

Current dependancies
	1.  pygenomics, https://github.com/tiagoantao/pygenomics.git
		The pygenomics python modules should be installed using the supplied setup.py, so that they can be imported by your python interpereter.
	2.  SimuPOP, http://simupop.sourceforge.net
		The SimuPOP modules should be installed using setup.py (or pip), so that they can be imported by your python interpreter. 
	3.  NeEstimator, http://www.molecularfisherieslaboratory.com.au/neestimator-software.  Our program will look for the executable Ne2L in your Linux PATH variable.

Installation.  While TODO may include setup.py installation into python library directories, or using it pre-installed as a VM, as of now:

	1. Clone the repository or download the files from https://github.com/popgengui/negui
	2. Add the location of the python modules to your PYTHONPATH variable.
		Linux: example:  If you downloaded the python files into /home/myname/mydir/negui-master, you can either:
			a. On starting a new terminal type:
				PYTHONPATH=$PYTHONPATH:/home/myname/mydir/negui-master
			b. If your Linux has the typical configuration, then you can add the above line to the .bashrc file in your home directory, adding one line after it:
				export PYTHONPATH

Current functionality

	1. Simulation GUI interface.  Currently the GUI offers  AgeStructureNe-based simuPop simulations when supplied with configuration files and life tables as exemplified in the resources/*life.table.info and configuration_files/simulation/*with.model.name files.  Limititations now include incorrect implementation of replicates in the simulation interface.  If some multiple run values N is indicated by entering 2 or more in the "replicates" text box in the simulation interface, simuPop will be run N times, but the inititial gender distribution will be identical in all runs.  Non-random instantitaion of populations across ptyon processes is still being solved.

	2. Ne estimation from terminal command line, currently for genepop files with a single population, and offering subsampling of individuals using  percentages of the populaion (randomly selected), or values of N in a remove-N scheme, whereby N randomly selected individuals are removed from the population before the Ne is estimated.  Repicates at each percentage or N value is user set.  In the remove-N case of N=1, all combinations are run.

Current limitations
	1. The program has been run and tested so far only on Linux.
	2. SimuPOP replicates bug. Run in parallel initial populations not indepedantly created (see Current functionality, section 1).
	3. Genepop files for the command-line NeEstimation must have only one population per file.

Running the programs

	1. Simulation GUI interface.  We aimed to make the GUI interface self-explanatory, and so simply from the terminal typing 
		"python negui.py"
	   should get you the program's running state. Loading a new simulation from the "New" menu, then a configuration file (using the interface button) from the provided set, in the downloaded "configuration/simulation" subdirectory will then populate the GUI with the parameters that will be used in the simulation.  You can edit these values.  The current set of values will be written to a new configuration file with the "Out files base name" that you accept or input yourself in the text box so labelled.
	2. Ne Estimation from your terminal.  Providing that the python modules are in your PYTHONPATH variable, or that you are invoking the program from the directory containing them, then you can invoke the program with:

		"python pgdriveneestimator.py <"glob expression"> <"percent" or "remove"> <comma-separated list of integers, percentages, or N's for remove-N sampling> <integer, minimum population size> <float, minimum allele frequency (NeEstimator "critical" value)> <integer, number of replicates to run> <optional, integer, total processes to use (default is 1), required if the "debug" parameter is used> <optional, "debug1" to add to the output a table listing, for each indiv. in each file, which replicate Ne estimates include the indiv, or, "debug2" to run without parallelized processes,to produce the table, and to save all subsample genepop files and NeEstimator output files.>
	
