'''
Description
'''
__filename__ = "temp.py"
__date__ = "20160502"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from Tkinter import *
from ttk import *
import pgguiutilities as pgu


reload( pgu )

myr=Tk()

def geterr():
	pgu.PGGUIInfoMessage( myr, "warn1" )
	pgu.PGGUIInfoMessage( myr, "warn2" )
	pgu.PGGUIInfoMessage( myr, "warn2" )

mybutton=Button( myr, text="command", command=geterr )

mybutton.pack()





if __name__ == "__main__":
	pass
#end if main

