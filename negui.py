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

def cleanup_gui( o_host ):
	o_host.cleanupAllTabs()
	#end if yes
	return
#end cleanup_gui


if __name__ == "__main__":

	WINDOW_MARGIN=0.20
	CONTAINER_PADDING=10


	ls_optional_args=[  "number of processes to use for replicate simulations" ]

	s_usage=pgut.do_usage_check( sys.argv, [], ls_optional_arg_descriptions=ls_optional_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	s_my_mod_path=os.path.abspath( __file__ )
	
	s_my_mod_dir=os.path.dirname( s_my_mod_path )

	if len( sys.argv ) == 2:
		i_total_simultaneous_processes=int( sys.argv[1] )
	else:
		i_total_simultaneous_processes=1
	#end if sys args exits

	s_default_life_tables = s_my_mod_dir + "/resources/*life.table.info"
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
	o_master.title( "Age Structure Ne" )	
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
