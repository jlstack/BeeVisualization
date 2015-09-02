__author__ = 'lukestack'
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
import matplotlib.ticker as tkr
import Tkinter as Tk
import tkSimpleDialog
import tkMessageBox
import matplotlib.pyplot as plt
import Dates
import ftplib
from scipy.io.wavfile import read
from pydub import AudioSegment
import tempfile
import os
import math
import numpy as np

global ftp
ftp = username = password = None
if not os.path.isdir("Gui_files"):
    os.mkdir("Gui_files")


class LoginDialog(tkSimpleDialog.Dialog):
    """
    Pop-up box that prompts user for login information.
    """
    def body(self, master):
        """
        Creates the box.
        :param master: root
        :return: self.name to highlight the username input box
        """
        Tk.Label(master, text="username:").grid(row=0)
        Tk.Label(master, text="password:").grid(row=1)
        self.name = Tk.Entry(master)
        self.password = Tk.Entry(master, show="*")
        self.name.grid(row=0, column=1)
        self.password.grid(row=1, column=1)
        return self.name  # initial focus

    def apply(self):
        """
        Retrieves all of the information and stores it in self.result
        :return: None
        """
        self.result = self.name.get(), self.password.get()


class DateDialog(tkSimpleDialog.Dialog):
    """
    Pop-up box that gets the desired date, time, and channel to look at.
    """
    def body(self, master):
        """
        Creates the box.
        :param master: root
        :return: self.date to highlight the date input box
        """
        Tk.Label(master, text="Date:").grid(row=0)
        Tk.Label(master, text="Time:").grid(row=1)
        self.date = Tk.Entry(master)
        self.time = Tk.Entry(master)
        self.date.insert(0, "2015-07-21")
        self.time.insert(0, "18:16:30")
        self.date.grid(row=0, column=1)
        self.time.grid(row=1, column=1)

        self.pit = Tk.StringVar()
        self.pit.set('pit2')
        self.pit1 = Tk.Radiobutton(master, text='pit1', variable=self.pit, value='pit1')
        self.pit2 = Tk.Radiobutton(master, text='pit2', variable=self.pit, value='pit2')
        self.pit_label = Tk.Label(master, text="Pit:")
        self.pit_label.grid(row=2, column=0)
        self.pit1.grid(row=2, column=1)
        self.pit2.grid(row=2, column=2)

        self.channel = Tk.StringVar()
        self.channel.set('left')
        self.left = Tk.Radiobutton(master, text='left', variable=self.channel, value='left')
        self.right = Tk.Radiobutton(master, text='right', variable=self.channel, value='right')
        self.channel_label = Tk.Label(master, text="Channel:")
        self.channel_label.grid(row=3, column=0)
        self.left.grid(row=3, column=1)
        self.right.grid(row=3, column=2)
        return self.date  # initial focus

    def apply(self):
        """
        Retrieves all of the information and stores it in self.result
        :return: None
        """
        date = self.date.get()
        time = self.time.get()
        pit = self.pit.get()
        channel = self.channel.get()
        self.result = date, time, pit, channel


class BeeApp(Tk.Tk):
    """
    Creates an interface that helps the user visualize audio data located on the server.
    """
    def __init__(self, date, time, pit, channel):
        """
        Initializes the whole interface.
        :param date: starting date
        :param time: starting time
        :param channel: specified channel
        :return: None
        """
        Tk.Tk.__init__(self)
        self.title("Bee App")
        self.pit = pit
        self.input_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs2/%s/" % self.pit
        self.mp3_dirs = ["/usr/local/bee/beemon/beeW/Luke/mp3s/" + self.pit + "/%s/audio/",
                         "/usr/local/bee/beemon/" + self.pit + "/%s/audio/"]
        self.video_dir = "/usr/local/bee/beemon/" + self.pit + "/%s/video/"
        start_hex, start_dir = Dates.to_hex(date, time)
        self.current_input = self.input_dir + start_dir
        self.channel = channel
        self.leftmost = make_hex8("".join(start_dir.split("/")))
        self.center = format(int(self.leftmost, 16) + 8, 'x')
        self.zoom = 1
        self.files = self.server_files = {'pit1': {}, 'pit2': {}}
        self.cax = self.stream = self.combined_spec = None
        self.current_view = "spec"
        self.update_combined_spec(self.center)

        self.option_add('*tearOff', False)  # Creating a menubar
        self.menubar = Tk.Menu(self)
        self.config(menu=self.menubar)
        pit = Tk.Menu(self.menubar)
        channel = Tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=pit, label="pit")
        self.menubar.add_cascade(menu=channel, label="channel")
        self.menubar.add_command(label="Search Date", command=self.search_date)
        pit.add_radiobutton(label="pit1", command=lambda: self.change_pit("pit1"))
        pit.add_radiobutton(label="pit2", command=lambda: self.change_pit("pit2"))
        channel.add_radiobutton(label="left", command=lambda: self.change_channel("left"))
        channel.add_radiobutton(label="right", command=lambda: self.change_channel("right"))

        self.matplotlib_plot = Tk.Frame(self)  # Frame that holds the matplotlib figure
        fig, ax = plt.subplots()
        fig.canvas.draw()
        self.fig = fig
        self.ax = ax
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.matplotlib_plot)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.canvas.mpl_connect('key_press_event', self.toolbox_event)
        self.matplotlib_plot.pack(fill=Tk.BOTH, expand=True)
        self.create_specgram()  # creates the initial spectrogram

        self.control_frame = Tk.Frame(self, width=400)  # Frame that holds the navigational buttons
        self.zoom_out = Tk.Button(self.control_frame, text="-", command=self.on_zoom_out)
        self.zoom_out.grid(row=0, column=0)
        self.zoom_in = Tk.Button(self.control_frame, text="+", command=self.on_zoom_in)
        self.zoom_in.grid(row=0, column=1)
        if self.zoom == -8:
            self.zoom_in['state'] = 'disabled'  # Makes zoom in button unclickable
        self.play = Tk.Button(self.control_frame, text="Audio", command=self.on_audio)
        self.play.grid(row=0, column=2)
        self.play_video = Tk.Button(self.control_frame, text="Video", command=self.on_video)
        self.play_video.grid(row=0, column=3)
        self.toggle = Tk.Button(self.control_frame, text="Frequencies", command=self.on_plot)
        self.toggle.grid(row=0, column=4)
        self.left = Tk.Button(self.control_frame, text="<", command=self.on_left)
        self.left.grid(row=0, column=5)
        self.right = Tk.Button(self.control_frame, text=">", command=self.on_right)
        self.right.grid(row=0, column=6)
        self.control_frame.pack()

        self.message_frame = Tk.LabelFrame(self, height=50, width=400)  # Frame that holds the message
        self.message = Tk.Label(self.message_frame, text="Last Played:")
        self.message.pack()
        self.message_frame.pack()

    def toolbox_event(self, event):
        """
        Handles events for matplotlib toolbox.
        :param event: event that occurred
        :return: None
        """
        key_press_handler(event, self.canvas, self.toolbar)

    def search_date(self):
        """
        Uses DateDialog to search for a date and time.
        :return: None
        """
        root = Tk.Tk()
        root.withdraw()
        d = DateDialog(root)
        try:
            date, time, pit, channel = d.result
            root.destroy()
            start_hex, start_dir = Dates.to_hex(date, time)
            self.current_input = self.input_dir + start_dir
            self.channel = channel
            self.pit = pit
            self.leftmost = make_hex8("".join(start_dir.split("/")))
            self.center = format(int(self.leftmost, 16) + 8, 'x')
            self.update_combined_spec(self.center)
            self.on_spec()
        except TypeError:
            pass

    def change_pit(self, pit):
        """
        Changes which pit is being observed.
        :param pit: pit to be observed
        :return: None
        """
        self.pit = pit
        self.input_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs2/%s/" % self.pit
        self.mp3_dirs = ["/usr/local/bee/beemon/mp3/" + self.pit + "/%s/audio/",
                         "/usr/local/bee/beemon/" + self.pit + "/%s/audio/"]
        self.video_dir = "/usr/local/bee/beemon/" + self.pit + "/%s/video/"
        self.update_combined_spec(self.center)
        self.update_matplotlib_fig()

    def change_channel(self, channel):
        """
        Changes which channel is being observed.
        :param channel: channel to be observed
        :return: None
        """
        self.channel = channel
        self.update_combined_spec(self.center)
        self.update_matplotlib_fig()

    def on_zoom_out(self):
        """
        Zooms out one level and calls self.update_combined_spec to update the spectrogram.
        :return: None
        """
        if self.zoom < 1:
            self.zoom += 1
            self.ax.set_xlim((512 - 2**(9 + self.zoom) / 2, 512 + 2**(9 + self.zoom) / 2 - 1))
            self.canvas.draw()
        elif self.zoom < 28:
            self.zoom += 1
            self.update_combined_spec(self.center)
            self.update_matplotlib_fig()
        if self.zoom > -8:
            self.zoom_in['state'] = 'normal'

    def on_zoom_in(self):
        """
        Zooms in one level and calls self.update_combined_spec to update the spectrogram.
        :return: None
        """
        if self.zoom != -8 and self.zoom > 1:
            self.zoom -= 1
            self.update_combined_spec(self.center)
        elif self.zoom != -8 and self.zoom <= 1:
            self.zoom -= 1
            self.ax.set_xlim((512 - 2**(9 + self.zoom) / 2, 512 + 2**(9 + self.zoom) / 2 - 1))
            self.canvas.draw()
        if self.zoom == -8:
            self.zoom_in['state'] = 'disabled'
        self.update_matplotlib_fig()


    def on_plot(self):
        """
        Handler for toggle button when the view is being changed
        from a spectrogram to a frequency plot.
        :return: None
        """
        self.toggle.config(text="Spectrogram", command=self.on_spec)
        self.current_view = "plot"
        self.create_plot()

    def on_spec(self):
        """
        Handler for toggle button when the view is being changed
        from a frequency plot to a spectrogram.
        :return: None
        """
        self.toggle.config(text="Frequencies", command=self.on_plot)
        self.current_view = "spec"
        self.create_specgram()

    def create_plot(self):
        """
        Creates plot of frequencies for combined_spec.
        :return: None
        """
        self.ax.clear()
        date1, time1 = Dates.to_date(self.leftmost)
        date2, time2 = Dates.to_date('{:08x}'.format(int(self.leftmost, 16) + 2 ** (9 + self.zoom) - 1))
        self.ax.set_title(date1 + "T" + time1 + " - " + date2 + "T" + time2)
        freqs = np.arange(0, self.combined_spec.shape[1] / 2.0, .5)
        if not math.isnan(np.mean(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T)):
            self.ax.plot(freqs, np.mean(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T, axis=1))
            for i in range(len(self.combined_spec.T)):
                if np.amax(self.combined_spec.T[20:, :]) in self.combined_spec.T[i]:
                    for j in range(len(self.combined_spec.T[i])):
                        if self.combined_spec.T[i, j] == np.amax(self.combined_spec.T[20:, :]):
                            print i, j
                            break
                    break
            self.ax.set_ylim((0, np.amax(self.combined_spec.T[20:, :])))
        else:
            self.ax.plot(freqs, [0] * len(freqs))
        self.canvas.draw()

    def create_specgram(self):
        """
        Creates the current spectrogram for combined_spec.
        :return: None
        """
        rightmost = '{:08x}'.format(int(self.leftmost, 16) + 2 ** (9 + self.zoom) - 1)
        date1, file_time1 = Dates.to_date(self.leftmost)
        date2, file_time2 = Dates.to_date(rightmost)
        if not date1 == date2:
            title = date1 + "  -  " + date2
        else:
            title = date1
        self.ax.clear()
        self.ax.set_xticks(np.arange(0, self.combined_spec.shape[0], 16.0))
        self.ax.set_xticklabels(["" for x in range(self.combined_spec.shape[0])])
        cax = self.ax.imshow(20 * np.log10(self.combined_spec.T), origin='lower',
                             aspect='auto', interpolation='nearest')
        self.ax.set_title(title)
        labels = [item.get_text() for item in self.ax.get_xticklabels()]
        labels[0] = file_time1
        center_date, center_time = Dates.to_date(self.center)
        labels[len(labels) / 2] = center_time
        labels[len(labels) - 1] = file_time2
        self.ax.set_xticklabels(labels)
        yfmt = tkr.FuncFormatter(numfmt)
        self.ax.yaxis.set_major_formatter(yfmt)
        # sets the colorbar for all spectrograms
        if self.cax is None and np.count_nonzero(self.combined_spec) != 0:
            self.cax = self.ax.imshow(20 * np.log10(self.combined_spec.T), origin='lower',
                                      aspect='auto', interpolation='nearest')
            self.fig.colorbar(cax)
        if self.cax is not None:
            cax.set_clim(self.cax.get_clim())
        if self.canvas is not None:
            self.canvas.draw()

    def update_matplotlib_fig(self):
        """
        Calls the appropriate method to generate the current
        spectrogram of frequency plot.
        :return:
        """
        if self.current_view == "spec":
            self.create_specgram()
        else:
            self.create_plot()

    def on_audio(self):
        """
        Callback for play button. Locates the file associated with given time if the file exists.
        Then calls the play function to play the located file.
        :return: None
        """
        audio_dir = None
        audio_file = None
        for i in range(0, 60):
            sec = int(self.center, 16)
            sec -= i
            sec = format(sec, 'x')
            date, time = Dates.to_date(sec)
            date = date.split('-')
            date.reverse()
            date = '-'.join(date)
            for j in range(0, len(self.mp3_dirs)):
                try:
                    ftp.cwd(self.mp3_dirs[j] % date)
                    files = ftp.nlst()
                    if files is not None:
                        for f in files:
                            if time in f:
                                audio_dir = self.mp3_dirs[j] % date
                                audio_file = f
                                break
                except ftplib.error_perm, e:
                    if "550" in e.message:
                        pass
                    else:
                        pass
                """
                elif "421" in e.message:
                    print "relogged in"
                    ftp = ftplib.FTP('cs.appstate.edu', user, password)
                """
            if audio_file is not None:
                break
        if audio_file is not None:
            print audio_dir + audio_file
            if audio_file not in self.server_files[self.pit]:
                with open("Gui_files/" + "-".join(audio_file.split(":")), 'wb') as r:
                    ftp.retrbinary('RETR ' + audio_dir + audio_file, r.write)
                os.startfile("Gui_files\\" + "-".join(audio_file.split(":")))
                self.server_files[self.pit][audio_file] = "Gui_files\\" + "-".join(audio_file.split(":"))
                self.message.config(text="Found:" + audio_dir + audio_file)
            else:
                self.message.config(text="Found:" + audio_dir + audio_file)
                os.startfile(self.server_files[self.pit][audio_file])
        else:
            self.message.config(text="No audio file.")

    def on_video(self):
        """
        Callback for play button. Locates the file associated with given time if the file exists.
        Then calls the play function to play the located file.
        :return: None
        """
        video_dir = video_file = None
        for i in range(0, 60):
            sec = int(self.center, 16)
            sec -= i
            sec = format(sec, 'x')
            date, time = Dates.to_date(sec)
            date = date.split('-')
            date.reverse()
            date = '-'.join(date)
            try:
                ftp.cwd(self.video_dir % date)
                files = ftp.nlst()
                print len(files)
                if files is not None:
                    for f in files:
                        if time in f or '-'.join(time.split(':')) in f:
                            video_dir = self.video_dir % date
                            video_file = f
                            break
            except ftplib.error_perm, e:
                if "550" in e.message:
                    pass
                else:
                    pass
                """
                elif "421" in e.message:
                    print "relogged in"
                    ftp = ftplib.FTP('cs.appstate.edu', user, password)
                """
            if video_file is not None:
                break
        if video_file is not None:
            print self.video_dir + video_file
            if video_file not in self.server_files[self.pit]:
                with open("Gui_files\\" + "-".join(video_file.split(":")), 'wb') as r:
                    ftp.retrbinary('RETR ' + video_dir + video_file, r.write)
                self.server_files[self.pit][video_file] = "Gui_files\\" + "-".join(video_file.split(":"))
                os.startfile("Gui_files\\" + "-".join(video_file.split(":")))
                self.message.config(text="Found:" + video_dir + video_file)
            else:
                self.message.config(text="Found:" + video_dir + video_file)
                os.startfile(self.server_files[self.pit][video_file])
        else:
            self.message.config(text="No video file.")

    def on_right(self):
        """
        Moves the center time to the right and updates the plot.
        :return: None
        """
        cen = int(self.center, 16)
        cen += 2 ** (9 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.update_combined_spec(self.center)
        self.update_matplotlib_fig()

    def on_left(self):
        """
        Moves the center time to the left and updates the plot.
        :return: None
        """
        cen = int(self.center, 16)
        cen -= 2 ** (9 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.update_combined_spec(self.center)
        self.update_matplotlib_fig()

    def update_combined_spec(self, hex_num):
        """
        Gets the 16 files surrounding the specified hex time stamp.
        Center time should be the time passed in.
        :param hex_num: hex time stamp that will be the center of the data
        :return: None
        """
        from datetime import datetime
        start_datetime = datetime.now()
        print ("Zoom: ", self.zoom)
        combined_spec = None
        lm = int(hex_num, 16)
        lm -= 2 ** (9 + self.zoom) / 2  # leftmost value
        self.leftmost = make_hex8('{:08x}'.format(lm))
        start_date, start_time = Dates.to_date('{:08x}'.format(lm))
        end_date, end_time = Dates.to_date('{:08x}'.format(lm + 2 ** (9 + self.zoom)))
        self.combined_spec = self.get_specgram(start_date, start_time, end_date, end_time)
        print datetime.now() - start_datetime

        """
        print start_date, start_time, end_date, end_time
        ftp.cwd("/u/css/stackjl/BeeVisualization/")
        print "changed directories"
        # ftp.sendcmd("python create_specgram2.py " + start_date + " " + start_time + " " + end_date + " " + end_time +
        #             " " + self.pit + " " + self.channel + " " + self.zoom + " &> test2.txt")
        for i in range(0, 2 ** (9 + self.zoom), 2 ** (self.zoom - 1)):
            i_hex = '{:08x}'.format(int(lm + i))
            i_hex = i_hex[:int(len(i_hex) - ((self.zoom - 1) / 4))]
            i_dir = "/".join(i_hex[:-1]) + "/"
            i_file = None
            try:
                if self.zoom == 1:
                    date, time = Dates.to_date(i_hex)
                    fname = i_hex + "_" + date + "T" + time + "_" + self.channel + ".spec.npy"
                elif 4 - (self.zoom - 1) % 4 == 4:
                    fname = i_hex + "_" + self.channel + ".spec.npy"
                else:
                    bi = "{0:04b}".format(int(i_hex[-1], 16))[:(4 - (self.zoom - 1) % 4)]
                    fname = i_hex[:-1] + "_" + bi + "_" + self.channel + ".spec.npy"
                if fname in self.files[self.pit]:
                    i_file = fname
                else:
                    ftp.cwd(self.input_dir + i_dir)
                    files = ftp.nlst()
                    for f in files:
                        if f == fname:
                            i_file = f
                            break
            except ftplib.error_perm, e:  # thrown if directory does not exist
                if "550" in e.message:
                    pass
                else:
                    pass
            if i_file is not None:
                print (i_file)
                if i_file not in self.files[self.pit]:
                    r = open("Gui_files/from_server.npy", 'wb')
                    ftp.retrbinary('RETR ' + self.input_dir + i_dir + i_file, r.write)
                    r.close()
                    data = np.load("Gui_files/from_server.npy").item()
                    self.files[self.pit][i_file] = data
                else:
                    data = self.files[self.pit][i_file]
                if combined_spec is None:
                    combined_spec = data["intensities"]
                else:
                    combined_spec = np.vstack((combined_spec, data["intensities"]))
            else:
                if combined_spec is None:
                    combined_spec = [0] * 2049
                else:
                    combined_spec = np.vstack((combined_spec, [0] * 2049))
        print combined_spec.shape
        self.combined_spec = combined_spec
        print datetime.now() - start_datetime
        start_datetime = datetime.now()
        r = open("Gui_files/from_server.npz", 'wb')
        ftp.retrbinary('RETR /u/css/stackjl/BeeVisualization/test.npz', r.write)
        r.close()
        data = np.load("Gui_files/from_server.npz")
        """

    def get_specgram(self, start_date, start_time, end_date, end_time):
        fname = start_date + '_' + start_time + "-" + end_date + '_' + end_time + '_' + self.pit + "_" + str(self.zoom) + '.npz'
        if fname.replace(':', '-') not in os.listdir("Gui_files"):
            ftp.cwd("/u/css/stackjl/BeeVisualization/specgrams/")
            files = ftp.nlst()
            if fname not in files:
                import paramiko
                import select
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect("cs.appstate.edu", username='stackjl', password='sta.44,ck')
                print "python ./BeeVisualization/create_specgram2.py " + start_date + " " + start_time + " " + \
                      end_date + " " + end_time + " " + self.pit + " " + self.channel + " " + str(self.zoom)
                stdin, stdout, stderr = ssh.exec_command("python ./BeeVisualization/create_specgram2.py " + start_date + " " +
                                                         start_time + " " + end_date + " " + end_time + " " + self.pit + " " +
                                                         self.channel + " " + str(self.zoom))
                # Found at http://sebastiandahlgren.se/2012/10/11/using-paramiko-to-send-ssh-commands/
                while not stdout.channel.exit_status_ready():
                    pass
                    """
                    # Only print data if there is data to read in the channel
                    if stdout.channel.recv_ready():
                        rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
                        if len(rl) > 0:
                            # Print data from stdout
                            print stdout.channel.recv(1024),
                    """
                ssh.close()
            import time
            now = time.time()
            r = open("Gui_files/" + fname.replace(':', '-'), 'wb')
            ftp.retrbinary('RETR /u/css/stackjl/BeeVisualization/specgrams/' + fname, r.write)
            r.close()
            np.load("Gui_files/" + fname.replace(':', '-'))['intensities']
            print time.time() - now
        return np.load("Gui_files/" + fname.replace(':', '-'))['intensities']




def numfmt(y, pos):
    """
    Divides each y label by 2.
    :param y: initial y value
    :param pos: position of label
    :return: modified y value
    """
    s = '{}'.format(y / 2)
    return s


def get_data(path):
    """
    Retrieves data from audio file. If file is not a wav, a wav file is generated from the file.
    :param path: path to audio file (wav, flac, and mp3 are acceptable)
    :return: sample rate, data from wav
    """
    if path.endswith(".wav"):
        bee_rate, bee_data = read(path)
    else:
        temp = tempfile.NamedTemporaryFile(suffix=".wav")
        temp.close()
        if path.endswith(".flac"):
            sound = AudioSegment.from_file(path, "flac")
            sound.export(temp.name, format="wav")
        elif path.endswith(".mp3"):
            sound = AudioSegment.from_file(path, "mp3")
            sound.export(temp.name, format="wav")
        bee_rate, bee_data = read(temp.name)
    return bee_rate, bee_data


def make_hex8(hex_num):
    """
    Pads end of hex with 0s to make it length 8.
    :param hex_num: Number to be padded
    :return: padded hex number
    """
    for i in range(0, 8 - len(hex_num)):
        hex_num += "0"
    return hex_num


def on_closing(app):
    """
    Callback for the closing of the application.
    :return: None
    """
    for f in os.listdir("Gui_files"):
        try:
            os.remove("Gui_files\\" + f)
        except:
            pass
    os.rmdir("Gui_files")
    ftp.close()
    app.destroy()
    plt.close()


def main():
    root = Tk.Tk()
    root.withdraw()
    while True:  # continues prompting until login is successful or window is closed
        try:
            login = LoginDialog(root)
            global user, password
            user, password = login.result
            global ftp
            ftp = ftplib.FTP('cs.appstate.edu', user, password)
            login.destroy()
            break
        except ftplib.error_perm:
            tkMessageBox.showwarning("Login Failure", "Incorrect login credentials.\nPlease try again.")
        except TypeError:
            return
    try:
        d = DateDialog(root)
        date, time, pit, channel = d.result
        root.destroy()
        app = BeeApp(date, time, pit, channel)
        app.protocol("WM_DELETE_WINDOW", lambda: on_closing(app))
        app.mainloop()
    except TypeError:
        return

if __name__ == "__main__":
    main()
