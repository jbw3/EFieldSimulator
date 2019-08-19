# E-field Simulation
#
# John Wilkes

# TO DO:
# - allow user to see grid
# - allow user to change colors of charges
# - allow user to save charge arangment
# - give focus back to window when charge is deselected
# - figure out what to do when charges overlap (stop simulation?)
# - allow user to copy and paste charges
# - mark selected charge
# - allow user to select charges with keyboard arrows
# - allow user to select a group of charges
# - find out cause of random error
# - display coordinates of selected charge
# - possible error with automatic stop

from Tkinter import *
import cPickle, FileDialog, math, os.path, time, tkFont, tkMessageBox

# default settings
DEFAULT = {
    "grid"    : False,
    "spacing" : 40,
    "minutes" : False}

# get settings
try:
    file = open("settings.dat", "r")
except(IOError):
    file = open("settings.dat", "w")
    cPickle.dump(DEFAULT, file)
    file.close()
    settings = DEFAULT
else:
    settings = cPickle.load(file)
    file.close()

def save_destroy():
    """ Save settings and destroy root window. """
    settings["grid"] = app.grid_on.get()
    settings["spacing"] = app.grid_spacing.get()
    settings["minutes"] = app.clock.display_min.get()
    file = open("settings.dat", "w")
    cPickle.dump(settings, file)
    file.close()
    root.destroy()

def config(num):
    """ Converts float to string with ".0" stripped off the end. """
    string = str(num).rstrip("0").rstrip(".")
    if string == "-0":
        string = "0"
    return string

class Charge(object):
    """ A basic charge. """
    RADIUS = 10          # radius of charge
    posColor = "#ff0000" # color of positive charge
    negColor = "#0000ff" # color of negative charge
    neuColor = "#00e000" # color of neutral charge

    def __init__(self, app, charge=0.0, x=0, y=0):
        """ Initialize charge and set variables. """
        self._x = x            # x coordinate
        self._y = y            # y coordinate
        self._charge = charge  # charge
        self.app = app         # used to access Application's atributes
        self.draw()

    def draw(self):
        """ Draw image on screen. """
        self.id = self.app.canvas.create_oval(self.x-Charge.RADIUS,
                                              self.y-Charge.RADIUS,
                                              self.x+Charge.RADIUS,
                                              self.y+Charge.RADIUS,
                                              outline=self.color,
                                              fill=self.color, tag="charge")

    def erase(self):
        """ Remove image from screen. """
        self.app.canvas.delete(self.id)

    def update(self):
        """ Syncs up image with x and y values. """
        self.erase()
        self.draw()

    def follow(self, event):
        """ Follow cursor on screen. """
        if self.app.grid_on.get():
            self._x = int(event.x + self.app.grid_spacing.get() // 2) // self.app.grid_spacing.get() * self.app.grid_spacing.get()
            self._y = int(event.y + self.app.grid_spacing.get() // 2) // self.app.grid_spacing.get() * self.app.grid_spacing.get()
        else:
            self._x = event.x
            self._y = event.y
        self.update()

    ### Properties ###
    ## x
    def get_x(self):
        return self._x
    x = property(get_x)
    ## y
    def get_y(self):
        return self._y
    y = property(get_y)
    ## calc_x
    def get_calc_x(self):
        return self._x
    calc_x = property(get_calc_x)
    ## calc_y
    def get_calc_y(self):
        return self._y
    calc_y = property(get_calc_y)
    ## color
    def get_color(self):
        if self.charge > 0:
            return Charge.posColor
        elif self.charge < 0:
            return Charge.negColor
        else:
            return Charge.neuColor
    color = property(get_color)
    ## charge
    def get_charge(self):
        return self._charge
    def set_charge(self, new_charge):
        self._charge = new_charge
    charge = property(get_charge, set_charge)

class Moveable(Charge):
    """ A charge that will move in an E-field. """
    FIELD_CONSTANT = 800 # used to adjust force between charges
    PRECISION = 5        # number of decimal places to round acceleration to
    def __init__(self, app, charge=0.0, x=0, y=0, dx0=0.0, dy0=0.0):
        """ Initialize charge and set variables. """
        Charge.__init__(self, app, charge, x, y)
        self._calc_x = x # x before last movement
        self._calc_y = y # y before last movement
                         # (used to calculate distances between charges when
                         #  calculating force, not updated until all charges
                         #  are moved to simulate simaltaneous forces)
        self._x0 = x     # initial x
        self._y0 = y     # initial y
        self._dx = dx0   # x-component of velocity
        self._dy = dy0   # y-component of velocity
        self._dx0 = dx0  # initial x-component of velocity
        self._dy0 = dy0  # initial y-component of velocity

    def follow(self, event):
        """ Update initial x and y when following cursor. """
        Charge.follow(self, event)
        self._x0 = self._x
        self._y0 = self._y
        self._calc_x = self._x
        self._calc_y = self._y

    def sync_calc(self):
        """ Sync calc coords with actual coords. """
        self._calc_x = self._x
        self._calc_y = self._y

    def update_pos(self):
        """ Change position based on forces from E-field. """
        for charge in self.app.charges:
            if charge != self:
                force = Moveable.FIELD_CONSTANT * self.charge * charge.charge / (math.pow(self.calc_x - charge.calc_x, 2) + math.pow(self.calc_y - charge.calc_y, 2))
                angle = math.atan2(self.calc_y - charge.calc_y,
                                   self.calc_x - charge.calc_x)
                self._dx += round(force * math.cos(angle), Moveable.PRECISION)
                self._dy += round(force * math.sin(angle), Moveable.PRECISION)
        # update coordinates
        self._x += self._dx
        self._y += self._dy
        self.update()

    def reset(self):
        """ Reset position and velocity and update. """
        self.reset_pos()
        self.reset_vel()
        self.update()

    def reset_pos(self):
        """ Set x and y to initial x and y. """
        self._x = self._calc_x = self._x0
        self._y = self._calc_y = self._y0

    def reset_vel(self):
        """ Set velocity to initial velocity. """
        self._dx = self._dx0
        self._dy = self._dy0

    ### Properties ###
    ## calc_x
    def get_calc_x(self):
        return self._calc_x
    calc_x = property(get_calc_x)
    ## calc_y
    def get_calc_y(self):
        return self._calc_y
    calc_y = property(get_calc_y)

    ## x0
    def get_x0(self):
        return self._x0
    x0 = property(get_x0)
    ## y0
    def get_y0(self):
        return self._y0
    y0 = property(get_y0)

    ## dx0
    def get_dx0(self):
        return self._dx0
    def set_dx0(self, new_dx0):
        self._dx0 = self._dx = new_dx0
    dx0 = property(get_dx0, set_dx0)
    ## dy0
    def get_dy0(self):
        return self._dy0
    def set_dy0(self, new_dy0):
        self._dy0 = self._dy = new_dy0
    dy0 = property(get_dy0, set_dy0)

class Clock(Label):
    """ Clock for displaying how long simulation has been running. """
    def __init__(self):
        Label.__init__(self, font=tkFont.Font(family="Cambria Math", size=11))

        self._value = 0.0     # time on clock
        self._last = 0        # value of last call to time.time()
        self._running = False # whether or not clock is running
        self.display_min = BooleanVar(
                value=settings["minutes"]) # whether or not to display minutes

        self.update_val()

    def tick(self):
        """ Increase value of clock. """
        if self._running:
            temp = time.time()
            self._value += temp - self._last
            self._last = temp
            self.update_val()

    def update_val(self):
        """ Syncs label with value. """
        r_value = round(self._value, 1) # value rounded to 1 decimal place
        if self.display_min.get():
            text = str(int(r_value) // 60) + ":" + str(r_value % 60).zfill(4)
        else:
            text = str(r_value)
        self.config(text=text)

    def start(self):
        """ Start clock. """
        self._running = True
        self._last = time.time()

    def stop(self):
        """ Stop clock. """
        self._running = False

    def reset(self):
        """ Reset clock to zero. """
        self._value = 0.0
        self.update_val()

    ### Properties ###
    ## value
    def get_value(self):
        return round(self._value, 1)
    value = property(get_value)

class Grid_Window(Toplevel):
    """ Window to allow user to set grid spacing. """
    def __init__(self, app):
        """ Initialize window and set variables. """
        Toplevel.__init__(self, app.master)
        self.geometry("200x46")
        self.title("Grid Spacing")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.clear_destroy)

        self.frame = Frame(self)
        self.frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.app = app

        self.create_widgets()

    def create_widgets(self):
        """ Put all widgets in the window. """
        self.entry = Entry(self.frame)
        self.entry.bind("<KeyPress>", self.num_only)
        self.entry.bind("<Return>", self.set_spacing)
        self.entry.place(x=0, y=0, width=200)
        Button(self.frame, text="Apply", command=self.set_spacing
               ).place(x=0, y=20, width=100)
        Button(self.frame, text="Cancel", command=self.clear_destroy
               ).place(x=100, y=20, width=100)

    def num_only(self, event):
        """ Allow only numbers in entry widget. """
        if event.char not in "0123456789" and event.keysym != "BackSpace":
            return "break"

    def focus_entry(self):
        """ Set the focus to the entry widget. """
        self.entry.focus_set()

    def set_spacing(self, event=None):
        """ Set app's spacing var to entry contents and destroy self. """
        try:
            num = int(self.entry.get())
        except(ValueError):
            pass
        else:
            # make sure spacing is within min and max bounds
            if num < Application.MIN_SPACING:
                num = Application.MIN_SPACING
            elif num > Application.MAX_SPACING:
                num = Application.MAX_SPACING

            self.app.grid_spacing.set(num)
            self.clear_destroy()

    def clear_destroy(self):
        """ Clear app's variable that references self and destroy self. """
        self.app.gWindow = None
        self.destroy()

class Application(Frame):
    DELAY = 25                   # milliseconds between simulation screen updates
    MIN_SPACING = 21             # minimum grid spacing
    MAX_SPACING = 100            # maximum grid spacing
    TITLE = "E-field Simulation" # window title
    def __init__(self, master):
        """ Initialize Frame and set variables. """
        Frame.__init__(self, master)
        self.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self.charges = []                      # list of charges on screen
        self.selected = None                   # id of charge last clicked on
        self.grid_on = BooleanVar(
            value=settings["grid"])            # whether or not to center charges on grid points
        self.grid_spacing = IntVar(
            value=settings["spacing"])         # pixels between grid points
        self.spacing_options = [               # grid spacing options in menu
            30, 40, 50, 60, 70, 80, 90, 100]
        self.running = False                   # whether or not simulation is running
        self.paused = True                     # whither or not simulation is paused
        self._stop_time = None                 # when to stop simulation
        self.gWindow = None                    # widow to set custom spacing
        self.set_filename("")                  # name of file currently open

        self.create_widgets()
        self.create_menu()
        # schedule function call to update simulation every DELAY milliseconds
        master.after(Application.DELAY, self.update_sim)

    def create_menu(self):
        """ Create all menu objects. """
        self.menubar = Menu(self.master)

        # File
        self.filemenu = Menu(self.menubar, tearoff=False)
        self.filemenu.add_command(label="New", underline=0,
                                  command=self.new_file)
        self.filemenu.add_command(label="Open...", underline=0,
                                  command=self.open_file)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Save", underline=0,
                                  command=self.save)
        self.filemenu.add_command(label="Save As...", underline=5,
                                  command=self.save_as)

        # Charges
        self.chargemenu = Menu(self.menubar, tearoff=False)
        self.chargemenu.add_command(label="Fixed Charge", underline=0,
                                    command=self.add_fixed)
        self.chargemenu.add_command(label="Moveable Charge", underline=0,
                                    command=self.add_moveable)
        self.chargemenu.add_separator()
        self.chargemenu.add_command(label="Clear Screen", underline=0,
                                    command=self.clear)

        # Settings
        self.setmenu = Menu(self.menubar, tearoff=False)
        self.setmenu.add_checkbutton(label="Grid", underline=0,
                                     variable=self.grid_on)
        submenu = Menu(self.setmenu, tearoff=False)
        for num in self.spacing_options:
            submenu.add_radiobutton(label=str(num), var=self.grid_spacing,
                                    value=num)
        submenu.add_separator()
        submenu.add_command(label="Custom Spacing", underline=0,
                            command=self.grid_window)

        self.setmenu.add_cascade(label="Grid Spacing", underline=5, menu=submenu)
        self.setmenu.add_separator()
        self.setmenu.add_checkbutton(label="Display Minutes", underline=0,
                                     variable=self.clock.display_min,
                                     command=self.clock.update_val)

        self.menubar.add_cascade(label="File", underline=0, menu=self.filemenu)
        self.menubar.add_cascade(label="Charges", underline=0, menu=self.chargemenu)
        self.menubar.add_cascade(label="Settings", underline=0, menu=self.setmenu)

    def create_widgets(self):
        """ Put all widgets on the screen. """
        # canvas - where charges will be displayed
        self._canvas = Canvas(self, background="#ffffff")
        self._canvas.bind("<ButtonPress-1>", self.evaluate)
        self._canvas.bind("<ButtonPress-3>", self.evaluate)
        self._canvas.bind("<ButtonPress-1>", self.select_charge, True)
        self._canvas.bind("<ButtonPress-3>", self.select_charge, True)
        self._canvas.bind("<ButtonPress-1>", self.grab_charge, True)
        self._canvas.bind("<ButtonRelease-1>", self.release_charge)
        self._canvas.bind("<ButtonPress-3>", self.post_charge_menu, True)
        self._canvas.place(x=0, y=40, relwidth=1.0, relheight=1.0)

        # start/pause button - starts and pauses simulation
        self.spBttn = Button(self, text="Start", width=6,
                             background="#00c000",
                             activebackground="#00a000",
                             foreground="#ffffff",
                             activeforeground="#dddddd",
                             command=self.start_pause)
        self.spBttn.place(x=0, y=20, height=20)

        # stop button - stops simulation
        self.stopBttn = Button(self, text="Stop", width=6,
                               background="#e00000",
                               activebackground="#c00000",
                               foreground="#ffffff",
                               activeforeground="#dddddd",
                               command=self.stop)
        self.stopBttn.place(x=53, y=20, height=20)

        # reset button - reset simulation
        self.resetBttn = Button(self, text="Reset", width=6,
                                background="#0000a0",
                                activebackground="#000080",
                                foreground="#ffffff",
                                activeforeground="#dddddd",
                                command=self.reset)
        self.resetBttn.place(x=106, y=20, height=20)

        # clock label - how long simulation has been running
        self.clock = Clock()
        self.clock.place(x=10, y=0, height=20)

        # stop time entry field - when to stop simulation
        Label(self, text="stop:").place(x=80, y=0, height=20)
        self.sTime = Entry(self, width=5)
        self.sTime.bind("<KeyPress>", self.time_only)
        self.sTime.place(x=115, y=0)

        # charge entry field - sets the charge of the selected charge
        Label(self, text="charge:").place(x=165, y=20)
        self.chargeEntry = Entry(self, width=8, state=DISABLED)
        self.chargeEntry.bind("<KeyPress>", self.num_only)
        self.chargeEntry.place(x=215, y=20)

        # velocity entry fields - sets initial velocity
        Label(self, text="initial velocity:").place(x=275, y=10)
        # dx
        Label(self, text="x:").place(x=430, y=0, anchor="ne")
        self.dxEntry = Entry(self, width=5, state=DISABLED)
        self.dxEntry.bind("<KeyPress>", self.num_only)
        self.dxEntry.bind("<KeyPress>", self.syncVelEntries, True)
        self.dxEntry.place(x=440, y=0)
        # dy
        Label(self, text="y:").place(x=520, y=0, anchor="ne")
        self.dyEntry = Entry(self, width=5, state=DISABLED)
        self.dyEntry.bind("<KeyPress>", self.num_only)
        self.dyEntry.bind("<KeyPress>", self.syncVelEntries, True)
        self.dyEntry.place(x=530, y=0)
        # magnitude
        Label(self, text="magnitude:").place(x=430, y=20, anchor="ne")
        self.magEntry = Entry(self, width=5, state=DISABLED)
        self.magEntry.bind("<KeyPress>", self.num_only)
        self.magEntry.bind("<KeyPress>", self.syncVelEntries, True)
        self.magEntry.place(x=440, y=20)
        # angle
        Label(self, text="angle:").place(x=520, y=20, anchor="ne")
        self.angEntry = Entry(self, width=5, state=DISABLED)
        self.angEntry.bind("<KeyPress>", self.num_only)
        self.angEntry.bind("<KeyPress>", self.syncVelEntries, True)
        self.angEntry.place(x=530, y=20)

        # menu - posted when charge is right clicked on
        self.charge_menu = Menu(self, tearoff=False)
        self.charge_menu.add_command(label="Remove", command=self.remove_charge)

    def new_file(self):
        """ Clear screen and filename. """
        self.clear()
        self.set_filename("")

    def open_file(self):
        """ Open a file to get charge arangment. """
        openWindow = FileDialog.LoadFileDialog(self.master, "Open")
        path = openWindow.go()
        if path != None:
            ext = os.path.splitext(path)[1]
            if ext == ".efd":
                self.read_file(path)
                self.set_filename(path)
            else:
                tkMessageBox.showerror("Error",
                            "Cannot open file with \""+ext+"\" extention.")

    def save(self):
        """ Save charge arangment to file. """
        if self.filename == "":
            self.save_as()
        else:
            self.write_file(self.filename)

    def save_as(self):
        """ Open dialog box so user can specify filename to save to. """
        saveWindow = FileDialog.SaveFileDialog(self.master, "Save As")
        path = saveWindow.go()
        if path != None:
            if os.path.splitext(path)[1] != ".efd":
                path += ".efd"
            self.set_filename(path)
            self.save()

    def write_file(self, filename):
        """ Save charge data to file. """
        file = open(filename, "w")
        # write stop time
        file.write(self.sTime.get()+"\n")
        # write charge data
        for chg in self.charges:
            if type(chg) == Charge:
                data = "f "+str(chg.charge)+" "+str(chg.x)+" "+str(chg.y)+"\n"
            elif type(chg) == Moveable:
                data = "m "+str(chg.charge)+" "+str(chg.x0)+" "+str(chg.y0)+" "+str(chg.dx0)+" "+str(chg.dy0)+"\n"
            file.write(data)
        file.close()

    def read_file(self, filename):
        """ Put charges on screen based on data from file. """
        file = open(filename, "r")
        time = file.readline().strip()
        data = file.readlines()
        file.close()
        # insert stop time
        self.sTime.delete(0, END)
        if time != "":
            self.sTime.insert(0, time)
        # add charges
        self.clear()
        for string in data:
            info = string.strip().split(" ")
            charge = float(info[1])
            x = int(info[2])
            y = int(info[3])
            if info[0] == "f":
                self.add_fixed(charge, x, y)
            else:
                dx0 = float(info[4])
                dy0 = float(info[5])
                self.add_moveable(charge, x, y, dx0, dy0)

    def evaluate(self, event):
        """ Stops other bindings from executing if simulation is running. """
        if self.running:
            return "break"

    def start_pause(self):
        """ Starts and pauses simulation. """
        if not self.running:
            self.menubar.entryconfig(1, state=DISABLED)
            self.menubar.entryconfig(2, state=DISABLED)
            self.menubar.entryconfig(3, state=DISABLED)
            self.deselect()
            self.running = True
            self._stop_time = self.get_stop_time()
            self.sTime.config(state=DISABLED)
            self.clock.reset()
        self.paused = not self.paused
        # configure button and start or stop clock
        if self.paused:
            self.clock.stop()
            self.spBttn.config(text="Start",
                               background="#00c000",
                               activebackground="#00a000")
        else:
            self.clock.start()
            self.spBttn.config(text="Pause",
                               background="#eeee00",
                               activebackground="#cece00")

    def stop(self):
        """ Stops simulation and resests charges' velocities. """
        self.running = False
        self.paused = True
        self.menubar.entryconfig(1, state=NORMAL)
        self.menubar.entryconfig(2, state=NORMAL)
        self.menubar.entryconfig(3, state=NORMAL)
        self.sTime.config(state=NORMAL)
        self.clock.stop()
        for charge in self.charges:
            if type(charge) == Moveable:
                charge.reset_vel()
        # configure button
        self.spBttn.config(text="Start",
                           background="#00c000",
                           activebackground="#00a000")

    def reset(self):
        """ Reset all charges to their initial positions. """
        self.clock.reset()
        for charge in self.charges:
            if type(charge) == Moveable:
                charge.reset()

    def update_sim(self):
        """ Update simulation when it is running. """
        self.clock.tick()
        if self.clock.value == self._stop_time:
            self.stop()
        if self.running and not self.paused:
            # update positions of all moveable charges
            for charge in self.charges:
                if type(charge) == Moveable:
                    charge.update_pos()
            # sync calc coords with actual coords
            for charge in self.charges:
                if type(charge) == Moveable:
                    charge.sync_calc()
        # reschedule function call
        self.master.after(Application.DELAY, self.update_sim)

    def select_charge(self, event):
        """ Remember charge last clicked on. """
        overlapping = self.canvas.find_overlapping(event.x, event.y,
                                                   event.x, event.y)
        if len(overlapping) > 0:
            self.select(self.find(overlapping[0]))
        else:
            self.deselect()
        print self.selected#temp

    def select(self, charge):
        """ Select charge with 'id'. Put charge's charge in entry widget and give
            widget the focus. """
        if self.selected != None:
            self.update_data() # update previously selected charge's data
        self.selected = charge
        # configure entry widgets
        self.chargeEntry.config(state=NORMAL)
        self.chargeEntry.delete(0, END)
        self.chargeEntry.insert(0, config(self.selected.charge))
        self.chargeEntry.selection_range(0, END)
        self.chargeEntry.focus_set()
        if type(self.selected) == Moveable:
            self.dxEntry.config(state=NORMAL)
            self.dyEntry.config(state=NORMAL)
            self.magEntry.config(state=NORMAL)
            self.angEntry.config(state=NORMAL)
            self.syncVelEntries()
        else:
            self.dxEntry.delete(0, END)
            self.dxEntry.config(state=DISABLED)
            self.dyEntry.delete(0, END)
            self.dyEntry.config(state=DISABLED)
            self.magEntry.delete(0, END)
            self.magEntry.config(state=DISABLED)
            self.angEntry.delete(0, END)
            self.angEntry.config(state=DISABLED)

    def deselect(self):
        """ Called when charges are deselected. Delete contents of entry widget
            and disable it. """
        if self.selected != None:
            self.update_data()
        self.selected = None
        for entry in (self.chargeEntry, self.dxEntry, self.dyEntry, self.magEntry, self.angEntry):
            entry.delete(0, END)
            entry.config(state=DISABLED)

    def insertChar(self, event):
        """ Returns Entry widget's contents with pressed key's char inserted. """
        string = event.widget.get()
        if event.widget.select_present():
            i1 = event.widget.index(ANCHOR)
            i2 = event.widget.index(INSERT)
            idx1 = min(i1, i2)
            idx2 = max(i1, i2)
        else:
            idx1 = idx2 = event.widget.index(INSERT)
        return string[:idx1] + event.char + string[idx2:]

    def syncVelEntries(self, event=None):
        """ Syncs x and y velocity components and magnitude and angle. """
        if event == None:
            # calculate new contents
            dx = self.selected.dx0
            dy = -self.selected.dy0 # negative so +y-axis is up to user
            mag = round(math.sqrt(math.pow(dx, 2) + math.pow(dy, 2)), 5)
            angle = round(math.degrees(math.atan2(dy, dx)), 5)
            # delete previous contents
            self.dxEntry.delete(0, END)
            self.dyEntry.delete(0, END)
            self.magEntry.delete(0, END)
            self.angEntry.delete(0, END)
            # insert new contents
            self.dxEntry.insert(0, config(dx))
            self.dyEntry.insert(0, config(dy))
            self.magEntry.insert(0, config(mag))
            self.angEntry.insert(0, config(angle))
        else:
            # get contents of entry widget and add pressed key's char to string
            string = self.insertChar(event)
            if event.widget in (self.dxEntry, self.dyEntry):
                # calculate new contents
                if event.widget == self.dxEntry:
                    dx = string
                    dy = self.dyEntry.get()
                else:
                    dx = self.dxEntry.get()
                    dy = string
                try:
                    dx = float(dx)
                    dy = float(dy)
                except(ValueError):
                    # return if dx or dy is not a number (i.e. "." or "-")
                    return
                mag = round(math.sqrt(math.pow(dx, 2) + math.pow(dy, 2)), 5)
                angle = round(math.degrees(math.atan2(dy, dx)), 5)
                # delete previous contents
                self.magEntry.delete(0, END)
                self.angEntry.delete(0, END)
                # insert new contents
                self.magEntry.insert(0, config(mag))
                self.angEntry.insert(0, config(angle))
            elif event.widget in (self.magEntry, self.angEntry):
                # calculate new contents
                if event.widget == self.magEntry:
                    mag = string
                    ang = self.angEntry.get()
                else:
                    mag = self.magEntry.get()
                    ang = string
                try:
                    mag = float(mag)
                    ang = float(ang)
                except(ValueError):
                    # return if mag or ang in not a number (i.e. "." or "-")
                    return
                dx = round(mag * math.cos(math.radians(ang)), 5)
                dy = round(mag * math.sin(math.radians(ang)), 5)
                # delete previous contents
                self.dxEntry.delete(0, END)
                self.dyEntry.delete(0, END)
                # insert new contents
                self.dxEntry.insert(0, config(dx))
                self.dyEntry.insert(0, config(dy))

    def find(self, id):
        """ Return charge in list that has id. """
        for charge in self.charges:
            if charge.id == id:
                return charge
        # if charge not found return None
        return None

    def add_fixed(self, charge=0.0, x=None, y=None):
        """ Put a fixed charge on the screen. """
        if x == None:
            x = self.grid_spacing.get()
        if y == None:
            y = self.grid_spacing.get()
        charge = Charge(self, charge, x, y)
        self.charges.append(charge)

    def add_moveable(self, charge=0.0, x=None, y=None, dx0=0.0, dy0=0.0):
        """ Put a moveable charge on the screen. """
        if x == None:
            x = self.grid_spacing.get()
        if y == None:
            y = self.grid_spacing.get()
        charge = Moveable(self, charge, x, y, dx0, dy0)
        self.charges.append(charge)

    def remove_charge(self):
        """ Remove a charge from the screen. """
        selected = self.selected
        self.deselect()
        selected.erase()
        self.charges.remove(selected)

    def clear(self):
        """ Remove all charges from screen. """
        self.deselect()
        for charge in self.charges:
            charge.erase()
        self.charges = []

    def grab_charge(self, event):
        """ Make charge follow cursor around screen. """
        if self.selected != None:
            self.canvas.bind("<Motion>", self.selected.follow)

    def release_charge(self, event):
        """ Release charge from following cursor around screen. """
        self.canvas.unbind("<Motion>")

    def get_stop_time(self):
        """ Return when to stop simulation. """
        try:
            return float(self.sTime.get())
        except(ValueError):
            return None

    def post_charge_menu(self, event):
        """ Post menu when charge is right clicked on. """
        if self.selected != None:
            self.charge_menu.post(event.x_root, event.y_root)

    def grid_window(self):
        """ Display window that sets custom grid spacing. """
        if self.gWindow == None:
            self.gWindow = Grid_Window(self)
        self.gWindow.focus_entry()

    def num_only(self, event):
        """ Bound to Entry widget to allow only numbers to be entered. """
        # do not break if pressed key is one of the following
        if event.keysym in ("BackSpace", "Tab", "Delete", "Left", "Right", "Home", "End"):
            return
        # break if char is a space
        if event.char == " ":
            return "break"
        # get contents of entry widget and add pressed key's char to string
        string = self.insertChar(event)
        # do not break if string is one of the following
        if string in ("-", ".", "-."):
            return
        # break if string cannot be converted to float
        try:
            test = float(string)
        except(ValueError):
            return "break"

    def time_only(self, event):
        """ Bount to Entry stop time widget to allow only a valid time to be
            entered. """
        # do not break if pressed key is one of the following
        if event.keysym in ("BackSpace", "Tab", "Delete", "Left", "Right", "Home", "End"):
            return
        # break if char is a space
        if event.char == " ":
            return "break"
        # get contents of entry widget and add pressed key's char to string
        string = event.widget.get()
        if event.widget.select_present():
            i1 = event.widget.index(ANCHOR)
            i2 = event.widget.index(INSERT)
            idx1 = min(i1, i2)
            idx2 = max(i1, i2)
        else:
            idx1 = idx2 = event.widget.index(INSERT)
        string = string[:idx1] + event.char + string[idx2:]
        # do not break if string is a period
        if string == ".":
            return
        # break if number has more than 1 decimal place
        if "." in string and len(string[string.index(".")+1:]) > 1:
            return "break"
        # break if string cannot be converted to float
        try:
            test = float(string)
        except(ValueError):
            return "break"
        # break if number is negative
        if test < 0:
            return "break"

    def update_data(self):
        """ Sets charge of selected charge to contents of entry widget. """
        # charge
        try:
            num = float(self.chargeEntry.get())
        except(ValueError):
            # entry widget is empty so let variable retain previous value
            pass
        else:
            self.selected.charge = num
        # dx0
        try:
            num = float(self.dxEntry.get())
        except(ValueError):
            # entry widget is empty so let variable retain previous value
            pass
        else:
            self.selected.dx0 = num
        # dy0
        try:
            num = -float(self.dyEntry.get()) # negative so +y-axis is up to user
        except(ValueError):
            # entry widget is empty so let variable retain previous value
            pass
        else:
            self.selected.dy0 = num
        # redraw to update any color change
        self.selected.update()

    ### Properties ###
    ## canvas
    def get_canvas(self):
        return self._canvas
    canvas = property(get_canvas)

    ## filename
    def get_filename(self):
        return self._filename
    def set_filename(self, new_filename):
        self._filename = new_filename
        if new_filename == "":
            self.master.title(Application.TITLE)
        else:
            self.master.title(Application.TITLE+" - "+os.path.basename(new_filename))
    filename = property(get_filename, set_filename)

root = Tk()

app = Application(root)

root.protocol("WM_DELETE_WINDOW", save_destroy)
root.title(Application.TITLE)
root.geometry("600x500")
root.config(menu=app.menubar)

root.mainloop()
