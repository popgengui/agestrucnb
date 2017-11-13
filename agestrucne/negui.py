#!/usr/bin/env python

'''
Description

Driver for the negui program
'''
from __future__ import division

from future import standard_library
standard_library.install_aliases()
from past.utils import old_div
__filename__ ="negui.py"
__date__ = "20160427"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from tkinter import *
from tkinter.ttk import *

import os
import glob
import atexit

import agestrucne.setup_negui_environment as sne
import agestrucne.pghostnotebook as pgn
import agestrucne.pgutilities as pgut
from agestrucne.pgguiutilities import PGGUIYesNoMessage
from agestrucne.pgguiutilities import PGGUIErrorMessage
from agestrucne.pgguiutilities import PGGUIWarningMessage

PARAM_NAME_FILES=[ "simupop.param.names", "neestimation.param.names", "viz.param.names" ]
PARAM_FILE_KEYS_BY_FILE_NAME = { "simupop.param.names":"sim", 
									"neestimation.param.names":"ne", 
										"viz.param.names":"viz" }

def cleanup_gui( o_host ):
	o_host.cleanupAllTabs()
	#end if yes
	return
#end cleanup_gui

def confirm_resources( s_life_table_glob, s_menu_config, s_param_name_file_dir ):

	ls_msgs=[]

	b_found_life_tables=False
	b_found_menu_config=False
	b_found_param_names_files=False

	ls_lifetables=glob.glob( s_life_table_glob )
	
	if len( ls_lifetables ) > 0 :
		b_found_life_tables=True
	else:
		ls_msgs.append( "No life table files found." )
	#end if at least one life table

	if os.path.exists( s_menu_config ):
		b_found_menu_config=True
	else:
		ls_msgs.append( "No menu configuration file found." )
	#end if menu config file exists

	i_num_param_files=len( PARAM_NAME_FILES )

	if os.path.exists( s_param_name_file_dir ):
		i_number_found=0
		for s_param_file in PARAM_NAME_FILES:
			s_path_to_this_file=os.sep.join( [ s_param_name_file_dir, s_param_file ] )
			if os.path.exists( s_path_to_this_file ):
				i_number_found+=1
			else:
				ls_msgs.append( "Paramater names file, " + s_param_file + ", not found." )
			#end if path exists
		#end for each param names file prefix

		if i_number_found == i_num_param_files:
			b_found_param_names_files=True
		#end if found at least the expected param files		
	else:
		ls_msgs.append( "No paramater name files found." )
	#end if param name file path exists		
			
	return { "life_tables":b_found_life_tables,
					"menu_file": b_found_menu_config,
					"param_name_files":b_found_param_names_files,
					"msgs":ls_msgs }
#end confirm_resources

def get_param_file_names( s_param_name_file_dir ):
	ds_param_file_names={}

	for s_filename in PARAM_NAME_FILES:
		s_full_path=os.sep.join( [ s_param_name_file_dir, s_filename ] )
		ds_param_file_names[ PARAM_FILE_KEYS_BY_FILE_NAME[ s_filename ] ] = s_full_path
	#end for each file name

	return ds_param_file_names
#end get_param_file_names

def negui_main():

	'''
	Note, 2016_12_29: I removed all optional arguments for negui.py, by now
	unnecessary.  The optional args were and int giving total processes (now
	defaulting to 1 process, and settable in the indivudual interfaces), and
	a default life table file, which I've discarded in favor of always loading
	all life tables.
	'''

	WINDOW_MARGIN=0.20
	CONTAINER_PADDING=10
	
	s_my_mod_path=os.path.abspath( __file__ )
	
	s_my_mod_dir=os.path.dirname( s_my_mod_path )

	i_total_simultaneous_processes=1

	s_default_life_tables = s_my_mod_dir + "/resources/*life.table.info"
	s_menu_config=s_my_mod_dir + "/resources/menu_main_interface.txt" 
	s_param_name_file_dir=s_my_mod_dir + "/resources"

	db_found_files=confirm_resources( s_default_life_tables, 
												s_menu_config, 
												s_param_name_file_dir )

	#The program can't run without these files:
	if not ( db_found_files[ "menu_file" ] and db_found_files[ "param_name_files" ] ):
		s_msg="In negui, def negui_main, " \
				+ "there were resource files not found: " \
				+ "\n".join( db_found_files[ "msgs" ] )
		
		PGGUIErrorMessage( None, s_msg )
		raise Exception( s_msg )
	#end if required file not found

	'''
	The program can run without life table files loaded,
	but we'll send a warning to the console that all
	needed params need to be supplied by the config file.
	'''
	if not db_found_files[ "life_tables" ]:
		s_msg="In negui, def negui_main, " \
						+ "warning: " \
						+ "\n".join( db_found_files[ "msgs" ]  )

		PGGUIWarningMessage( None, s_msg )
		sys.stderr.write( s_msg + "\n" )

		s_default_life_tables=None
	#end if param names

	ds_param_file_names=get_param_file_names( s_param_name_file_dir )

	if pgut.is_windows_platform():
		if s_default_life_tables is not None:
			s_default_life_tables=pgut.fix_windows_path( s_default_life_tables )
		#end if life table files exist
		s_menu_config=pgut.fix_windows_path( s_menu_config )

		for s_filekey in ds_param_file_names:
			ds_param_file_names[ s_filekey ] = \
					pgut.fix_windows_path( \
							ds_param_file_names[ s_filekey ] )
		#end for each param file
	#end if windows, fix paths

	o_master=Tk()

	i_width=o_master.winfo_screenwidth()
	i_height=o_master.winfo_screenheight()

	i_geo_width=int( ( old_div(i_width,2) ) * ( 1 - WINDOW_MARGIN ) )
	i_geo_height=int( ( old_div(i_height,2) ) * ( 1 - WINDOW_MARGIN ) )

	o_host=pgn.PGHostNotebook( o_master, 
			s_menu_config, 
			ds_param_file_names[ "sim" ], 
			ds_param_file_names[ "ne" ], 
			ds_param_file_names[ "viz" ], 
			s_glob_life_tables=s_default_life_tables,
			i_max_process_total=i_total_simultaneous_processes )

	o_host.grid( row=0 )
	o_host.grid_rowconfigure( 0, weight=1 )
	o_host.grid_columnconfigure( 0, weight=1 )
	o_host.grid( row=0, column=0, sticky=( N,W,S,E ))

	o_master.geometry( str(  i_geo_width ) + "x" + str( i_geo_height ) )
	o_master.title( "Age Structure Nb" )	
	o_master.grid_rowconfigure( 0, weight=1 )
	o_master.grid_columnconfigure( 0, weight=1 )

	atexit.register( cleanup_gui, o_host )


	def ask_before_exit():
		s_msg="Exiting will kill any unfinished analyses " \
				+ "and remove their output files.  Exit anyway?"

		o_mbox=PGGUIYesNoMessage( None, s_msg )

		s_answer=o_mbox.value

		if s_answer == True:
			o_master.destroy()
		#end if do exit
	#end ask_before_exit
	
	o_master.protocol( "WM_DELETE_WINDOW", ask_before_exit )

	o_master.mainloop()

	return
#end def negui_main

if __name__ == "__main__":
	
	negui_main()	

#end if __main__
