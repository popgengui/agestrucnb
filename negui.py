#!/usr/bin/env python

'''
Description

Provisional driver for the negui program
'''

__filename__ ="negui.py"
__date__ = "20160427"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
from Tkinter import *
from ttk import *
import glob

#currently local modules
import pgutilities as pgut
import pgmenubuilder as pgmb
import pgguisimupop as pggs
##### temp rem out to try new class
#FrameContainerScrolled
#from pgguiutilities import FrameContainerVScroll
from pgguiutilities import FrameContainerScrolled


def mymain( s_glob_for_config_files ):
	
	WINDOW_MARGIN=0.20
	CONTAINER_PADDING=10

	s_progdir="/home/ted/documents/source_code/python/negui"
	ls_rfiles=glob.glob( s_glob_for_config_files )
	s_menu_config=s_progdir + "/resources/menu.config.txt" 
	s_param_name_file="resources/simupop.param.names"

	o_master=Tk()

	o_nb_simupop=Notebook( o_master )

	o_nb_simupop.grid( row=0 )

	o_container=Frame( o_nb_simupop, padding=CONTAINER_PADDING )

	o_canvas=Canvas( o_container )

	o_pgg=pggs.PGGuiSimuPop( o_container, ls_rfiles, s_param_name_file )

	o_menu=pgmb.PGMenuBuilder( s_menu_config, o_pgg, o_master )

	##### temp rem out to try new class FrameContainerSrolled,
	#meaht to behave exactly as the FrameContainerVScroll,
	#but add option to have horiz. scroll instead of vertical
	#by adding  optional i_scroll_direction=FrameContainerSrolled.SCROLLHORIZONTAL
	#defult is vertical scroll
	#o_scan=FrameContainerVScroll( o_container, o_pgg, o_canvas )
	o_scan=FrameContainerScrolled( o_container, o_pgg, o_canvas, 
			i_scroll_direction=FrameContainerScrolled.SCROLLVERTICAL)
	mytest=Text(o_master )

	o_nb_simupop.add( o_container, text='Simulation' )
	o_nb_simupop.add( mytest, text='Ne Estimation' )

	o_nb_simupop.grid_rowconfigure( 0, weight=1 )
	o_nb_simupop.grid_columnconfigure( 0, weight=1 )
	o_nb_simupop.grid( row=0, column=0, sticky=( N,W,S,E ))

	i_width=o_master.winfo_screenwidth()
	i_height=o_master.winfo_screenheight()

	i_geo_width=int( ( i_width/2 ) * ( 1 - WINDOW_MARGIN ) )
	i_geo_height=int( ( i_height/2 ) * ( 1 - WINDOW_MARGIN ) )

	o_master.geometry( str(  i_geo_width ) + "x" + str( i_geo_height ) )
	o_master.title( "Age Structure Ne" )	
	o_master.grid_rowconfigure( 0, weight=1 )
	o_master.grid_columnconfigure( 0, weight=1 )
	o_master.mainloop()

	return
#end mymain

if __name__ == "__main__":

	ls_required_args=[]

	ls_optional_args=[ "optional, quoted glob expression to fetch life table files " \
			+ "associated with your organism(s), " \
			+ "Default is \"resources/*life.table.info\"" ]

	DEFAULT_LIFE_TABLES="resources/*life.table.info"

	s_usage=pgut.do_usage_check( sys.argv, ls_required_args, b_multi_line_msg=True )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage

	i_num_args_required=0
	i_num_args_optional=1

	s_glob_for_config_files=DEFAULT_LIFE_TABLES

	if len( sys.argv ) > i_num_args_required + 1:
		s_glob_for_config_files=sys.argv[ 1 ]
	#end if user passed a glob for fetching life tables

	mymain( s_glob_for_config_files )

#end if main

