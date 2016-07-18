'''
Description

Deploy tkinter by subclassing Frame class.  See class description.
'''
__filename__ = "pgguiapp.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from Tkinter import *
from ttk import *

class PGGuiApp( Frame ):
	'''
	The standard way to deploy tkinter with application object that inherits Frame
	(see example at https://docs.python.org/2/library/tkinter.html#Tkinter.Tk)
	this app instantiated by driver code like, 

	root = Tk()
	app = Application(master=root)
	app.mainloop()
	root.destroy()

	Adds member attribute "master" (ref to the master Tk() object).
	This class is to be subclassed by specific PGGui* classes that
	perform specific PG operations (ex: class PGGuiSimuPop).
	'''

	def __init__( self,  s_name,  master=None  ):
		Frame.__init__( self, master, name=s_name )
		self.__master=master
		return
	#end init

	@property
	def master(self):
		"""master, tk.TK() object"""
		return self.__master
	#end menu getter

	@master.setter
	def master( self, i_value ):
		raise Exception( "in PGGuiApp object, " \
		+ "there is no setter for the master object. " )
	#end master setter

	@master.deleter
	def master(self):
		del self.__master
	#end master deleter

#end class

