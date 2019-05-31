from Tkinter import *
import tkMessageBox
import serial
import ConfigParser
from thread import start_new_thread
import time
import dromacros as macros
import os
from  poslib import LinearPositionComm
myfolder = os.path.dirname(os.path.realpath(__file__))

#from PIL import ImageTk, Image
configfile = os.path.join(myfolder,"dro.ini")
os.chdir(myfolder)
print "Reading config file %s"%configfile
root = Tk()
xdisplay = StringVar()
ydisplay = StringVar()
wdisplay = StringVar()
bdisplay = StringVar()
rpmdisplay = StringVar()
root.coords_display = StringVar()
debugstr = StringVar()
xstep, ystep, zstep = None, None, None
config = ConfigParser.ConfigParser()
config.read(configfile)

try:
    xstep = float(config.get('RESOLUTION', 'x_step_size'))
    ystep = float(config.get('RESOLUTION', 'y_step_size'))
    zstep = float(config.get('RESOLUTION', 'z_step_size'))
except Exception, e:
    print "Invalid config file: %s"%(str(e))
    exit(1)

class Storage(list): pass
class Display:pass #forward declaration

def on_closing():
    #if tkMessageBox.askokcancel("Quit", "Do you want to quit?"):
    Display.exit = 1
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

class Display():
    globalerr = None
    (xval, yval, zval) = (0,0,0)
    (xval_corr, yval_corr, zval_corr) = (0, 0, 0)
    xstorage = Storage()
    ystorage = Storage()
    #zstorage = Storage()
    exit = 0 #flag for exit
    def refresh_threadfunc(self):
        while self.exit == 0:
            self.refresh()
            
    def refresh_dro(self):
        if self.globalerr:
            xdisplay.set( "%s %s"%(self.globalerr,self.xval))
            ydisplay.set( self.globalerr)
            #zdisplay.set( self.globalerr)
        else:    
            #xdisplay.set(xval)
            xdisplay.set("%.3f"%(self.xval - self.xval_corr))
            ydisplay.set("%.3f"%(self.yval - self.yval_corr))
            #zdisplay.set("%.3f"%(zstep*(self.zval - self.zval_corr)/ 1000))
                
    def history(self):
        self.xval_corr = self.xstorage.pull()
    def zeroX(self): 
        self.saveX()
        self.xval_corr = self.xval 
    def zeroY(self): 
        self.saveY()
        self.yval_corr = self.yval
    def zeroZ(self):
        self.saveZ()    
        self.zval_corr = self.zval
    def saveX(self): 
        self.xstorage.append(self.xval)
    def saveY(self): 
        self.ystorage.append(self.yval)
    def saveZ(self): 
        self.zstorage.append(self.zval)
   #enum {
   #   OK,
   #   WARN_LIN_OR_COF,
   #   ERROR_MAG_FIELD_LOW,
   #   ERROR_NO_MAG_FIELD,
   #   ERROR_PARITY_ERROR,
   #   ERROR_OCF,
   #   ERROR_UNKNOWN
   # };
SENSOR_ERRORS = {
    "1":'Lin warn',
    "2":'Low mag field',
    "3":'No mag field',
    "4":'Parity error',
    "5":'OCF error',
}
                    
display = Display()

class Settings():
    def __init__(self, parent):
        self.parent = parent
        self.window = Toplevel(parent)
        self.window.geometry('+600+600')
        
    def open(self):
        e = Entry(self.window)
        e.pack()
        e.focus_set()
        self.window.transient(root)
        self.window.grab_set()
        self.parent.wait_window(wdw)
        #self.window.wm_title("Settings")
        #l = Label(self.window, text="This is window" )
        #l.pack(side="top", fill="both", expand=True, padx=100, pady=100)

    
class Application(Frame):
    def settings(self):
        Settings(self).open()
    
    def histframe(self):
        return Frame(self.HISTORYFRAME, height=30, bd=1, relief=SUNKEN)
        
    def update_pos(self):
        #Button(self.HISTORYFRAME_X, text='QUIT', fg='red', command=on_closing).grid(row=0,column=self.chx)
        self.master.after(100, self.update_pos)
        self.pos_display.refresh_dro()
        
    def nextrow(self):
        self._thisrow += 1
        return self._thisrow
    
    def place_next(self, obj):
        obj.grid(row=self.nextrow())
        return obj
    
    def create_axis_digitdisplay(self, axis, parent, pos_variable):
        #setattr(self, '%POSFRAME'
        f = Frame(parent)
        Label(f, text=axis, bg='#efe', relief=FLAT, height=1, width=10, font = "Calibri 32").pack({"side": "left"})
        Button(f, text="Zero", command=display.zeroX).pack({"side": "right"})
        Button(f, text="Abs/Rel", command=display.saveX).pack({"side": "right"})
        Label(f, textvariable=pos_variable, bg='#efe', relief=FLAT, height=1, width=10, font = "Arial 32 ").pack({"side": "left"})
        f.pack()
        
    def createWidgets(self):
        self.MENUFRAME = Frame(root, width=self.width, height=30)
        
        self.QUIT = Button(self.MENUFRAME, text='QUIT', fg='red', command=on_closing).grid(row=0, column=0)
        self.Settings = Button(self.MENUFRAME, text='Settings', fg='green', command=self.settings).grid(row=0, column=1)
        self.place_next(self.MENUFRAME)
        
        self.dbg = Label(root, textvariable=debugstr, relief=FLAT, height=1, width=70, font="Arial 10 bold")
        self.dbg.grid(row=self.nextrow())
        self.HISTORYFRAME = Frame(root, width=self.width, height=30)
        
        Label(self.HISTORYFRAME, text="XMEM", bg='#efe',  height=1,  bd=1, width=12, font = "Calibri 12 bold").grid(row=0)
        self.HISTORYFRAME_X = self.histframe().grid(row=self.nextrow(), column=1)
        
        Label(self.HISTORYFRAME, text="YMEM", bg='#efe',  height=1,  bd=1, width=12, font = "Calibri 12 bold").grid(row=1)
        self.HISTORYFRAME_Y = self.histframe().grid(row=self.nextrow(), column=1)

        #Label(self.HISTORYFRAME, text="ZYMEM", bg='#efe',  height=1,  width=12, font = "Calibri 12 bold").grid(row=2)
        #self.HISTORYFRAME_Z = self.histframe().grid(row=self.nextrow(), column=1) 
        #Label(self.HISTORYFRAME_Z, text="ZMEM", bg='#efe',  height=1, width=12, font = "Calibri 12 bold").pack(side=LEFT)
        self.place_next(self.HISTORYFRAME)
        
        self.DISPLAYFRAME = Frame(root, width=self.width)
        self.place_next(self.DISPLAYFRAME)
        
        self.TOOLSFRAME = Frame(root, bg='#fff', width=self.width)
        self.place_next(self.TOOLSFRAME)
        
        self.create_axis_digitdisplay('X', self.DISPLAYFRAME, xdisplay)
        self.create_axis_digitdisplay('Y', self.DISPLAYFRAME, ydisplay)
        #self.create_axis_digitdisplay('Z', self.DISPLAYFRAME, zdisplay)

        canvas_height = 300
        c = self.canvas = Canvas(root, width=self.width, height=canvas_height)
        c.height = canvas_height
        c.width = self.width
        c.config(relief=GROOVE, bg="#aa9")
        c.grid(row=self.nextrow())
        macros.canvas = c
        macros.root = root
        self.drillseries_rect_icon = PhotoImage(file="rect_drills.gif")
        self.drillseries_circ_icon = PhotoImage(file="circle_drills.gif")
        b = Button(self.TOOLSFRAME, compound=LEFT, image=self.drillseries_rect_icon, command=macros.Funcs.drillseries_rect).pack({"side": "left"})
        b = Button(self.TOOLSFRAME, compound=LEFT, image=self.drillseries_circ_icon, command=macros.Funcs.drillseries_circ).pack({"side": "left"})
        
        self.cd = Label(root, textvariable=root.coords_display, relief=FLAT, height=1, width=70, font="Arial 10")
        self.cd.grid(row=self.nextrow())
    
        self.update_pos()
        

    def __init__(self, master, pos_display, width=600, height=600):
        Frame.__init__(self, master)
        self.width, self.height = width, height
        self._thisrow = 0
        self.grid(row=2)
        self.pos_display = pos_display
        self.createWidgets()
        

app = Application(master=root, pos_display=display)

title = "Spaxx DRO "
app.master.title(title)
port = config.get('GENERAL', 'comport')
baudrate = config.get('GENERAL', 'baudrate')
try:
    mode = config.get('GENERAL', 'mode')
except:
    mode = 0


#thread_display = start_new_thread(display.refresh, ())
class PosDataRefresh():    
    def __init__(self, port, baudrate, display):
        self.display = display
        self.port = port
        self.baudrate = baudrate

    def get_axis_pos(self):
        with LinearPositionComm(self.port, self.baudrate) as comm:
            while not Display.exit:
                #print (self.xval, self.yval)
                display.xval = comm.pos_receiver_lib.get_x_pos()
                display.yval = comm.pos_receiver_lib.get_y_pos()
                time.sleep(0.2)

msg = " "

threadmethod = PosDataRefresh(port, baudrate, display).get_axis_pos
print msg

app.master.title(title  + msg ) 
start_new_thread(threadmethod, ())
try:
    start_new_thread(threadmethod, ())
except Exception, e:
    debugstr.set(`e`)
    display.globalerr = 'INIT ERR'
        
app.mainloop()