'''
Description
Class objects in this module are TKinter=based
helper objects, with no PG specific function.
'''
from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
from past.utils import old_div
__filename__ = "pgguiutilities.py"
__date__ = "20160427"
__author__ = "Ted Cosart<ted.cosart@umontana.edu and " \
				+ "Fredrik Lundh for the Autoscrollbar class (see below)"
from tkinter import *
from tkinter.ttk import *
import createtooltip as ctt
import sys
import tkinter.messagebox
import pgutilities as pgut

try:
	import tkSimpleDialog as TKSimp
except ImportError as ie:
	import tkinter.simpledialog as TKSimp
#end try...

'''
Fred Lundh's code from
http://effbot.org/zone/tkinter-autoscrollbar.htm
'''
class FredLundhsAutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")
#end class FredLundhsAutoScrollbar

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

		if self.__scroll_direction==FrameContainerScrolled.SCROLLVERTICAL:
			o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=VERTICAL )
			self.__canvas.config( yscrollcommand=o_scroll.set )
			o_scroll.config( command=self.__canvas.yview )
			o_scroll.grid( row=0, column=2, sticky=( N, S ) )

		elif self.__scroll_direction==FrameContainerScrolled.SCROLLHORIZONTAL:
			o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=HORIZONTAL )
			self.__canvas.config( xscrollcommand=o_scroll.set )
			o_scroll.config( command=self.__canvas.xview )
			o_scroll.grid( row=2, column=0, sticky=( W, E ) )

		else:
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

		if self.__scroll_direction == FrameContainerScrolled.SCROLLVERTICAL:
			i_width_canvas=self.__canvas.winfo_width()
			self.__canvas.itemconfigure( self.__child_id, width=i_width_canvas )
		elif self.__scroll_direction == FrameContainerScrolled.SCROLLHORIZONTAL:
			i_height_canvas=self.__canvas.winfo_height()
			self.__canvas.itemconfigure( self.__child_id, height=i_height_canvas )
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

class FrameContainerVScroll( object ):
	'''
	Description
	Objects are arrangements of two Frames and a 
	Canvas, such that one frame contains the 
	canvas and 2nd frame, and the 2nd frame 
	is vertically scrollable.

	Note that this is not a Tkinter object, but
	simply accomplishes the arragnement. 

	Note that this uses Fred Lundh's AutoScrollbar class
	(from http://effbot.org/zone/tkinter-autoscrollbar.htm)
	and depends on using only the grid geometry manager to place
	the scrollbar.
	'''

	def __init__( self, o_parent_frame, o_child_frame, o_canvas  ):
		#need the top level window for the menu:
		self.__parent_frame=o_parent_frame
		self.__child_frame=o_child_frame
		self.__canvas=o_canvas
		self.__setup()
		return
	#end __init__

	def __setup( self ):

		self.__child_id=self.__canvas.create_window( 0,0,anchor=NW, window=self.__child_frame )

		o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=VERTICAL )

		self.__canvas.config( yscrollcommand=o_scroll.set )

		o_scroll.config( command=self.__canvas.yview )

		o_scroll.grid( row=0, column=2, sticky=( N, S ) )

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

		i_width_canvas=self.__canvas.winfo_width()

		self.__canvas.itemconfigure( self.__child_id, width=i_width_canvas )
		return
	#end __on_configure_child
		
#end class FrameContainerVScroll

class PGGUIErrorMessage( object ):
	def __init__( self, o_parent=None, s_message="Unknown Error" ):
		root=None
		if o_parent is None:
			root=Tk()
			root.withdraw()
			tkinter.messagebox.showerror( title="Error", message=s_message )
		else:
			tkinter.messagebox.showerror(  parent=o_parent, title="Error", message=s_message )
		#end if no parent, then make a parent and hide it, else just invode messagebox

		if root is not None:
			root.destroy()
		#end if root was made

		return
	#end __init__
#End class PGGUIErrorMessage

class PGGUIWarningMessage( object ):
	def __init__( self, o_parent, s_message ):
		root=None
		if o_parent is None:
			root=Tk()
			root.withdraw()
			tkinter.messagebox.showinfo( title="Warning", message=s_message, icon=tkinter.messagebox.WARNING )
		else:
			tkinter.messagebox.showinfo(  parent=o_parent, title="Warning", message=s_message, icon=tkinter.messagebox.WARNING )
		#and if no parent

		if root is not None:
			root.destroy()
		#end if root was made

		return
	#end __init__
#End class PGGUIWarningMessage

class PGGUIInfoMessage( object ):
	def __init__( self, o_parent, s_message ):
		root=None
		if o_parent is None:
			root=Tk()
			root.withdraw()
			tkinter.messagebox.showinfo( title="Info", message=s_message, icon=tkinter.messagebox.INFO )
		else:
			tkinter.messagebox.showinfo(  parent=o_parent, title="Info", message=s_message, icon=tkinter.messagebox.INFO )
		#end if no parent, then make a parent and hide it, else just invode messagebox

		if root is not None:
			root.destroy()
		#end if root was made

		return
	#end __init__
#End class PGGUIInfoMessage

class PGGUIMessageWaitForResultsAndActionOnCancel( TKSimp.Dialog ):

	AFTERTIME=5
	MAX_ELLIPSES=15

	def __init__( self, o_parent, s_message="", s_title="Info", 
									def_boolean_signaling_finish=None,
									def_on_cancel=None ):

		if o_parent is None:
			s_msg="In PGGUIMessageWaitForResultsAndActionOnCancel instance, " \
							+ "def __init__, " \
							+ "param o_parent must be non-None."
			raise Exception( s_msg )
		#end if o_parent is None

		#IF these are not assigned before we instantiate
		#the parent, then they will not exist for the parent
		#calls to defs "body" and "cancel":
		self.__parent=o_parent
		self.__def_on_cancel=def_on_cancel
		self.__label_text=s_message
		self.__title=s_title
		self.__def_bool_is_finished=def_boolean_signaling_finish
		self.__myc=PGGUIMessageWaitForResultsAndActionOnCancel
		self.__parent_init( o_parent, s_title )
	#end __init__

	def __parent_init( self,  parent, title ):	

		'''
		This is the code for the __init__ of the
		parent class (from http://effbot.org/tkinterbook/tkinter-dialog-windows.htm)
		with an "after()" call inserted prior to window_wait(), in order to allow
		the self-destruction after the child class' attribure __def_bool_is_finished
		returns True.

		I also made the default geometry bigger.
		'''
		XPACKPAD=150
		YPACKPAD=0o50
		XGEOPAD=350
		YGEOPAD=150

		Toplevel.__init__(self, parent)
		self.transient(parent)

		if title:
			self.title(title)

		self.parent = parent

		self.result = None

		body = Frame(self)
		self.initial_focus = self.body(body)
		body.pack(padx=XPACKPAD, pady=YPACKPAD)

		self.buttonbox()

		self.grab_set()

		if not self.initial_focus:
			self.initial_focus = self

		self.protocol("WM_DELETE_WINDOW", self.cancel)

		self.geometry("+%d+%d" % (parent.winfo_rootx()+150,
								  parent.winfo_rooty()+150))
		
		self.initial_focus.focus_set()
		
		self.after( self.__myc.AFTERTIME, self.__check_if_finished )

		self.wait_window(self)

	#end __parent_init

	def __update_label( self ):
		return
	#ene __update_label

	def __check_if_finished( self ):
		if self.__def_bool_is_finished is not None:
			if self.__def_bool_is_finished() == True:
				if self.parent is not None:
					self.parent.focus_set()
				#end if parent exists
				self.destroy();
			else:
				'''
				I need to implement the label update def
				'''
				self.__update_label()
				self.after( self.__myc.AFTERTIME, self.__check_if_finished )
			#end if finished, destroy self
		#end if we have a def that returns True or False
		return
	#end __check_if_finished

	def body( self, master ):
		'''
		Overrides the emtpy def of parent.  The parent class creates the frame
		in its __init__ and then passes to this def as param master.
		'''
		self.__label=Label( master, text=self.__label_text )
		self.__label.grid( row=0, padx=5, sticky=W )

		return

	#end bocy

	def buttonbox(self):

		'''
		Overrides parent's add standard button box.
		Parent class has an OK and a Cancel,
		We just want Cancel. We also skip
		the parent's "bind" of cancel to escapte key.

		'''

		box = Frame(self)

		w = Button(box, text="Cancel", width=10, command=self.cancel)

		w.pack(side=LEFT, padx=5, pady=5)

		self.bind("<Return>", self.cancel )

		box.pack()

		return
	#end buttonbox
	
	def cancel(self, event=None):

		'''
		Overrides parent version.  This
		version calls the user-supplied def
		(in not None) before the focus_set
		and destroy of the parent's version.
 		'''

		#Call clients supplied def if available:
		if self.__def_on_cancel is not None:
			self.__def_on_cancel()
		#end if we have clients def to call

		# put focus back to the parent window
	
		if self.parent is not None:
			self.parent.focus_set()
		#end if parent exists

		self.destroy();
		return
	#end cancel

#end class PGGUIMessageWaitForResultsAndActionOnCancel

class PGGUIYesNoMessage( object ):
	def __init__( self, o_parent, s_message ):
		o_msgbox=tkinter.messagebox.askyesno( parent=o_parent, title="Info", message=s_message, icon=tkinter.messagebox.INFO )
		self.value=o_msgbox
		return
	#end __init__

	@property
	def user_response( self ):
		return self.value
	#end property user_response

#end class PGGUIYesNoMessage

class RightClickMenu( Menu ):

	def __init__( self, o_parent, ddefs_by_label={} ):

		Menu.__init__( self, o_parent, tearoff=0 )

		for s_label in ddefs_by_label:
			self.add_command( label=s_label, 
							command=ddefs_by_label[ s_label ] )
		#end for each label/command, add to menu

		o_parent.bind( "<Button-3>", self.__popup ) 

		return
	#end __init__

	def __popup( self, event ):
		print( "in popup" )
		self.post( event.x_root, event.y_root )
		return
	#end __popup
#end class RightClickMenu

def destroy_on_def_returning_true( o_object_to_destroy, def_that_returns_boolean ):
	#Blocks execution until def returns true
	pgut.return_when_def_is_true( def_that_returns_boolean, f_sleeptime_in_seconds=0.25 )
	o_object_to_destroy.destroy()
	return
#end destroy_on_def_returning_true

if __name__=="__main__":
#	import pgutilities as modut
#	import test_code.testdefs as td
#
#	ls_args=[ "test number" ]
#
#	s_usage=modut.do_usage_check( sys.argv, ls_args )
#
#	if s_usage:
#		print( s_usage )
#		sys.exit()
#	#end if usage
#	
#	s_test_number=sys.argv[ 1 ]
#
#	ddefs={ 1:td.testdef_pgguiutilities_1,
#			2:td.testdef_pgguiutilities_2 }
#	
#	ddefs[ int( s_test_number ) ] ( )
	myr=Tk()
	obox=PGGUIYesNoMessage( myr, "yes or no" )

	print( "answer: " + str( obox.user_response ) )
#end if  __main__

