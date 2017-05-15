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
	simultaneous simulation, LD-baseed Nb and Ne estimations, and plotting
	interfaces.  Further, within simulations and estimations, multi-processing
	allows simultaneous processing replicates and subsample instances.

Current compatible python versions
----------------------------------
	python 2.7
	python 3.6

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

Current dependencies
--------------------
	1.  SimuPOP, a python package, available at http://simupop.sourceforge.net. See the installation
	    instructions at http://simupop.sourceforge.net/Main/Download.  Python 3.6 
	    users using the Anaconda3 distribution can easily install simuPOP with 

		conda config --add channels conda-forge
		conda install simupop
		
	    Python 2 users will have a more involved installation, as you'll see at the installation page.  Below
 	    are a few notes of our experience installing simuPOP for python 2 in Windows.

		i. VC++ Library, 2008 (Windows only).  We found that the installation of SimuPOP
		on Windows (10 ) did not work without installing the Microsoft VC++
		Redistributable 2008 library, as noted in the SimuPOP installation web page.
		Note that the link on the Simupop installation web page points to the Microsoft
		to the 32-bit libary download-page (unless I missed an option).  Most of us will
		actually need the x64 verion at
		https://www.microsoft.com/en-us/download/details.aspx?id=15336

		ii.  SWIG.  On one linux machine tested we found that, before
		python would install simuPOP we needed the SWIG tool at
		http://www.swig.org/download.html. (This tool makes C and C++ code in simuPOP
		python compatible). Since we found that most of our python installations will
		had have the necessary SWIG resources, it's be best to try to install simuPOP
		first, and install SWIG if you get a message that it is missing missing.

		iii. Python compiler for Windows. On two of our platforms that
		had 32-bit Windows versions we also needed to install the windows python
		compiler.  Simupop, if it's installation fails for lack of this compiler, will
		give you the correct web address from which to download and intall it.
	2. Other python packages, available through pip with the command "pip
	install <package>", or, if you use the Anaconda distribution of python,
	"conda install <package>".
				
		i.   numpy	

		ii.  scipy
		
		iii. future

		iv.  psutils
		
		v.   configparser, for python 2 only. This is a backported python 3 package, different 
		     than the default python2 ConfigParser package, which is a default package. 

Installation.  
------------

	1. Clone the repository using the git program, or download the zipped files from
	https://github.com/popgengui/negui

Starting the program
--------------------

	1. From a console, a terminal in Linux in OS X, or a DOS prompt or
	   powershell in Windows, you can start the program with the command:
		
		<python> <path_to_negui.py>

	   <python> can be anyalias for python 2.7 or python 3.6 executable.
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
	on "Add".  

	For details about runnin running the different interfaces, see the
	user manual.
