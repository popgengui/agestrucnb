overview
--------
	For more details about the program, see the manual.pdf file distributed
	with the program. Briefly, our program is a front end that incorporates the
	simulation and LDNe based population genetics functions provided by Tiago
	Antao's python program at https://github.com/tiagoantao/agestructurene.git,
	enhanced by multiple methods for population subsampling when performing LD-based
	Ne and Nb estimations from genepop file inputs.  Further, we have added
	simulation functionality and subsampling methods and interfaces for LDNe
	estimation, as well as  plotting interfaces to show estimate distributions and
	regression lines. 

	The program uses multi-processing to allow an arbitrary number of
	simultaneous simulation, LD-based Nb and Ne estimations, and plotting
	interfaces.  Further, within simulations, it can run simulation replicates
	simultaneously, and, within ne or nb estimation sessions, it allows
	simultaneously running genepop-file population sections. 

	The core functionality for simulation is provided by the python simuPOP
	package (Peng, B. & Kimmel, M. simuPOP: a forward-time population genetics
	simulation environment. Bioinformatics 21, 3686–3687, 2005). The LDNe
	estimation by version 2 of the LDNe program (Waples, R. S. & Do, C.  LDNe: a
	program for estimating effective population size from data on linkage
	disequilibrium. Molecular Ecology Resources 8, 753–756, 2008).

	Please direct questions/issues to our program's email account, agestrucne@gmail.com

current compatible python versions
----------------------------------
	1.  python 3.5 and 3.6.  On Windows 64-bit and OS X platforms , we strongly recommend using
	    the Anaconda 3 python distribution, as it's "conda" installer supplies a
	    pre-compiled version of SimuPop, which is often difficult to install 
	    through pip and setuptools.

	2. python 2.7 Note that python 3 is the recommended environment, since 2.7 requires building
	    an older version of SimuPop, which can be difficult, especially in Windows (see
	    the Dependancies and Installation sections, below.) the above are the python
	    versions on which the program was developed and tested.  other versions may
	    work, too.

os-comaptibility
-----------------
	1. Linux. the program has been run on linux (ubuntu 16.04).

	2. OS X. The program has been run successfully on OS X, v10.13 (High Sierra).

	3. Windows 10 and 8.1 (64-bit).  Note that on windows, a persistent problem 
	   we have not yet solved is the inability of the program to remove files for
	   some cleanup operations when processes do not finish (through error or
	   user-cancellation). Thus you may have to remove output and temporary files
	   manually when a run is cancelled or fails.

dependencies
------------
	The following are the python packages on which our program depends.
	Aside from the installation of SimuPop, pip and setup tools,  dependancies 
        are automatically installed when you use python's pip installer, or the 
	setup.py method (see the Installation section, below).

	1. pip and setuptools, the python package installation modules, included
	   in most recent python distributions (see the installation section for
	   details).  All methods require the "pip" and "setuptools" python packages.  If
	   your distribution does not include them, please see
	   https://packaging.python.org/tutorials/installing-packages/.  

	2.  SimuPOP, a python package, hosted at
	    http://SimuPop.sourceforge.net.  See our instllation section below
	    for recommendations on aquiring this package. As we note below, the
	    easiest way to install simuPOP is through the 64-bit, Anaconda3 python3
	    distribution. See the installation section below.	
	
	3. Other python packages, which should be automatically installed when
	   you use the pip installer, or the "setup.py install" command (see
	   Installation, below), can also be installed one at a time through pip with the
	   command "pip install <package>", or, if you use the Anaconda distribution of
	   python, "conda install <package>".
		
		i.   numpy	

		ii.  scipy
		
		iii. future

		iv.  psutil
		
		v.   for python 2 only, configparser. This is a backported python 3 package, different 
		     than the default python2 ConfigParser package. 

		vi.  for python2 only, if not already in your distribution, the ttk package.  The pip package
		     can be installed with pip install pyttk.

		vii. natsort

Installation  
------------
	1. Download the configuration files, README.md file (this file), and manual from 
	   https://github.com/popgengui/agestrucne/tree/data.  On the web page you will see
	   a green button on the right side of the screen, and labeled, "Clone or download."
           Besides the program manual and README.md file, this data branch of our github 
	   repository supplies simulation configuration files that will get you started 
           in the program pipeline (see the manual for details on how to load and edit the 
	   configuration files).

	2. Recommended Installation procedures, by platform.

		A. Linux, 64-bit, python3:

			i. From a terminal, type "pip3 install agestrucne".

			ii. Note:  according to the speed and RAM capacity of your computer,
				SimuPop can take many minutes to be compiled and installed.
		
		B. Windows, 64-bit, Anaconda3 python installation, 
			i. from the Anaconda Prompt program window, type
			   the following commands:
			
				conda config --add channels conda-forge

				conda install SimuPop

			ii. Clone (using the git program) or download the zip archive from 
			    our master repository at, https://github.com/popgengui/agestrucne.

			iii. Open the Anaconda Prompt window, and use "cd" to move to the "agestrucne" 
			     directory containing the unzipped files, in particular look for the "setup.py"
                             file.  Type the following command:
				
				python setup.py install

			iv. Our testing shows that, after the installation,  the main program executable, 
			    "agestrucne", will be available directly at from the Anaconda
			    Prompt, the console-based exectuables, "pgdriveneestimator.py" and
			    "pgdrivesimulation.py" will need to be invoked by using the path to the
			    "Scripts" subdirectory of your Anaconda installation.  (See the manual
			    for information about these scripts.)  In most cases the command
			    at the Anaconda Prompt window will be of the form:			    

				    /Users/[my-user-name]/Anaconda3/Scripts/[console-script]

			    For which you should substitute the name of your home directory under 
			    the Users directory, and one of the two script names noted above.

		C. OS X, Anaconda3 python installation, 

			i. from OX X Terminal window, type the following commands:
			
				conda config --add channels conda-forge

				conda install SimuPop

			ii. Clone (using the git program) or download the zip archive from 
			    our master repository at, https://github.com/popgengui/agestrucne.

			iii. Open a Terminal window, and use "cd" to move to the directory
			     conaining the unzipped files, into the directory in which the setup.py
                             file.  Type the following command:
				
				python setup.py install

		D. Installation methods, in general, if your platform and python
		   installations do not match the above.

			i. Single command method with pip:  

			   a. Open a terminal and type

			      "pip install agestrucne."

			ii. Single command method with setup.py:

				a. Download the program files  available at	
				   https://github.com/popgengui/agestrucne
				   by clicking on the green button on the
				   right side of the screen labelled "clone or download."

				b. From a terminal whose current directory is
				   download's main  directory, "agestrucne"
				   which contains the "setup.py" file), type the
				   command "python setup.py install."

			iii. Using setup.py, with an Anaconda3 python installation.

				a.  Open a terminal or Anaconda Prompt and type:

					conda config --add channels conda-forge

					conda install SimuPop

				b. Install the progarm using method (ii)

			iii. Manual simuPOP installation followed by pip.

				a. Install simuPOP into your python distribution
				   following the instructions at
				   http://SimuPop.sourceforge.net/Main/Download.

					1. If you are using python3 from an Anaconda 3 installation,
					   you can install simuPOP quickly with these
					   commands at a terminal:
						conda config --add channels conda-forge
						conda install SimuPop

					2. Note If you are using python2, pip
					   will not install the correct version
					   of SimuPop, and you will need to compile it from source.  
					   This procedure can be difficult and fraught with missing 
					   dependancies, especially in Windows. It is a
					   procedure beyond the scope of these instructions. 

				b. Install the program and remaining dependancies with
				   "pip install agestrucne" 

			iv. SimuPOP installation followed by setup.py.  This method is
			    the same as (iii), but, after you've installed simuPOP, then
			    use the method (ii) instructions to download the program
			    source and intall with the setup.py module.
				
Starting the program
--------------------

	1. From terminal in Linux or OS X, or  an Anaconda
	   prompt in Windows, you can start the program with the command,
	   "agestrucne."  The python pip installer should have added this
 	   command to your PATH variable in your user environment. 

		A. Note that when you open the program, the current directory of your
		   terminal will determine where the file-loading dialog will be initially
		   set, as you locate, for example, a configuration file to load into
		   the simulation interface.
	
	2. In addition to "agestrucne,"  the installation should also add two
	   more commands to your user environment, which offer non-graphical
	   ways to run simulations and LDNe estimations. Windows installations
	   may fail to add these commands under Anaconda3.  In this case, see
           the Note in the Installation section B.2.iv.

		A. Command "pgdrivesimulation.py" performs simulations from the
		   terminal, as specified in the user manual.

		B. Command "pgdriveneestimator.py" performs LDNe estimations
		   from the terminal, as specified in the user manual.

Using the program	
-----------------

	To run a simulation, calculate Nb or Ne estimates, or plot results, load one
	of the three interfaces by clicking "New" on the main menu.

	For details about running the different interfaces, see the
	user manual.

