'''
Description
Abstract class PGOperation is to be implemented by subclasses.
Wraps the code required to perform a pop gen analysis, such as a simuPop simulation,
Or an Ne calculation.  Instantiated subclass objects are the expected type members 
of the PGGuiApp class objects attribute "gp_operation".

'''
from builtins import object
from future.utils import with_metaclass
__filename__ = "pgoperation.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from abc import ABCMeta, abstractmethod

class APGOperation( with_metaclass(ABCMeta, object) ):
	'''
	Abstract class PGOperation is to be implemented by subclasses.
	Wraps the code required to perform a pop gen analysis, such as a simuPop simulation,
	Or an Ne calculation.  Instantiated subclass objects are the expected type members 
	of the PGGuiApp class objects attribute "gp_operation".
	'''

	def __init__( self, o_input, o_output ):
		self.__input=o_input
		self.__output=o_output
		return
	#end __init__

	@abstractmethod
	def prepareOp( self ):
		return
	#end prepareOp

	@abstractmethod
	def doOp( self ):
		return
	#end doOp

	@abstractmethod
	def deliverResults( self ):
		return
	#end deliverResults

	@property
	def input( self ):
		return self.__input
	#end input

	@input.setter
	def input( self, o_input_object ):
		self.__input=o_input_object
		return
	#end setter

	@input.deleter
	def input( self ):
		del self.__input
		return
	#end delete

	@property
	def output( self ):
		return self.__output
	#end output

	@output.setter
	def output( self, o_output_object ):
		self.__output=o_output_object
		return
	#end setter

	@output.deleter
	def output( self ):
		del self.__output
		return
	#end delete

#end class PGOperation

