'''
Description
Creates and managesthe ttk notebook frame
that hosts tabbed pages that each implement 
a PGOperation, such as doing simupop simulations,
or ne estimations
'''

__filename__ = "pghostnotebook.py"
__date__ = "20160623"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

NE_GUI_IS_IMPLEMENTED=True

VERBOSE=False

import sys
import os
from Tkinter import *
from ttk import *
import glob

#currently local modules
import pgutilities as pgut
import pgmenubuilder as pgmb
import pgguisimupop as pggs

if NE_GUI_IS_IMPLEMENTED:
	import pgguineestimator as pgne
#end if ne estimation gui is ready

from pgguiutilities import FrameContainerScrolled
from pgguiutilities import PGGUIYesNoMessage

class PGHostNotebook( Notebook ):
	'''
	Interface that uses tabbed windows to implement interfaces, one or more PGGuiSimupop and/or PGGuiNeEstimator
	objects.
	'''
	def __init__( self, o_parent, s_menu_config, 
					s_param_names_file_for_simulation, 
					s_glob_life_tables=None, i_max_process_total=1, 
					i_container_padding=10 ):
		'''
		params 
		o_parent, parent ttk.Frame object

		s_menu_config, file for PGMenuBuilder object, gives the main menu

		s_param_names_file_for_simulation, table file that lists the parameter names
		   as read into a PGInputSimuPop object

		s_glob_life_tables, glob expression used by PGOpSimuPop objects to load all life tables
			into memory

		'''
		Notebook.__init__( self, o_parent )
		self.__parent=o_parent
		self.__menu=pgmb.PGMenuBuilder( s_menu_config, self, o_parent )
		self.__param_names_file_for_simulations=s_param_names_file_for_simulation
		self.__tab_count=0
		self.__tab_children=[]
		self.__glob_life_tables=s_glob_life_tables
		self.__max_process_total=i_max_process_total
		self.__container_padding=i_container_padding
		self.__param_names_file_for_neestimation=s_param_names_file_for_simulation.replace( "simupop", "neestimation" )
		#we collect references to the pggui* objects created
		#and on delete, we clean up using these references:
		self.__my_gui_objects_by_tab_text={}
		return
	#end __init__

	def addPGGuiSimupop( self ):
		'''
		Add a tabbed frame that offers a PGGuiSimuPop interface
		'''
		o_container=Frame( self, padding=self.__container_padding )
		o_canvas=Canvas( o_container )

		o_pgg=pggs.PGGuiSimuPop( o_container, 
						self.__param_names_file_for_simulations, 
						self.__glob_life_tables, 
						i_total_processes_for_sims=self.__max_process_total )

		o_scan=FrameContainerScrolled( o_container, o_pgg, o_canvas, 
		i_scroll_direction=FrameContainerScrolled.SCROLLVERTICAL)

		s_tab_text="Simulation " + str( self.__tab_count )
		self.add( o_container, text=s_tab_text )
		self.__tab_children.append( o_container )
		self.__tab_count+=1
		self.select( o_container )
		self.__my_gui_objects_by_tab_text[ s_tab_text ] = o_pgg 
		return
	#end addPGGuiSimupop

	def addPGGuiNeEstimation( self ):
		'''
		Add a tabbed frame that offers a PGGuiSimuPop interface
		'''
		if NE_GUI_IS_IMPLEMENTED:
			o_container=Frame( self, padding=self.__container_padding )

			o_canvas=Canvas( o_container )

			o_pgg=pgne.PGGuiNeEstimator( o_container, 
							self.__param_names_file_for_neestimation )

			o_scan=FrameContainerScrolled( o_container, o_pgg, o_canvas, 
			i_scroll_direction=FrameContainerScrolled.SCROLLVERTICAL)

			s_tab_text="Ne Estimation " + str( self.__tab_count )
			self.add( o_container, text=s_tab_text )
			self.__tab_children.append( o_container )
			self.__tab_count+=1
			self.select( o_container )

			self.__my_gui_objects_by_tab_text[ s_tab_text ] = o_pgg 
		#end if NE_GUI_IS_IMPLEMENTED
		return

	#end addPGGuiNeEstimation

	def exitNotebook( self ):
		if self.__get_tab_count() > 0:
			s_msg="Exiting will kill any running analyses, " \
					+ "and remove their output. Exit anyway?" 

			o_msgbox=PGGUIYesNoMessage( self, s_msg )

			b_do_it=o_msgbox.value

			if b_do_it:
				self.cleanupAllTabs()
				self.__parent.destroy()
			#end if answer is yes
		else:
			self.__parent.destroy()
		#end if we have at least 1 tab then ask, else just destroy
		return
	#end exitNotebook

	def __get_tab_count( self ):
		return len( self.tabs() )
	#end __get_tab_count

	def removeCurrentTab( self ):
		if self.__get_tab_count() > 0:
			s_msg="If you're currently running a program in this tab, " \
					"closing it will kill the run and remove its output files. " \
					"Exit anyway?"

			o_msgbox=PGGUIYesNoMessage( self, s_msg )

			b_do_it=o_msgbox.value

			if b_do_it:
				i_tab_index=self.index( "current" )
				s_text_this_tab = self.tab( "current" , option="text"	 )
				
				if VERBOSE:
					print( "removing gui with tab text: " + s_text_this_tab )
				#end if VERBOSE

				o_gui_in_this_tab=self.__my_gui_objects_by_tab_text[ s_text_this_tab ]
				o_gui_in_this_tab.cleanup()
				self.forget(  "current" )

			#end if answer is yes
		#end if we have at least one tab

		return
	#end __close_current_tab

#	As of 2016_08_11, this def is not yet implemented 
#   correctly -- need to add cleanup

#
#	def removeTab( self, i_tab_index ):
#		if self.__get_tab_count() > 0:
#			o_msgbox=PGGUIYesNoMessage( self, "Are you sure you want to close " \
#					+ "this tab and any modelling program runs in progress?" )
#			b_do_it=o_msgbox.value
#
#			if b_do_it:
#				self.remove(self.__tab_children[ i_tab_index - 1 ] )
#			#end if answer is yes
#		#end if we have at least one tab
#		return
#	#end removeTab

	def removeAllTabs( self ):
		if self.__get_tab_count() > 0:
			o_msgbox=PGGUIYesNoMessage( self, "Are you sure you want to close all tabs " \
					+ "and kill all currently running modelling programs?" )
			b_do_it=o_msgbox.value

			if b_do_it:
				while len( self.tabs() ) > 0:
					self.forget( self.tabs()[ 0 ] )
				#end while tabs exist
				self.cleanupAllTabs()
			#end if answer is do it

		#end if we have at least one tab
	#end removeAllTabs


	def cleanupAllTabs( self ):
		for o_gui in self.__my_gui_objects_by_tab_text.values():
			if o_gui is not None:
				if VERBOSE: 
					print ( "cleaning up running operations in gui: " + str ( o_gui ) )
				#end if verbose
				o_gui.cleanup()
			#end if gui object exists, cleanup
		#end for each gui
	#end cleanupAllTabs

#end class PGHostNotebook

if __name__ == "__main__":
	
	WINDOW_MARGIN=0.20
	CONTAINER_PADDING=10

	DEFAULT_LIFE_TABLES="resources/*life.table.info"
	s_progdir="/home/ted/documents/source_code/python/negui"
	s_menu_config=s_progdir + "/resources/menu_main_interface.txt" 
	s_param_name_file="resources/simupop.param.names"

	o_master=Tk()

	i_width=o_master.winfo_screenwidth()
	i_height=o_master.winfo_screenheight()


	f_width_proportion=0.75
	f_height_proportion=0.5

	i_geo_width=int( ( i_width * f_width_proportion ) * ( 1 - WINDOW_MARGIN ) )
	i_geo_height=int( ( i_height * f_height_proportion ) * ( 1 - WINDOW_MARGIN ) )


	o_host=PGHostNotebook( o_master, 
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


	o_host.addPGGuiSimupop()

#end if main

