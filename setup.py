'''
Description
'''
__filename__ = "setup.py"
__date__ = "20171105"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"


from setuptools import setup, find_packages

setup(
    name = 'agestrucne',
    packages = [ 'agestrucne', 'agestrucne/asnviz' ],
    version = '0.1.10',     
	license = 'AGPLv3',
	description = "GUI and command line program for simulating populations, " \
				+  "estimating Nb and Ne using LDNe, and vizualizing the results.",
    author = 'several people',
    author_email = 'agestrucne@gmail.com',
	url = '',
    download_url = 'https://github.com/popgengui/agestrucne/archive/v0.0.0a.tar.gz',
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

