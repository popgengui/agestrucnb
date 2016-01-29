'''
Description
A PGGUIApp object with widgets that manage a simuPop simulation
'''
__filename__ = "pgsimupopper.py"
__date__ = "20160124"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import pgguiapp as pgg

class PGGuiSimuPop( pgg.PGGuiApp ):
	'''
	Subclass of PGGuiApp builds a gui and uses its member object "op", which
	implements PGOperaion to enable a  simuPop simulation.
	'''
	def __init__( self, o_parent, o_simupop_operation ):
		'''
		param o_parent is the Tk() Frame object on which the 
		main window is based
		param o_simupop_operation is the object that the widgets
		control to setup and perform a simuPop simulation
		'''
		super().__init__( o_parent, o_simupop_operation )

	#end __init__
	
	#override the empty def in the parent class:
	def __createWidgets( self ):
		pass
#end __createWidgets

