'''
Description

2017_03_25.  This class code was extracted from the 
pgguiutilities.py module, in order to ease debugging.
'''
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import range
__filename__ = "pgkeyvalueframe.py"
__date__ = "20170325"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from tkinter import *
from tkinter.ttk import *
from agestrucne.pglisteditingsubframe import ListEditingSubframe 
from agestrucne.pgguiutilities import FredLundhsAutoScrollbar

from agestrucne.pgguiutilities import PGGUIInfoMessage
from agestrucne.pgguiutilities import PGGUIYesNoMessage
from agestrucne.pgguiutilities import PGGUIErrorMessage

import agestrucne.createtooltip as ctt
import sys

'''
2017_04_18.  To consolidate some of the objects and functions
common to the key-value-frame classes, we make  parent class that
itself inherits Frame, while also implementing other common functions.
'''
from agestrucne.pgkeycontrolframe import PGKeyControlFrame

class KeyValFrame( PGKeyControlFrame ):
	
	'''
	Description

	Tkinter frame object that creates,
	from left to right, a label, then 
	one or more entry boxes, one entry box 
	if the type is not "list", otherwise one 
	entry box for each list item.

	the instance stores changes in the value(s)
	via callback on enter key.  The current
	key/value state is delivered via a getValue

	Optionally also updates a an attribute
	in its master object, by name (using getattr)
	whenever the entry box value is updated.

	Optionally also places a button to the right
	of the entry box or boxes, and calls a user-supplied
	def whenever a box is updated.

	2016_09_18

	Revise by adding list editing functions.

	'''

	VERBOSE=False

	def __init__( self, 
					s_name, 
					v_value, 
					o_type,
					v_default_value=None,
					o_master=None, 
					s_associated_attribute=None,
					o_associated_attribute_object=None,
					i_entrywidth=7, 
					i_labelwidth=15,
					b_is_enabled=True,
					s_label_justify='right',
					s_entry_justify='right',
					s_button_text = 'Cmd',
					def_button_command = None,
					def_entry_change_command = None,
					type_replaces_none=float,
					s_label_name=None,
					i_subframe_padding=0,
					o_validity_tester=None,
					b_force_disable=False,
					s_tooltip=None,
					b_use_list_editor=False,
					i_entry_row=0,
					i_entry_col=1,
					i_label_row=0,
					i_label_col=0 ):
		
		"""
		Param s_name provides the label text.
		param v_value is the current value to be set as the
				value for this KeyValFrame instance.  Note
				if the client suppliesa list, the type given
				here will be that of each item in the list.
		param o_type gives the type of the value, or, if
				the value is a list, the type of the list items
				(uniform type assumed for list items.
		param v_default_value gives the value that will be used
				if the v_value is a list and the list ListEditingSubframe
				object is being used.  In this case, when the current v_value
				has len==0, then when the user invokes the "extend" def
				in the ListEditingSubframe instance, a new list appears with
				the v_default value as the single list item.
		Param o_master is the parent Tkinter object.
		Param s_associated_attribute is the name of 
			attribute instance that can be accessed
			using "getattr", and that will be
			updated when the value is updated.
		Param o_associated_attribute_object is the object whose attribute
			is to be unpdated when the value is updated.  If
			s_associated_attribute is not None, and this parameter
			is None, the attribute is presumed to be
			owned by the o_master object.
		Param i_entrywidth gives the width of Entry widget(s).
		Param i_labelwidth gives the width the the Label widget.
		Param s_label_justify gives Label widget "justify" value.
		Param s_entry_justify gives Entry Widget text "justify" value.
		Param s_butten_text gives the Button Widget's text value.
		Param def_button_command gives the def to set to the Button's "command" param.
		Param def_entry_change_command gives a def to call when the value of an entry is changed. 			  
			  it should be used when an attribute is asssociated with this object,
			  and so is automatically updated, after which some other action is required 
			  (ex: Parent PGGuiSimuPop object needs to reconstiture the PGOutputSimuPop object 
			  after this object updates its output basename attribute.
		Param type_replaces_none: if a value is initially None, and the value is then updated, 
		      this parameter.
		      gives the type required for a valid value.
		Param s_label_name, if supplied, replaces s_name as the text for the label.
		Param i_subframe_padding gives the padding in pixels of the subframe inside its master frame
		Param o_validity_tester, an object of class type ValueValidator or FloatIntStringParamValidity,
			  (the latter class may be deprecated). If supplied, the KeyValFrame will use it to test all
			  input values into an entry box, and disallow, with error message, when invalid values are
			  entered. For class details see module pgutilityclasses.py
		Param b_force_disable, if True, will cause all Entry objects to be disabled 
			  in the def __make_entry
		Param b_use_list_editor, if True, and if param v_value (see above) is passed as a list, 
			  then a ListEditingSubframe object will be instantiated, allowing a GUI user to
			  trim, extend, or assign one value to a range of list indices.
		Param i_entry_row, integer, grid row at which to layout the entry or entries.
		Param i_entry_col, integer, grid column at which to layout the first entry (incrementing for otherentries).
				note that when a button is present, this will be it's column number, the entries following. 
		Param i_label_row, integer, grid row at which to layout the label.
		Param i_label_col, integer, grid column at which to layout the label.
		"""

		PGKeyControlFrame.__init__( self, o_master, name=s_name.lower() )

		self.__master=o_master
		'''
		This boolean var will be  reassigned
		if the client passed a list instead of an
		atomic type.  If true it will be reassigned
		in def __store_value:
		'''
		self.__orig_value_is_list=False
		#Holds updated value, intiialized
		#in def __store_value
		self.__value=None
		self.__default_value=v_default_value
		self.__value_type=o_type
		self.__store_value( v_value )
		self.__last_state=self.__value
		self.__name=s_name
		self.__entrywidth=i_entrywidth
		self.__lablewidth=i_labelwidth
		self.__labeljustify=s_label_justify
		self.__entryjustify=s_entry_justify
		self.__isenabled=b_is_enabled
		self.__associated_attribute=s_associated_attribute
		self.__associated_attribute_object=o_associated_attribute_object
		self.__button_text=s_button_text
		self.__button_command=def_button_command
		self.__entry_change_command=def_entry_change_command
		self.__type_replaces_none=type_replaces_none
		self.__subframe_padding=i_subframe_padding
		self.__validity_tester=o_validity_tester
		self.__force_disable=b_force_disable
		self.__entry_row=i_entry_row
		self.__entry_col=i_entry_col
		self.__label_row=i_label_row
		self.__label_col=i_label_col
		self.__idx_none_values=[]
		self.__entryvals=[]
		
		self.__label_name=s_name if s_label_name is None \
											else s_label_name		
		#end if no label name, use name, else use label

		'''
		If the value is passed as a list (see def __store_value)
		and this param was passed as True in the __init__ args,
		a ListEditingSubframe instance will be created:
		'''
		self.__tooltip=s_tooltip if s_tooltip is not None \
										else self.__label_name

		self.__use_list_editor=b_use_list_editor

		#ListEditingSubframe object created if
		#our value as passed by client is a list:
		self.__list_editor=None

		#references to the tkinter controls
		#that may be subject to config
		#after init:
		self.__entry_boxes=[]
		self.__textvariables=[]
		self.__button_object=None

		#Canvas, Frame, and other attributes
		#that will allow scrolling and correct
		#resizing (see def __setup_subwidgets)
		self.__canvas=None
		self.__subframe=None
		self.__subframe_id=None
		
		self.__setup()

	#end init

	def __store_value( self, v_value ):
		if type( v_value ) != list:
			self.__value = [ v_value ]
		else:
			self.__value=v_value 

			'''
			Because we store all values as a list,
			we use this flag to tell us how to update 
			the parent attribute (if any),
			and how to return a request for the value --
			i.e. return as a list, or as a scalar, whichever
			was the original type:
			'''
			self.__orig_value_is_list=True

		#end if scalar, else list
		
		return
	#end __store_value
		
	def __reset_value( self, idx_val ):

		o_type=self.__value_type
		o_entryval=self.__entryvals[ idx_val ]
		v_currval=self.__value[ idx_val ]

		v_newval=None

		try:

			#python accepts bool("mystring" ) as True,
			#but we want 0 or 1 only in those fields:
			if o_type==bool:
				if int( o_entryval.get() ) not in [ 0, 1 ]:

					raise ValueError( "Boolean type requires int 0 or 1" )
				else:
					#stored as string -- bool will convert
					#to True unless we pre-convert to int
					v_newval=o_type( int( o_entryval.get() ) )
				#end if not 1 or 0, else is one or zero

				'''
			if a currently "None" value, we check to see
			if the new value is valid for the replacement type
			as given in the init def.  Note that "NoneType",
			although returned to stdout given type( myv ) where
			myv is None, is not the __name__ attribute, and
			type Nonetype has no name, so:
				'''
			elif  o_type == type( None ):
				if o_entryval.get() != "None":
					s_msg="In KeyValFrame instance, " \
							+ "def __reset_value, " \
							+ "value type is: "  \
							+ o_type.__name__ \
							+ ", but entry value is " \
							+ o_entryval.get() + "."
					raise Exception( s_msg )	
					
				else: #no change to value or type if None is still in entry as "None"
					v_newval=None
				#end if entry string is not "None" else is

			#if user entered "None" we treat as a special signal to use
			#value None, as long as our type is not str
			elif o_entryval.get() == "None" and self.__value_type != str:
				if self.__orig_value_is_list:
					s_question="None value invalid for list.  Do you want " \
								+ "to empty the current list (CLicking No "\
								+ "return the cell to its former value.)?"
					b_answer=PGGUIYesNoMessage( self, s_msg )
				v_newval=None
			#if client passed us a validity object,
			#we use it to vett the new entry:
			elif self.__validity_tester is not None:
				
				v_val_to_test=o_type( o_entryval.get() )

				self.__validity_tester.value=v_val_to_test			

				if not self.__validity_tester.isValid():
					#message to user:
					s_msg=self.__validity_tester.reportInvalidityOnly()
					PGGUIInfoMessage( self, s_msg )

					#reset the value to the old
					o_entryval.set( v_currval )

					#return the old value
					v_newval=v_currval
				else:
					v_newval=v_val_to_test
				#end if not valid 
			else:
				v_newval=o_type( o_entryval.get() )
			#end if bool, else if val type  None, else if entry box has "None",
			#else if we have a validity tester
		except ValueError as ve:

			s_msg= "KeyValFrame instance, trying to update value(s) " \
				+ " for key/value associated with " + self.__name + ": " \
				+ "current entry value is \"" + o_entryval.get() \
				+ "\" original value type is: " + o_type.__name__ + "\n"
			sys.stderr.write( s_msg + "\n" )
			
			s_usermsg="Can't update to value, " + o_entryval.get() \
					+ ". Entry must be of type, " + o_type.__name__ + "."
			PGGUIInfoMessage( self, s_usermsg )	
	
			#invalid value in entry box, so reset to current underlying value:
			o_entryval.set( v_currval )
			#and we don't use the new value:
			v_newval=v_currval			
		#end try...except

		return v_newval
	#end __reset_value

	def __setup( self ):
		self.__item_types=[]
		self.__entryvals=[]
		self.__setup_subwidgets()
		self.__subframe.bind( '<Configure>', self.__on_configure_subframe )
		return
	#end __setup

	def __on_configure_subframe( self, event ):
		#we need the scroll region and the canvas dims to 
		#always match the subframe dims.
		q_size=( self.__subframe.winfo_reqwidth(), self.__subframe.winfo_reqheight() )
		self.__canvas.config( scrollregion="0 0 %s %s" % q_size )
		self.__canvas.config( width=q_size[ 0 ] )
		self.__canvas.config( height=q_size[ 1 ] )
		return
	#end __configure_subframe

	def __setup_subwidgets( self ):

		o_horiz_scroll=FredLundhsAutoScrollbar( self, orient=HORIZONTAL )
		self.__canvas=Canvas( self, xscrollcommand=o_horiz_scroll.set )
		self.__subframe=Frame( self.__canvas, padding=self.__subframe_padding )

		self.__setup_label()
		self.__setup_entries()
		self.__setup_button()

		if self.__orig_value_is_list==True \
				and self.__use_list_editor:
			self.__setup_list_editing()
		#end if we manage as a list

		self.__subframe_id=self.__canvas.create_window(0,0, 
											anchor=NW, 
											window=self.__subframe )

		o_horiz_scroll.config( command=self.__canvas.xview )

		self.__canvas.grid( row=0, column=0, sticky=( N,W,E,S ) )
		o_horiz_scroll.grid( row=1, column=0, sticky=(W,E) )
		
		self.grid_rowconfigure( 0, weight=1 )
		self.grid_columnconfigure( 0, weight=1 )

		self.__canvas.grid_rowconfigure( 0, weight=1 )
		self.__canvas.grid_columnconfigure( 0, weight=1 )

	#end __setup_subwidgets

	def __setup_label( self ):
		s_state="enabled"

		if self.__force_disable==True or self.__isenabled==False:
			s_state="disabled"
		#end if force disable

		o_label=Label( self.__subframe, text=self.__label_name, 
										justify=self.__labeljustify, 
														state=s_state )
		o_label.config( width=self.__lablewidth )
		o_label.grid( row=self.__label_row, column=self.__label_col )
		'''
		A parent-class (PGKeyControlFrame)  instance handle on the label is added 2017_04_18.  We now
		manipulate its state through the parent class methods.
		'''
		self.label=o_label
		return
	#end __setup_label

	def __setup_entries( self ):

		self.__make_value_row()

		return

	#end __setup_entries

	def __setup_button( self ):

		'''
		No button made if client
		does not have a command to
		attach to it.
		'''
		if self.__button_command is None:
			return
		#end if no button command, return

		'''
		The Button is at the first entry col 
		the entries will be put at following 
		columns:
		'''

		BUTTON_ROW=self.__entry_row
		BUTTON_COL=self.__entry_col
		BUTTON_XPAD=10
		BUTTON_YPAD=10
		
		s_state="enabled"

		if self.__force_disable==True:
			s_state="disabled"
		#end if force disabled
		
		o_button=Button( self.__subframe, 
							text=self.__button_text, 
							command=self.__button_command,
							state=s_state )

		i_num_entries = len( self.__value ) 

		#we place the button to the left of the entries:
		o_button.grid( row=BUTTON_ROW, 
						column=BUTTON_COL, 
						padx=BUTTON_XPAD,
						pady=BUTTON_YPAD)

		self.__button_object=o_button

		return
	#end _setup_button

	def __setup_list_editing( self ):
		
		set_types=set( self.__item_types )

		if not( len( set_types ) < 2 ):
			s_msg="In KeyValFrame instance, " \
					+ "def __setup_list_editing, " \
					+ "list items have more than one " \
					+ "type. Set of types: " + str( set_types ) \
					+ "."
			raise Exception( s_msg )

		#end if > 1 type
		
		o_type_list_items=self.__value_type	

		self.__list_editor= \
			ListEditingSubframe( o_master=self.__subframe,
									lv_list=self.__value, 
									o_acceptable_item_type=self.__value_type,
									def_to_call_when_list_changes= \
												self.__on_list_change_from_list_editor,
									v_default_value=self.__default_value,
									s_state=self.__isenabled and \
											not( self.__force_disable ),  
									i_control_width=self.__entrywidth )
		
		return

	#end __setup_list_editing

	def __on_list_change_from_list_editor( self ):

		lv_new_list=self.__list_editor.thelist

		self.__update_value_in_clients( lv_new_list )

		self.__store_value( lv_new_list )
		self.__setup()
		return
	#end __on_list_change_from_list_editor

	def __make_entry( self, o_strvar ):
		s_enabled="enabled"
		if self.__isenabled==False or self.__force_disable == True:
			s_enabled="disabled"
		#end if not enabled

		#we want black foreground, even when disabled:

		o_entry = Entry( self.__subframe, 
				textvariable=o_strvar,
				width=self.__entrywidth,
				state=s_enabled,
				foreground="black",
				justify=self.__entryjustify )

		self.__entry_boxes.append( o_entry )

		self.__textvariables.append( o_strvar )

		return o_entry

	#end __make_entry

	def __make_value_row( self ):

		i_num_vals=len( self.__value )
	
		if self.__button_command is not None:
			i_colcount=self.__entry_col + 1
		else:
			i_colcount=self.__entry_col
		#end if we have a button, then
		#first entry will start at 2nd column (col 1),
		#else start at first column (col 0)

		for idx in range( i_num_vals ):
			i_colcount+=1
			o_strvar = StringVar()
			o_strvar.set( self.__value[idx] )
			o_entry=self.__make_entry( o_strvar ) 

			'''
			PGParamSet derived tooltip text needs newlines
			inserted whereever there are double-tildes.
			'''
			self.__tooltip=ctt.insertNewlines( self.__tooltip )

			if i_num_vals > 1: 

				s_delimit="\n"
				s_ttip_text=s_delimit.join( [ self.__tooltip,
								"Entry " + str( idx + 1 ) ] )
			
			else:

				s_ttip_text=self.__tooltip

			#end if more than one value, add item num to tool tip,
			#else just tooltip

			o_tooltip=ctt.CreateToolTip( o_entry,  s_ttip_text )

			self.__entryvals.append( o_strvar  )
			o_entry.grid( row = self.__entry_row, column = i_colcount )
			o_entry.bind( '<Return>', self.__on_enterkey )
			o_entry.bind( '<Tab>', self.__on_enterkey )

			'''
			Note that I moved this binding  to FocusOut, to
			this location in the code.  Originally it
			was executed in def __make_entry above.  I found
			that the binding done before these in the separate
			def caused it to be masked or otherwise nullified,
			so that the focusout event was not causing a call
			to __on_enterkey
			'''
			o_entry.bind( "<FocusOut>", self.__on_enterkey )
		#end for each index
		return
	#end __make_value_row

	def __update_value_in_clients( self, v_val ):

		#we also re-assign the parent attribute (if the caller gave us a ref to it) 
		#from which our key-value was derived
		if self.__associated_attribute is not None:
			#default object whose attribute is to be 
			#updated is the master to this keyvalframe object
			if self.__associated_attribute_object is None:

				if KeyValFrame.VERBOSE:
					print ( "for master: " + str( self.__master)  \
							+ " updating attribute: " \
							+ str( self.__associated_attribute  ) \
							+ " to value: " + str( v_val ) )
				#end if verbose

				setattr( self.__master, self.__associated_attribute, v_val )
			else:
				setattr( self.__associated_attribute_object, self.__associated_attribute, v_val )
			#end if attribute object is None, then use master, else use object
		#end if caller passed an attribute 

		#if there is a command associated with an update in the entry (or list of entries), execute:
		if self.__entry_change_command is not None:
			self.__entry_change_command()
		#end if entry change command is not none
	#end __update_value_in_clients

	def __update_list( self ):

		lv_newlist=[]

		for idx in range ( len(  self.__entryvals ) ):
			v_newval=self.__reset_value( idx )
			lv_newlist.append( v_newval )
		#end for each strvar
		
		self.__value=lv_newlist

		return

	#end __update_list

	def __update_after_entry_change( self ):

		i_len_entryvals=len( self.__entryvals )

		i_len_vals=len( self.__value )

		if i_len_entryvals == i_len_vals:
			self.__update_list()
		else:
			raise Exception ( "In KeyValFrame instance, the current entry values " \
						+ " are not equal to length of the value list" )
		#end if lengths same else not

		'''	
		We extract the value for updating the client's attribute 
		or sending to client's def, and returnn a list only if 
		orig was a list, else return scalar
		'''
		v_attr_val=self.__value if self.__orig_value_is_list else self.__value[0]

		self.__update_value_in_clients( v_attr_val )

		'''	
		If we also have an associated list editor, 
		we need to reassign its list member to 
		match our current:
		'''
		if self.__list_editor is not None:
			self.__list_editor.thelist=self.__value
		#end if we have a list editor object

	#end _update_after_entry_change

	def __on_enterkey( self, event=None ):

		if self.__isenabled == False or self.__force_disable == True:

			return

		else:

			self.__update_after_entry_change()

		#end if not enabled or force disable is True

		return
	#end __on_enterkey

	def manuallyUpdateValue( self, v_value, i_idx=0 ):

		o_strvar=self.__textvariables[ i_idx ]
		o_strvar.set( str( v_value ) )
		self.__update_after_entry_change()

		return
	#end manallyUpdateValue

	def __are_valid_lists( self ):
		i_len_entryvals=len( self.__entryvals )
		i_len_vals=len( self.__value )

		return i_len_entryvals == i_len_vals
	#end __are_valid_lists

	def setStateControls( self, s_state ):
		'''
		Set the state of all this objects
		entry boxes and (if present) button
		to the value passed.
		'''

		self.__isenabled=( s_state == "enabled" )

		for o_entry_box in self.__entry_boxes:
			o_entry_box.configure( state=s_state )
		#end for each entry box

		if self.__button_object is not None:
			self.__button_object.configure( state=s_state )
		#end if we have a button

		return
	#end disableControls

	def getControlStates( self ):
		ls_states=[]
		for o_entry_box in self.__entry_boxes:
			'''
			Trials show that sometimes this call returns
			a string, other times an "index object", whose
			str() value is as expected ('enabled', 'disabled', 
			'normal'...)
			'''
			s_state=str( o_entry_box.cget( "state" ) )
			ls_states.append( s_state )
		#end for each entry box

		if self.__button_object is not None:
			s_button_state=str( self.__button_object.cget( "state" ) )
			ls_states.append( s_state )
		#end if there is a button

		return ls_states
	#end getControlStates

	@property
	def val( self ):
		if self.__orig_value_is_list:
			return self.__value
		else:
			return self.__value[ 0 ]
		#end if orig val is list return value, 
		#else return as orig. scalar -- first item in list
	#end getter

	@val.deleter
	def val( self ):
		del self.__value
		return
	#end val deleter

	@property
	def is_enabled( self ):
		return self.__isenabled
	#end property is_enabled

	@property
	def force_disable( self ):
		return self.__force_disable
	#end force_disable

#end class KeyValFrame

if __name__ == "__main__":

	mym=Tk()

	mykv=KeyValFrame( s_name="test", 
						v_value=1, 
						o_type=int,
						v_default_value=0,
						o_master=mym )	
	mykv.grid()

	mym.mainloop()
	pass
#end if main

