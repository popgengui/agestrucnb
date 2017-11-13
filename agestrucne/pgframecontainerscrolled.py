'''
Description 

This class code was moved from
the pgguiutilities.py module into its own
module.
'''
from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object

from past.utils import old_div

from tkinter import *
from tkinter.ttk import *

import agestrucne.pgutilities as pgut

from agestrucne.pgguiutilities import FredLundhsAutoScrollbar

__filename__ = "pgframecontainerscrolled.py"
__date__ = "20170926"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class FrameContainerScrolled( object ):
	'''
	Description
	Objects are arrangements of two Frames and a 
	Canvas, such that one frame contains the 
	canvas and 2nd frame, and the 2nd frame 
	is scrollable, either vertically or horizontally 
	(but not yet both, as of Thu Jun  2 19:59:32 MDT 2016 )
	

	Note that this is not a Tkinter object, but
	simply accomplishes the arragnement. 

	Note that this uses Fred Lundh's AutoScrollbar class
	(from http://effbot.org/zone/tkinter-autoscrollbar.htm)
	and depends on using only the grid geometry manager to place
	the scrollbar.
	'''

	SCROLLVERTICAL=0
	SCROLLHORIZONTAL=1
	'''
	2017_09_13.  Add a horiz+vert scrolling option.
	'''
	SCROLLBOTH=2

	def __init__( self, o_parent_frame, o_child_frame, o_canvas, 
			i_scroll_direction=SCROLLVERTICAL ):
		#need the top level window for the menu:
		self.__parent_frame=o_parent_frame
		self.__child_frame=o_child_frame
		self.__canvas=o_canvas
		self.__scroll_direction=i_scroll_direction
		self.__setup()
		return
	#end __init__

	def __setup( self ):

		#as of Thu Jun  2 20:23:03 MDT 2016, horizontal scrolling is not yet working
		#correctly:
#		if self.__scroll_direction==FrameContainerScrolled.SCROLLHORIZONTAL:
#			s_msg="In pguitilities.FrameContainerScrolled object instance, " \
#					+ "horizontal scrolling is not yet implemented, " \
#					+ "please construct with " \
#					+ "i_scroll_direction=FrameContainerScrolled.SCROLLVERTICAL" 
#			raise Exception( s_msg )
#		#end if horizontal	

		o_scroll=None

		self.__child_id=self.__canvas.create_window( 0,0,anchor=NW, window=self.__child_frame )

		if self.__scroll_direction in [ FrameContainerScrolled.SCROLLVERTICAL, FrameContainerScrolled.SCROLLBOTH ]:
			o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=VERTICAL )
			self.__canvas.config( yscrollcommand=o_scroll.set )
			o_scroll.config( command=self.__canvas.yview )
			o_scroll.grid( row=0, column=2, sticky=( N, S ) )
		#end if we need a vertical scroll

		if self.__scroll_direction in [ FrameContainerScrolled.SCROLLHORIZONTAL, FrameContainerScrolled.SCROLLBOTH ]:
			o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=HORIZONTAL )
			self.__canvas.config( xscrollcommand=o_scroll.set )
			o_scroll.config( command=self.__canvas.xview )
			o_scroll.grid( row=2, column=0, sticky=( W, E ) )
		#end if we need a horizontal scroll

		if self.__scroll_direction not in [ FrameContainerScrolled.SCROLLVERTICAL, 
											FrameContainerScrolled.SCROLLHORIZONTAL,
											FrameContainerScrolled.SCROLLBOTH ]:
			s_msg="In pguitilities.FrameContainerScrolled object instance, " \
					+ "invalid value for scroll direction: " \
					+ str( self.__scroll_direction ) + "."
			raise Exception( s_msg )
		#end if scroll dir vert, else horiz, else except

		self.__canvas.grid( row=0, column=0, sticky=( N,S,E,W) )

		self.__canvas.grid_rowconfigure( 0, weight=1 )
		self.__canvas.grid_columnconfigure( 0, weight=1 )

		self.__canvas.grid_rowconfigure( 1, weight=1 )
		self.__canvas.grid_columnconfigure( 1, weight=1 )
			
		self.__parent_frame.grid_rowconfigure( 0, weight=1 )
		self.__parent_frame.grid_columnconfigure( 0, weight=1 )
	
		self.__child_frame.bind( '<Configure>', self.__on_configure_child )
		self.__canvas.bind( '<Configure>', self.__on_configure_canvas )

		self.__bind_canvas_to_scrollwheel()

		return
	#end __setup 

	def __bind_canvas_to_scrollwheel( self ):

		'''
		Platform dependant event name and handling.
		(See also, below, def __scrollCanvas).
		'''
		s_platform=pgut.get_platform()
		if s_platform==pgut.SYS_LINUX:
			self.__canvas.bind_all( '<4>', self.__scrollCanvas )
			self.__canvas.bind_all( '<5>', self.__scrollCanvas )
		elif s_platform==pgut.SYS_MAC or s_platform==pgut.SYS_WINDOWS:
			self.__canvas.bind_all( '<MouseWheel>', self.__scrollCanvas )
		#end if linux, else mac/win
		return
	#end __bind_canvas_to_scrollwheel

	def rebindScrollwheel(self):
		'''
		This def allows clients to rebind the mouse scrollwheel
		to this object's canvas.  This was necessitated by
		tab swithes in the pghostnotebook.py class object,
		which casue the mouse wheel to be bound to the latest
		tab, and "disconnects" it from all others, so that,
		returning to an older tab, gives an inteface without
		mouse wheel scrolling enabled.
		'''

		self.__bind_canvas_to_scrollwheel()
		return
	#end rebindScrollwheel

	def __on_configure_child( self, event ):
		
		#we need the scroll region and the canvas dims to 
		#always match the subframe dims.

		i_child_width, i_child_height=( self.__child_frame.winfo_reqwidth(), self.__child_frame.winfo_reqheight() )

		self.__canvas.config( scrollregion="0 0 %s %s" % ( i_child_width, i_child_height ) )
		self.__canvas.config( width=i_child_width )
		self.__canvas.config( height=i_child_height )

		return
	#end __on_configure_child

	def __on_configure_canvas( self, event ):
		#sync the child to canvas width only -- if you reset the height,
		#the lower part of the childframe is truncated when
		#scrolling down -- the scoll reveals nothing but bg:

		o_myc=FrameContainerScrolled

		i_width_canvas=self.__canvas.winfo_width()
		i_height_canvas=self.__canvas.winfo_height()

		if self.__scroll_direction in [ o_myc.SCROLLVERTICAL ]:
			self.__canvas.itemconfigure( self.__child_id, width=i_width_canvas )
		elif self.__scroll_direction in [ o_myc.SCROLLHORIZONTAL ]:
			self.__canvas.itemconfigure( self.__child_id, height=i_height_canvas )
		elif self.__scroll_direction in [ o_myc.SCROLLBOTH ]:
			#self.__canvas.itemconfigure( self.__child_id, width=i_width_canvas, 
			#													height=i_height_canvas )
			pass
		else:
			s_msg="In pguitilities.FrameContainerScrolled object instance, " \
					+ "invalid value for scroll direction: " \
					+ str( self.__scroll_direction ) + "."
			raise Exception( s_msg )
		#end if scroll vert, else horiz, else except 

		return
	#end __on_configure_child

	def __scrollCanvas( self, event ):
		'''
		Platform-dependant handling according to,
		http://stackoverflow.com/questions/17355902
					/python-tkinter-binding-mousewheel-to-scrollbar
		also, used the linux handling code from:
		https://mail.python.org/pipermail/tkinter-discuss
										/2006-June/000808.html.
		'''
		s_platform=pgut.get_platform()
		if s_platform == pgut.SYS_LINUX:
			if event.num == 4:
				self.__canvas.yview( 'scroll', -1, 'units' )
			elif event.num== 5:
				self.__canvas.yview( 'scroll', 1, 'units' )
			#end if event num is 4 else 5
		elif s_platform == pgut.SYS_MAC:
			self.__canvas.yview_scroll( old_div(event.delta,120) , 'units' )
		elif s_platform == pgut.SYS_WINDOWS:
			self.__canvas.yview_scroll( -1 * ( old_div(event.delta,120) ), 'units' )
		#end if linux, else mac, else windows
		return
#end class FrameContainerScrolled






if __name__ == "__main__":
	pass
#end if main

