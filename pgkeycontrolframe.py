'''
Description
This class was created (2017_04_18)
after the separate creation of classes in modules:
	pgkeycategoricalvalueframe.py
	pgkeycheckboxvalueframe.py
	pgkeycontrolframe.py
	pgkeylistcomboframe.py
	pgkeyvalueframe.py

It is a post-facto created parent class to simplify some of the
operations common to these classes (which admittedly should have been
designed before creating the several related classes).

My first consolidation is to simply abstract out the parent Frame, and
implement a label object common to most of the above classes, with
state property.

It may be advantageous to abstract more of the common funcionality from 
these classes into this parent class as interface features and demands
increase.
'''

from future import standard_library
standard_library.install_aliases()
__filename__ = "pgkeycontrolframe.py"
__date__ = "20170418"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"
from tkinter import *
from tkinter.ttk import *

class PGKeyControlFrame( Frame ):

	def __init__( self, o_master, name ):

		#TCL won't allow uppercase names for windows
		#(note that we save the name, case in-tact, in
		#member __name:

		Frame.__init__( self, o_master, name=name.lower() )
		self.label=None
		return
	#end __init__
	

	'''
	I would have preferred to use a setter
	and getter for a "label_state" property,
	but, as I've encountered too often, python 
	has an overwrought inheritance implementation 
	surrounding properties, which as far as I can penetrate 
	the byzantine rules, would seem to require coding in all 
	the children.  
	'''
	def getLabelState( self ):
		return str( self.label.cget( "state" ) )
	#end getLabelStatee

	def setLabelState( self, s_value ):
		self.label.configure( state=s_value )
		return
	#end setLabelState



#end class PGKeyControlFrame

if __name__ == "__main__":
	pass
#end if main

