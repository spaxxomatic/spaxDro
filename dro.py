from Tkinter import *
import tkMessageBox
import serial
import ConfigParser
from thread import start_new_thread
#from PIL import ImageTk, Image

root = Tk()
xdisplay = StringVar()
ydisplay = StringVar()
zdisplay = StringVar()
wdisplay = StringVar()
bdisplay = StringVar()
rpmdisplay = StringVar()
debugstr = StringVar()
xstep = float(15)  #micron/step
ystep = float(15)  #micron/step
zstep = float(15)  #micron/step

class Storage(list): pass
class Display:pass #forward declaration
thread_display = None
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
    def refresh(self):
        while self.exit == 0:
            if self.globalerr:
                xdisplay.set( "%s %s"%(self.globalerr,self.xval))
                self.xval += 1
                ydisplay.set( self.globalerr)
                zdisplay.set( self.globalerr)
            else:    
                #xdisplay.set(xval)
                xdisplay.set("X: %.3f"%(xstep*(self.xval - self.xval_corr) / 1000))
                ydisplay.set("Y: %.3f"%(ystep*(self.yval - self.yval_corr)/ 1000))
                zdisplay.set("Z: %.3f"%(zstep*(self.zval - self.zval_corr)/ 1000))
    def zeroX(self): 
        self.xval_corr = self.xval 
    def zeroY(self): 
        self.yval_corr = self.yval
    def zeroZ(self): 
        self.zval_corr = self.zval
    def saveX(self): self.xstorage.append(self.xval)
    def saveY(self): self.ystorage.append(self.yval)
    def saveZ(self): self.zstorage.append(self.zval)

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

class DroFunctions:
    def drillseries(self):
        pass
        
class Application(Frame):
    def say_hi(self):
        print "sayhi"
    def settings(self):
        #t = Toplevel(self)
        #t.wm_title("Window "  )
        #l = Label(t, text="This is window ")
        #l.pack(side="top", fill="both", expand=True, padx=100, pady=100)        
        Settings(self).open()

    def createWidgets(self):
        self.dbg = Label(root, textvariable=debugstr, relief=FLAT, height=1, width=70, font="Arial 10 bold")
        self.dbg.pack({"side": "top"})
        
        self.DISPLAYFRAME = Frame(root, width=768, height=576)
        self.DISPLAYFRAME.pack({"side": "left"})
        self.TOOLSFRAME = Frame(root, bg='#fff', width=400)
        self.TOOLSFRAME.pack({"side": "right"})
        self.XFRAME = Frame(self.DISPLAYFRAME)
        self.XFRAME.pack()
        self.XZERO = Button(self.XFRAME, text="Zero", command=display.zeroX).pack({"side": "right"})
        self.XSTORE = Button(self.XFRAME, text="Abs/Rel", command=display.saveX).pack({"side": "right"})
        self.XD = Label(self.XFRAME, textvariable=xdisplay, bg='#efe', relief=FLAT, height=1, width=30, font = "Calibri 32 bold")
        self.XD.pack({"side": "left"})
        #self.XZERO.pack({"side": "right"})
        #self.XSTORE.pack({"side": "right"})

        self.YFRAME = Frame(self.DISPLAYFRAME)
        self.YFRAME.pack()
        self.YZERO = Button(self.YFRAME, text="Zero", command=display.zeroY).pack({"side": "right"})
        self.YSTORE = Button(self.YFRAME, text="Abs/Rel", command=display.saveY).pack({"side": "right"})
        self.YD = Label(self.YFRAME, textvariable=ydisplay, bg='#efe', relief=FLAT, height=1, width=30, font = "Calibri 32 bold")
        self.YD.pack({"side": "left"})
        #self.YZERO.pack({"side": "right"})
        #self.YSTORE.pack({"side": "right"})


        self.ZFRAME = Frame(self.DISPLAYFRAME)
        self.ZFRAME.pack()
        self.ZZERO = Button(self.ZFRAME, text="Zero", command=display.zeroZ).pack({"side": "right"})
        self.ZSTORE = Button(self.ZFRAME, text="Abs/Rel", command=display.saveZ).pack({"side": "right"})
        self.ZD = Label(self.ZFRAME, textvariable=zdisplay, bg='#efe', relief=FLAT, height=1, width=30, font = "Calibri 32 bold")
        self.ZD.pack({"side": "left"})
        #self.ZZERO.pack({"side": "right"})

        #self.TOOLSFRAME = Frame(root, bg='red',relief=FLAT, borderwidth=5)
        #self.TOOLSFRAME.pack(side=TOP)
        self.drillseries_icon = PhotoImage(file="drill.gif")
        b = Button(self.TOOLSFRAME, compound=LEFT, image=self.drillseries_icon, command=DroFunctions().drillseries)
        #b.grid(row=1, column=1, padx=130)#
        b.pack({"side": "top"})
        
        self.QUIT = Button(self, text='QUIT', fg='red', command=on_closing).pack({"side": "left"})
        self.Settings = Button(self, text='Settings', fg='green', command=self.settings).pack({"side": "left"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

app = Application(master=root)
app.master.title("Nutiu DRO")
app.master.minsize(1000, 800)
config = ConfigParser.ConfigParser()
config.read("dro.ini")
try:
    xstep = int(config.get('RESOLUTION', 'x_step_size'))
    ystep = int(config.get('RESOLUTION', 'y_step_size'))
    zstep = int(config.get('RESOLUTION', 'z_step_size'))
except Exception:
    raise "Invalid config file: %s"%(`e`)
port = 'COM7'
debugstr.set('..opening ' + port)
thread_display = start_new_thread(display.refresh, ())
try:
    start_new_thread(SerialConn(port, display).receive, ())
except Exception, e:
    debugstr.set(`e`)
    display.globalerr = 'INIT ERR'

app.mainloop()