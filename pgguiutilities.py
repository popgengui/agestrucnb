'''
Description
Class objects in this module are TKinter=based
helper objects, with no PG specific function.

'''
__filename__ = "pgguiutilities.py"
__date__ = "20160427"
__author__ = "Ted Cosart<ted.cosart@umontana.edu and " \
				+ "Fredrik Lundh for the Autoscrollbar class (see below)"
from Tkinter import *
from ttk import *
import createtooltip as ctt
import sys

import tkMessageBox

'''
Fred Lundh's code from
http://effbot.org/zone/tkinter-autoscrollbar.htm
'''
class FredLundhsAutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"
#end class FredLundhsAutoScrollbar

class KeyValFrame( Frame ):
	
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
					b_use_list_editor=False ):
		
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
			  and so is automatically updated, after wich some other action is required 
			  (ex: Parent PGGuiSimuPop object needs to reconstiture the PGOutputSimuPop object 
			  after this object updates its output basename attribute.
		Param type_replaces_none: if a value is initially None, and the value is then updated, 
		      this parameter.
		      gives the type required for a valid value.
		Param s_label_name, if supplied, replaces s_name as the text for the label.
		Param i_subframe_padding gives the padding in pixels of the subframe inside its master frame
		Param b_force_disable, if True, will cause all Entry objects to be disabled 
			  in the def __make_entry
		Param b_use_list_editor, if True, and if param v_value (see above) is passed as a list, 
			  then a ListEditingSubframe object will be instantiated, allowing a GUI user to
			  trim, extend, or assign one value to a range of list indices.
		"""

		#TCL won't allow uppercase names for windows
		#(note that we save the name, case in-tact, in
		#member __name:
		Frame.__init__( self, o_master, name=s_name.lower() )
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
		o_label=Label( self.__subframe, text=self.__label_name, justify=self.__labeljustify )
		o_label.config( width=self.__lablewidth )
		o_label.grid( row=0, column=0 )
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
		The Button is at col 1, that is,
		Between the label (col 0)
		and the entry (first entry 
		if list, col1):
		'''

		BUTTON_ROW=0
		BUTTON_COL=1
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
		o_entry.bind( "<FocusOut>", self.__on_enterkey )

		self.__entry_boxes.append( o_entry )
		self.__textvariables.append( o_strvar )

		return o_entry

	#end __make_entry

	def __make_value_row( self ):

		i_num_vals=len( self.__value )
	
		if self.__button_command is not None:
			i_colcount=2
		else:
			i_colcount=1
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
			o_entry.grid( row = 0, column = i_colcount )
			o_entry.bind( '<Return>', self.__on_enterkey )
			o_entry.bind( '<Tab>', self.__on_enterkey )
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
	
		#Because we store even scalars as list items, we extract the 
		#value for updating the client's attribute or sending to 
		#client's def -- we returnn a list only if orig was a list, else return scalar
		v_attr_val=self.__value if self.__orig_value_is_list else self.__value[0]

		self.__update_value_in_clients( v_attr_val )

		'''	
		If we also have an associated list editor, 
		we need to reassigne its list member to 
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
		#end
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

#end class KeyValFrame

class KeyCategoricalValueFrame( Frame ):

	'''
	Description
	
	Revised KeyValueFrame
	substituting a Radiobutton widget
	for the entry box used in KeyValFrame
	
	'''

	def __init__( self, s_name, 
			lq_modes,
			i_default_mode_number,
			o_value_type=None,
			o_master=None, 
			s_associated_attribute=None,
			o_associated_attribute_object=None,
			def_on_button_change=None,
			i_labelwidth=15,
			b_is_enabled=True,
			s_label_justify='right',
			s_buttons_justify='right',
			s_label_name=None,
			b_buttons_in_a_row=False,
			b_force_disable=False,
			s_tooltip = "" ):

		"""
		Param lq_modes, list of sequences, each a pair
		    giving the mode label text, and its associated value
			assigned when it is the selected radio button
		Param i_default_mode_number gives the ith (one-indexed)
			item in modes, that is to be the active button,
			and that gives the default value
		Param o_value_type gives the python type for the values
			given in lq_modes value items.  Currently implemented
			for bool, int, float, and string.
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
		Param def_on_button_change, if not None, execute the def
			after updating both the value and the attribute (if any).
			This def is to have no passed params.
		Param i_labelwidth gives the width the the Label widget.
		Param s_label_justify gives Label widget "justify" value.
		Param s_buttons_justify gives Radiobutten Widget text "justify" value.
				currently not implemented (ttk radio button widgets are not
				settable for justify and foreground, without using a syle map).
		Param s_label_name, if not None, replaces s_name as the text for the label.
		Param b_buttons_in_a_row, if False (default) all buttons are in a single column, if True,
				then all buttons side by side in a single row
		Param b_force_disable, if True, will override the b_is_enabled value and disable all entry 
			  boxes
		"""

		#TCL won't allow uppercase names for windows
		#(note that we save the name, case in-tact, in
		#member __name:
		Frame.__init__( self, o_master, name=s_name.lower() )
		self.__master=o_master
		self.__value=None
		self.__default_mode_number=i_default_mode_number
		self.__modes=lq_modes
		self.__name=s_name
		self.__lablewidth=i_labelwidth
		self.__labeljustify=s_label_justify
		self.__buttons_justify=s_buttons_justify
		self.__isenabled=b_is_enabled
		self.__associated_attribute=s_associated_attribute
		self.__associated_attribute_object=o_associated_attribute_object
		self.__def_on_button_change=def_on_button_change
		self.__put_buttons_in_row=b_buttons_in_a_row
		self.__current_button_value=self.__init_current_button_val( o_value_type )
		self.__label_name=self.__name if s_label_name is None else s_label_name
		self.__force_disable=b_force_disable
		self.__tooltip=self.__label_name if s_tooltip == "" else s_tooltip
		self.__subframe=None
		self.__setup()
	#end init

	def __init_current_button_val( self, o_value_type ):
		
		o_var=None

		if o_value_type==bool:
			o_var=BooleanVar()
		elif o_value_type==int:
			o_var=IntVar()
		elif o_value_type==float:
			o_var=DoubleVar()
		elif o_value_type==StringVar:
			o_var=StringVar()
		else:
			s_msg="in KeyCategoryValFrame object instance, " \
					+ "value type, " + str( o_value_type ) \
					+ " has no associated Tkinter variable type"
			raise Exception( s_msg )
		#end if bool ... else int ... etc
	
		return o_var

	#end __init_current_button_val

	def __reset_value( self ):

		try:

			self.__value= self.__current_button_value.get()

		except ValueError as ve:

			s_msg= "KeyCategoryValFrame instance, trying to update values: " \
				+ "current entry value is \"" + o_entryval.get() \
				+ "\" original value type is: " + o_type.__name__ + "\n"
			sys.stderr.write( s_msg + "\n" )
			raise ( ve )
		#end try...except

	#end __reset_value

	def __setup( self ):
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
		self.__subframe=Frame( self.__canvas )

		self.__setup_label()
		self.__setup_buttons()

		self.__subframe_id=self.__canvas.create_window(0,0, anchor=NW, window=self.__subframe )
		o_horiz_scroll.config( command=self.__canvas.xview )

		self.__canvas.grid( row=0, column=0, sticky=( N,W,E,S ) )
		o_horiz_scroll.grid( row=1, column=0, sticky=(W,E) )
		
		self.grid_rowconfigure( 0, weight=1 )
		self.grid_columnconfigure( 0, weight=1 )

		self.__canvas.grid_rowconfigure( 0, weight=1 )
		self.__canvas.grid_columnconfigure( 0, weight=1 )

	#end __setup_subwidgets

	def __setup_label( self ):
		o_label=Label( self.__subframe, text=self.__label_name, justify=self.__labeljustify )
		o_label.config( width=self.__lablewidth )
		o_label.grid( row=0, column=0 )
	#end __setup_label

	def __setup_buttons( self ):

		self.__make_radio_buttons()

		return

	#end __setup_entries

	def __make_radio_buttons( self ):

		i_rowcount=0

		s_state="enabled"
		if self.__isenabled==False or self.__force_disable==True:
			s_state="disabled" 
		#end if enabled else not

		for idx in range( len( self.__modes ) ):

			#modes is a list of sequences, pairs
			#giving ( buttontext, buttonvalue):
			s_text, v_value=self.__modes[ idx ]
			
			i_rowcount+=1

			self.__current_button_value.set( v_value )
			
			o_radio_button=Radiobutton( self.__subframe, 
										text=s_text,
										variable=self.__current_button_value,
										value=v_value,
										command=self.__on_button_change,
										state=s_state )
			
			self.__tooltip=ctt.insertNewlines( self.__tooltip )
			o_tooltip=ctt.CreateToolTip( o_radio_button,  self.__tooltip )

			i_row_val=i_rowcount
			i_column_val=0

			#if user wants buttons in a row
			#invert the default row,col vals:
			if self.__put_buttons_in_row == True:
				i_row_val=0
				i_column_val=i_rowcount
			#end if we want buttons in single row

			o_radio_button.grid( row = i_row_val, column = i_column_val, sticky=(NW) )

			if idx == self.__default_mode_number - 1:
				o_defaul_button=o_radio_button
			#end if this is the default button

		#end for each index

		self.__current_button_value.set( o_defaul_button.cget( "value" ) )

		return
	#end __make_value_row

	def __on_button_change( self, event=None ):

		if self.__isenabled == False or self.__force_disable == True:
			return
		else:
			self.__reset_value()
		#end

		#we also re-assign the parent attribute (if the caller gave us a ref to it) 
		#from which our key-value was derived
		if self.__associated_attribute is not None:
			
			#default object whose attribute is to be 
			#updated is the master to this keyvalframe object
			if self.__associated_attribute_object is None:
				setattr( self.__master, self.__associated_attribute, self.__value )
			else:
				setattr( self.__associated_attribute_object, self.__associated_attribute, self.__value )
			#eend if attribute object is None, then use master, else use object
		#end if caller passed a def 

		#if there is a command associated with a button change, execute:
		if self.__def_on_button_change is not None:
			self.__def_on_button_change()
		#end if change command

		return
	#end __on_button_change

	@property
	def val( self ):
		return self.__value
	#end getter

	@val.deleter
	def val( self ):
		del self.__value
		return
	#end deleter
#end class KeyCategoricalValueFrame


class KeyListComboFrame( Frame ):

	'''
	Description
	
	Revised KeyValueFrame
	substituting a combo box widget
	for the entry box used in KeyValFrame.

	The combobox updates the master
	(or other parent subframe) with its
	current selection.  Selections are always
	strings.

	This revised KeyValueFrame class was 
	motivated by pgguineestimator.py interface
	need to have a control by which users
	select a genepop file sampling 
	scheme. The the scheme name should then be a 
	variable by which to offer sampling parameters
	for the given sampling scheme, in I think 
	a dynamically loaded subframe.
	'''

	def __init__( self, s_name, 
			qs_choices,
			i_default_choice_number=1,
			o_master=None, 
			s_associated_attribute=None,
			o_associated_attribute_object=None,
			def_on_new_selection=None,
			i_labelwidth=15,
			i_cbox_width=20,
			b_is_enabled=True,
			s_label_justify='right',
			s_label_name=None,
			b_force_disable=False,
			s_tooltip = "" ):

		"""
		Param qs_choices, sequence of string values selectable in combobox
		Param i_default_choice_number gives the ith (one-indexed)
			item in modes, that is to be the active button,
			on intital presentation, and that gives the default value
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
		Param def_on_selebutton_change, if not None, execute the def
			after updating both the value and the attribute (if any).
			This def is to have no passed params.
		Param i_labelwidth gives the width the the Label widget.
		Param s_label_justify gives Label widget "justify" value.
		Param s_label_name, if not None, replaces s_name as the text for the label.
		Param b_force_disable, if True, will override the b_is_enabled value and disable all entry 
			  boxes
		"""

		#TCL won't allow uppercase names for windows
		#(note that we save the name, case in-tact, in
		#member __name:
		Frame.__init__( self, o_master, name=s_name.lower() )
		self.__master=o_master
		self.__value=StringVar()
		self.__default_choice_number=i_default_choice_number
		self.__choices=qs_choices
		self.__name=s_name
		self.__lablewidth=i_labelwidth
		self.__cbox_width=i_cbox_width
		self.__labeljustify=s_label_justify
		self.__isenabled=b_is_enabled
		self.__associated_attribute=s_associated_attribute
		self.__associated_attribute_object=o_associated_attribute_object
		self.__def_on_new_selection=def_on_new_selection
		self.__label_name=self.__name if s_label_name is None else s_label_name
		self.__force_disable=b_force_disable
		self.__tooltip=self.__label_name if s_tooltip == "" else s_tooltip
		self.__subframe=None
		self.__setup()
	#end init

	def __setup( self ):
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
		self.__subframe=Frame( self.__canvas )

		self.__setup_label()
		self.__setup_combobox()

		self.__subframe_id=self.__canvas.create_window(0,0, anchor=NW, window=self.__subframe )
		o_horiz_scroll.config( command=self.__canvas.xview )

		self.__canvas.grid( row=0, column=0, sticky=( N,W,E,S ) )
		o_horiz_scroll.grid( row=1, column=0, sticky=(W,E) )
		
		self.grid_rowconfigure( 0, weight=1 )
		self.grid_columnconfigure( 0, weight=1 )

		self.__canvas.grid_rowconfigure( 0, weight=1 )
		self.__canvas.grid_columnconfigure( 0, weight=1 )

	#end __setup_subwidgets

	def __setup_label( self ):
		o_label=Label( self.__subframe, text=self.__label_name, justify=self.__labeljustify )
		o_label.config( width=self.__lablewidth )
		o_label.grid( row=0, column=0 )
	#end __setup_label

	def __setup_combobox( self ):

		i_rowcount=0

		s_state="enabled"

		if self.__isenabled==False or self.__force_disable==True:
			s_state="disabled" 
		#end if enabled else not

		o_combobox=Combobox( self.__subframe,
					textvariable=self.__value,
					width=self.__cbox_width )

		o_combobox[ 'values' ] = self.__choices

		o_combobox.bind("<<ComboboxSelected>>", self.__on_new_combobox_selection )

		#For PGParamSet object-derived text, we need to
		#substiture double-tildes with newlines.
		self.__tooltip=ctt.insertNewlines( self.__tooltip )
		o_tooltip=ctt.CreateToolTip( o_combobox,  self.__tooltip )

		o_combobox.grid( row = 0, column = 1, sticky=(NW) )
		
		#list items are zero-indexed, but clients pass a 1-indexed
		#referenc to combobox choices
		o_combobox.current( self.__default_choice_number - 1 )

		#initialize the parent attr and 
		#execute parent def if needed
		self.__on_new_combobox_selection()
		return
	#end __setup_combobox

	def __update_parent_attr_and_def( self ):

		s_current_val=self.__value.get()

		#updated is the master to this keyvalframe object
		if self.__associated_attribute_object is None:
			setattr( self.__master, self.__associated_attribute, s_current_val )
		else:
			setattr( self.__associated_attribute_object, self.__associated_attribute, s_current_val )
		#eend if attribute object is None, then use master, else use object

		#if there is a command associated with a button change, execute:
		if self.__def_on_new_selection is not None:
			self.__def_on_new_selection()
		#end if change command
	#end __update_parent_attr_and_def

	def __on_new_combobox_selection( self, event=None ):

		if self.__isenabled == False or self.__force_disable == True:
			return
		#end if disabled, do nothing


		self.__update_parent_attr_and_def()
		return
	#end __on_button_change

	@property
	def val( self ):
		return self.__value.get()
	#end getter

	@val.deleter
	def val( self ):
		del self.__value
		return
	#end deleter
#end class KeyListComboFrame


class FrameContainerScrolled( object ):
	'''
	Description
	Objects are arrangements of two Frames and a 
	Canvas, such that one frame contains the 
	canvas and 2nd frame, and the 2nd frame 
	is scrollable, either vertically or horizontally 
	(but not yet both, as of Thu Jun  2 19:59:32 MDT 2016 )
	

	Note that this is not a Tkinter object, but
	simply accomplishes the arragnement. 

	Note that this uses Fred Lundh's AutoScrollbar class
	(from http://effbot.org/zone/tkinter-autoscrollbar.htm)
	and depends on using only the grid geometry manager to place
	the scrollbar.
	'''

	SCROLLVERTICAL=0
	SCROLLHORIZONTAL=1

	def __init__( self, o_parent_frame, o_child_frame, o_canvas, 
			i_scroll_direction=SCROLLVERTICAL ):
		#need the top level window for the menu:
		self.__parent_frame=o_parent_frame
		self.__child_frame=o_child_frame
		self.__canvas=o_canvas
		self.__scroll_direction=i_scroll_direction
		self.__setup()
		return
	#end __init__

	def __setup( self ):

		#as of Thu Jun  2 20:23:03 MDT 2016, horizontal scrolling is not yet working
		#correctly:
#		if self.__scroll_direction==FrameContainerScrolled.SCROLLHORIZONTAL:
#			s_msg="In pguitilities.FrameContainerScrolled object instance, " \
#					+ "horizontal scrolling is not yet implemented, " \
#					+ "please construct with " \
#					+ "i_scroll_direction=FrameContainerScrolled.SCROLLVERTICAL" 
#			raise Exception( s_msg )
#		#end if horizontal	

		o_scroll=None

		self.__child_id=self.__canvas.create_window( 0,0,anchor=NW, window=self.__child_frame )

		if self.__scroll_direction==FrameContainerScrolled.SCROLLVERTICAL:
			o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=VERTICAL )
			self.__canvas.config( yscrollcommand=o_scroll.set )
			o_scroll.config( command=self.__canvas.yview )
			o_scroll.grid( row=0, column=2, sticky=( N, S ) )

		elif self.__scroll_direction==FrameContainerScrolled.SCROLLHORIZONTAL:
			o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=HORIZONTAL )
			self.__canvas.config( xscrollcommand=o_scroll.set )
			o_scroll.config( command=self.__canvas.xview )
			o_scroll.grid( row=2, column=0, sticky=( W, E ) )

		else:
			s_msg="In pguitilities.FrameContainerScrolled object instance, " \
					+ "invalid value for scroll direction: " \
					+ str( self.__scroll_direction ) + "."
			raise Exception( s_msg )
		#end if scroll dir vert, else horiz, else except

		self.__canvas.grid( row=0, column=0, sticky=( N,S,E,W) )

		self.__canvas.grid_rowconfigure( 0, weight=1 )
		self.__canvas.grid_columnconfigure( 0, weight=1 )

		self.__canvas.grid_rowconfigure( 1, weight=1 )
		self.__canvas.grid_columnconfigure( 1, weight=1 )
			
		self.__parent_frame.grid_rowconfigure( 0, weight=1 )
		self.__parent_frame.grid_columnconfigure( 0, weight=1 )
	
		self.__child_frame.bind( '<Configure>', self.__on_configure_child )
		self.__canvas.bind( '<Configure>', self.__on_configure_canvas )

		return
	#end __setup 

	def __on_configure_child( self, event ):
		
		#we need the scroll region and the canvas dims to 
		#always match the subframe dims.

		i_child_width, i_child_height=( self.__child_frame.winfo_reqwidth(), self.__child_frame.winfo_reqheight() )

		self.__canvas.config( scrollregion="0 0 %s %s" % ( i_child_width, i_child_height ) )
		self.__canvas.config( width=i_child_width )
		self.__canvas.config( height=i_child_height )

		return
	#end __on_configure_child

	def __on_configure_canvas( self, event ):
		#sync the child to canvas width only -- if you reset the height,
		#the lower part of the childframe is truncated when
		#scrolling down -- the scoll reveals nothing but bg:

		if self.__scroll_direction == FrameContainerScrolled.SCROLLVERTICAL:
			i_width_canvas=self.__canvas.winfo_width()
			self.__canvas.itemconfigure( self.__child_id, width=i_width_canvas )
		elif self.__scroll_direction == FrameContainerScrolled.SCROLLHORIZONTAL:
			i_height_canvas=self.__canvas.winfo_height()
			self.__canvas.itemconfigure( self.__child_id, height=i_height_canvas )
		else:
			s_msg="In pguitilities.FrameContainerScrolled object instance, " \
					+ "invalid value for scroll direction: " \
					+ str( self.__scroll_direction ) + "."
			raise Exception( s_msg )
		#end if scroll vert, else horiz, else except 

		return
	#end __on_configure_child

#end class FrameContainerScrolled

class FrameContainerVScroll( object ):
	'''
	Description
	Objects are arrangements of two Frames and a 
	Canvas, such that one frame contains the 
	canvas and 2nd frame, and the 2nd frame 
	is vertically scrollable.

	Note that this is not a Tkinter object, but
	simply accomplishes the arragnement. 

	Note that this uses Fred Lundh's AutoScrollbar class
	(from http://effbot.org/zone/tkinter-autoscrollbar.htm)
	and depends on using only the grid geometry manager to place
	the scrollbar.
	'''

	def __init__( self, o_parent_frame, o_child_frame, o_canvas  ):
		#need the top level window for the menu:
		self.__parent_frame=o_parent_frame
		self.__child_frame=o_child_frame
		self.__canvas=o_canvas
		self.__setup()
		return
	#end __init__

	def __setup( self ):

		self.__child_id=self.__canvas.create_window( 0,0,anchor=NW, window=self.__child_frame )

		o_scroll=FredLundhsAutoScrollbar( self.__parent_frame, orient=VERTICAL )

		self.__canvas.config( yscrollcommand=o_scroll.set )

		o_scroll.config( command=self.__canvas.yview )

		o_scroll.grid( row=0, column=2, sticky=( N, S ) )

		self.__canvas.grid( row=0, column=0, sticky=( N,S,E,W) )

		self.__canvas.grid_rowconfigure( 0, weight=1 )
		self.__canvas.grid_columnconfigure( 0, weight=1 )

		self.__canvas.grid_rowconfigure( 1, weight=1 )
		self.__canvas.grid_columnconfigure( 1, weight=1 )
			
		self.__parent_frame.grid_rowconfigure( 0, weight=1 )
		self.__parent_frame.grid_columnconfigure( 0, weight=1 )

	
		self.__child_frame.bind( '<Configure>', self.__on_configure_child )
		self.__canvas.bind( '<Configure>', self.__on_configure_canvas )

		return
	#end __setup 

	def __on_configure_child( self, event ):
		
		#we need the scroll region and the canvas dims to 
		#always match the subframe dims.

		i_child_width, i_child_height=( self.__child_frame.winfo_reqwidth(), self.__child_frame.winfo_reqheight() )

		self.__canvas.config( scrollregion="0 0 %s %s" % ( i_child_width, i_child_height ) )
		self.__canvas.config( width=i_child_width )
		self.__canvas.config( height=i_child_height )

		return
	#end __on_configure_child

	def __on_configure_canvas( self, event ):
		#sync the child to canvas width only -- if you reset the height,
		#the lower part of the childframe is truncated when
		#scrolling down -- the scoll reveals nothing but bg:

		i_width_canvas=self.__canvas.winfo_width()

		self.__canvas.itemconfigure( self.__child_id, width=i_width_canvas )
		return
	#end __on_configure_child
		
#end class FrameContainerVScroll

class PGGUIErrorMessage( object ):
	def __init__( self, o_parent, s_message ):
		tkMessageBox.showerror(  parent=o_parent, title="Error", message=s_message )
		return
	#end __init__
#End class PGGUIErrorMessage

class PGGUIWarningMessage( object ):
	def __init__( self, o_parent, s_message ):
		tkMessageBox.showinfo(  parent=o_parent, title="Warning", message=s_message, icon=tkMessageBox.WARNING )
		return
	#end __init__
#End class PGGUIWarningMessage

class PGGUIInfoMessage( object ):
	def __init__( self, o_parent, s_message ):
		tkMessageBox.showinfo(  parent=o_parent, title="Info", message=s_message, icon=tkMessageBox.INFO )
		return
	#end __init__
#End class PGGUIInfoMessage

class PGGUIMessageAndActionOnCancel( object ):
	def __init__( self, o_parent, s_message, def_on_cancel ):
		o_msgbox=tkMessageBox.showinfo( parent=o_parent, title="Info", message=s_message, icon=tkMessageBox.INFO )
		return
	#end __init__
#end class PGGUIInfoMessage

class PGGUIYesNoMessage( object ):
	def __init__( self, o_parent, s_message ):
		o_msgbox=tkMessageBox.askyesno( parent=o_parent, title="Info", message=s_message, icon=tkMessageBox.INFO )
		self.value=o_msgbox
		return
	#end __init__
#end class PGGUIInfoMessage

class RightClickMenu( Menu ):

	def __init__( self, o_parent, ddefs_by_label={} ):

		Menu.__init__( self, o_parent, tearoff=0 )

		for s_label in ddefs_by_label:
			self.add_command( label=s_label, 
							command=ddefs_by_label[ s_label ] )
		#end for each label/command, add to menu

		o_parent.bind( "<Button-3>", self.__popup ) 

		return
	#end __init__

	def __popup( self, event ):
		print( "in popup" )
		self.post( event.x_root, event.y_root )
		return
	#end __popup
#end class RightClickMenu

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
	'''

	def __init__( self, 
					o_master, 
					lv_list, 
					def_to_call_when_list_changes=None,
					v_default_value=0.0,
					s_state="enabled",
					i_control_width=10,
					o_acceptable_item_type=float,
					b_allow_none_value_for_list=True ):

		self.__validate_list( lv_list, o_acceptable_item_type  )

		Frame.__init__( self,  o_master )
		
		self.__mylist=[ v_val for v_val in lv_list  ]
		self.__def_to_call_when_list_changes=def_to_call_when_list_changes
		self.__default_value=v_default_value
		self.__state=s_state
		self.__control_width=i_control_width
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

		i_num_entries=len( self.__mylist )

		o_editing_subframe=self

		self.__btn_extend=Button( self,
								text="Extend",
								command=self.__extend_list,
								state=self.__state,
								width=self.__control_width )

		self.__btn_trim=Button( self, text="Trim", 
								command=self.__trim_list,
								state=self.__state,
								width=self.__control_width )

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

		self.__btn_extend.grid( row=0, column=self.BTN_COL_EXTEND )
		self.__btn_trim.grid( row=0, column=self.BTN_COL_TRIM )
		self.__label_assign.grid( row=0, column=self.LABEL_COL_ASSIGN )
		self.__entry_from.grid( row=0, column=self.ENTRY_COL_FROM )
		self.__label_to.grid( row=0, column=self.LABEL_COL_TO )
		self.__entry_to.grid( row=0, column=self.ENTRY_COL_TO )
		self.__label_assign_val.grid( row=0, column=self.LABEL_COL_VALUE )
		self.__entry_assign_val.grid( row=0, column=self.ENTRY_COL_VALUE )
		self.__btn_assign.grid( row=0, column=self.BTN_COL_ASSIGN )

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

		print( "in extend with mylist: " + str( self.__mylist ) )

		lv_newlist=self.__get_copy_mylist()

		print ( "in extend with copy list: " + str( lv_newlist ) )
		print ( "in extend with defaultval: " + str( self.__default_value) )
		v_value_to_add=self.__default_value


		'''
		If we have at least one item in 
		the list, use the last item's
		value as the appended value:
		''' 
		if len( lv_newlist ) > 0:
			v_value_to_add=self.__mylist[ len( self.__mylist ) - 1 ]
		#end if list has at least one item

		print( "in extend with value to add " + str( v_value_to_add ) ) 
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

if __name__=="__main__":
	import pgutilities as modut
	import test_code.testdefs as td

	ls_args=[ "test number" ]

	s_usage=modut.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage
	
	s_test_number=sys.argv[ 1 ]

	ddefs={ 1:td.testdef_pgguiutilities_1,
			2:td.testdef_pgguiutilities_2 }
	
	ddefs[ int( s_test_number ) ] ( )

#end if  __main__

