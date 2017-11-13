'''
Description

Builds a Tkinter menu bar and menus using a configuration file.  See class description.

'''
from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object
__filename__ = "pgmenubuilder.py"
__date__ = "20160123"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import os
import configparser as modCP
from tkinter import Menu

class PGMenuBuilder(object):
	'''
	Instantiates a tkinter menu_bar, with parent gui object (usually the main window) 
	as given by __init__ param, and populates it by reading a list of menu items and 
	parameters from a configuration file, also an __init__ param. The menus get their 
	command callback defs, as named in the configuration file, in the class object 
	passed as init param o_pg_gui_app.

	The configuration file key=value entries inside each [section] are of two classes:

	1. keys that are not param keywords for the call to menu.add_command.  These include 
		(a) "parent=value", which tells the
		builder which of the file labels (sections in the config file) is the parent menu
		to it's submenu.  As of 20160116 this is not implemented, and only parent=None (unquoted) 
		is allowed.
		(b) "menu_underline=value", where value is an (zero-based) index into the menu label name 
		(as given by the section name).

	2. key=value pairs whose keys are param keywords (like "accelerator").  Keys must match exactly
		prarm names in the menu.add_command definition's param list.  Their values should be 
		entered in square brackets like a python list, with one entry for each of the menu items.  
		If the nth item is to be "seperator" item, the nth item in the label list should be 
		"sep", and other items like "command" or accelerator, can be any value (ex: None), 
		as they will be ignored.

	For example, a menubar with 2 items "File" and "Edit", each with 2 menu items, with
	Edit having a seperator between its items would look like this: 

	#file menu
	[File]
	parent=None
	#which characters to underline in the File label:
	menu_underline=0
	label=[ "New" , "Open" ]
	#which characters to underline in the menu items:
	underline=[ 0, 0 ]
	accelerator=[ "Ctrl+N","Ctrl+O" ]
	command=[ "new_file", "open_file" ]

	#edit menu
	[Edit]
	parent=None
	menu_underline=0
	label=["Undo","sep","Options"]
	underline=[ 1,None, 1 ]
	accelerator=["Ctrl+Z", None, "Ctrl+T"]
	command=[ "undo", None, "showopts" ]  
    '''

	CONFIG_OPTIONS_NON_COMMAND_ARGS=[ "parent", "menu_underline", "menu_accelerator" ]

	def __init__( self, s_config_file, o_pg_gui_app,  o_tk_master, i_tearoff=0 ):
		'''
		param s_config_file gives menu attribute values (see module documentation)
		param o_pg_gui_app is a class object that has the definitions
				that match the command names to be bound to the menus ('command' 
				option values in the config file). It also has a member Tk()
				root window object that the menu builder assigns to member "parent"
		param i_tearoff tells the gui whether the menu items can be dragged off of 
			the parent menubar (tearoff=1) or not (tearoff=0)
		'''
		self.__menubar = None
		self.__pg_gui_app = o_pg_gui_app
		self.__tearoff = i_tearoff
		self.__parent=o_tk_master
		o_config = self.__get_menu_info( s_config_file )
		self.__build_menu( o_config )
		return
	#end init



	def __get_menu_info( self, s_config_file ):
		o_config = modCP.ConfigParser()
		try:
			o_file=open( s_config_file, 'r' )
			o_config.readfp( o_file )

		except IOError as ioe:
			sys.stderr.write( "PGMenuBuilder Instance is unable to read file, " \
				+ s_config_file  + "\n" )
			raise ioe
		#end try . . . except
		return o_config
	#end __get_menu_info

	def __build_menu( self, o_config ):
		self.__menubar = Menu( self.__parent )
		for s_menu_label in o_config.sections():
			self.__add_menu_item ( o_config, s_menu_label )
		#end for each menu
		self.__parent.config( menu=self.__menubar )
		return
	#end __build_menu	
    

	def __get_num_labels_menu( self, o_config, s_top_menu_label ):
		'''
		num labels should equal number of values
		for all of the options like accelerator and
		underline.  hence this def called to know
		how many menu.add_command calls needed 
		to make menu
		'''
		s_label = o_config.get( s_top_menu_label, "label" ) 
		l_labels = eval( s_label )
		
		return( len( l_labels ) )
	#end __get_num_labels_menu

	def get_add_command_params_and_args( self,  o_config, s_menu_label ):
		'''
		returns a list of dictionaries, one for each menu item, of the param=value
		settings for calls to menu.add_command.  We skip the config key=value for keys
		that are not part of the params needed for add_command. 
		'''
		l_keyword_menu_params = o_config.options( s_menu_label )	

		#how many items on this menu should equal number of labels:
		i_num_items = self.__get_num_labels_menu( o_config, s_menu_label )

		ld_args = [ {} for idx in range( i_num_items ) ]

		#for each submenu item, we get a dict of keyword:value to pass to "add_command"
		for s_keyword in l_keyword_menu_params:
			s_vals=o_config.get( s_menu_label, s_keyword )

			#for each keyword that is a param name in the menu.add_command call
			if s_keyword not in PGMenuBuilder.CONFIG_OPTIONS_NON_COMMAND_ARGS:

				l_vals=eval( s_vals )

				if len( l_vals ) != i_num_items:
					raise Exception( "in pgmenubuilder, config entry should have " \
							+ "one item for each label, but the option with keyname, " \
							+ s_keyword + " does not." )
				#end if wrong number values
				
				#if this is the list of command values (callback defs) 
				#for each submenu item,
				#then we must be able to find it among the attributes
				#of our member operation object
				#note: if "sep" is the label, we set other param values 
				#to None, but they are ignored (see for loop below)
				if s_keyword =="command":
					l_vals = [ getattr( self.__pg_gui_app, thisval ) \
							if thisval is not None \
							else None for thisval in l_vals ]
				#end if command list

				for idx in range( i_num_items ):
					ld_args[ idx ][ s_keyword ] = l_vals[ idx ]
				#end for each item
			#end if not a param keyword for add_command
		#end for each keyword

		return ld_args
    #end def get_add_command_params_and_args

	def __get_menu_values( self, o_config, s_menu_label ):

		v_parent_value=eval( o_config.get( s_menu_label, "parent" ) )

		if v_parent_value is not None:
			raise Exception ( "for section " + s_menu_label \
				   + ", parent value is " + str( v_parent_value) \
				   + ".  Submenus are not yet implemented. " \
				   + "Under this section please set parent=None in " \
				   + "the configuraton file" )
		#end if non-None for parent

		i_underline=eval( o_config.get( s_menu_label, "menu_underline" ) )

		if o_config.has_option( s_menu_label, "menu_accelerator" ):
			s_accelerator=eval( o_config.get( s_menu_label, "menu_accelerator" ) )


			'''
			while linux and osx were igoring the accelerator text when
			labelling the top-level menu, Windows (win10 and 7) were concatenating
			the label text with the accel text.  Leaving out the accelerator arg
			when menu building de-activated the underline-char accel. in all
			platforms.  
				Adding an empty string by using double quote ("\"\"") for "eval"
			to the menu config file evals fine in all platforms,
			but windows concats double-quotes to the main menu labels.			
			this test and reassignment is the fix:
			'''
			if s_accelerator=="\"\"":
				s_accelerator=""
			#end if accel is empty string
		else:
			s_accelerator=None
		#end if accelerator, add

		return { "parent":v_parent_value, "underline":i_underline, "accelerator":s_accelerator }
	#end __get_menu_values

	def __add_menu_item( self, o_config, s_menu_label ):

		#this will be the menu labeled s_menu_label (ex: "File" menu)
		#and the command items (like "Open" or "Save""Save") are then added
		#to this item using the o_config objects options:
		o_this_menu = Menu( self.__menubar, tearoff = self.__tearoff ) 

		ld_args = self.get_add_command_params_and_args(  o_config, s_menu_label )

		for d_args in ld_args:
			if d_args[ "label" ] == "sep":
				o_this_menu.add_separator()
			else:
				o_this_menu.add_command( **d_args )
			#end if seperator, else sub menu
		#end for each set of args

		dv_menu_values = self.__get_menu_values( o_config, s_menu_label )

		s_accel = dv_menu_values[ "accelerator" ] if dv_menu_values[ "accelerator" ] is not None  else None

		self.__menubar.add_cascade( label = s_menu_label, 
			menu = o_this_menu, 
			underline=dv_menu_values[ "underline" ],
			accelerator=s_accel )
		return

	#end __add_menu_item

	@property
	def menu(self):
		"""menu, tk.TKMenu object"""
		return self.__menubar
	#end menu getter

	@menu.setter
	def menu( self, i_value ):
		raise Exception( "in PGMenuBuilder object, " \
		+ "there is no setter for the menu object. " )
	#end menu setter

	@menu.deleter
	def menu(self):
		del self.__menubar
	#end menu deleter

#end class PGMenuBuilder

