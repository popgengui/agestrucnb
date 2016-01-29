'''
Description
Implements abstract class AGPOperation for simuPop simulations.  See class description.
'''
__filename__ = "pgopsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import apgoperation as modop

class PGOpSimuPop( modop.APGOperation ):
	'''
	This class inherits its basic interface from class APGOperation, with its 3
	basic defs "prepareOp", "doOP", and "deliverResults"

	Its motivating role is to be a member object of a PGGuiApp object, and to contain the
	defs that do a simupop simulation and give results back to the gui.

	Should use no GUI classes, but strictly utils or pop-gen calls.

	This object has member two objects, an input object that fetches and prepares the
	data needed for the simuPop run, and an output object that formats and/or delivers
	the results.   These objects are exposed to users via getters.  The defs in these 
	member objects can thus be accessed by gui widgets when an object of this class  
	is used as a member of a PGGuiApp object
	'''

	def __init__(self, o_input=None, o_output=None ): 
		super().__init__()

		self.__input=o_input
		self.__output=o_output

	#end __init__

	def prepareOp( self ):
		return
	#end prepareOp

	def doOp( self ):
		return
	#end doOp

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
	#end deleter
#end class

