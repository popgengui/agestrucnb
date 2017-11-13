'''
Description
Creates and managesthe ttk notebook frame
that hosts tabbed pages that each implement 
a PGOperation, such as doing simupop simulations,
or ne estimations
'''
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
__filename__ = "pghostnotebook.py"
__date__ = "20160623"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

NE_GUI_IS_IMPLEMENTED=True

VERBOSE=False

from tkinter import *
from tkinter.ttk import *

import agestrucne.pgmenubuilder as pgmb

#These classes provide the interfaces, 
#each offered in the main "Add"
#menu.

##### temp rem out and replace
#for testing life plotting during sim
#import agestrucne.pgguisimupop as pggs
import agestrucne.pgguisimupop as pggs
##### end temp rem out

import agestrucne.pgguiviz as pggv

##### temp rem out and replace
#as above for testing embedded plotting
import agestrucne.pgguineestimator as pgne
#####

import agestrucne.pgneestimationboxplotinterface as pgbp
import agestrucne.pgneestimationregressplotinterface as pgrp

from agestrucne.pgframecontainerscrolled import FrameContainerScrolled
from agestrucne.pgguiutilities import PGGUIYesNoMessage
from agestrucne.pgutilities import get_cpu_count

class PGHostNotebook( Notebook ):
	'''
	Interface that uses tabbed windows to implement interfaces, one or more PGGuiSimupop and/or PGGuiNeEstimator
	objects.
	'''
	def __init__( self, 
						o_parent, 
						s_menu_config, 
						s_param_names_file_for_simulation, 
						s_param_names_file_for_neestimations, 
						s_param_names_file_for_viz, 
						s_glob_life_tables=None, 
						i_max_process_total=1, 
						i_container_padding=10 ):
		'''
		params 
		o_parent, parent ttk.Frame object

		s_menu_config, file for PGMenuBuilder object, gives the main menu

		s_param_names_file_for_simulation, table file that lists the parameter names 
		as read into a PGInputSimuPop object

		s_param_names_file_for_neestimations, table file that lists the parameter names 
		as required by the PGGuiNeEstimator object

		s_param_names_file_for_viz, table file that lists the parameter names 
		as required by the PGGuiViz object

		s_glob_life_tables, glob expression used by PGOpSimuPop objects to load all 
		life tables into memory, if none, pgguisimupop's attribute pginputsimupop 
		object tries to load params using config file only.

		'''
		Notebook.__init__( self, o_parent )
		self.__parent=o_parent
		self.__menu=pgmb.PGMenuBuilder( s_menu_config, self, o_parent )

		self.__param_names_file_for_simulations=s_param_names_file_for_simulation
		self.__param_names_file_for_neestimation=s_param_names_file_for_neestimations
		self.__param_names_file_for_viz=s_param_names_file_for_viz

		self.__tab_count=0
		self.__tab_children=[]
		self.__glob_life_tables=s_glob_life_tables
		self.__max_process_total=i_max_process_total
		self.__container_padding=i_container_padding
			
		#we collect references to the pggui* objects created
		#and on delete, we clean up using these references:
		self.__my_gui_objects_by_tab_text={}
		#This allows direct access to the rebindScrollwheel def
		#in the FrameContainerScrolled instance in each gui interface:
		self.__scrolled_frame_objects_by_tab_text={}

		self.bind( "<<NotebookTabChanged>>", self.__on_tab_change )
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
		self.__scrolled_frame_objects_by_tab_text[ s_tab_text ] = o_scan
		self.enable_traversal()
	#end addPGGuiSimupop

	def addPGGuiNeEstimation( self ):
		'''
		Add a tabbed frame that offers a PGGuiSimuPop interface
		'''

		o_container=Frame( self, padding=self.__container_padding )

		o_canvas=Canvas( o_container )

		'''
		2017_10_19.  We now default to half the 
		existing (logical) cores as the default setting
		for number of processes to use for 
		Ne estimations.  Note that before this
		update  the PGGuiNeEstimator was intitializing 
		its i_total_processes_for_est param with
		this object's self.__max_process_total, which
		is still used by the other interfaces.
		'''
		i_total_cpus=get_cpu_count()

		i_floor_half=int( i_total_cpus/2.0 )
		
		i_total_processes_for_est=\
				1 if i_floor_half <= 0 else i_floor_half

		o_pgg=pgne.PGGuiNeEstimator( o_container, 
						self.__param_names_file_for_neestimation,
						i_total_processes_for_est=i_total_processes_for_est )

		o_scan=FrameContainerScrolled( o_container, o_pgg, o_canvas, 
		i_scroll_direction=FrameContainerScrolled.SCROLLVERTICAL)

		s_tab_text="Nb Estimation " + str( self.__tab_count )

		self.add( o_container, text=s_tab_text )
		self.__tab_children.append( o_container )
		self.__tab_count+=1
		self.select( o_container )

		self.__my_gui_objects_by_tab_text[ s_tab_text ] = o_pgg 
		self.__scrolled_frame_objects_by_tab_text[ s_tab_text ] = o_scan

		return
	#end addPGGuiNeEstimation

	def addPGGuiViz( self ):
		'''
		2016_12_12
		Adds an interface to perform plotting programs on a table 
		of Ne estimations.
		'''
		
		o_container=Frame( self, padding=self.__container_padding )

		o_canvas=Canvas( o_container )

		'''
		2016_12_13
		Note that we load the param names file for ne estimation,
		as the PGGuiViz object filters the param names for the
		proper ones for the Viz functions.

		Also note that we do not allow more than a single process
		for plotting.
		'''
		o_pgg=pggv.PGGuiViz( o_container, 
						self.__param_names_file_for_viz,
						i_total_processes_for_viz=1 )

		o_scan=FrameContainerScrolled( o_container, o_pgg, o_canvas, 
		i_scroll_direction=FrameContainerScrolled.SCROLLVERTICAL)

		s_tab_text="Nb Vizualizations " + str( self.__tab_count )

		self.add( o_container, text=s_tab_text )
		self.__tab_children.append( o_container )
		self.__tab_count+=1
		self.select( o_container )

		self.__my_gui_objects_by_tab_text[ s_tab_text ] = o_pgg 
		self.__scrolled_frame_objects_by_tab_text[ s_tab_text ] = o_scan

		return
	#end addPGGuiViz

	def addPGNeBoxplot( self ):

		o_container=Frame( self, padding=self.__container_padding )

		o_canvas=Canvas( o_container )

		o_plot_master_frame=Frame( o_container)

		o_plot_master_frame.grid( row=0, column=0, sticky=( N,S,E,W ) )
		o_pgbp=pgbp.PGNeEstimationBoxplotInterface( o_plot_master_frame )
		

		o_scan=FrameContainerScrolled( o_container, o_plot_master_frame, o_canvas, 
			i_scroll_direction=FrameContainerScrolled.SCROLLBOTH )

		s_tab_text="Estimation Distribution Boxplots " + str( self.__tab_count )

		self.add( o_container, text=s_tab_text )
		self.__tab_children.append( o_container )
		self.__tab_count+=1
		self.select( o_container )

		self.__my_gui_objects_by_tab_text[ s_tab_text ] = o_pgbp 
		self.__scrolled_frame_objects_by_tab_text[ s_tab_text ] = o_scan

		return
	#end addPGNeBoxplot

	def addPGNeRegressPlot( self ):

		o_container=Frame( self, padding=self.__container_padding )

		o_canvas=Canvas( o_container )

		o_plot_master_frame=Frame( o_container)

		o_plot_master_frame.grid( row=0, column=0, sticky=( N,S,E,W ) )
		o_pgbp=pgrp.PGNeEstimationRegressplotInterface( o_plot_master_frame )
		

		o_scan=FrameContainerScrolled( o_container, o_plot_master_frame, o_canvas, 
			i_scroll_direction=FrameContainerScrolled.SCROLLBOTH )

		s_tab_text="Estimation Regression Plots " + str( self.__tab_count )

		self.add( o_container, text=s_tab_text )
		self.__tab_children.append( o_container )
		self.__tab_count+=1
		self.select( o_container )

		self.__my_gui_objects_by_tab_text[ s_tab_text ] = o_pgbp 
		self.__scrolled_frame_objects_by_tab_text[ s_tab_text ] = o_scan

		return
	#end addPGNeRegressPlot


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

	def __on_tab_change( self, event ):
		'''
		As of 2016_11_13, on tab change our only
		action is to rebind the mouse scrollwheel
		to the canvas inside the FrameContainerScrolled
		instance associated with each GUI interface.
		'''

		if self.index("end") > 0:
			
			s_text_this_tab=self.tab( "current", option="text" )
			self.__scrolled_frame_objects_by_tab_text[ s_text_this_tab ].rebindScrollwheel()
		#end if we have at least one tab

		return
	#end __on_tab_change

	def removeCurrentTab( self ):
		if self.__get_tab_count() > 0:
			s_msg="If you're currently running a program in this tab, " \
					"closing it will kill the run and remove its output files. " \
					"Exit anyway?"

			o_msgbox=PGGUIYesNoMessage( self, s_msg )

			b_do_it=o_msgbox.value

			if b_do_it:

				s_text_this_tab = self.tab( "current" , option="text" )
				
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
			#end if do it
		#end if we have at least one tab
		return
	#end removeAllTabs

	def cleanupAllTabs( self ):
		for o_gui in list(self.__my_gui_objects_by_tab_text.values()):
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
	'''
	For testing -- in normal operation, the class
	PGHostNotebook should be instantiiated by client 
	code (ex: negui.py).
	'''
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

	i_use_this_many_procs=1

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
	o_master.title( "Age Structure Nb" )	
	o_master.grid_rowconfigure( 0, weight=1 )
	o_master.grid_columnconfigure( 0, weight=1 )

	o_master.mainloop()

#	o_host.addPGGuiSimupop()

#end if main

