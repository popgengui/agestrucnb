I. overview
-----------

    For more details about the program, see the manual.pdf file distributed
    with the program. Briefly, our program is a GUI front end that incorporates the
    simulation and LDNe-based population genetics functions provided by Tiago
    Antao's python program at https://github.com/tiagoantao/agestructurene.git,
    enhanced by multiple methods for population and loci subsampling when performing
    LD-based Nb estimations from genepop file inputs. It also provides
    plotting facilities to show estimate distributions and regression lines.

    The program uses multi-processing to allow an arbitrary number of
    simultaneous simulations, LD-based Nb estimations, and plotting
    interfaces.  Further, within simulations, it can run simulation replicates
    simultaneously, and, within Nb estimation sessions, it allows
    simultaneously running genepop-file population sections. 

    The core functionality for simulation is provided by the python simuPOP
    package (Peng, B. & Kimmel, M. simuPOP: a forward-time population genetics
    simulation environment. Bioinformatics 21, 3686–3687, 2005). The LDNe
    estimation by version 2 of the LDNe program (Waples, R. S. & Do, C.  LDNe: a
    program for estimating effective population size from data on linkage
    disequilibrium. Molecular Ecology Resources 8, 753–756, 2008).

    Please direct questions/issues to our program's email account, agestrucne@gmail.com

II. current compatible python versions
--------------------------------------

    1.  python, 64-bit, version 3.5 or greater, on 64-bit operating systems,
        including Windows, Mas OS (OS X) and linux distributions.  If you don't 
        already have python 3 installed on your computer, we strongly recommend 
        using the Anaconda 3 python distribution (see 
        https://www.anaconda.com/distribution/), 
        because it's "conda" installer supplies a pre-compiled version of SimuPop, 
        which can be difficult to install through pip and setuptools, especially
        on the Windows OS.


III. quickest installation procedures 
------------------------------------

    1. Find out if python 3 (version 3.5 or greater) is installed on your computer

         i. From a Mac OS (OSX) or Linux terminal
               a. type this command:

                    python3 --version

               b. if the command is not recognized, type:

                    python --version

               c. if the version is 3.4 or more, you have a version
                  compatible with agestrucnb

          ii. In Windows, a python distribution is not always accessible
              from a command prompt. If you're not sure whether
              you have python3 installed  you'll need to search
              your application list (e.g. using the windows key). 

    2. If python 3 (version 3.5 or greater)  is not installed on your computer,
       we strongly recommend installing the Anaconda3 python3 distribution, in
       order to access the pre-compiled simuPOP package.

         i.  Download and install the current 64-bit Anaconda3 distro for your OS
             from the Anaconda download page: 

                  https://www.anaconda.com/distribution/

         ii. Open the Anaconda Prompt window and type these commands 
             in this order:

               conda config --add channels conda-forge
               conda install simupop
               pip install agestrucnb

    3. If python 3 (3.5 or greater) is already on your computer

         i.  If your python 3 distribution is Anaconda3, then follow
             (2) above, step (ii).  Otherwise, type this command 
             (here we assume that your non-Anaconda installation 
             has supplied an alias for pip, "pip3", to distinguish
             it from the pip installed for a python2 distribution):

                 pip3 install agestrucnb

             a. Note for Linux users:  to install into your default 
                python location you may need to issue the command as a super user:

                 sudo pip3 install agestrucnb

                 and supply the sudo password.

         ii. If the install fails with a message indicating
             that simuPOP could not be installed,
             this likely means your computer needs some compiler-related
             packages.  Please see the simuPOP installation information
             for installing simuPOP using pip.  See item (6), at
             http://simupop.sourceforge.net/Main/Download

         iii. Note that installing the program using a non-Anaconda3
              python distribution requires that simupop is compiled,
              which can take a long time, on slower systems more than
              an hour. Further, simuPOP compile errors may not appear
              until late in the compilation steps.

    4. If you have installation problems, see the section following,
       which list a few that we encountered.

IV. Notes about known installation problems
-------------------------------------------
    1. Mac OS (OS X)

        a. Using the Homebrew version of python3, the GUI backend
           has a bug that crashes the program when the mouse scroll
           wheel is used.  Our successful Mac installs were under
           the Anaconda3 distro and the distribution available at 
           https://python.org.  Under the latter the simuPOP
           package took a long time compiling but was successful.

        b. Using the Mac OS installation of python3 available at
           python.org, the pip install agestrucnb fails, unless
           the SSL/TLS cerificate validation command is executed
           after the installation.  Please see the installation
           messages and the notes for Mac users at
           https://www.python.org/download

    2. Windows

       a. It can be very difficult to install simuPOP under Windows
          with a non-Anaconda distrubution, because only
          Anaconda's conda repository has a pre-compiled
          package.  For details please see the documentation at 
          http://simupop.sourceforge.net/Main/Download

       b. Under the Anaconda3 distribution, the commandline 
          scripts pgdriveneestimation.py and 
          pgdrivesimulation.py are not treated as executables.
          To use them you must run them as arguments to the python
          executable, using the full path to their location inside 
          the Anaconda3 installation.  For example, if your installation 
          path is, C:\Users\myname\Anaconda3, then, you can execute
          one of these command line scripts in an Anaconda
          promt window with this command:

           python C:\Users\myname\Anaconda3\Scripts <scriptname> <myarguments>
 
V. getting the manual and the example configuration files
---------------------------------------------------------
    
    1. If you have the "git" program, you can open a terminal,
       "cd" into a suitable directory, and clone the data branch with,
       the command:

           git clone -b data https://github.com/popgengui/agestrucne

    2. Instead of using git, you can download a zip archive of the 
       files at https://github.com/popgengui/agestrucne/tree/data.  
       You will see a green button on the right side of 
       the screen, offering a download.

    3. The files provided include the program manual, this README.md 
       file, and simulation configuration files that will get you
       started in the program pipeline (see the manual for details on how 
       to load and edit the configuration files).

VI. notes on OS distributions
-----------------------------
    1. Linux. The program has been run on Linux (ubuntu 16.04).

    2. Mac OS (OS X). The program has been run successfully on Mac OS (OS X), 
       v10.13 (High Sierra).

    3. Windows 10 and 8.1 (64-bit).  Note that on Windows, a persistent problem
       we have not solved is the inability of the program to remove files for
       some cleanup operations when processes do not finish (through error or
       user-cancellation). Thus you may have to remove output and temporary files
       manually when a run is cancelled or fails.

VII. dependencies
-----------------
    The following python packages, except pip and setuptools (which are provided by 
    almost all python distribution),  are automatically installed when you use
    the installation methods outlined in section III, as well as the 
    setup.py method (section VIII, below).

    1. pip and setuptools, the python package installation modules, included
       in nearly all recent python distributions.  If your 
       distribution does not include them, please see

       https://packaging.python.org/tutorials/installing-packages/.  

    2.  SimuPOP, a python package, hosted at
        http://SimuPop.sourceforge.net. Our python package scripts 
        are designed to install simuPOP automatically.  However,
        If your python 3 distribution is not Anaconda3, the installer
        will will have to compile the simuPOP package, which can take 
        a long time, and, in some cases can require extra steps.   
        See our installation instructions and notes in sections III 
        and IV. For troubleshooting failed simuPOP package compilation,
        the best source is the information at 
             
             http://simupop.sourceforge.net/Main/Download

    3. Below are the other required python packages, which should be 
       automatically installed when you use the pip installer, or the 
       "setup.py install" command (see section III and VIII).  
       These can also be installed one at a time through pip with the 
       command "pip install <package>", or, if you use 
       the Anaconda3 distribution of python, "conda install <package>".
        
        i.    numpy    

        ii.   matplotlib

        iii.  scipy
        
        iv.   future

        v.    psutil

        vi.   natsort

VIII. alternative installation methods
--------------------------------------

    1. Alternatives to the quickest installation methods (see above, section III).
        
        A. Installing without the "pip" installer: 

            ii. Clone (using the git program) or download the zip archive from 
                our master repository at, https://github.com/popgengui/agestrucne.

            iii. Use the setup.py file.

                 a. If under Widows, with an Anaconda3 python distrubution, open 
                    an Anaconda Prompt window, otherwise open a terminal.
                 b. use the "cd" command to move to the "agestrucne" directory 
                    containing the unzipped files, in particular looking for the 
                    "setup.py" file.  Type the following command, leading with "sudo"

                 c. If your python3 is an Anaconda3 distribution get the pre-compiled
                    simupop version with these commands:
                         conda config --add channels conda-forge
                         conda install simupop

                 d. Install the program and dependencies using
                    the setup.py:
                
                        python setup.py install
            
                    Note for Linux users, you may have to precede this
                    command with "sudo" and then provide your password.
                
        B. Using our program without installing it inside the python package directory.

           i.   Use pip to install the dependancy packages (see the dependancies 
                section above) 

           ii.  Download the master branch of our github repository.

                a. clone command:
                   git clone -b master https://github.com/popgengui/agestrucne

                b. Or get the zip archive at https://github.com/popgengui/agestrucne. 

           iii. Run the program directly using a terminal from the downloaded directories 
                using the applicable one of these methods: 

                a. In Windows, with an Anaconda distribution of python, open an 
                   Anaconda prompt and use cd, to move into the outermost "agestrucne" 
                   folder in the github repository you downloaded.  
                   Then, type these commands:                   

                    set PYTHONPATH=%PYTHONPATH%;%cd%
                    set NEPATH=%cd%\agestrucne
                
                   Now, you can cd into any folder you'd like and execute the
                   program with:
                    
                    python %NEPATH%\negui.py
                
                   You can also invoke the console-based
                   modules, pgdrivesimulation.py and pgdriveneestimation.py using
                    
                    python %NEPATH%\<module name>    
                
                b. In Windows with a non-Anaconda python distribution, use a DOS command
                   prompt and use the same procedure as above in (a).  However, just
                   typing "python" may fail if your distrubution does not add python
                   to your console's environmental variables.  If so, 
                   when you issue a python command, you may need to fully type the
                   path to your python executable, where ever your disribution places
                   it during the installation.    

                c. In linux or OSX, you can open a terminal and cd into the outermost
                   "agestrucne" directory of the programs github directories.
                   Then you can type the following command:
                    
                    export PYTHONPATH=$PYTHONPATH:$(pwd); NEPATH=$(pwd)/agestrucne     
                   
                    This terminal will then be able to execute the program interface
                    or the console-based modules from any directory by typing

                    python $NEPATH/<module name>    

                    where <module name> is negui.py, pgdrivesimulation.py, or
                    pgdriveneestimation.py

                d. Using this method PYTHONPATH and NEPATH variables will need to be 
                    set every time you open a new console to run the program. If you 
                    are conversant with setting environmental variables for your user 
                    environment, you can add the agestrucne path to the PYTHONPATH 
                    path, and NEPATH to your
                    environment so that they are available automatically when you open 
                    a console windows.
                
IX. starting the program
---------------------------

    1. If you installed the Anaconda3 python distribution,
       then, at an Anaconda prompt, start the program with the command,
       "agestrucnb"  

        A. Note that when you open the program, the current directory of your
           terminal will determine where the file-loading dialog will be initially
           set, as you locate, for example, a configuration file to load into
           the simulation interface.
    
    2. In addition to the "agestrucnb" command, there are two python scripts that offer 
       ways to run simulations and LDNe estimations from a terminal command prompt. 

        A. Command "pgdrivesimulation.py" performs simulations from the
           terminal, as specified in the user manual.

        B. Command "pgdriveneestimator.py" performs LDNe estimations
           from the terminal, as specified in the user manual.

X. using the program    
---------------------

    To run a simulation, calculate Nb estimates, or plot results, load one
    of the three interfaces by clicking "New" on the main menu.

    For details about running the different interfaces, see the
    user manual.
