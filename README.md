# negui

We plan to make a front end for ease of use, and incorporate the population genetics functions provided by Tiago Antao's python program at https://github.com/tiagoantao/AgeStructureNe.git.  

Current implemenation is for python 2.7.

Thu Jan 28 18:05:47 MST 2016

We plan on an iterative implementation of the several analyses performed by Tiago's code.  As we begin, I've committed skeletal source files to begin a tkinter framework.  Even this approach may change.  The basic class structure includes a gui class that contains an popgen (PG) operation.  This is seen in the file, preliminary_uml_classes.png.  The current strucure of the program can be seen via descriptions of classes and relationships by loading doxydoc/html/index.html into a browser. 

Sun Jul 17 23:00:41 MDT 2016

Current dependancies

Current functionality:

--Simulation GUI interface.
	Currently the GUI offers simuPop simulations based on configuration files and life tables as exemplified in the resources/*life.table.info and configuration_files/simulation/*with.model.name files.  Limititations now include incorrect implementation of replicates in the simulation interface.  If some multiple run values N is indicated by entering 2 or more in the "replicates" text box in the simulation interface, simuPop will be run N times, but the inititial gender distribution will be identical in all runs.  Non-random instantitaion of populations across ptyon processes is still being solved.

