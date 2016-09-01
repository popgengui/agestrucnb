'''
Description
Instead of putting utility classes in pgutilities,
this module will house all classes not directly related
to front or back end of the pg operations.
'''

__filename__ = "pgutilityclasses.py"
__date__ = "20160702"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys

class IndependantProcessGroup( object ):
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

	def terminateAllProcesses( self ):
		for o_process in self.__processes:
			o_process.terminate()
		#end for each process
		return
	#end terminatAllProcesses

#end class IndependantProcessGroup


class IndependantSubprocessGroup( object ):
	'''
	Minimal Revision of class independantProcessGroup	
	to operate on python subprocess.Popen proccesses.

	The main changes include use of kill() instead of 
	terminate in def terminateAllSubprocesses() and
	use poll() (is None) instead of is_alive() to get
	a count of living processes
	'''

	def __init__( self, lo_subprocesses=[] ):
		self.__subprocesses=lo_subprocesses
		self.__pids=[ o_subprocess.pid for o_subprocess in lo_subprocesses ]
		return
	#end __init__

	def addSubprocess( self, o_subprocess ):
		self.__subprocesses.append( o_subprocess )
		self.__pids.append( o_subprocess.pid )
		return
	#end addSubprocess

	def getTotalAlive( self ):
		i_count_living=0
		for o_subprocess in self.__subprocesses:
			if o_subprocess.poll() is None:
				i_count_living+=1
			#end if subprocess is alive
		#end for each subprocess
		return i_count_living
	#end getTotalAlive

	def terminateAllSubprocesses( self ):
		for o_subprocess in self.__subprocesses:
			try:
				o_subprocess.kill()
			except OSError as ose:
				s_msg="In IndependantSubprocessGroup instance, def " \
							+ " terminateAllSubprocesses, " \
							+ " on call to kill(), an OSError was generated: " \
							+ str( ose )  + "."
				sys.stderr.write( "Warning: " + s_msg + "\n" )
			#end 
		#end for each subprocess
		return
	#end terminateAllSubprocesses

#end class independantSubprocessGroup

class FloatIntStringParamValidity( object ):

	'''
	For validation checks on a parameter value
	before it is used to run an analysis.
	'''

	def __init__( self, s_name, o_type, o_value, i_min_value=None, i_max_value=None ):
		self.__name=s_name
		self.__param_type=o_type
		self.__value=o_value
		self.__min_value=i_min_value
		self.__max_value=i_max_value

		self.__type_message=None
		self.__value_message=None

		self.__is_valid=False
		self.__value_valid=False
		self.__type_valid=False
	
		self.__set_validity()
	#end __init__

	def __set_validity( self ):

		b_set_type_valid=self.__param_type in ( float, int, str )
		b_type_matches=type( self.__value) == self.__param_type
		b_value_in_range=self.__value_is_in_range()

		if b_set_type_valid:
			self.__type_message="Type, " + str( self.__param_type ) + "is valid."
			self.__type_valid=True
		else:
			self.__type_message="Type, " + str( self.__param_type ) \
					+ "is not among the valid types, float, int, str."
			self.__type_valid=False
		#end if not valid type	
		
		if b_type_matches:
			self.__type_message="Type, " + str( self.__param_type ) + " is valid."
			self.__type_valid=True
		else:
			self.__type_message="Param type is, " + str( self.__param_type ) \
					+ " but value, " + str( self.__value ) + " is of type, " \
					+ str( type( self.__value ) ) + "."
			self.__type_valid=False

		#end if not type match

		if b_value_in_range:
			self.__value_message= "Value, " + str( self.__value ) + " is valid."
			self.__value_valid=True
		else:
			if type( self.__value ) == str:
				self.__value_message="Length of string value " + str( self.__value ) \
					 		+ " is out of range.  Range is from " \
							+ str( self.__min_value ) + " to " +  str( self.__max_value ) \
							+ "."
			else:
				self.__value_message="Value, " + str( self.__value ) \
					 		+ ", is out of range.  Range is from " \
							+ str( self.__min_value ) + " to " \
							+  str( self.__max_value ) \
							+ "."
			#end if string else otehr

			self.__value_valid=False
		#end if not b_value_in_range
	
		if  b_set_type_valid + b_type_matches + b_value_in_range  == 3:
			self.__is_valid=True
		else:
			self.__is_valid=False
		#end if all checks good, else invalid param	

		return
	#end __set_validity

	def __value_is_in_range( self ):
		
		o_type_val=type( self.__value )
		i_range_val=None

		b_meets_min=False
		b_meets_max=False

		if o_type_val  in ( int, float ):
			i_range_val=self.__value
		elif o_type_val == str:
			i_range_val=len( self.__value )	
		else:
			''' 
				value has invalid type,
				so we default to designating
				it out-of-range
			'''
			return False
		#end if numeric, else string

		if self.__min_value is None:
			#infer no min:
			b_meets_min=True
		else:

			if i_range_val >= self.__min_value:
				b_meets_min=True
			#end if meets min
		#end if min is None, else test

		if self.__max_value is None:
				#infer no man:
				b_meets_max=True
		else:

			if i_range_val <= self.__max_value:
				b_meets_max=True
			#end if meets max			
		#end if max is none, else test

		return b_meets_min and b_meets_max
	#end __value_is_in_range

	def isValid( self ):
		self.__set_validity()
		return self.__is_valid
	#end is

	def reportValidity( self ):
		s_report="\n".join( \
				[ self.__type_message,
				self.__value_message] )
		return s_report
	#end __report_validity

	def reportInvalidityOnly( self ):

		ls_reports=[]
		s_report=""

		if not self.__type_valid:
			ls_reports.append( self.__type_message )
		#end if invalid type
		
		if not self.__value_valid:
			ls_reports.append( self.__value_message )
		#end if invalid value

		s_report="\n".join( ls_reports )

		return s_report 
	#end reportInvalidityOnly

	@property
	def value( self ):
		return self.__value
	#end def value

	@ value.setter
	def value( self, v_value ):
		self.__value=v_value
		self.__set_validity()
	#end setter
#end class FloatIntStringParamWrapped


if __name__ == "__main__":
#	import multiprocessing
#	import time
#
#	i_num_reps=30
#
#	i_num_processes=30
#
#	SLEEPTIMEDEF=1
#	SLEEPTIMEPROCCHECK=0.1
#
#	o_myprocs=independantProcessGroup()
#
#	def target_def( i_rep_number ):
#		print( "executing for rep: " + str( i_rep_number ) )
#		time.sleep( SLEEPTIMEDEF )
#		return
#	#end target_def
#
#	i_living_procs=0
#	i_total_replicates_started=0
#
#	while i_total_replicates_started < i_num_reps:
#
#		i_living_procs=o_myprocs.getTotalAlive()
#
#		while i_living_procs == i_num_processes:
##			time.sleep( SLEEPTIMEPROCCHECK )
#			i_living_procs=o_myprocs.getTotalAlive()
#		#end while living procs is max
#
#		i_num_procs_to_add=i_num_processes - i_living_procs
#
#		for idx in range( i_num_procs_to_add ):
#			o_process=multiprocessing.Process( target=target_def, args=( i_total_replicates_started, ) )
#			o_process.start()
#			o_myprocs.addProcess( o_process )
#			i_total_replicates_started+=1
#		#end for each index, num procs to add
#	#end for each replicate
	
	p1=1
	p2=-3333.12
	p3="hello0000000000000000000000"

	o1=FloatIntStringParamValidity( "p1", float, p1, 0, 10 )
	o2=FloatIntStringParamValidity( "p2", int, p2, 0, 10 )
	o3=FloatIntStringParamValidity( "p3", str, p3, 0, 10 )

	for o in [ o1, o2, o3 ]:
		print( o.isValid() )
		print( o.reportValidity() )
	pass
#end if main

