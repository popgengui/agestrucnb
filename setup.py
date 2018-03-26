'''
Description
'''
__filename__ = "setup.py"
__date__ = "20171105"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os

from setuptools import setup, find_packages

def get_version():

	PARAMNAME="progversion"
	PARAM_VAL_DELIMIT="="
	IDX_VAL=1
	STARTUP_INFO_LOC="/agestrucne/resources/startup.info"

	s_version="version.unknown"

	s_my_mod_path=os.path.abspath( __file__ )
	s_my_mod_dir=os.path.dirname( s_my_mod_path )

	s_startup_info_file=s_my_mod_dir + STARTUP_INFO_LOC

	if os.path.exists( s_startup_info_file ):
		o_file=open( s_startup_info_file )
		for s_line in o_file:
			if s_line.startswith( PARAMNAME ):
				s_version= s_line.strip().split( PARAM_VAL_DELIMIT )[ IDX_VAL ]
			#end if line starts with param name
		#end for each line in file
		o_file.close()
	#end if path exists
	return s_version
#end get_version

setup(
    name = 'agestrucne',
    packages = [ 'agestrucne', 'agestrucne/asnviz' ],
    version = get_version(),     
	license = 'AGPLv3',
	description = "GUI and command line program for simulating populations using simuPOP, " \
				+  "estimating Nb and Ne using LDNe, and vizualizing the results.",
    author = 'several people',
    author_email = 'agestrucne@gmail.com',
	url = '',
    download_url = '',
    keywords = ['population genetics', 'simuPOP', 'LDNe', 'AgeStructureNe'],
	classifiers = ['License :: OSI Approved :: GNU Affero General Public License v3' ],
	include_package_data=True,
	install_requires=[ "numpy",	
						"scipy", 
						"future", 
						"psutil", 
						"natsort", 
						'configparser;python_version=="2.7"', 
						'pyttk;python_version=="2.7"',
						'simupop;python_version>="3.0"' ],
	python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*,<=4',
	entry_points={ 'console_scripts': [ 'agestrucne=agestrucne.negui:negui_main' ] },
	scripts=[ 'agestrucne/pgdriveneestimator.py', 'agestrucne/pgdrivesimulation.py' ]
)

