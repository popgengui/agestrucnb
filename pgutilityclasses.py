'''
Description
Instead of putting utility classes in pgutilities,
this module will house all classes not directly related
to front or back end of the pg operations.
'''

__filename__ = "pgutilityclasses.py"
__date__ = "20160702"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class independantProcessGroup( object ):
	'''
	Simple convenience wrapper around a set of processes,
	allowing calls into the instance to add a process,
	or terminate all processes. This class is motivated
	by implementing parallell replicate AgeStructureNe-inititated
	simuPop simulations in a PGGuiSimuPop instance via
	python's multiprocessing class, which apparently interacts
	with simuPOP such that the multiprocessing.Pool and 
	multiprocessing.Queue process managers do not create
	simuPOP objects independant of each other.  This
	necessitated using separately instantiated and started
	multiprocessing.Process objects.  Because the typical
	case will be to run y replicates using x processes, with
	y>>x, then we need to manage the set of x processes, replacing
	those finished with fresh processes.
	
	
	All member processes are assumed to be completely 
	independant of all others, so that any I/O messes 
	caused by calling terminate() will not lock up 
	the parent process
	'''

	def __init__( self, lo_processes=[] ):
		self.__processes=lo_processes
		self.__pids=[ o_process.pid for o_process in lo_processes ]
		return
	#end __init__

	def addProcess( self, o_process ):
		self.__processes.append( o_process )
		self.__pids.append( o_process.pid )
		return
	#end addProcess

	def getTotalAlive( self ):
		i_count_living=0
		for o_process in self.__processes:
			if o_process.is_alive():
				i_count_living+=1
			#end if process is alive
		#end for each process
		
		return i_count_living
	#end getTotalAlive

	def terminatAllProcesses( self ):
		for o_process in self.__processes:
			o_process.terminate()
		#end for each process
		return
	#end terminatAllProcesses

#end class independantProcessGroup

if __name__ == "__main__":
	import multiprocessing
	import time

	i_num_reps=30

	i_num_processes=30

	SLEEPTIMEDEF=1
	SLEEPTIMEPROCCHECK=0.1

	o_myprocs=independantProcessGroup()

	def target_def( i_rep_number ):
		print( "executing for rep: " + str( i_rep_number ) )
		time.sleep( SLEEPTIMEDEF )
		return
	#end target_def

	i_living_procs=0
	i_total_replicates_started=0

	while i_total_replicates_started < i_num_reps:

		i_living_procs=o_myprocs.getTotalAlive()

		while i_living_procs == i_num_processes:
#			time.sleep( SLEEPTIMEPROCCHECK )
			i_living_procs=o_myprocs.getTotalAlive()
		#end while living procs is max

		i_num_procs_to_add=i_num_processes - i_living_procs

		for idx in range( i_num_procs_to_add ):
			o_process=multiprocessing.Process( target=target_def, args=( i_total_replicates_started, ) )
			o_process.start()
			o_myprocs.addProcess( o_process )
			i_total_replicates_started+=1
		#end for each index, num procs to add
	#end for each replicate

	pass
#end if main

