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

	'''

	VERBOSE=False

	def __init__( self, s_name, v_value, 
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
			o_validity_tester = None ):
		
		"""
		Param s_name provides the label text.
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

		"""
		#TCL won't allow uppercase names for windows
		#(note that we save the name, case in-tact, in
		#member __name:
		Frame.__init__( self, o_master, name=s_name.lower() )
		self.__master=o_master
		self.__store_value( v_value )
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
		self.__idx_none_values=[]
		self.__item_types=[]
		self.__entryvals=[]
		self.__label_name=self.__name if s_label_name is None \
												else s_label_name
		self.__subframe=None
		self.__setup()


	#end init

	def __store_value( self, v_value ):
		if type( v_value ) != list:
			self.__value = [ v_value ]
		else:
			self.__value=v_value 
		#end if scalar, else list

		#because we store all values as a list,
		#we use this flag to tell us how to update 
		#the parent attribute (if any),
		#and how to return a request for the value --
		#i.e. return as a list, or as a scalar, whichever
		#was the original type:
		self.__orig_value_is_list=type( v_value ) == list
		return
	#end __store_value
	
	def __reset_value( self, idx_val ):

		o_type=self.__item_types[ idx_val ]
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

			#if a currently "None" value, we check to see
			#if the new value is valid for the replacement type
			#as given in the init def:
			elif  o_type.__name__ == 'NoneType':
				if o_entryval.get() != "None":
					v_newval=self.__type_replaces_none( o_entryval.get() )
					#if the type coersion worked, we now reset the stored
					#list of types so that this item is now the new type:
					self.__item_types[ idx_val ] = self.__type_replaces_none
				else: #no change to value or type if None is still in entry as "None"
					v_newval=None
				#end if entry string is not "None" else is

			#if user entered "None" to return to an original value of None:
			elif o_entryval.get() == "None" and idx_val in self.__idx_none_values:
				v_newval=None
				#return to nonetype:
				self.__item_types[ idx_val ] = type( None )
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
			#end if bool and not 0 or 1

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

	def __setup_entries( self ):

		self.__make_value_row()

		return

	#end __setup_entries

	def __setup_button( self ):

		if self.__button_command is None:
			return
		else:
			o_button=Button( self.__subframe, text=self.__button_text, command=self.__button_command )
			i_num_entries = len( self.__value ) 
			o_button.grid( row=0, column=i_num_entries+1 )
		#end if we don't have a command def

		return
	#end _setup_button

	def __make_entry( self, o_strvar ):
		s_enabled="enabled"
		if self.__isenabled==False:
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

		return o_entry

	#end __make_entry

	def __make_value_row( self ):
		i_num_vals=len( self.__value )
		i_colcount=0
		for idx in range( i_num_vals ):
			i_colcount+=1
			o_strvar = StringVar()
			o_strvar.set( self.__value[idx] )
			o_entry=self.__make_entry( o_strvar ) 

			if i_num_vals > 1: 
				o_tooltip=ctt.CreateToolTip( o_entry, self.__label_name \
							+ ", item " + str( idx + 1 ) )
			#end if more than one value, make tool tip

			self.__item_types.append( type( self.__value[idx] ) )

			if self.__item_types[ idx ].__name__=="NoneType":
				self.__idx_none_values.append( idx )
			#end if None type, record the index

			self.__entryvals.append( o_strvar  )
			o_entry.grid( row = 0, column = i_colcount )
			o_entry.bind( '<Return>', self.__on_enterkey )
			o_entry.bind( '<Tab>', self.__on_enterkey )
		#end for each index
		return
	#end __make_value_row

	def __update_list( self ):

		lv_newlist=[]

		for idx in range ( len(  self.__entryvals ) ):
			v_newval=self.__reset_value( idx )
			lv_newlist.append( v_newval )
		#end for each strvar
		
		self.__value=lv_newlist

		return

	#end __update_list

	def __on_enterkey( self, event=None ):

		if self.__isenabled == False:
			return
		#end

		i_len_entryvals=len( self.__entryvals )
		i_len_vals=len( self.__value )

		if i_len_entryvals == i_len_vals:
			self.__update_list()
		else:
			raise Exception ( "In KeyValFrame instance, the current entry values " \
						+ " are not equal to length of the value list" )
		#end if lengths same else not
	
		#Because we store even scalars as list items, we extracnt the 
		#value for updating the client's attribute or sending to 
		#client's def -- we returnn a list only if orig was a list, else return scalar
		v_attr_val=self.__value if self.__orig_value_is_list else self.__value[0]

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
							+ " to value: " + str( v_attr_val ) )
				#end if verbose

				setattr( self.__master, self.__associated_attribute, v_attr_val )
			else:
				setattr( self.__associated_attribute_object, self.__associated_attribute, v_attr_val )
			#eend if attribute object is None, then use master, else use object

		#end if caller passed an attribute 

		#if there is a command associated with an update in the entry (or list of entries), execute:
		if self.__entry_change_command is not None:
			self.__entry_change_command()
		#end if entry change command is not none

		return
	#end __on_enterkey

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
	#end deleter
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
			b_buttons_in_a_row=False ):

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
		"""

		#TCL won't allow uppercase names for windows
		#(note that we save the name, case in-tact, in
		#member __name:
		Frame.__init__( self, o_master, name=s_name.lower() )
		self.__master=o_master
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
		if self.__isenabled==False:
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

		if self.__isenabled == False:
			return
		else:
			self.__reset_value()
		#end

		#we also re-assign the parent attribute (if the caller gave us a ref to it) from which our key-value was derived
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



