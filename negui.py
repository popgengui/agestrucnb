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
import pghostnotebook as pgn


if __name__ == "__main__":

	WINDOW_MARGIN=0.20
	CONTAINER_PADDING=10

	DEFAULT_LIFE_TABLES="resources/*life.table.info"
	s_progdir="/home/ted/documents/source_code/python/negui"
	s_menu_config=s_progdir + "/resources/menu_main_interface.txt" 
	s_param_name_file="resources/simupop.param.names"
	i_use_this_many_procs=10

	o_master=Tk()

	i_width=o_master.winfo_screenwidth()
	i_height=o_master.winfo_screenheight()

	i_geo_width=int( ( i_width/2 ) * ( 1 - WINDOW_MARGIN ) )
	i_geo_height=int( ( i_height/2 ) * ( 1 - WINDOW_MARGIN ) )


	o_host=pgn.PGHostNotebook( o_master, 
			s_menu_config, 
			s_param_name_file, 
			s_glob_life_tables=DEFAULT_LIFE_TABLES,
			i_max_process_total=i_use_this_many_procs )

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
