'''
Description

2017_03_25.  This class was extracted from the
pgguiutilities.py module, so that it is easier
to debug.
'''
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
__filename__ = "pgkeycategoricalvalueframe.py"
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
class KeyCheckboxValueFrame( PGKeyControlFrame ):

	'''
	Description
	
	Revised KeyValueFrame
	substituting a Checkbutton widget
	for the entry box used in KeyValFrame
	
	'''

	def __init__( self, s_name, 
			v_value=True,
			o_master=None, 
			s_associated_attribute=None,
			o_associated_attribute_object=None,
			def_on_button_change=None,
			i_labelwidth=15,
			b_is_enabled=True,
			s_label_justify='right',
			s_label_name=None,
			b_force_disable=False,
			s_tooltip = "" ):

		"""
		Param lq_modes, list of sequences, each a pair
		    giving the mode label text, and its associated value
			assigned when it is the selected radio button
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
		Param s_label_name, if not None, replaces s_name as the text for the label.
		Param b_force_disable, if True, will override the b_is_enabled value and disable all entry 
			  boxes
		"""

		PGKeyControlFrame.__init__( self, o_master, name=s_name.lower() )

		self.__master=o_master
		self.__value=v_value
		self.__name=s_name
		self.__lablewidth=i_labelwidth
		self.__labeljustify=s_label_justify
		self.__isenabled=b_is_enabled
		self.__associated_attribute=s_associated_attribute
		self.__associated_attribute_object=o_associated_attribute_object
		self.__def_on_button_change=def_on_button_change
		self.__label_name=self.__name if s_label_name is None else s_label_name
		self.__force_disable=b_force_disable
		self.__tooltip=self.__label_name if s_tooltip == "" else s_tooltip
		self.__subframe=None

		#To maintain a reference to the Checkbutton object,
		#this will be appended-to as they are created:
		self.__check_button=None

		self.__current_button_value=BooleanVar()
		self.__current_button_value.set( v_value )
		self.__setup()

	#end init

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
		self.label=o_label
	#end __setup_label

	def __setup_button( self ):

		self.__make_check_button()

		return

	#end __setup_entries

	def __make_check_button( self ):
	
		i_row_val=0
		i_column_val=0

		s_state="enabled"
		if self.__isenabled==False or self.__force_disable==True:
			s_state="disabled" 
		#end if enabled else not

			
		self.__check_button=Checkbutton( self.__subframe, 
									onvalue=True,
									offvalue=False,
									text=self.__name,
									variable=self.__current_button_value,
									command=self.__on_button_change,
									state=s_state )
	
		self.__tooltip=ctt.insertNewlines( self.__tooltip )
		o_tooltip=ctt.CreateToolTip( self.__check_button,  self.__tooltip )



		self.__check_button.grid( row = i_row_val, column = i_column_val, sticky=(NW) )

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

	def setStateControls( self, s_state ):
		'''
		Set the Checkbutton's state.
		'''
		self.__check_button.configure( state=s_state )

		return
	#end disableControls

	def getControlStates( self ):

		return str( self.__check_button.cget( "state" ) )

	#end getControlStates

	@property
	def is_enabled( self ):
		return self.__isenabled
	#end property is_enabled

	@property
	def force_disable( self ):
		return self.__force_disable
	#end property force_disable

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

if __name__ == "__main__":

	class myattr( object ):
		def __init__( self, vval=False ):
			self.vval=vval
		#end __init__
	#ende myattr	

	omya=myattr(True)

	myr=Tk()

	def lookatvval():
		print( "vval in mya: " + str( omya.vval ) )
		return
	#end lookatmya

	mycb=KeyCheckboxValueFrame( s_name="mybool", 
			v_value=omya.vval,
			o_master=myr, 
			s_associated_attribute="vval",
			o_associated_attribute_object=omya,
			def_on_button_change=lookatvval,
			i_labelwidth=15,
			b_is_enabled=True,
			s_label_justify='right',
			s_label_name=None,
			b_force_disable=False,
			s_tooltip = "" )

	mycb.grid()

	myr.mainloop()
	pass
#end if main

