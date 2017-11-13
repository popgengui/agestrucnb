'''
Description
'''
__filename__ = "setup_environement.py"
__date__ = "20170103"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import os

USE_GUI_ERROR_MESSAGING=True
VARPYPATH="PYTHONPATH"
VARPATH="PATH"



if USE_GUI_ERROR_MESSAGING:
	try:
		from agestrucne.pgguiutilities import PGGUIErrorMessage as pgge
		from agestrucne.pgguiutilities import PGGUIInfoMessage as pggi
		from agestrucne.pgguiutilities import PGGUIWarningMessage as pggw
	except ImportError as oie:
		'''
		2017_03_26.  When I added the importatio of the above PGGUI modules
		into module pgopsimupop.py, in order to allow for GUI error messaging
		during the simulation runs (which run in a new python instance), I 
		received an import error when this module loaded.  Instead of aborting
		the session, I am issueing a warning, since this module does not use
		these classes, despite the importation.
		'''
		sys.stderr.write( "Warning, in setup_negui_environment.py, there was and import error "  \
							+ "when importing the PGGUI message classes.  The error message " \
							+ "is: " + str( oie ) + ".\n" )

		USE_GUI_ERROR_MESSAGING=False
	#end try ... except

#end if USE_GUI_ERROR_MESSAGING	


def looks_like_correct_program_directory( s_path ):
	'''
	A check that the arg s_path gives the correct one in which
	the negui program is installed.
	'''

	b_result_value=True

	s_msg=""

	'''
	A list of files whose presence
	we'll consider sufficient to infer
	the arg has the correct path to the
	full program installation.
	'''
	ls_filenames_indicating_correct_directory=[ \
										"negui.py",
										"pgguineestimator.py",
										"pgguisimupop.py",
										"pgguiutilities.py",
										"pghostnotebook.py",
										"pgutilities.py" ]

	b_path_exists=os.isdir( s_path )

	s_path_delimiter=os.sep

	if b_path_exists:
		for s_file in ls_filenames_indicating_correct_directory:
			s_path_and_file=os.path.sep.join( [ s_path, s_file ] )
			if not os.path.exists( s_path_and_file ):
				b_result_value=False
				s_msg="Looking for key program files, missing:, " \
												+ s_path_and_file + "."
				break
			#end if path does not exist, missing file
		#end for each file 
	else:
		b_result_value=False
		s_msg="Path, " + s_path + ", does not exist."
	#end if path exists else not

	return b_result_value, s_msg
#end looks_like_correct_program_directory


def resources_files_are_found( s_path ):
	'''
	We look for the correct resources 
	subdirectory, and then check for important
	resource files.
	'''

	RESOURCES_DIR_NAME="resources"

	ls_important_resource_files=[ \
				"lineregress.param.names",
				"neestimation.param.names",
				"simupop.param.names",
				"viz.param.names",
				"menu_main_interface.txt" ]
	s_msg=""
	b_result_value=True
	s_path_and_dir=os.path.sep.join( [ s_path, RESOURCES_DIR_NAME ] )	
	b_resources_dir_exits=os.isdir( s_path_and_dir )

	if b_resources_dir_exits:
		for s_file in ls_important_resource_files:
			s_path_and_file=os.path.sep.join( [ s_path_and_dir, s_file ] )
			if not os.path.exists( s_path_and_file ):
				s_msg="Looking for resource files, missing: " \
												+ s_path_and_file + "."
				b_result_value=False
				break
			#end if path does not exist
		#end for each file
	else:
		b_result_value=False
		s_msg="Looking for resource directory, path does not exist: " \
														+ s_path_and_dir \
														+ "."
	#end if resources dir exists, else not
			
	return
#end resources_files_are_found

def negui_dir_already_in_env():

	b_result_value=False

	b_pythonpath_var_exists=VARPYPATH in os.environ

	if b_pythonpath_var_exists:

		ls_python_paths = os.environ[ VARPYPATH ].split( os.pathsep ) 

		ls_program_directories=[]

		for s_dir in ls_python_paths:
			#We do not use the msg returned by this call.
			#We are only interested in whether the path
			#looks like an negui installation
			b_looks_like_program_dir, s_progdir_msg = \
						looks_like_correct_program_directory ( s_dir )
			if b_looks_like_program_dir:
				ls_program_directories.append( s_dir )
				b_result_value=True
			#end if the dir looks like an negui program directory
		#end for each pypath directory
		s_msg=os.sep.join( ls_program_directories )
	else:
		b_result_value=False
		s_msg="No pythonpath variable found"
	#end if we have a pythonpath variable else not

	return b_result_value, s_msg
#end negui_dir_already_in_env


def remove_any_negui_program_directories_from_pythonpath():

	'''
	Rebuilds the pythonpath environmental variable to 
	inlcude all current paths except those that look
	like negui program module directories (as evaluated
	above in def looks_like_correct_program_directory.

	Note that if the pythonpath environmental variable
	does not exist, this def simply returns.
	'''
	i_total_paths_removed = 0

	if VARPYPATH in os.environ:

		ls_python_paths = os.environ[ VARPYPATH ].split( os.pathsep ) 

		ls_paths_to_keep=[]

		for s_dir in ls_python_paths:
			#We are only interested in whether the path
			#looks like an negui installation
			b_looks_like_program_dir, s_progdir_msg = \
						looks_like_correct_program_directory ( s_dir )
			if not b_looks_like_program_dir:
				ls_paths_to_keep.append( s_dir )
			#end if not an negui program dir
		#end for each dir in python paths

		#Now we reset the python path env variable
		#with all of its current paths minus any
		#that hold the negui modules:
		s_new_pypath_var_value=os.pathsep.join( ls_paths_to_keep )

		os.environ[ VARPYPATH ]=s_new_pypath_var_value
	#end if there is a python path variable
	return
#end remove_any_negui_program_directories_in_pythonpath

def setup_environment( s_use_path=None ):
	'''
	We use this def to add to the PYTHONPATH var
	the correct path to the negui modules, which 
	are assumed to be complete and in one directory,
	with resrouces *param.names files and the main
	menu config file present in the resources sub
	directory.
	'''

	s_program_directory=os.path.dirname( os.path.abspath(__file__) )

	'''
	If the caller gave us a path, we use that instead
	of the directory in which this mod resides.
	'''
	if s_use_path is not None:
		s_program_directory=s_use_path
	#end if caller passed a directory name

	b_path_looks_like_program_dir, s_program_dir_msg = \
			looks_like_correct_program_directory( s_program_directory )

	if not b_path_looks_like_program_dir:
		s_msg="In module setup_negui_environment, " \
						+ "def setup_environment, " \
						+ "failed to find correct " \
						+ "program directory.  Message: " \
						+ s_program_dir_msg 
		if USE_GUI_ERROR_MESSAGING:
			pgge( None, s_msg )
		#end if use gui

		raise Exception( s_msg )
	#end if not path looks like program dir

	b_resources_found, s_resources_check_msg = \
			resources_files_are_found( s_program_directory )

	if not b_resources_found:
		s_msg="In module setup_negui_environment, " \
						+ "def setup_environment, " \
						+ "failed to find resources files " \
						+ "Message: " +  s_resources_check_msg 
		if USE_GUI_ERROR_MESSAGING:
			pgge( None, s_msg )
		#end if use gui messaging
		raise Exception( s_msg )
	#end if resources not found

	b_negui_already_in_path, s_negui_dir_present_msg = \
					negui_dir_already_in_env()

	if b_negui_already_in_path:
		s_msg="Warning: the program was inferred to already " \
						+ "exist in one or more paths: " \
						+ s_negui_dir_present_msg \
						+ "\nFor the current run the program used will be " \
						+ "the installation at, "  + s_program_directory
		if USE_GUI_ERROR_MESSAGING:
			pggw( None, s_msg )
		#end if use gui
		sys.stderr.write( s_msg + "\n" )

		#we want only the current installation to be used:
		remove_any_negui_program_directories_from_pythonpath()
	#end if we find the program already in one or more
	#pythonpath values

	#We add the current program directory to the pythonpath
	#environmental variable.
	s_new_pypath_value=os.pathsep.join( [ os.environ[ VARPYPATH ], s_program_directory ] )
	os.environ[ VARPYPATH ]=s_new_pypath_var_value
		
	return 
#end setup_environement

if __name__ == "__main__":
	pass
#end if main

