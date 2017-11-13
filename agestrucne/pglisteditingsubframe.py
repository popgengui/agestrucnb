'''
Description

2017_03_25.  This class was extracted from 
the pgguiutilities.py module, to ease debugging.
'''

from future import standard_library
standard_library.install_aliases()
from builtins import range
__filename__ = "pglisteditingsubframe.py"
__date__ = "20170325"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"



from tkinter import *
from tkinter.ttk import *

import agestrucne.pgutilities as pgut

class ListEditingSubframe( Frame ):
	'''
	2016_09_18

	A frame with gui controls to add or trim
	an item from a list, or to assign a single
	value to a range of list indices.  

	This class created as a subframe to sit
	below a list of items in a KeyValFrame
	instance whose client passed a list into
	the KeyValFrame.  Because trimming and extending
	a list are not easily implemented in the current
	KeyValFrame class, and because values in the displayed
	list are only editable one at a time, this
	class is meant to offer them (in a basic form).	

	Note that this class would be unneccesary if Tkinter
	has a sreadsheet-like widget.

	2016_10_31 
	Because I'm currently not using the assign-range, 
	funcion, and, although it seems to be working, it nonetheless
	complicates the communications between this class objectd
	and its parent KeyValFrame, I'm for now going to hide these
	controls. See def __setup, where I've commented out the
	grid assignments of the assign-range controls.
	'''

	def __init__( self, 
					o_master, 
					lv_list, 
					def_to_call_when_list_changes=None,
					v_default_value=0.0,
					s_state="enabled",
					i_control_width=10,
					i_button_width=8,
					o_acceptable_item_type=float,
					b_allow_none_value_for_list=True ):

		self.__validate_list( lv_list, o_acceptable_item_type  )

		Frame.__init__( self,  o_master )
		
		self.__mylist=[ v_val for v_val in lv_list  ]
		self.__def_to_call_when_list_changes=def_to_call_when_list_changes
		self.__default_value=v_default_value
		self.__state=s_state
		self.__control_width=i_control_width
		'''
		Button width default was sized on Linux,
		but it is not sufficient for Windows,
		and button text gets trunctated.
		'''
		i_adjusted_button_width= \
				self.__adjust_button_width_if_on_windows(  \
												i_button_width )

		self.__button_width=i_adjusted_button_width
		self.__acceptable_item_type=o_acceptable_item_type
		self.__allow_none_value=b_allow_none_value_for_list

		self.__btn_extend=None
		self.__btn_trim=None
		self.__label_assign=None
		self.__entry_from=None
		self.__label_to=None
		self.__entry_to=None
		self.__label_assign=None
		self.__entry_assign_val=None
		self.__btn_assign=None

		self.__range_value=StringVar()
		self.__from_value=IntVar()
		self.__to_value=IntVar()

		self.BTN_COL_EXTEND=0
		self.BTN_COL_TRIM=1
		self.LABEL_COL_ASSIGN=2
		self.ENTRY_COL_FROM=3
		self.LABEL_COL_TO=4
		self.ENTRY_COL_TO=5
		self.LABEL_COL_VALUE=6
		self.ENTRY_COL_VALUE=7
		self.BTN_COL_ASSIGN=8
		self.TOTAL_CONTROLS=self.BTN_COL_ASSIGN+1

		self.__setup()

		return

	#end __init__

	def __adjust_button_width_if_on_windows( self, i_button_width ):

		WINDOWS_REQUIRED_WIDTH_INCREASE=2

		i_adjusted_width=i_button_width

		b_is_windows_platform= pgut.is_windows_platform()

		if b_is_windows_platform:
			i_adjusted_width=i_button_width \
					+ WINDOWS_REQUIRED_WIDTH_INCREASE
		#end if is windows platform

		return i_adjusted_width
	#end __adjust_button_width_if_on_windows

	def __validate_list( self, lv_list, o_correct_item_type ):

		s_errmsg="In ListEditingSubframe instance, " \
		
		b_is_valid=True
		
		b_is_none_and_none_val_allowed= lv_list is None \
				and self.__allow_none_value == True

		if type( lv_list ) != list:
			if	lv_list is not None \
					or self.__allow_none_value==False:

				s_errmsg += "non-list type passed by client.  " \
						+ "Passed value: " + str( lv_list ) \
						+ ".  Type: " + str( type( lv_list ) ) \
						+ "."
				b_is_valid=False
			#end if val is not none, or none is dissallowed
		elif len( lv_list ) > 0:
			for v_val in lv_list:
				o_item_type= type ( v_val )
				if o_item_type != o_correct_item_type:
					s_errmsg += "incorrect type in list.  " \
							+ "list: " + str( lv_list ) + ".  " \
							+ "Item with incorrect type: " \
							+ str( v_val ) + ".  " \
							+ "Correct type: " + str(o_correct_item_type) \
							+ "."

					b_is_valid=False
					break
				#end if incorrect item type
			#end for each item in list
		#end if type not list, else if non-empty list
		if b_is_valid == False:
			raise Exception( s_errmsg )
		#end if invalid value

		return
	#end def __validate_list

	def __setup( self ):
		
		''' 
		This innter subframe allows
		the value list above the 
		editing buttons to retain
		their spacing.
		'''

		BUTTON_PADDING=3

		i_num_entries=len( self.__mylist )

		o_editing_subframe=self

		self.__btn_extend=Button( self,
								text="Add Value",
								command=self.__extend_list,
								state=self.__state,
								width=self.__button_width )

		self.__btn_trim=Button( self, text="Trim", 
								command=self.__trim_list,
								state=self.__state,
								width=self.__button_width )

		self.__label_assign=Label( self, \
				text="       Assign range from: " )

		self.__entry_from=Entry(  self, 
							textvariable=self.__from_value,
							state=self.__state,
							foreground="black",
							width=self.__control_width )

		self.__label_to=Label( self, text=" to: " )
	
		self.__entry_to=Entry(  self, 
							textvariable=self.__to_value,
							state=self.__state,
							foreground="black",
							width=self.__control_width ) 

		self.__label_assign_val=Label( self, text=" value: " )

		self.__entry_assign_val=Entry( self,
							textvariable=self.__range_value,
							state=self.__state,
							foreground="black",
							width=self.__control_width )
		self.__btn_assign=Button( self, text="Assign",
								command=self.__assign_range,
								state=self.__state,
								width=self.__control_width )

		self.__btn_extend.grid( row=0, column=self.BTN_COL_EXTEND, padx=BUTTON_PADDING )
		self.__btn_trim.grid( row=0, column=self.BTN_COL_TRIM )
		'''
		Because I'm currently (2016_10_31) not using the assign-range, 
		funcion, and, though it seems to be working, it nonetheless
		complicates the communications between this class objectd
		and its parent KeyValFrame, I'm for now going to hide these
		controls.
		'''
#		self.__label_assign.grid( row=0, column=self.LABEL_COL_ASSIGN )
#		self.__entry_from.grid( row=0, column=self.ENTRY_COL_FROM )
#		self.__label_to.grid( row=0, column=self.LABEL_COL_TO )
#		self.__entry_to.grid( row=0, column=self.ENTRY_COL_TO )
#		self.__label_assign_val.grid( row=0, column=self.LABEL_COL_VALUE )
#		self.__entry_assign_val.grid( row=0, column=self.ENTRY_COL_VALUE )
#		self.__btn_assign.grid( row=0, column=self.BTN_COL_ASSIGN )

		self.grid( row=1, column=1, columnspan=max( i_num_entries, self.TOTAL_CONTROLS ), sticky="nw")

	#end __setup


	def __get_copy_mylist( self ):

		lv_newlist=[]

		#if not None, copy current list
		if self.__mylist is not None:
			lv_newlist=[ v_val for v_val in self.__mylist ]
		#end if list not none

		return lv_newlist

	#end __get_copy_mylist

	def __extend_list( self ):

		lv_newlist=self.__get_copy_mylist()

		v_value_to_add=self.__default_value

		'''
		If we have at least one item in 
		the list, use the last item's
		value as the appended value:
		''' 
		if len( lv_newlist ) > 0:
			v_value_to_add=self.__mylist[ len( self.__mylist ) - 1 ]
		#end if list has at least one item

		lv_newlist.append( v_value_to_add )

		self.__validate_list( lv_newlist, 
					self.__acceptable_item_type )

		self.__mylist=lv_newlist

		if self.__def_to_call_when_list_changes is not None:
			self.__def_to_call_when_list_changes()
		#end if there is a def to call when the list changes

		return

	#end __extend_list

	def __trim_list( self ):

		lv_newlist=self.__get_copy_mylist()

		if len( lv_newlist ) > 0:
			lv_newlist.pop()
		#end if our list has at least one item

		self.__validate_list( lv_newlist, 
						self.__acceptable_item_type )

		self.__mylist=lv_newlist
		
		if self.__def_to_call_when_list_changes is not None:
			self.__def_to_call_when_list_changes()
		#end if there is a def to call when the list changes

		return
	#end __trim_list

	def __range_is_valid( self, lv_list, 
									i_from, 
									i_to ):

		b_is_valid=True

		i_len_list=len( lv_list )

		if i_to < i_from  \
				or i_from < 1 \
				or i_to >  i_len_list :
			b_is_valid = False
		#end if bad interval

		return b_is_valid
	#end __range_is_valid

	def __assign_range( self ):

		'''
		We expect interface users to give 1-indexed
		ranges, with inclusive ends, so that from 1
		to 10, for example, means python list indices
		0 to 9
		'''
	
		lv_newlist=self.__get_copy_mylist()

		i_from=self.__from_value.get()
		i_to=self.__to_value.get()
		s_value=self.__range_value.get()

		if not self.__range_is_valid( lv_newlist,
											i_from, 
											i_to ):

			s_msg="In ListEditingSubframe instance, " \
					+ "def __assign_range, " \
					+ "invalid range from, " \
					+ str( i_from ) \
					+ " to " + str( i_to ) \
					+ ", with list size: " \
					+ str( len( self.__mylist ) )
			raise Exception( s_msg )

		#end if invalid range

		try:
			v_value=eval( s_value )
		except Exception as oex:
			s_msg="In ListEditingSubframe instance, " \
					+ "def __assign_range, " \
					+ "eval failed on the value to be " \
					+ "assigned to the range: " \
					+ s_value  + ".  Exception raised: " \
					+ str( oex ) + "."

			raise Exception( s_msg )
		#end try, except

		i_python_index_from=i_from-1

		for idx in range( i_python_index_from, i_to ):
			lv_newlist[ idx ] = self.__acceptable_item_type( v_value )
		#end for each index to be reassigned

		self.__validate_list( lv_newlist, 
								self.__acceptable_item_type )

		self.__mylist=lv_newlist

		if self.__def_to_call_when_list_changes is not None:
			self.__def_to_call_when_list_changes()
		#end if we have a def to call when list changes

		return
	#end def __assign_range

	@property
	def thelist( self ):
		return [ v_val for v_val in self.__mylist ]
	#end thelist

	@thelist.setter
	def thelist( self, lv_list ):
		self.__validate_list( lv_list, self.__acceptable_item_type )
		self.__mylist=[ i_val for i_val in lv_list ]
		return
	#end getter thelist

	@property
	def defaultvalue( self ):
		return self.__default_value
	#end 

	@defaultvalue.setter
	def defaultvalue( self, v_value ):
		self.__default_value=v_value
#end class ListEditingSubframe





if __name__ == "__main__":
	pass
#end if main

