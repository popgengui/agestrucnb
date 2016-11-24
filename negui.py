#!/usr/bin/env python

'''
Description

Provisional driver for the negui program
'''

__filename__ ="negui.py"
__date__ = "20160427"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from Tkinter import *
from ttk import *
import sys
import os
import pghostnotebook as pgn
import pgutilities as pgut
import atexit
from pgguiutilities import PGGUIYesNoMessage
from pgguiutilities import PGGUIErrorMessage

def cleanup_gui( o_host ):
	o_host.cleanupAllTabs()
	#end if yes
	return
#end cleanup_gui

if __name__ == "__main__":

	import argparse as ap

	WINDOW_MARGIN=0.20
	CONTAINER_PADDING=10


	LS_FLAGS_SHORT_OPTIONAL=[ "-p", "-l" ]
	LS_FLAGS_LONG_OPTIONAL=[ "--processes", "--lifetable" ]

	s_help_processes_option="Number of processes to use in the simulation (1 used per replicate, one process " \
							+ "used if not supplied)"
	s_help_lifetable_option="life table file or pattern to match multiple life table files (use quotes). " \
							+ "If not supplied, all life table files in the " \
							+ "\"resources\" directory, " \
							+ "matching pattern, *life table info, will be loaded, " \
							+ "and the life table file with its model (species) value " \
							+ "matching the config file \"model\" (species) value will be used."

	LS_ARGS_HELP_OPTIONAL=[ s_help_processes_option , s_help_lifetable_option ]


	o_parser=ap.ArgumentParser()


	i_total_options=len( LS_FLAGS_SHORT_OPTIONAL )


	for idx in range( i_total_options ):
		o_parser.add_argument( \
				LS_FLAGS_SHORT_OPTIONAL[ idx ],
				LS_FLAGS_LONG_OPTIONAL[ idx ],
				help=LS_ARGS_HELP_OPTIONAL[ idx ],
				required=False )
	#end for each optional arg

	o_args=o_parser.parse_args()

	s_my_mod_path=os.path.abspath( __file__ )
	
	s_my_mod_dir=os.path.dirname( s_my_mod_path )

	i_total_simultaneous_processes=1

	if o_args.processes is not None:
		i_total_simultaneous_processes=int( o_args.processes  )
	#end if sys args exits

	s_default_life_tables = s_my_mod_dir + "/resources/*life.table.info"

	if o_args.lifetable is not None:
		s_default_life_tables=o_args.lifetable
	#end iw optional life table file entered

	s_menu_config=s_my_mod_dir + "/resources/menu_main_interface.txt" 
	s_param_name_file=s_my_mod_dir + "/resources/simupop.param.names"


	if pgut.is_windows_platform():
		s_default_life_tables=pgut.fix_windows_path( s_default_life_tables )
		s_menu_config=pgut.fix_windows_path( s_menu_config )
		s_param_name_file=pgut.fix_windows_path( s_param_name_file )
	#end if windows, fix paths

	o_master=Tk()

	i_width=o_master.winfo_screenwidth()
	i_height=o_master.winfo_screenheight()

	i_geo_width=int( ( i_width/2 ) * ( 1 - WINDOW_MARGIN ) )
	i_geo_height=int( ( i_height/2 ) * ( 1 - WINDOW_MARGIN ) )

	o_host=pgn.PGHostNotebook( o_master, 
			s_menu_config, 
			s_param_name_file, 
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

#end if __main__
