'''
Description
This code was copied from 
https://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
tk_ToolTip_class101.py
gives a Tkinter widget a tooltip as the mouse is above the widget
tested with Python27 and Python34  by  vegaseat  09sep2014
'''

__filename__ = "tooltip.py"
__date__ = "20160605"
__author__ = " vegaseat on DANIWEB, https://www.daniweb.com/members/19440/vegaseat"

try:
	# for Python2
	import Tkinter as tk
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
		self.widget = widget
		self.text = text
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.close)
		self.font_size=i_font_size
	#end __init__

	def enter(self, event=None):
		x = y = 0
		x, y, cx, cy = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 20
		# creates a toplevel window
		self.tw = tk.Toplevel(self.widget)
		# Leaves only the label and removes the app window
		self.tw.wm_overrideredirect(True)
		self.tw.wm_geometry("+%d+%d" % (x, y))
		label = tk.Label(self.tw, text=self.text, justify='left',
					   background='yellow', relief='solid', borderwidth=1,
					   font=("times", self.font_size, "normal"))
		label.pack(ipadx=1)
	#end def enter

	def close(self, event=None):
		if self.tw:
			self.tw.destroy()
		#end if
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




