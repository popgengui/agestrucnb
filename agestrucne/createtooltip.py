'''
Description
This code was copied from 
https://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
tk_ToolTip_class101.py
gives a Tkinter widget a tooltip as the mouse is above the widget
tested with Python27 and Python34  by  vegaseat  09sep2014
'''

from future import standard_library
standard_library.install_aliases()
from builtins import object
from sys import platform

__filename__ = "tooltip.py"
__date__ = "20160605"
__author__ = " vegaseat on DANIWEB, https://www.daniweb.com/members/19440/vegaseat"

#For special treatement of this widget in python
#(see def enter):
OSX_NAME_ACCORDING_TO_PYTHON="darwin"

try:
	# for Python2
	import tkinter as tk
except ImportError:
	# for Python3
	import tkinter as tk

'''
	Mod level def added 2016_10_04, for tool tip text read 
	in from param.names files (see class PGParamSet ), 
	because when read in from PGParamSet objects,
	newlines are not properly read, this def inserts 
	newlines in place of the s_delim character.
'''
def insertNewlines( s_text, s_delim="~~", s_newline="\n" ):
	
	ls_splits=s_text.split( s_delim )
	
	s_with_newlines=s_newline.join( ls_splits )

	return s_with_newlines
#def insertNewlines


class CreateToolTip(object):
	'''
	Creates a tooltip for a given widget.
	This code was copied from 
	https://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
	tk_ToolTip_class101.py
	gives a Tkinter widget a tooltip as the mouse is above the widget
	tested with Python27 and Python34  by  vegaseat  09sep2014

	'''
	def __init__(self, widget, text='widget info', i_font_size=10 ):
		'''
		Ted added, in case close gets called before enter,
		we'll have tw inditialzed to None.
		'''
		self.tw=None
		self.widget = widget
		self.text = text
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.close)
		'''
		Trying to fix bug in which tooltop persists
		permanently.
		'''
		self.widget.bind( "<FocusOut>", self.close)
		self.font_size=i_font_size
		self.using_osx=False

		'''
		Ted added 20180225, to treat use of this class in OSX
		differently (see rems in def enter).
		'''
		if platform == OSX_NAME_ACCORDING_TO_PYTHON:
		    self.using_osx=True
		#end if on OS X

	#end __init__

	def enter(self, event=None):

		'''
		Code added 2016_10_31, setting the tw member 
		to None in __init__ (see above), then always 
		testing it before recreating it, seems to have
		resolved a bug, seemingly only associated with
		comboboxes and very rarely with text boxes,
		via my KeyVal objects, in which the tooltip
		window was created but never closed.  This
		was reliably invoked by using the keyboard
		to update a combobox, while the mouse was still
		over the control. On th ekeyboard selection, the
		tooltip windows would appear and persist, while
		new ones would appear over it.  This management
		and testing of the tw member seems to have solved
		it.
		'''
		if self.tw is None:

			'''
			I added 2016_10_31
			constants used below,
			instead of literals,
			'''	
			PADX=25
			PADY=20

			x = y = 0
			x, y, cx, cy = self.widget.bbox("insert")
			x += self.widget.winfo_rootx() + PADX
			y += self.widget.winfo_rooty() + PADY
			# creates a toplevel window
			self.tw = tk.Toplevel(self.widget)
			# Leaves only the label and removes the app window
			self.tw.wm_overrideredirect(True)
			self.tw.wm_geometry("+%d+%d" % (x, y))

			'''
			OS X problem only -- when window decorators are removed
			via wm_overrideredirect() call, then OX X won't show the 
			window without help, one solution at least is this
			call to lift() see, https://stackoverflow.com/questions
			/44969674/remove-title-bar-in-python-3-tkinter-toplevel
			'''
			if self.using_osx:
				self.tw.lift()
			#end if we're on OS X, need this call to makee

			label = tk.Label(self.tw, text=self.text, justify='left',
						   background='yellow', relief='solid', borderwidth=1,
						   font=("times", self.font_size, "normal"))
			label.pack(ipadx=1)
		#end if self.tw is  None

	#end def enter

	def close(self, event=None):
		'''
		Code testing and assigning tw for/to None,
		added 2016_10_31 to more consistently manage 
		the tw member.  See the def "enter",
		for more details on some buggy
		behavior.
		'''
		if self.tw is not None:
			self.tw.destroy()
		#end if

		'''
		Consistent value for tw after call
		to close, no matter its previous one:
		'''
		self.tw = None
	#end def close
#end class CreateToolTip

# testing ...
if __name__ == '__main__':
	root = tk.Tk()
	btn1 = tk.Button(root, text="button 1")
	btn1.pack(padx=10, pady=5)
	button1_ttp = CreateToolTip(btn1, "mouse is over button 1")
	btn2 = tk.Button(root, text="button 2")
	btn2.pack(padx=10, pady=5)
	button2_ttp = CreateToolTip(btn2, "mouse is over button 2")
	root.mainloop()
#end if main




