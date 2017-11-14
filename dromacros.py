from Tkinter import *
import tkMessageBox
import ConfigParser
import math

canvas = None
root = None

class Projector():
    def __init__(self, canvas, keep_scale_ratio=True):
        self.canvas = canvas
        self.xpad = 10
        self.ypad = 10
        self.keep_scale_ratio = keep_scale_ratio
        canvas.delete("all")
    def show_points(self, coords, x_max, y_max, x_min=0, y_min=0):
        radius = 6#self.screenwidth*self.screenheight/(len(coords)**2)
        #print "diam %s"%diam
        (xpad, ypad) = self.xpad , self.ypad
        
        x_len = float(x_max) - float(x_min)
        y_len = float(y_max) - float(y_min)
        if x_len == 0 or y_len == 0: #only one point?
            x_size_factor = 1
            y_size_factor = 1
        else:
            x_size_factor = float((self.canvas.width)/x_len)
            y_size_factor = float((self.canvas.height)/y_len)
        if self.keep_scale_ratio:
            if x_size_factor < y_size_factor:
                y_size_factor = x_size_factor
            else:
                x_size_factor = y_size_factor
        self.cwidth = x_len*x_size_factor 
        self.cheight = y_len*y_size_factor
        x_size_factor = float((self.cwidth-2*xpad)/x_len)
        y_size_factor = float((self.cheight-2*ypad)/y_len)
        
        print "w %i l %i"%(self.cwidth, self.cheight)
        self.canvas.config(width=self.cwidth, height=self.cheight)
        x_center_offset = (float(self.cwidth) - x_len*x_size_factor)/2 + xpad
        y_center_offset = (float(self.cheight) - x_len*y_size_factor)/2 + ypad
        #x_center_offset = (x_len*x_size_factor)/2 + xpad 
        #y_center_offset = (x_len*y_size_factor)/2 + ypad 
        
        #y_center_offset = xpad
        #x_center_offset = ypad
        print "factor %.3f"%x_size_factor
        print "center_offset %.3f %.3f"%(x_center_offset, y_center_offset)
        #canvas_width, canvas_height = self.canvas.width, self.canvas.height
        for idx, p in enumerate(coords):
            x = (p[0]-x_min)*x_size_factor + x_center_offset #x_min -> shift to 0
            y = (p[1]-y_min)*y_size_factor + y_center_offset
            self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill='#55b')
            #create a cross on each point 
            self.canvas.create_line(x-10, y, x+10, y, fill="#fff")
            self.canvas.create_line(x, y-10, x, y+10, fill="#fff")
        
            
class Mbox(object):

    root = None

    def __init__(self, msg, dict_key=None):
        """
        msg = <str> the message to be displayed
        dict_key = <sequence> (dictionary, key) to associate with user input
        (providing a sequence for dict_key creates an entry for user input)
        """
        tki = tkinter
        self.top = tki.Toplevel(Mbox.root)

        frm = tki.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        label = tki.Label(frm, text=msg)
        label.pack(padx=4, pady=4)

        if caller_wants_an_entry:
            self.entry = tki.Entry(frm)
            self.entry.pack(pady=4)

            b_submit = tki.Button(frm, text='Submit')
            b_submit['command'] = lambda: self.entry_to_dict(dict_key)
            b_submit.pack()

        b_cancel = tki.Button(frm, text='Cancel')
        b_cancel['command'] = self.top.destroy
        b_cancel.pack(padx=4, pady=4)

    def entry_to_dict(self, dict_key):
        data = self.entry.get()
        if data:
            d, key = dict_key
            d[key] = data
            self.top.destroy()
            
class MacroDialog:
    def __init__(self, parent, title, inputs, defvals=None):
        top = self.top = Toplevel(parent)
        Label(top, text=title).grid(row=0)
        row = 0
        self.inputboxes = []
        self.returns = []
        for d in inputs:
            Label(top, text=d).grid(row=row, column=0)
            b = Entry(top)
            self.inputboxes.append(b)
            if defvals:
                b.insert(0,defvals[row])
            #b_submit['command'] = lambda: self.entry_to_dict(dict_key)
            b.grid(row=row, column=1)
            row += 1  
        
        b = Button(top, text="OK", command=self.ok)
        b.grid(row=5)
        #top.update()
    
    def validate(self):
        try:
            for inp in self.inputboxes:
                val = int(inp.get())
                self.returns.append(val)
            return 1
        except ValueError:
            tkMessageBox.showwarning(
                "Bad input",
                "Illegal values, no chars allowed"
            )
            return 0
    def ok(self):
        #self.input = (self.no_x.get(), self.spacing_x.get(),self.no_y.get(), self.spacing_y.get())
        if self.validate():
            self.top.destroy()

class Funcs:

    @classmethod
    def drillseries_rect(self):
        projector = Projector(canvas)
        
        #canvas.create_rectangle(50, 25, 150, 75, fill="blue")
        #projector.show_points([(0,0), (0,22), (3,0), (3,24)], 3, 24)
        inputs = ["X Number of holes", "X Spacing", "Y Number of holes", "Y Spacing"]
        d = MacroDialog(root, 'Rectangular drill grid', inputs, defvals=[1,1,1,1])
        root.wait_window(d.top)
        ret = d.returns
        def calculate_coords(x_no, x_space, y_no, y_space):
            coords = []
            for i in range(x_no):
                for j in range(y_no):
                    coords.append((x_space*i, y_space*j))
            return coords, x_space*x_no, y_space*y_no,0,0
        coords, x_max, y_max, x_min, y_min = calculate_coords(*ret)
        projector.show_points(coords, x_max, y_max, x_min, y_min)

    @classmethod
    def drillseries_circ(self):    
        projector = Projector(canvas)
        inputs = ["Circle radius", "No of holes", "Start angle"]
        d = MacroDialog(root, 'Circular drill grid', inputs, defvals=[20,4,0])
        root.wait_window(d.top)
        ret = d.returns
        def calculate_coords(radius, no_holes, start_angle):
            coords = []
            x_max, y_max, x_min, y_min =  0,0,0,0
            for i in range(no_holes):
                angle_step = 360.0/no_holes
                x,y = (radius*math.cos(math.radians(i*angle_step+start_angle)), 
                        radius*math.sin(math.radians(i*angle_step+start_angle)))
                coords.append((x,y))
                if x < x_min: x_min = x
                if y < y_min: y_min = y
                if x > x_max: x_max = x
                if y > y_max: y_max = y
            return coords, x_max, y_max, x_min, y_min
        #coords, x_max, y_max = calculate_coords(*ret)
        projector.show_points(*calculate_coords(*ret))            
        #canvas.create_rectangle(50, 25, 120, 75, fill="red")
        