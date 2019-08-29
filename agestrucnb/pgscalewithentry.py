'''
Description
This class creates a Frame that has atkinter.Scale widget (note
this is not the ttk.Scale, which lacks some features
in the tkinter version, which I wanted to keep).  It
adds an entry box, as implemented by KeyValueFrame, 
that is user editable, and also sets the scale to 
the value entered.  Likewise, when the Scale is reset,
its current value updates the Entry.
'''
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

__filename__ = "pgscalewithentry.py"
__date__ = "20171020"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from tkinter import *
from tkinter.ttk import *

from agestrucne.pgkeyvalueframe import KeyValFrame
from agestrucne.pgutilityclasses import FloatIntStringParamValidity
from agestrucne.pgutilityclasses import ValueValidator
'''
We use this reference to specify the tkinter Scale instead of 
the ttk.Scale.
'''
import tkinter as tki
from agestrucne.pgguiutilities import PGGUIErrorMessage
from agestrucne.pgguiutilities import PGGUIInfoMessage

class PGScaleWithEntry( Frame ):
	'''
	This class extends the tkinter.Scale widget (note
	this is not the ttk.Scale, which lacks some features
	in the tkinter version, which I wanted to keep).  It
	adds an entry box, as implemented by KeyValueFrame, 
	that is user editable, and also sets the scale to 
	the value entered.  Likewise, when the Scale is reset,
	its current value updates the Entry.
	'''

	ROWNUM_SCALE=0
	ROWNUM_ENTRY=1
	COLNUM_SCALE=0
	COLNUM_ENTRY=0

	def __init__( self,
					o_master_frame=None,
					def_scale_command=None,
					v_orient=HORIZONTAL,
					f_scale_from=0.0,
					f_scale_to=0.0,
					f_resolution=1.0,
					f_bigincrement=0.0,
					s_scale_label="",
					i_scale_length=100,
					i_entry_width=10,
					i_length=100 ): 
		Frame.__init__( self, o_master_frame ),

		self.__scale_command_def=def_scale_command					
		self.__orient=v_orient
		self.__resolution=f_resolution
		self.__bigincrement=f_bigincrement 
		self.__scale_length=i_scale_length
		self.__entry_width=i_entry_width
		self.__scale_from=f_scale_from
		self.__scale_to=f_scale_to
		self.__scale_label=s_scale_label
		
		self.__scale=None
		self.__entry=None
		self.__entry_value=None
		self.__entry_validator=None
		
		self.__setup_widgets()

		return
	#end __init__

	def __setup_widgets( self ):
		self.__setup_scale()
		self.__setup_entry()
		return
	#end __setup_widgets

	def __setup_scale( self ):

		o_myc=PGScaleWithEntry

		self.__scale=tki.Scale( self, 
						from_=self.__scale_from,
						to = self.__scale_to,
						command=self.__on_scale_change,
						orient=HORIZONTAL,
						resolution=self.__resolution,
						bigincrement=self.__bigincrement,
						length=self.__scale_length,
						label=self.__scale_label )

		self.__scale.grid( row=o_myc.ROWNUM_SCALE, 
							column=o_myc.COLNUM_SCALE, 
											sticky=(N,W) )

		return
	#end __setup_scale

	def __setup_entry( self ):

		myc=PGScaleWithEntry
		self.__entry_value=float( self.__scale.get() )

		o_validator=None

		o_config_kv=KeyValFrame( s_name="Set scale to:", 
						v_value= self.__entry_value,
						o_type=float,
						v_default_value=0.0,
						o_master=self,
						o_associated_attribute_object=self,
						s_associated_attribute="_PGScaleWithEntry" \
									+ "__entry_value",
						def_entry_change_command=self.__on_entry_change,
						i_entrywidth=self.__entry_width,
						i_labelwidth=10,
						b_is_enabled=True,
						s_entry_justify='left',
						s_label_justify='left',
						b_force_disable=False,
						s_tooltip = "Use the slider or set the value in the entry box.",
						o_validity_tester=o_validator,
						i_entry_row= 1,
						i_entry_col=-1,
						i_label_row=0, 
						i_label_col=0 )
		
		self.__entry=o_config_kv
		self.__entry.grid ( row=myc.ROWNUM_ENTRY, 
								column=myc.COLNUM_ENTRY, sticky=(N,W) )
	#end __setup_entry

	def __get_current_scale_range( self ):

		f_min=None 
		f_max=None

		s_errmsg="In PGScaleWithEntry instance, "  \
					+ "def __get_current_scale_range, " \
					+ "the program can't get the scale " \
					+ "range."

		if self.__scale is None:
				PGGUIErrorMessage( self, s_errmsg )
				raise Exception( s_errmsg )
		#end if no scale
		
		try: 
			f_min=self.__scale[ 'from' ]
			f_max=self.__scale[ 'to' ]
		except Exception as oex:
			s_errmsg=s_errmsg \
						+ "An exception occurred: "  \
						+ str( oex )
			PGGUIErrorMessage( s_errmsg )
			raise Exception( oex )
		#end try...except....	

		return f_min, f_max
	#end __get_current_scale_range

	def __on_scale_change( self, o_event=None ):
		PRECISION=1e-10
		f_current_scale_val=float( self.__scale.get() )

		if self.__entry is not None:
			if self.__entry_value is not None:
				if abs( self.__entry_value - f_current_scale_val ) > PRECISION:
					self.__entry.manuallyUpdateValue( f_current_scale_val )
				#end if scale value and entry value are not effectively  the same, reset the entry
			#end if we have an entry value
		#end if we have an entry widget
		self.__scale_command_def( o_event )
		return
	#end __on_scale_change

	def __on_entry_change( self, o_event=None ):
		'''
		We assume we have an existing scale widget. We set the scale
		and the entry to min or max if user entered a val too small
		or large, else we set scale to entry value (or closest resolved
		value as determined by resolutioin and bigincrement).
		'''
		
		f_temp_old_scale_val=self.__scale.get()

		if self.__entry_value > self.__scale[ 'to' ]:
			self.__scale.set( self.__scale[ 'to' ] )
		elif self.__entry_value < self.__scale[ 'from' ]:
			self.__scale.set( self.__scale[ 'from' ] )
		else:
			self.__scale.set( self.__entry_value )
			
		#end if over max, else under min, else valid

		'''
		If the entry's value resolved to the same
		value as the last, then the __on_scale_change
		command wasn't be called, so we need to update the 
		entry back to the scale value, else they
		will show as different
		'''
		if f_temp_old_scale_val == self.__scale.get():
			self.__on_scale_change()
		#end if we need to update entry value	
		return
	#end __on_entry_change

	@property
	def scale( self ):
		return self.__scale
	#end property scale

#end class PGScaleWithEntry	

if __name__ == "__main__":
	def my_scale_activity( self, o_event=None ):
		print( "my scalewithentry value changed"  )

	#end

	of=Tk()
	os=PGScaleWithEntry( o_master_frame=of,
				def_scale_command=my_scale_activity,
				v_orient=HORIZONTAL,
				f_scale_from=0.0,
				f_scale_to=10.0,
				f_resolution=1.0,
				f_bigincrement=0.0,
				s_scale_label="",
				i_scale_length=100,
				i_entry_width=20  )
	
	os.grid()

	of.mainloop()

#end if main

