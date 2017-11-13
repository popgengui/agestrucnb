'''
Description
2017_09_25.  This class is meant to be part of a plotting
interface for the values in the tsv file output by 
pgdriveneestimator.py
'''
from __future__ import print_function

from future import standard_library

standard_library.install_aliases()

__filename__ = "pgneesttableselectioncombo.py"
__date__ = "20170925"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from tkinter import *
from tkinter.ttk import *

from agestrucne.pgneestimationtablefilemanager import NeEstimationTableFileManager

DEFAULT_CBOX_WIDTH=10
TSV_FILE_DELIMITER="\t"

class PGNeEstTableSelectionCombo( Combobox ):
	'''
	2017_09_26. This class was abstracted out from 
	class PGNeEstTableValueSelectionCombo, in order to 
	allow code common to it and the column selection combo
	class.
	'''

	COL_ALIASES=\
		NeEstimationTableFileManager.COLUMN_NAME_ALIASES_BY_COLUMN_NAME
	COL_NAMES_BY_ALIAS=\
		NeEstimationTableFileManager.COLUMN_NAMES_BY_ALIAS

	def __init__( self, o_master, 
						o_tsv_file_manager,
						s_column_name=None,
						def_to_call_on_selection_change=None ):
		'''
		Argument def_to_call_on_selection_change should
		take three args, one the column name , next
		the current (selected) value as string 
		in the combobox, and the third, the o_tsv_file_manager object.
		'''


		Combobox.__init__( self, o_master )

		self.__tsv_file_manager=o_tsv_file_manager
		self.__my_text_var=StringVar()
		self.__selection_options=None
		self.__state='readonly'
		self.__my_width=None
		self.__def_to_call_on_selection_change = \
									def_to_call_on_selection_change
		self.__column_name=s_column_name

		return
	#end __init__


	def config_me( self ):

		self.set_selection_options()

		self.__set_width()

		self.config( textvariable = self.__my_text_var )
		self.config( state=self.__state )
		self.config( width = self.__my_width )
		self.config( values = self.__selection_options )

		self.bind("<<ComboboxSelected>>", self.on_new_combobox_selection )
		
		if self.__selection_options is not None \
				and len( self.__selection_options ) > 0:
			self.current(  0  )
		#end ther is an options value with len>0, set cbox
		#current val to first

		self.on_new_combobox_selection()

		return
	#end __config_me

	def __set_width( self ):

		i_width=0 
		if self.__selection_options is not None:
			for s_selection in self.__selection_options:
				i_this_len=len( s_selection )
				i_width=i_width if i_this_len <= i_width else i_this_len
			#end for each selection, check for longer length
		#end if we have a value for options	

		self.__my_width = DEFAULT_CBOX_WIDTH if i_width < DEFAULT_CBOX_WIDTH else i_width

	# end __set width

	def set_selection_options( self ):

		s_msg = "In PGNeEstTableSelectionCombo instance " \
					+ "def set_selection_options, "  \
					+ "this def should be overridden by " \
					+ "child class code."

		raise Exception( s_msg )
	#end set_selection_options 

	def on_new_combobox_selection( self, v_event=None ):

		if self.__def_to_call_on_selection_change is not None:
			self.__def_to_call_on_selection_change( self.__column_name, 
														self.__my_text_var.get(), 
															self.__tsv_file_manager )
		#end if we have a def to call
		return

	#end on_new_combobox_selection
		
	@property 
	def current_value( self ):
		return self.__my_text_var.get()
	#end current_value

#end class PGNeEstTableSelectionCombo

class PGNeEstTableValueSelectionCombo( PGNeEstTableSelectionCombo ):
	'''
	2017_09_25.  This class is meant to be part of a plotting
	interface for the values in the tsv file output by 
	pgdriveneestimator.py  It creates a tkinter combobox
	that lists the uniq set of values under the column as
	named by the contructor parameter, "s_tsv_col_name." It
	also always includes the value "All" so that the user can
	indicate that no filter should be applied to the column values.
	'''
	def __init__( self, o_master, o_tsv_file_manager, 
									s_tsv_col_name, 
									def_to_call_on_selection_change=None,
									b_sort_numerically=False ):
	
		
		PGNeEstTableSelectionCombo.__init__( self, o_master = o_master, 
									s_column_name=s_tsv_col_name,
									o_tsv_file_manager=o_tsv_file_manager,
									def_to_call_on_selection_change=def_to_call_on_selection_change ) 
		self.__sort_numerically=b_sort_numerically

		self.config_me()

		return
	#end __init__
		
	def set_selection_options( self ):
		o_tsv_manager=self._PGNeEstTableSelectionCombo__tsv_file_manager

		self._PGNeEstTableSelectionCombo__selection_options=( "All", )
		
		ls_values=o_tsv_manager.getUniqueStringValuesForColumn( self._PGNeEstTableSelectionCombo__column_name )	

		if self.__sort_numerically==False:
			self._PGNeEstTableSelectionCombo__selection_options+=tuple( sorted( ls_values ) )
		else:
			try:
				lf_values=[ float( s_val ) for s_val in ls_values ]
			except ValueError as ve:
				s_msg="In PGNeEstTableValueSelectionCombo instance, " \
							+ "def set_selection_options, " \
							+ "the program can't sort the values " \
							+ "for the column " \
							+ self._PGNeEstTableSelectionCombo__column_name \
							+ " numerically."
				raise Exception( s_msg )
			#end try ... except

			ls_sorted_numerically=[ ls_values[ tup_i[ 0 ] ] \
					for tup_i in sorted( enumerate( lf_values ), key=lambda x:x[1] ) ]

			self._PGNeEstTableSelectionCombo__selection_options+=tuple( ls_sorted_numerically )

		#end if sort non-numerically, else numerically	

		return
	#end set_selection_options

#end class PGNeEstTableValueSelectionCombo

class PGNeEstTableColumnSelectionCombo( PGNeEstTableSelectionCombo ):

	def __init__( self, o_master, 
						o_tsv_file_manager, 
						def_to_call_on_selection_change=None,
						ls_column_names_to_show_excluding_others=None,
						b_add_none_selection=True ):
		'''
		Arg b_add_none_selection, when True (the default), will prepend
		a string "None" to the combos option list.
		'''
		PGNeEstTableSelectionCombo.__init__( self, o_master = o_master, 
									o_tsv_file_manager=o_tsv_file_manager,
									def_to_call_on_selection_change=def_to_call_on_selection_change )

		self.__columns_inclusion_list=ls_column_names_to_show_excluding_others
		self.__add_none_selection=b_add_none_selection
		self.config_me()

		return
	#end __init__

	def set_selection_options( self ):

		COLNAME_ALIASES=PGNeEstTableColumnSelectionCombo.COL_ALIASES

		o_tsv_file_manager=self._PGNeEstTableSelectionCombo__tsv_file_manager
		
		ls_column_names=o_tsv_file_manager.header.split( TSV_FILE_DELIMITER )

		ls_options=[ COLNAME_ALIASES[ s_name ] for s_name in ls_column_names ]

		if self.__columns_inclusion_list is not None:
			ls_options=[]
			for s_name in ls_column_names:
				if s_name in self.__columns_inclusion_list:
					ls_options.append( COLNAME_ALIASES[s_name] )
				#end if column to be included
			#end for each column name
		#end if we have an inclusion list

		if self.__add_none_selection == True:
			self._PGNeEstTableSelectionCombo__selection_options=( "None", ) + tuple( ls_options )
		else:
			self._PGNeEstTableSelectionCombo__selection_options=tuple( ls_options )
		#end if we should prepend a choice "None" to the options else not.
		return
	#end set_selection_options

	def __get_column_name_or_none_from_current_value( self ):
	
		COLBYALIAS=PGNeEstTableSelectionCombo.COL_NAMES_BY_ALIAS
		
		s_current_value=self._PGNeEstTableSelectionCombo__my_text_var.get() 

		if s_current_value != "None":
			s_selected_column_name=COLBYALIAS[ s_current_value ]
		else:
			s_selected_column_name=s_current_value
		#end if non-None value, get the tsv col name, else "None"

		return s_selected_column_name
	#end __get_column_name_or_none_from_alias

	def on_new_combobox_selection( self, v_event=None ):
		'''
		We overide the parent class version of this def,
		since our combox's value will be an alias of a tsv column name,
		and we want to return the actual tsv column name.
		'''
	
		s_selected_column_name=self.__get_column_name_or_none_from_current_value()

		if self._PGNeEstTableSelectionCombo__def_to_call_on_selection_change is not None:
			'''
			Note that the client's def requires a first "column_name" arg.
			In this child class, which does not use the __column_name attr
			to derive a set of value selections.  Hence, it will simply be 
			passing the default init value in the parent class, None.
			'''
			self._PGNeEstTableSelectionCombo__def_to_call_on_selection_change(\
											self._PGNeEstTableSelectionCombo__column_name, 
											s_selected_column_name,	
											self._PGNeEstTableSelectionCombo__tsv_file_manager )
		#end if we have a def to call
		return
	#end on_new_combobox_selection

	@property 
	def current_value( self ):
		s_selected_column_name=self.__get_column_name_or_none_from_current_value()
		return s_selected_column_name
	#end property current_value

	'''
	Note that the following was originally implemented as a setter of 
	the "current_value property", but the setter did not get called 
	in python2, though it did in python3.  For cross comaptibility
	I use a regular class def.
	'''
	def resetCurrentValue( self, s_column_name ):
		ds_aliases_by_col_name=PGNeEstTableColumnSelectionCombo.COL_ALIASES
		if s_column_name in ds_aliases_by_col_name:
			s_column_name_alias=ds_aliases_by_col_name[ s_column_name ]
			if s_column_name_alias in self[ "values" ]:
				idx_alias=self[ "values" ].index( s_column_name_alias )
				self.current( idx_alias )
				self.on_new_combobox_selection()
			#end if alias is in our option list, set the combo to that selection
		#end if s_column
		return
	#end current_value setter
#end class PGNeEstTableColumnSelectionCombo

if __name__ == "__main__":

	from agestrucne.pgneestimationtablefilemanager import NeEstimationTableFileManager

	def printval( s_val, o_obj ):
		print( "current val: " + s_val )
	#end print val

	def printcolname( s_val, o_tsvfile):
		print( "current colname: " + s_val )
	#end printcolname
	
	s_tsv_file="/home/ted/documents/source_code/python/negui/temp_data/t2.nb.ldne.tsv"

	o_tsv=NeEstimationTableFileManager( s_tsv_file )
	mym=Tk()

	myc=PGNeEstTableValueSelectionCombo( mym, o_tsv, 'pop', b_sort_numerically=True, def_to_call_on_selection_change=printval )
	myc2=PGNeEstTableColumnSelectionCombo( mym, o_tsv, def_to_call_on_selection_change=printcolname )

	myc.grid()
	myc2.grid()

	mym.mainloop()
	
#end if main

