'''
Description
Abstract class PGOperation is to be implemented by subclasses.
Wraps the code required to perform a pop gen analysis, such as a simuPop simulation,
Or an Ne calculation.  Instantiated subclass objects are the expected type members 
of the PGGuiApp class objects attribute "gp_operation".

'''
__filename__ = "pgoperation.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from abc import ABCMeta, abstractmethod

class APGOperation( object ):
	'''
	Abstract class PGOperation is to be implemented by subclasses.
	Wraps the code required to perform a pop gen analysis, such as a simuPop simulation,
	Or an Ne calculation.  Instantiated subclass objects are the expected type members 
	of the PGGuiApp class objects attribute "gp_operation".
	'''

	__metaclass__ = ABCMeta

	def __init__(self):
		pass
		return
	#end __init__

	@abstractmethod
	def prepareOp( self ):
		pass
		return
	#end prepareOp

	@abstractmethod
	def doOp( self ):
		pass
		return
	#end doOp

	@abstractmethod
	def deliverResults( self ):
		pass
		return
	#end deliverResults

#end class PGOperation

