'''
Description

2017_03_25.  This class was extracted from the
pgguiutilities.py module, in order to ease debugging.
'''
from future import standard_library
standard_library.install_aliases()
__filename__ = "pgkeylistcomboframe.py"
__date__ = "20170325"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from tkinter import *
from tkinter.ttk import *
import agestrucne.createtooltip as ctt
import sys
from agestrucne.pgguiutilities import FredLundhsAutoScrollbar
from agestrucne.pgguiutilities import PGGUIInfoMessage
from agestrucne.pgguiutilities import PGGUIYesNoMessage
from agestrucne.pgguiutilities import PGGUIErrorMessage

'''
2017_04_18.  To consolidate some of the objects and functions
common to the key-value-frame classes, we add a second parent class.
'''
from agestrucne.pgkeycontrolframe import PGKeyControlFrame

class KeyListComboFrame( PGKeyControlFrame ):

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
			o_validity_tester=None,
			s_state='readonly',
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
		Param s_state, if (default) readonly, user can only select dropdown list items, if 'normal'
			  user can enter text as well, and if 'disabled' no change possible.
		Param o_validity_tester, object used to validate entry on combobox selection.  For details
			 see attribute of same name in class KeyValFrame
		"""

		PGKeyControlFrame.__init__( self, o_master, name=s_name.lower() )

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
		self.__validity_tester=o_validity_tester
		self.__tooltip=self.__label_name if s_tooltip == "" else s_tooltip
		self.__cbox_state=s_state,
		self.__subframe=None

		'''
		We want a reference to the combobox
		in order to use it to recreate the
		tooltip in def __on_new_combobox_selection:
		'''
		self.__combobox=None

		self.__setup()
		return	
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
		'''
		Added 2017_04_18, the label attribute is implemented in the
		new PGKeyControlFrame parent class.
		'''
		self.label=o_label
	#end __setup_label

	def __setup_combobox( self ):

		i_rowcount=0

		s_state=self.__cbox_state

		if self.__isenabled==False or self.__force_disable==True:
			s_state="disabled" 
		#end if enabled else not

		'''
		Registering and assigning the validation def does
		fire on the first leave focus on Linux.  I added this
		in an attempt to get a call to the on_new_combobox_selection
		def (which does validation), when the mouse pointer leaves
		the combobox. It does fire the first time, but not thereaafter
		(see cbox event bindings below).
		'''
		o_registered_validation=self.register( \
				self.__validate_per_registered_command )

		o_combobox=Combobox( self.__subframe,
					textvariable=self.__value,
					state=s_state,
					width=self.__cbox_width,
					validate='focusout',
					validatecommand=( o_registered_validation, '%P' ) )

		o_combobox[ 'values' ] = self.__choices

		o_combobox.bind("<<ComboboxSelected>>", self.__on_new_combobox_selection )
		'''
		Putatively, says tkk dpocuments, to fire when mouse pointer leaves
		the widget, but, in Linux at least, it does not fire.
		'''
		o_combobox.bind( '<Leave>', self.__on_new_combobox_selection )
		'''
		Fails except on first leaving focus, in Linux at least.
		'''
		o_combobox.bind( '<FocusOut>', self.__on_new_combobox_selection )
		o_combobox.bind( '<Return>', self.__on_new_combobox_selection )
		o_combobox.bind( '<Tab>', self.__on_new_combobox_selection )

		#For PGParamSet object-derived text, we need to
		#substiture double-tildes with newlines.
		self.__tooltip=ctt.insertNewlines( self.__tooltip )
		o_tooltip=ctt.CreateToolTip( o_combobox,  self.__tooltip )

		o_combobox.grid( row = 0, column = 1, sticky=(NW) )
		
		#list items are zero-indexed, but clients pass a 1-indexed
		#reference to combobox choices
		o_combobox.current( self.__default_choice_number - 1 )

		self.__combobox_object=o_combobox

		#initialize the parent attr and 
		#execute parent def if needed
		self.__on_new_combobox_selection()
		return
	#end __setup_combobox

	def __validate_per_registered_command( self, v_val ):
		'''
		Crated this def, along with validation registration
		per ttk docs, in an attempt to get a call to the 
		selection def after mouse pointer leaves the cbox, 
		but very limited performance (see __setup_combobox
		above).
		'''
		self.__on_new_combobox_selection()
	#end __validate

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

		if self.__validity_tester is not None:

			s_val_to_test=s_current_val=self.__value.get()

			self.__validity_tester.value=s_val_to_test			

			if not self.__validity_tester.isValid():
				#message to user:
				s_msg=self.__validity_tester.reportInvalidityOnly()
				PGGUIInfoMessage( self, s_msg )
	
				#list items are zero-indexed, but clients pass a 1-indexed
				#referenc to combobox choices
				self.__combobox_object.current( self.__default_choice_number - 1 )
			else:
				self.__update_parent_attr_and_def()
			#end if not valid reset to default, else update
		else:
			self.__update_parent_attr_and_def()
		#end if we have a validity tester, else just update

		return
	#end __on_new_combobox_selection

	def setStateControls( self, s_state ):
		'''
		Set the state of all this objects
		radio buttons.
		'''
		if self.__combobox is not None:
			self.__combobox.configure( state=s_state )
		#end for each entry box

		return
	#end disableControls

	def getControlStates( self ):
		ls_states=[]

		if self.__combobox is not None:
			s_state=self.__combobox.cget( "state" )
			ls_states.append( s_state )
		#end for each entry box

		return ls_states
	#end 

	@property
	def is_enabled( self ):
		return self.__isenabled
	#end property is_enabled

	@property
	def force_disable( self ):
		return self.__force_disable
	#end force_disable

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







if __name__ == "__main__":
	pass
#end if main

