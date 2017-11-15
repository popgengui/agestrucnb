# negui

Overview
--------

	Our program is a front end that incorporates the simulation and LDNe
	based population genetics functions provided by Tiago Antao's python program at
	https://github.com/tiagoantao/AgeStructureNe.git, enhanced by multiple methods
	for population subsampling when performing LD-based Ne and Nb estimations from
	genepop file inputs.  Further, we have added simulation functionality and subsampling
	methods and interfaces for LDNe estimation, as well as  plotting interfaces to show
	estimate distributions and regression lines. 

	The program uses multi-processing to allow an arbitrary number of
	simultaneous simulation, LD-based Nb and Ne estimations, and plotting
	interfaces.  Further, within simulations, it can run simulation replicates
	simultaneously, and, within Ne or Nb estimation sessions, it allows
	simultaneously running genepop-file population sections. 

Current compatible python versions
----------------------------------
	python 3.5 and 3.6.  On Windows platforms especially, we recommend using
	the Anaconda 3 python distribution, as it's "conda" installer supplies a
	pre-compiled version of simuPOP, which is often difficult to install on Windows, 
	when you try to install through pip and setuptools (see item 2. in the Dependancies
	section below).

	python 2.7 (python 3 is recommended, as 2.7 requires building an older version of simuPOP)

	The above are the python versions on which the program was developed and tested.  Other versions may work, too.

OS-comaptibility
-----------------
	1. Linux. The program has been run on Linux (Ubuntu 16.04).

	2. OS X. The program has been run successfully on OS X, but the most
	   recent versions have not been tested on that platform.

	3. Windows 10 and 8.1 (64-bit).  Earlier versions of the program
	   were also run successfully on 32-bit Windows 7 and Vista, and
	   we consider it likely that it will still run well on those older
	   Windows platforms.  Note that on Windows, a persistent problem 
	   is the inability of the program to remove files for
	   some cleanup operations when processes do not finish (through error or
	   user-cancellation). See the "BUGS" file for this and other issues.

Dependencies
------------
	The following are the python packages on which our program depends.
	Aside from the installation of SimuPOP, dependancies are automatically
	installed when you use one of the preferred installation methods enumerated in
	the Installation section below.
	

	1. pip, the python package installer, included in most recent python
	   distributions (see the Installation section for details).

	2. setuptools,  among other functions, this package works with pip to install 
	   packages. Also included in most recent python distributions.

	3.  SimuPOP, a python package, available at
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
		
	4. Other python packages, available through pip with the command "pip
	install <package>", or, if you use the Anaconda distribution of python,
	"conda install <package>".
				
		i.   numpy	

		ii.  scipy
		
		iii. future

		iv.  psutil
		
		v.   for python 2 only, configparser.y. This is a backported python 3 package, different 
		     than the default python2 ConfigParser package. 

		vi.  for python2 only, if not already in your distribution, the ttk package.  The pip package
		     can be installed with pip install pyttk.

		vii. natsort

Installation  
------------
	1. Methods.  All non-conda-installer methods require either the "pip" or
	   "setuptools" python packages.  Most recent distributions of python contain
	   these packages. If you are not using Anaconda, and need "pip" and
	   "setuptools", see the instrucutions at
	   https://packaging.python.org/tutorials/installing-packages/.  Once you have pip
	   installed, you can install setuptools using pip. There are several ways to
	   install agestrucne, listed here.  Then, see the Platform-based details directly
	   following to match a method with a platform/python combination.

		i. Single command method with pip:  
		   a. Open a terminal and type
		      "pip install agestrucne."
		ii. Single command method with setup.py:
			a. Download the program files (or use "git clone")
			   from the repostitory at from https://github.com/popgengui/agestrucne			  	
			b. From a terminal whose current directory is inside
			   outermost agestrucne directory (which contains the
			   "setup.py" file), type the command "python3 setup.py install."
		iii. simuPOP installation followed by pip.
			a. Install simuPOP into your python distribution
			   following the instructions at
			   http://simupop.sourceforge.net/Main/Download.
				1. If you are using python3 from an Anaconda 3 installation,
				   you can install simuPOP quickly with these 2
				   commands at a terminal:
					conda config --add channels conda-forge
					conda install simupop
			b. Install the program and remaining dependancies with
			   "pip install agestrucne" 
		iv. simuPOP installation followed by setup.py.  This method is
		    the same as (iii), but, after you've installed simuPOP, then
		    use the method (ii) instructions to download the program
		    source and intall with the setup.py module.

	2.  Platform/python combination specifics. These refer to the
	    installation methods listed above.
		i. Linux, python3, with setuptools and pip3 installed.
			a. Use method (i) or (ii) above.		
		ii. Linux, python3, using the Anaconda3 distribution.
			a. Use any method, but note that simuPOP will be
			   installed much more quickly if you use method (iii),
			   and the "conda" commands noted above.
		iii. Linux python 2 any distribution.
			a. use method (iii). 
		iv. Windows, 64-bit, with python3 through an Anaconda3 installation.
			a. Use method (iii) or (iv).
		v.  Windows, 32-bit installations, or any Windows version using
		    python2, or Windows.	
			a. Use method (iii) or (iv).
		vi. OS X, python3, using the Anaconda3 distribution.
		    a. Use method (i) or (ii).

		vii. OS X, any python3 or python2, using a non-Anaconda
		     distribution.
		    a. Use methods (iii) or (iv).
Starting the program
--------------------

	1. From a console, a terminal in Linux in OS X, or a DOS prompt or
	   powershell in Windows, you can start the program with the command:
		
		agestrucne	
		
	2. In windows from its File Explorer program, if you navigate the
	   programs main directory, you can double-click on the negui.py file.

Using the program	
-----------------
	To run a simulation, calculate Nb or Ne estimates, or plot results, load one
	load one of the three interfaces by clicking "New" on the main menu.

	For details about running the different interfaces, see the
	user manual.
