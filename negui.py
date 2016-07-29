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
import pghostnotebook as pgn
import pgutilities as pgu


if __name__ == "__main__":

	WINDOW_MARGIN=0.20
	CONTAINER_PADDING=10

	ls_args=[ "path to directory containing life table files (*life.table.info)", 
			"number of processes to use for replicate simulations" ]

	s_usage=pgu.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	s_resource_directory=sys.argv[1]
	i_total_simultaneous_processes=int( sys.argv[2] )

	s_default_life_tables=s_resource_directory + "/*life.table.info"
	s_menu_config=s_resource_directory + "/menu_main_interface.txt" 
	s_param_name_file=s_resource_directory + "/simupop.param.names"

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
	o_master.mainloop()

	o_host.addPGGuiSimupop( i_container_padding=CONTAINER_PADDING )

#end if __main__
