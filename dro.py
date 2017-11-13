from Tkinter import *
import tkMessageBox
import serial
import ConfigParser
from thread import start_new_thread
import time
import dromacros as macros
#from PIL import ImageTk, Image
configfile = "dro.ini"
root = Tk()
xdisplay = StringVar()
ydisplay = StringVar()
zdisplay = StringVar()
wdisplay = StringVar()
bdisplay = StringVar()
rpmdisplay = StringVar()
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
    if tkMessageBox.askokcancel("Quit", "Do you want to quit?"):
        Display.exit = 1
        root.destroy()
root.protocol("WM_DELETE_WINDOW", on_closing)

class Display():
    globalerr = None
    (xval, yval, zval) = (0,0,0)
    (xval_corr, yval_corr, zval_corr) = (0, 0, 0)
    xstorage = Storage()
    ystorage = Storage()
    zstorage = Storage()
    exit = 0 #flag for exit
    def refresh_threadfunc(self):
        while self.exit == 0:
            self.refresh()
            
    def refresh(self):
        if self.globalerr:
            xdisplay.set( "%s %s"%(self.globalerr,self.xval))
            ydisplay.set( self.globalerr)
            zdisplay.set( self.globalerr)
        else:    
            #xdisplay.set(xval)
            xdisplay.set("%.4f"%(xstep*(self.xval - self.xval_corr) / 1000))
            ydisplay.set("%.4f"%(ystep*(self.yval - self.yval_corr)/ 1000))
            zdisplay.set("%.4f"%(zstep*(self.zval - self.zval_corr)/ 1000))
                
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

SENSOR_ERRORS = {
    "1":'X magnet lost',
    "2":'Y magnet lost',
    "3":'Z magnet lost',
    "4":'Multichange IRQ',
    "5":'Spurious IRQ',
}

class SerialConn():
    buff = []
    def __init__(self, port, display):
        self.con = serial.Serial(
            port=port, \
            baudrate=57600, \
            parity=serial.PARITY_NONE, \
            stopbits=serial.STOPBITS_ONE, \
            bytesize=serial.EIGHTBITS, \
            timeout=None)
        self.display = display

    def receive(self):
        xdisplay.set( '..init..')
        while True:
            byte = self.con.read(1)
            if byte == ';':#separator
                    print "".join(self.buff)
                    val = "".join(self.buff[1:])
                    if self.buff[0] == 'X':
                        display.xval = int(val)
                    if self.buff[0] == 'Y':
                        display.yval = int(val)
                    if self.buff[0] == 'Z':
                        display.zval = int(val)
                    if self.buff[0] in ('E', 'M'):
                        debugstr.set("ERROR %s: %s"%(val, SENSOR_ERRORS.get(self.buff[1], "Unknown error" )))
                    del self.buff[:]
            else:
                if byte not in ('\n', '\r'):
                    self.buff.append(byte)
                    #debugstr.set(" ".join(self.buff))

class SerialConnMock(SerialConn):    
    def __init__(self, port, display):
        self.display = display
        
    def receive(self):
        self.xval = 10.1
        self.yval = 0.1
        self.zval = 0.1
        while True:
            self.xval += 1
            display.xval = self.xval
            display.yval = self.yval
            display.zval = self.zval
            #print " --------------%i "%self.xval
            time.sleep(0.02)
            
                    
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
        self.chx += 1
        #Button(self.HISTORYFRAME_X, text='QUIT', fg='red', command=on_closing).grid(row=0,column=self.chx)
        self.master.after(30, self.update_pos)
        self.pos_display.refresh()
    def nextrow(self):
        self._thisrow += 1
        return self._thisrow
    
    def place_next(self, obj):
        obj.grid(row=self.nextrow())
        return obj
    
    def create_axis_digitdisplay(self, axis, parent, pos_variable):
        #setattr(self, '%POSFRAME'
        f = Frame(parent)
        Label(f, text=axis, bg='#efe', relief=FLAT, height=1, width=30, font = "Calibri 32").pack({"side": "left"})
        Button(f, text="Zero", command=display.zeroX).pack({"side": "right"})
        Button(f, text="Abs/Rel", command=display.saveX).pack({"side": "right"})
        Label(f, textvariable=pos_variable, bg='#efe', relief=FLAT, height=1, width=30, font = "Arial 32 ").pack({"side": "left"})
        f.pack()
        
    
    def createWidgets(self):
        self.chx = 0
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

        Label(self.HISTORYFRAME, text="ZYMEM", bg='#efe',  height=1,  width=12, font = "Calibri 12 bold").grid(row=2)
        self.HISTORYFRAME_Z = self.histframe().grid(row=self.nextrow(), column=1) 
        #Label(self.HISTORYFRAME_Z, text="ZMEM", bg='#efe',  height=1, width=12, font = "Calibri 12 bold").pack(side=LEFT)
        self.place_next(self.HISTORYFRAME)
        
        self.DISPLAYFRAME = Frame(root, width=self.width)
        self.place_next(self.DISPLAYFRAME)
        
        self.TOOLSFRAME = Frame(root, bg='#fff', width=self.width)
        self.place_next(self.TOOLSFRAME)
        
        self.create_axis_digitdisplay('X', self.DISPLAYFRAME, xdisplay)
        self.create_axis_digitdisplay('Y', self.DISPLAYFRAME, ydisplay)
        self.create_axis_digitdisplay('Z', self.DISPLAYFRAME, zdisplay)
        #self.XPOSFRAME = Frame(self.DISPLAYFRAME)
        #self.XPOSFRAME.pack()
        #self.XZERO = Button(self.XPOSFRAME, text="Zero", command=display.zeroX).pack({"side": "right"})
        #self.XSTORE = Button(self.XPOSFRAME, text="Abs/Rel", command=display.saveX).pack({"side": "right"})
        #self.XD = Label(self.XPOSFRAME, textvariable=xdisplay, bg='#efe', relief=FLAT, height=1, width=30, font = "Calibri 32 bold")
        #self.XD.pack({"side": "left"})

        #self.YPOSFRAME = Frame(self.DISPLAYFRAME)
        #self.YPOSFRAME.pack()
        #self.YZERO = Button(self.YPOSFRAME, text="Zero", command=display.zeroY).pack({"side": "right"})
        #self.YSTORE = Button(self.YPOSFRAME, text="Abs/Rel", command=display.saveY).pack({"side": "right"})
        #self.YD = Label(self.YPOSFRAME, textvariable=ydisplay, bg='#efe', relief=FLAT, height=1, width=30, font = "Calibri 32 bold")
        #self.YD.pack({"side": "left"})
        #self.YZERO.pack({"side": "right"})
        #self.YSTORE.pack({"side": "right"})


        #self.ZFRAME = Frame(self.DISPLAYFRAME)
        #self.ZFRAME.pack()
        #self.ZZERO = Button(self.ZFRAME, text="Zero", command=display.zeroZ).pack({"side": "right"})
        #self.ZSTORE = Button(self.ZFRAME, text="Abs/Rel", command=display.saveZ).pack({"side": "right"})
        #self.ZD = Label(self.ZFRAME, textvariable=zdisplay, bg='#efe', relief=FLAT, height=1, width=30, font = "Calibri 32 bold")
        #self.ZD.pack({"side": "left"})
        #self.ZZERO.pack({"side": "right"})

        #self.TOOLSFRAME = Frame(root, bg='red',relief=FLAT, borderwidth=5)
        #self.TOOLSFRAME.pack(side=TOP)

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
                
        #c.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))
        #c.create_rectangle(50, 25, 150, 75, fill="blue")

        #b.grid(row=1, column=1, padx=130)#
        
        self.update_pos()
        

    def __init__(self, master, pos_display, width=1000, height=680):
        Frame.__init__(self, master)
        self.width, self.height = width, height
        self._thisrow = 0
        self.grid(row=2)
        self.pos_display = pos_display
        self.createWidgets()
        

app = Application(master=root, pos_display=display)

title = "Spaxx DRO "
app.master.title(title)
app.master.minsize(1000, 800)
port = config.get('GENERAL', 'comport')
mode = config.get('GENERAL', 'mode')
#thread_display = start_new_thread(display.refresh, ())

msg = " "
threadmethod = None
if mode and 'simul' in mode:
    msg = "Running in simulation mode"
    threadmethod = SerialConnMock(port, display).receive
else:
    debugstr.set('Opening DRO port ' + port)
    threadmethod = SerialConn(port, display).receive

print msg
app.master.title(title  + msg ) 
start_new_thread(threadmethod, ())
try:
        start_new_thread(threadmethod, ())
except Exception, e:
        debugstr.set(`e`)
        display.globalerr = 'INIT ERR'
        
app.mainloop()