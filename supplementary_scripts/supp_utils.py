'''
Description.  Defs to help
py scripts in this subdirectory
to run.  
'''
__filename__ = "supp_utils.py"
__date__ = "20170504"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os
import sys

def add_main_pg_dir_to_path():
	'''
	This def assumes that this module
	is in the main pg*py directory inside
	a subfolder called "supplementary_scripts"
	'''
	
	s_myloc=os.path.abspath( __file__ )
	s_mydir=os.path.dirname( s_myloc )
	s_mydir=s_mydir.replace( "supplementary_scripts", "" )
	sys.path.append( s_mydir )

	return
#end add_main_pg_dir_to_path

if __name__ == "__main__":
	pass
#end if main

