import time
import matplotlib
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk, FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib import style
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db_connect import get_sql_connection as dbc
from db_connect import initialize_db
from db_connect import update_db
from mag_text_file import mag_information
import pandas as pd
import numpy as np

matplotlib.use("TkAgg")


LARGE_FONT = ("Verdana", 10)
NORM_FONT = ("Verdana", 8)
SMALL_FONT = ("Verdana", 6)
style.use("ggplot")  # seaborn-colorblind
chartLoad = True
paused = True
bcolor = "#00A3E0"
lbcolor = "royalblue"
figure = plt.figure()


def popupmsg(msg):
    popup = tk.Tk()
    popup.wm_title("INFORMATION")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    button1 = ttk.Button(popup, text="Confirmation Logged", command=popup.destroy)
    button1.pack()
    popup.mainloop()


def load_chart(run):
    global chartLoad

    if run == "start":
        chartLoad = True

    elif run == "stop":
        chartLoad = False


class TheMagApp(tk.Tk):
    """
    This is the main App Frame for the CDS Tool -- the frame is created and initialized below,
    it is passed to each class
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize instance and tkinter, create frame/container to hold elements created later on
        set size, pass all possible frames.
        :param args:
        :param kwargs:
        """
        self.initialize_db = initialize_db()  # insert data into mysqldb
        self.post_care_update = update_db()  # insert data into mysqldb
        tk.Tk.__init__(self, *args, **kwargs)  # initialize tkinter as well
        tk.Tk.wm_title(self, "Magnesium Drip CDS")

        global chartLoad

        container = tk.Frame(self)  # create window frame/container to hold things
        container.pack(
            side="top", fill="both", expand=True
        )  # fill- fills is space alotted, expand- if there is space
        container.grid_rowconfigure(
            0, weight=1
        )  # 0- setting min size, weight- priority
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar)
        filemenu.add_command(
            label="Save Settings", command=lambda: popupmsg("Not working yet...")
        )
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # start_stop = tk.Menu(menubar, tearoff=1)
        # start_stop.add_command(label="Resume", command=lambda: chartLoad('start'))
        # start_stop.add_command(label="Pause", command=lambda: chartLoad('stop'))
        # menubar.add_cascade(label="Resume/Pause", menu=start_stop)

        tk.Tk.config(self, menu=menubar)

        self.frames = {}

        for F in (
            StartPage,
            MainPage,
            MagPage,
            MagCalculation,
            MagInformationPage,
            MagUpdate,
            MagLabLevels,
        ):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(
                row=0, column=0, sticky="nsew"
            )  # place things next to each other, nsew-sticky:alignment+stretch

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):
    """
    Opening page of application -- view as to whether you want to enter the CDS Tool
    """

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.parent = parent
        label = tk.Label(
            self,
            text="Do you want to proceed to the \n"
            "Magnesium Drip CDS Application (beta version)",
            font=LARGE_FONT,
        )
        label.pack(padx=10, pady=10)

        button1 = ttk.Button(
            self, text="Yes", command=lambda: controller.show_frame(MagPage)
        )  # if yes, send to MagPage class
        button1.pack()

        button2 = ttk.Button(self, text="No", command=quit)  # if no, QUIT/DESTROY
        button2.pack()


class MainPage(tk.Frame):
    """
    possible exit of application
    """

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Main Page", font=LARGE_FONT)
        label.pack(padx=10, pady=10)

        button2 = ttk.Button(
            self, text="EXIT", command=quit
        )  # lambda: controller.show_frame(StartPage))
        button2.pack(padx=4, pady=4)


class MagPage(tk.Frame):
    """
    Page -- animated graph for current patient status.  Data is read from mysql db
    """

    def __init__(self, parent, controller):
        """
        set frame, initialize reading from database, set variables start animations, set buttons for access to
        other parts of application
        :param parent:
        :param controller:
        """
        self.controller = controller
        self.parent = parent
        tk.Frame.__init__(self, parent)
        self.paused = False

        label = tk.Label(
            self, text="Graph Page\n Patient Status Information", font=LARGE_FONT
        )
        label.pack(padx=10, pady=10)

        button1 = ttk.Button(
            self, text="Back To Home", command=lambda: controller.show_frame(MainPage)
        )
        button1.pack(padx=4, pady=4)

        button2 = ttk.Button(
            self,
            text="Input Patient Vitals NOW",
            command=lambda: (controller.show_frame(MagCalculation), self.close_window),
        )
        button2.pack(padx=4, pady=4)

        # def build_new_graph(self):
        # create figure and draw on canvas
        fig, ax = plt.subplots(figsize=(12, 8))
        connection = dbc()
        data = connection.cursor()
        data.execute("SELECT * FROM BMI6300.Patient_BP;")  # read from db
        names = [x[0] for x in data.description]
        bp_data = [x for x in data.fetchall()]
        pt_data = pd.DataFrame(bp_data, columns=names)
        self.x = np.array(pt_data["TIME_Of_BP"])  # set x
        self.y1 = np.array(pt_data["SYSTOLIC"])  # set y
        self.y2 = np.array(pt_data["DIASTOLIC"])  # set y
        self.y3 = np.array(pt_data["PULSEOX"])  # set y
        self.y4 = np.array(pt_data["HR"])  # set y
        self.y5 = np.array(pt_data["TEMP"])  # set y

        # set x,y, color, label, linewidth on plot
        self.vline = np.where(self.y1 == 114)
        self.line1, = ax.plot(
            self.x, self.y1, color="royalblue", linewidth=2, label="SYSTOLIC"
        )
        self.line2, = ax.plot(
            self.x, self.y2, color="limegreen", linewidth=2, label="DIASTOLIC"
        )
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        self.line3, = ax.plot(
            self.x, self.y3, color="goldenrod", linewidth=2, label="O2".translate(SUB)
        )
        self.line4, = ax.plot(
            self.x, self.y4, color="darkslategray", linewidth=2, label="HR"
        )
        self.line5, = ax.plot(
            self.x, self.y5, color="darkorange", linewidth=2, label="TEMP"
        )
        plt.axhline(120, color="gray", linestyle="--", label="BP Reference Line")
        plt.axhline(70, color="gray", linestyle="--")  # reference lines
        self.x_line_annotation = "2019/10/29 06:32:27"
        self.x_line_anno_check = "2019/10/29 07:32:27"
        self.vline = plt.axvline(
            self.x_line_annotation, alpha=0.0, color="red", label="MagDrip START"
        )
        self.vline_text = plt.annotate(
            "MagDrip START", xy=(self.x_line_annotation, 114)
        )

        plt.title("Patient Status")  # set title
        plt.legend(
            bbox_to_anchor=(0, 1.01, 1, 0.102),
            loc=3,
            ncol=2,
            borderaxespad=0,
            fontsize=8,
        )  # legend
        for tick in ax.xaxis.get_major_ticks():
            # set xaxis ticks and angle
            tick.label.set_fontsize(6)
            tick.label.set_rotation(45)

        # draw graph on canvas, draw complete and frozen, animation set below
        self.canvas = FigureCanvasTkAgg(fig, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        # set animation, call function below to animate each point on graph
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.ani = animation.FuncAnimation(
            fig, self.pt_graph_start, frames=len(self.x), interval=600
        )
        self.ani.event_source.stop()

    def on_click(self, event):
        # function to start and stop graph animation on mouse click
        if self.paused:
            self.ani.event_source.stop()
        else:
            self.ani.event_source.start()
        self.paused ^= True

    def pt_graph_start(self, i):
        # set and graph EACH point
        self.line1.set_data(self.x[:i], self.y1[:i])
        self.line2.set_data(self.x[:i], self.y2[:i])
        self.line3.set_data(self.x[:i], self.y3[:i])
        self.line4.set_data(self.x[:i], self.y4[:i])
        self.line5.set_data(self.x[:i], self.y5[:i])

        # stop before it starts so when demo begins you get to say when
        if (i > 0) and max(self.y1[:i]) == 174:
            self.ani.event_source.stop()

        if (i > 0) and min(self.y1[:i]) == 101:
            # HARDCODED == at y=101 six hour as passed, send notification to nurse
            draw_labs = tk.messagebox.showinfo(
                "ALERT", "MAG START WAS 6 HOURS AGO. \n\nDRAW LABS FOR PATIENT"
            )
            if draw_labs == "ok":
                self.controller.show_frame(MagLabLevels)
                self.ani.event_source.stop()  # pause animation as we leave page
                self.close_window()

        if (i > 0) and min(self.y1[:i]) == 166:
            # HARDCODED == at y=166 one hour as passed, send notification to nurse
            vitals = tk.messagebox.showinfo(
                "ALERT", "MAG START WAS 1 HOUR AGO.  \n\nCHECK PATIENT VITALS"
            )
            if vitals == "ok":
                self.ani.event_source.stop()  # pause animation
                self.controller.show_frame(MagCalculation)

        if (i > 0) and max(self.y1[:i]) == 192:
            # HARDCODED == at y=192 write MagDrip start graph
            self.vline.set_alpha(1.0)
            self.vline_text.set_alpha(1.0)

        else:
            self.vline.set_alpha(0.0)
            self.vline_text.set_alpha(0.0)

    def close_window(self):
        self.destroy()


class MagCalculation(tk.Frame):
    """
    page for manual input of vitals by nurse at hour marks.  vitals collected and run through calculate
    suggestion to see if magdrip should be continued or stopped
    """

    def __init__(self, parent, controller):
        """
        Label and entry box created for each vital -- entry kept and used in calculate suggestion
        :param parent:
        :param controller:
        """
        self.controller = controller
        self.parent = parent
        self.MP = MagPage(parent, controller)
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Magnesium Drip Calculator", font=LARGE_FONT)
        label.grid(row=0, column=3)

        patient_calc = tk.Label(
            self,
            text="\nEnter Information below to Calculate Magnesium Drip Suggestion:\n\n",
        )
        patient_calc.grid(row=3, column=3)

        self.prr_options_var = tk.StringVar(self)
        self.prr_options = ["select option", "0-10", "11-15", "16-20", "21-25"]
        self.prr_options_var.set(self.prr_options[0])
        prr_label = tk.Label(self, text="Patient Respiratory Rate:")
        prr_label.grid(sticky="w", row=6, column=0)
        self.prr_entry = tk.OptionMenu(self, self.prr_options_var, *self.prr_options)
        self.prr_entry.config(borderwidth=6, width=19)
        self.prr_entry.grid(row=6, column=1)

        self.reflex_options_var = tk.StringVar(self)
        self.reflex_options = ["select option", "0", "1+", "2+", "3+", "4+", "5+"]
        self.reflex_options_var.set(self.reflex_options[0])
        reflex_label = tk.Label(self, text="Reflex (Select 0, 1+, 2+, 3+, 4+, 5+):")
        reflex_label.grid(sticky="w", row=8, column=0)
        self.reflex_entry = tk.OptionMenu(
            self, self.reflex_options_var, *self.reflex_options
        )
        self.reflex_entry.config(borderwidth=6, width=19)
        self.reflex_entry.grid(row=8, column=1)

        self.breath_options_var = tk.StringVar(self)
        self.breath_options = ["select option", "clear", "not clear"]
        self.breath_options_var.set(self.breath_options[0])
        breath_label = tk.Label(self, text="Breath Sounds (clear or not clear):")
        breath_label.grid(sticky="w", row=10, column=0)
        self.breath_entry = tk.OptionMenu(
            self, self.breath_options_var, *self.breath_options
        )
        self.breath_entry.config(borderwidth=6, width=19)
        self.breath_entry.grid(row=10, column=1)

        self.neuro_option_var = tk.StringVar(self)
        self.neuro_options = ["select option", "alert/oriented", "not alert"]
        self.neuro_option_var.set(self.neuro_options[0])
        neuro_label = tk.Label(self, text="Neuro ('alert/oriented' or 'no'):")
        neuro_label.grid(sticky="w", row=12, column=0)
        self.neuro_entry = tk.OptionMenu(
            self, self.neuro_option_var, *self.neuro_options
        )
        self.neuro_entry.config(borderwidth=6, width=19)
        self.neuro_entry.grid(row=12, column=1)

        uo_label = tk.Label(self, text="Urine Output (ml)")
        uo_label.grid(sticky="w", row=14, column=0)
        self.uo_entry = tk.Entry(self, bd=5)
        self.uo_entry.grid(row=14, column=1)

        button1 = ttk.Button(self, text="Submit", command=self.calculate_suggestion)
        button1.grid(row=16, column=1)

    def calculate_suggestion(self):
        """
        get entry, check entry type, if statements to decide suggestions.  Popup notifications created to guide user
        through suggestion process
        :return:  mag suggestion
        """
        # get entries
        resp_rate = self.prr_options_var.get()
        urine_output = self.uo_entry.get()
        reflex_output = self.reflex_options_var.get()
        breath_sounds = self.breath_options_var.get()
        neuro_level = self.neuro_option_var.get()
        try:  # try/check matches
            if (
                resp_rate in self.prr_options
                and urine_output.isdigit()
                and reflex_output in self.reflex_options
            ):  # checking entries
                # create integer variables for if statements below
                rr = str(resp_rate)
                uo = int(urine_output)
                ro = str(reflex_output)
                bs = str(breath_sounds)
                nl = str(neuro_level)

                # check input conditions are met, if not, throw error
                if (
                    rr == self.prr_options[1]
                    or ro == self.reflex_options[1]
                    or bs == self.breath_options[2]
                    or nl == self.neuro_options[2]
                    or uo < 30
                ):
                    tk.messagebox.showinfo("ALERT!", "\nSTOP MAGNESIUM DRIP NOW")
                    tk.messagebox.askokcancel(
                        "CONFIRM",
                        "Please Confirm Magnesium Drip is being stopped by "
                        "clicking 'OK'",
                    )
                    confirm = tk.messagebox.showinfo(
                        "INFORMATION", "Confirmation Logged"
                    )
                    if confirm == "ok":
                        self.controller.show_frame(MagUpdate)
                else:
                    answer = tk.messagebox.askquestion(
                        "INFORMATION",
                        "\nNO CHANGE IN MAG DRIP IS RECOMMENDED.\n\n"
                        "Do you wish to proceed with changing "
                        "Magnesium Drip dosage?",
                    )
                    if answer == "no":
                        tk_start = tk.messagebox.showinfo(
                            "INFORMATION", "Returning to Patient Information Page"
                        )
                        if tk_start == "ok":
                            self.controller.show_frame(MagPage)
                    else:
                        self.controller.show_frame(MagInformationPage)
                        self.destroy()
            else:
                tk.messagebox.showerror(
                    "ERROR",
                    "Must enter Numeric Value Only (e.g. 72) for Respiratory Rate and "
                    "Urine Output values.  Please Check for correct spelling.",
                )
        except Exception as e:
            print("Failed because of:", e)


class MagLabLevels(tk.Frame):
    """
    Patient lab levels checked after six hours
    """

    def __init__(self, parent, controller):
        """
        create button and entry option
        :param parent:
        :param controller:
        """
        self.controller = controller
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Magnesium Drip Calculator", font=LARGE_FONT)
        label.pack()

        serum_calc = tk.Label(
            self, text="\nEnter Patient Serum Level Below: (e.g. 4.2) \n\n"
        )
        serum_calc.pack()

        lab_label = tk.Label(self, text="Serum Level (ml)")
        lab_label.pack()
        self.lab_entry = tk.Entry(self, bd=5)
        self.lab_entry.pack()

        button1 = ttk.Button(self, text="Submit", command=self.calc_serum)
        button1.pack()

    def calc_serum(self):
        # get entry input -- check that it is a correct type.
        serum = float(self.lab_entry.get())
        try:
            if float(serum):
                s = float(serum)
                # suggestions calculated
                if s > 7:
                    tk.messagebox.showinfo("ALERT!", "\nSTOP MAGNESIUM DRIP NOW")
                    tk.messagebox.askokcancel(
                        "CONFIRM",
                        "Please Confirm Magnesium Drip is being stopped by "
                        "clicking 'OK'",
                    )
                    confirm = tk.messagebox.showinfo(
                        "INFORMATION", "Confirmation Logged"
                    )
                    if confirm == "ok":
                        self.controller.show_frame(MagUpdate)
                else:
                    if s < 7:
                        less_than_confirm = tk.messagebox.showinfo(
                            "INFORMATION",
                            "\nMAG DRIP CAN CONTINUE, "
                            "PLEASE CONTINUE TO CHECK VITALS\n"
                            "Exiting MagDrip Tool.",
                        )
                        if less_than_confirm == "ok":
                            self.quit()

            else:
                tk.messagebox.showerror(
                    "ERROR",
                    "Must enter Numeric Value Only (e.g. 72) for Respiratory Rate and "
                    "Urine Output values.",
                )
        except Exception as e:
            print("Failed because of:", e)


class MagUpdate(tk.Frame):
    """
    Post MagStop graph for patient.  shows patient progression.  'patient lives/gets better' because CDS Tool is so
    AWESOME!
    """

    def __init__(self, parent, controller):
        """
        initiate frame, create differnt table, read from different table in mysql
        title and button options created
        :param parent:
        :param controller:
        """
        self.controller = controller
        self.parent = parent
        tk.Frame.__init__(self, parent)
        self.paused = False

        label = tk.Label(self, text="Patient Status", font=LARGE_FONT)
        label.pack(padx=10, pady=10)

        button1 = ttk.Button(self, text="Exit", command=quit)
        button1.pack(padx=4, pady=4)

        # create figure and draw on canvas
        fig2, ax = plt.subplots(figsize=(12, 8))
        connection = dbc()
        new_data = connection.cursor()
        new_data.execute("SELECT * FROM BMI6300.Current_Patient_BP;")  # read from db
        names = [x[0] for x in new_data.description]
        bp_data = [x for x in new_data.fetchall()]
        pt_data = pd.DataFrame(bp_data, columns=names)
        self.x = np.array(pt_data["TIME_Of_BP"])  # set x
        self.y1 = np.array(pt_data["SYSTOLIC"])  # set y
        self.y2 = np.array(pt_data["DIASTOLIC"])  # set y
        self.y3 = np.array(pt_data["PULSEOX"])  # set y
        self.y4 = np.array(pt_data["HR"])  # set y
        self.y5 = np.array(pt_data["TEMP"])  # set y

        # set x,y, color, label, linewidth on plot
        self.line1, = ax.plot(
            self.x, self.y1, color="royalblue", linewidth=2, label="SYSTOLIC"
        )
        self.line2, = ax.plot(
            self.x, self.y2, color="limegreen", linewidth=2, label="DIASTOLIC"
        )
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        self.line3, = ax.plot(
            self.x, self.y3, color="goldenrod", linewidth=2, label="O2".translate(SUB)
        )
        self.line4, = ax.plot(
            self.x, self.y4, color="darkslategray", linewidth=2, label="HR"
        )
        self.line5, = ax.plot(
            self.x, self.y5, color="darkorange", linewidth=2, label="TEMP"
        )
        plt.axhline(120, color="gray", linestyle="--", label="BP Reference Line")
        plt.axhline(70, color="gray", linestyle="--")  # reference lines
        self.x_line_anno_check = "2019/10/29 17:32:27"  # hardcoded magstopped line draw
        self.vline = plt.axvline(
            self.x_line_anno_check, alpha=0.0, color="red", label="MagDrip STOPPED"
        )
        self.vline_text = plt.annotate(
            "MagDrip STOPPED", xy=(self.x_line_anno_check, 91)
        )

        plt.title("Patient Status")  # set title
        plt.legend(
            bbox_to_anchor=(0, 1.01, 1, 0.102),
            loc=3,
            ncol=2,
            borderaxespad=0,
            fontsize=8,
        )  # legend
        for tick in ax.xaxis.get_major_ticks():
            # set xaxis ticks and angle
            tick.label.set_fontsize(6)
            tick.label.set_rotation(45)

        # draw graph on canvas, draw complete and frozen, animation set below
        self.canvas1 = FigureCanvasTkAgg(fig2, self)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas1, self)
        self.toolbar.update()
        self.canvas1._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        # set animation, call function below to animate each point on graph
        self.canvas1.mpl_connect("button_press_event", self.on_click)
        self.ani2 = animation.FuncAnimation(
            fig2, self.pt_graph_update, frames=len(self.x), interval=600
        )
        self.ani2.event_source.stop()

    def on_click(self, event):
        # function to start and stop graph animation on mouse click
        if self.paused:
            self.ani2.event_source.stop()
        else:
            self.ani2.event_source.start()
        self.paused ^= True

    def pt_graph_update(self, i):
        # set and graph EACH point
        self.line1.set_data(self.x[:i], self.y1[:i])
        self.line2.set_data(self.x[:i], self.y2[:i])
        self.line3.set_data(self.x[:i], self.y3[:i])
        self.line4.set_data(self.x[:i], self.y4[:i])
        self.line5.set_data(self.x[:i], self.y5[:i])

        if (i > 0) and max(self.y1[:i]) == 91:
            # HARDCODED == draw line MagStopped
            self.vline.set_alpha(1.0)
            self.vline_text.set_alpha(1.0)
            self.ani2.event_source.stop()
        if (i > 0) and min(self.y1[:i]) == 91:
            self.vline.set_alpha(1.0)
            self.vline_text.set_alpha(1.0)
        else:
            self.vline.set_alpha(0.0)
            self.vline_text.set_alpha(0.0)


class MagInformationPage(tk.Frame):
    """
    In the event that the mag calculation suggestion is overridden. The user will be directed to this page to see
    the warnings related to continuing with too much mag
    User must read and CONFIRM they understand the warnings.  IF they confirm, they are exited from app
    """

    def __init__(self, parent, controller):
        """
        frame drawn, mag information text placed in frame....  nothing more, just regular text to read
        :param parent:
        :param controller:
        """
        self.controller = controller
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Information of Magnesium Drip", font=LARGE_FONT)
        label.pack(padx=10, pady=10)

        button1 = ttk.Button(
            self,
            text="Back To Patient Information",
            command=lambda: controller.show_frame(MagPage),
        )
        button1.pack()

        button2 = ttk.Button(self, text="Confirm", command=self.confirm_mag)
        button2.pack(padx=4, pady=4)

        mag_text = tk.Text(self, height=30, width=142)
        mag_text.pack()
        quote = mag_information
        mag_text.insert(tk.END, quote)

    def confirm_mag(self):
        confirm = tk.messagebox.showinfo("INFORMATION", "Confirmation Logged")
        if confirm == "ok":
            quit()


app = TheMagApp()  # run it
app.geometry("1280x720")
app.mainloop()  # keep it running
