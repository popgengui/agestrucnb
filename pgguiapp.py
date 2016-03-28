'''
Description

Deploy tkinter by subclassing Frame class.  See class description.
'''
__filename__ = "pgguiapp.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from Tkinter import *

class PGGuiApp( Frame ):
	'''
	The standard way to deploy tkinter with application object that inherits Frame
	(see example at https://docs.python.org/2/library/tkinter.html#Tkinter.Tk)
	this app instantiated by driver code like, 

	root = Tk()
	app = Application(master=root)
	app.mainloop()
	root.destroy()
	'''


	def __init__( self, master=None, o_pg_operation=None ):
		self.__op = o_pg_operation
		Frame.__init__( self, master )
		self.pack()
		self.__createWidgets()
	#end init

	def __createWidgets( self ):
		pass
		return
	#end def __createWidgets	

	@property
	def op( self ):
		"""object that performs a pop gen operation by implementing abstract class PGOperation"""
		return self.__op
	#end op getter

	@op.setter
	def op( self, o_op ):
		self.__op=o_op
	#end op setter


	@op.deleter
	def op( self ):
		del self.__op
	#end op deleter

#end class

