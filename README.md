# negui

Overview
--------

	Our program is a front end that incorporates the simulation and LDNe
	based population genetics functions provided by Tiago Antao's python program at
	https://github.com/tiagoantao/AgeStructureNe.git, enhanced by multiple methods
	for population subsampling when performing LD-based Ne and Nb estimations from
	genepop file inputs.  Further, we provide a plotting interface to visualize
	estimate distributions and regression lines. 

	The program uses multi-processing to allow an arbitrary number of
	simultaneous simulation, LD-based Nb and Ne estimations, and plotting
	interfaces.  Further, within simulations, it can run simulation replicates
	simultaneously, and, within Ne or Nb estimation sessions, it allows
	simultaneously running genepop-file population sections. 

Current compatible python versions
----------------------------------
	python 3.6 (recommended).
	python 2.7 (requires building an older version of simuPOP)

OS-comaptibility
-----------------
	1. Linux. The program has been run on Linux (Ubuntu 16.04).

	2. OSX. The program needs further testing on OS X.

	3. Windows 10 and 8.1 (64-bit).  Earlier versions of the program
	   were also run successfully on 32-bit Windows 7 and Vista, and
	   we consider it likely that it will still run well on those older
	   Windows platforms.  Note that on Windows  One persistent problem 
	   is the inability of the program to remove files for
	   some cleanup operations when processes do not finish (through error or
	   user-cancellation). See the "BUGS" file for this and other issues.

Dependencies
------------
	1.  SimuPOP, a python package, available at
	    http://simupop.sourceforge.net. See the installation instructions at
	    http://simupop.sourceforge.net/Main/Download.  The SimuPOP installation page
	    recommends using an Anaconda Python installation, since the conda package
	    distribution collection includes a pre-compiled simuPOP package.   
	    Python 3.6 users using the Anaconda3 distribution can easily install simuPOP with 

		conda config --add channels conda-forge
		conda install simupop
		
	    The Anaconda python3 distribution is escpecially recommended for Windows users.
	    Aquiring simupop without using the conda package manager requires compiling simuPOP 
	    source code, which can difficult in Windows.  See the simuPOP web page, noted above, 
	    for details.
		
	2. Other python packages, available through pip with the command "pip
	install <package>", or, if you use the Anaconda distribution of python,
	"conda install <package>".
				
		i.   numpy	

		ii.  scipy
		
		iii. future

		iv.  psutils
		
		v.   configparser, for python 2 only. This is a backported python 3 package, different 
		     than the default python2 ConfigParser package. 

Installation  
------------

	Clone the repository using the git program, or download the zipped files
	from https://github.com/popgengui/negui and unzip them inside any directory to
	which you have read and write access.

Starting the program
--------------------

	1. From a console, a terminal in Linux in OS X, or a DOS prompt or
	   powershell in Windows, you can start the program with the command:
		
		<python> <path_to_negui.py>

	   <python> can be any alias for python 2.7 or python 3.6 executable.
	   <path_to_negui> should give a full or relative path to the main program
	   directory and the file negui.py

	   For example, if you downloaded the program files to
	   /home/me/programs/agestructurene, you can start the program with the command,

		python /home/me/programs/agestructurene/negui.py
		
	2. In windows from its File Explorer program, if you navigate the
	   programs main directory, you can double-click on the negui.py file.

Using the program	
-----------------
	To load one of the three interfaces or either running a simulation,
	calculating Nb or Ne estimates, or plotting the results, on the main menu click
	on "New".  

	For details about running the different interfaces, see the
	user manual.
