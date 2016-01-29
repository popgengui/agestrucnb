'''
Description

Retrieves and prepares data needed to run simuPop.  See class description.

'''
__filename__ = "pginputsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class PGInputSimuPop( object ):
	'''
	Object meant to fetch parameter values and prepare them for 
	use in a simuPop simulation.  

	Object to be passed to a PGOpSimuPop object, which is, in turn,
	passed to a PGGuiSimuPop object, so that the widgets can then access
	defs in this input object, in order to, for example, show or allow
	changes in parameter values for users before they run the simulation.
	'''

	def __init__( self, s_config_file = None, s_resources_file = None ):
		pass
		return
	#end def
#end class

