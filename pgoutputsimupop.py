'''
Description
manages output of the PGOpSimuPop object
based on tiago anteo's code in sim.py
'''
__filename__ = "pgoutputsimupop.py"
__date__ = "20160327"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class PGOutputSimuPop( object ):
	'''
	Object meant to fetch parameter values and prepare them for 
	use in a simuPop simulation.  

	Object to be passed to a PGOpSimuPop object, which is, in turn,
	passed to a PGGuiSimuPop object, so that the widgets can then access
	defs in this input object, in order to, for example, show or allow
	changes in parameter values for users before they run the simulation.
	'''

	def __init__( self, s_output_files_prefix ):

		self.outname=s_output_files_prefix + ".sim"
		self.errname=s_output_files_prefix + ".gen"
		self.megadbname=s_output_files_prefix + ".db"
		
		self.out=None
		self.err=None
		self.megaDB=None
		return
	#end def __init__

	def openOut(self):
		self.out=open( self.outname, 'w' )
	#end openOut

	def openErr(self):
		self.err=open( self.errname, 'w' )
	#end openOut

	def openMegaDB(self):
		self.megaDB=open( self.megadbname, 'w' )
	#end openOut

#end class
