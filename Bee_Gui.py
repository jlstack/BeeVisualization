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
import numpy as np


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
        self.date.insert(0, "2015-05-15")
        self.time.insert(0, "17:46:38")
        self.date.grid(row=0, column=1)
        self.time.grid(row=1, column=1)

        self.pit = Tk.StringVar()
        self.pit.set('pit1')
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


class SearchDateDialog(tkSimpleDialog.Dialog):
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
        return self.date  # initial focus

    def apply(self):
        """
        Retrieves all of the information and stores it in self.result
        :return: None
        """
        date = self.date.get()
        time = self.time.get()
        self.result = date, time


class BeeApp(Tk.Tk):
    """
    Creates an interface that helps the user visualize audio data located on the server.
    """
    def __init__(self, date, time, pit, channel):
        """
        Initializes the whole interface. Sorry for the length, but there are a lot of buttons...
        :param date: starting date
        :param time: starting time
        :param channel: specified channel
        :return: None
        """
        Tk.Tk.__init__(self)
        self.title("Bee App")
        self.pit = pit
        self.input_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs/%s/" % self.pit
        self.mp3_dirs = ["/usr/local/bee/beemon/beeW/Luke/mp3s/" + self.pit + "/%s/audio/",
                         "/usr/local/bee/beemon/" + self.pit + "/%s/audio/"]
        self.video_dir = "/usr/local/bee/beemon/" + self.pit + "/%s/video/"
        self.center, start_dir = Dates.to_hex(date, time)
        print start_dir
        self.current_input = self.input_dir + start_dir
        self.channel = channel
        self.zoom = 10
        self.leftmost = '{:08x}'.format(int(self.center, 16) + (2 ** self.zoom) / 2)
        self.spec_files = self.media_files = {'pit1': {}, 'pit2': {}}
        self.cax = self.stream = self.current_spec = None
        self.current_view = "spec"
        self.update_current_spec()

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
        if self.zoom == 10:
            self.zoom_out['state'] = 'disabled'  # Makes zoom out button unclickable
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
        try:
            root = Tk.Tk()
            root.withdraw()
            d = SearchDateDialog(root)
            date, time, = d.result
            root.destroy()
            self.center, start_dir = Dates.to_hex(date, time)
            self.leftmost = '{:08x}'.format(int(self.center, 16) + (2 ** self.zoom) / 2)
            self.update_current_spec()
            self.on_spec()
        except TypeError as e:
            print e.message

    def change_pit(self, pit):
        """
        Changes which pit is being observed.
        :param pit: pit to be observed
        :return: None
        """
        self.pit = pit
        self.input_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs/%s/" % self.pit
        self.mp3_dirs = ["/usr/local/bee/beemon/beeW/Luke/mp3s/" + self.pit + "/%s/audio/",
                         "/usr/local/bee/beemon/" + self.pit + "/%s/audio/"]
        self.video_dir = "/usr/local/bee/beemon/" + self.pit + "/%s/video/"
        self.cax = None
        self.fig.clear()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.update_current_spec()
        self.update_matplotlib_fig()

    def change_channel(self, channel):
        """
        Changes which channel is being observed.
        :param channel: channel to be observed
        :return: None
        """
        self.channel = channel
        self.cax = None
        self.fig.clear()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.update_current_spec()
        self.update_matplotlib_fig()

    def on_zoom_out(self):
        """
        Zooms out one level and calls self.update_current_spec to update the spectrogram.
        :return: None
        """
        """
        if self.zoom < 1:
            self.zoom += 1
            # self.ax.set_xlim((512 - 2**(9 + self.zoom) / 2, 512 + 2**(9 + self.zoom) / 2 - 1))
            # self.canvas.draw()
        """
        if self.zoom < 10:
            self.zoom += 1
            self.update_current_spec()
            self.update_matplotlib_fig()
        if self.zoom == 10:
            self.zoom_out['state'] == "disabled"
        if self.zoom_in['state'] == "disabled" and self.zoom >= 1 and self.zoom < 10:
            self.zoom_in['state'] = 'normal'

    def on_zoom_in(self):
        """
        Zooms in one level and calls self.update_current_spec to update the spectrogram.
        :return: None
        """
        if self.zoom >= 1:
            self.zoom -= 1
            self.update_current_spec()
            if self.zoom == 0:
                self.zoom_in['state'] = 'disabled'
            self.update_matplotlib_fig()
        if self.zoom_out['state'] == "disabled" and self.zoom < 10:
            self.zoom_out['state'] = 'normal'

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
        date2, time2 = Dates.to_date('{:08x}'.format(int(self.leftmost, 16) + 2 ** self.zoom - 1))
        self.ax.set_title(date1 + "T" + time1 + " - " + date2 + "T" + time2)
        freqs = np.arange(0, self.current_spec.shape[0] / 2.0, .5)
        mask = np.all(np.isnan(self.current_spec), axis=0)
        if len(self.current_spec[:, ~mask]) != 0:
            self.ax.plot(freqs, np.mean(self.current_spec[:, ~mask], axis=1))
            self.ax.set_ylim((0, .00001))# np.amax(self.current_spec[20:, :])))
        else:
            self.ax.plot(freqs, [0] * len(freqs))
        self.canvas.draw()

    def create_specgram(self):
        """
        Creates the current spectrogram for combined_spec.
        :return: None
        """
        rightmost = '{:08x}'.format(int(self.leftmost, 16) + 2 ** self.zoom - 1)
        date1, file_time1 = Dates.to_date(self.leftmost)
        date2, file_time2 = Dates.to_date(rightmost)
        if not date1 == date2:
            title = date1 + "  -  " + date2
        else:
            title = date1
        self.ax.clear()
        self.ax.set_xticks(np.arange(0, self.current_spec.shape[1], 1.0))
        self.ax.set_xticklabels(["" for x in range(self.current_spec.shape[1])])
        cax = self.ax.imshow(20 * np.log10(self.current_spec), origin='lower',
                             aspect='auto', interpolation='nearest')
        self.ax.set_title(title)
        labels = [item.get_text() for item in self.ax.get_xticklabels()]
        labels[0] = file_time1
        center_date, center_time = Dates.to_date(self.center)
        labels[len(labels) / 2] = center_time
        if self.zoom > 2:
            labels[len(labels) - 1] = file_time2
        self.ax.set_xticklabels(labels)
        yfmt = tkr.FuncFormatter(numfmt)
        self.ax.yaxis.set_major_formatter(yfmt)
        # sets the colorbar for all spectrograms
        if self.cax is None and np.count_nonzero(~np.isnan(self.current_spec)) != 0:
            self.cax = self.ax.imshow(20 * np.log10(self.current_spec), origin='lower',
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
            if time == '17:46:07':
                pass
            for j in range(0, len(self.mp3_dirs)):
                if audio_file is not None:
                   break
                try:
                    ftp.cwd(self.mp3_dirs[j] % date)
                    files = ftp.nlst()
                    if files is not None:
                        for f in files:
                            if time in f and self.channel in f:
                                audio_dir = self.mp3_dirs[j] % date
                                audio_file = f
                                break
                except ftplib.error_perm, e:
                    if "550" in e.message:  # failed to change directory
                        pass
                    else:  # This is terrible and will be fixed later
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
            if audio_file not in self.media_files[self.pit]:
                with open("Gui_files/" + "-".join(audio_file.split(":")), 'wb') as r:
                    ftp.retrbinary('RETR ' + audio_dir + audio_file, r.write)
                os.startfile("Gui_files\\" + "-".join(audio_file.split(":")))
                self.media_files[self.pit][audio_file] = "Gui_files\\" + "-".join(audio_file.split(":"))
                self.message.config(text="Found:" + audio_dir + audio_file)
            else:
                self.message.config(text="Found:" + audio_dir + audio_file)
                os.startfile(self.media_files[self.pit][audio_file])
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
            if video_file not in self.media_files[self.pit]:
                with open("Gui_files\\" + "-".join(video_file.split(":")), 'wb') as r:
                    ftp.retrbinary('RETR ' + video_dir + video_file, r.write)
                self.media_files[self.pit][video_file] = "Gui_files\\" + "-".join(video_file.split(":"))
                os.startfile("Gui_files\\" + "-".join(video_file.split(":")))
                self.message.config(text="Found:" + video_dir + video_file)
            else:
                self.message.config(text="Found:" + video_dir + video_file)
                os.startfile(self.media_files[self.pit][video_file])
        else:
            self.message.config(text="No video file.")

    def on_right(self):
        """
        Moves the center time to the right and updates the plot.
        :return: None
        """
        cen = int(self.center, 16)
        cen += (2 ** self.zoom) / 2
        self.center = format(cen, 'x')
        self.update_current_spec()
        self.update_matplotlib_fig()

    def on_left(self):
        """
        Moves the center time to the left and updates the plot.
        :return: None
        """
        cen = int(self.center, 16)
        cen -= 2 ** self.zoom / 2
        self.center = format(cen, 'x')
        self.update_current_spec()
        self.update_matplotlib_fig()

    def update_current_spec(self):
        """
        Gets the 16 files surrounding the specified hex time stamp.
        Center time should be the time passed in.
        :param hex_num: hex time stamp that will be the center of the data
        :return: None
        """
        print ("Zoom: ", self.zoom)
        lm = int(self.center, 16)
        lm -= (2 ** self.zoom) / 2  # leftmost value
        self.leftmost = make_hex8('{:08x}'.format(lm))
        self.current_spec = self.get_specgram()

    def retrieve_file(self, hex_num):
        f_dir = "/".join(hex_num[:4]) + "/"
        fname = hex_num + "_" + self.channel + ".npz"
        if fname not in self.spec_files[self.pit]:
            try:
                print self.input_dir + f_dir
                ftp.cwd(self.input_dir + f_dir)
                files = ftp.nlst()
                print self.input_dir + f_dir + fname
                if fname in files:
                    r = open("Gui_files/" + fname, 'wb')
                    ftp.retrbinary('RETR ' + self.input_dir + f_dir + fname, r.write)
                    r.close()
            except ftplib.error_perm as e:
                print e.message
            if os.path.isfile("Gui_files/" + fname):
                npz_file = np.load("Gui_files/" + fname)
                self.spec_files[self.pit][fname] = {}
                self.spec_files[self.pit][fname]['intensities'] = npz_file['intensities']
                self.spec_files[self.pit][fname]['start_datetime'] = npz_file['start_datetime']
                self.spec_files[self.pit][fname]['end_datetime'] = npz_file['end_datetime']
                npz_file.close()
                return self.spec_files[self.pit][fname]['intensities']
            empty_spec = np.empty((2049, 4096))
            empty_spec[:] = np.NAN
            return empty_spec
        return self.spec_files[self.pit][fname]['intensities']

    def get_specgram(self):
        start_hex = self.leftmost
        combined_spec = np.empty((2049, 2**self.zoom))
        combined_spec[:] = np.NaN
        end_hex = '{:08x}'.format(int(start_hex, 16) + 2**self.zoom)
        for i in range(int(start_hex[:5], 16), int(end_hex[:5], 16) + 1):
            i_hex = '{:05x}'.format(i)
            i_specgram = self.retrieve_file(i_hex)
            if start_hex[:5] == end_hex[:5] and start_hex[:5] == i_hex:
                start_col = int(start_hex, 16) - int(make_hex8(start_hex[:5]), 16)
                end_col = int(end_hex, 16) - int(make_hex8(start_hex[:5]), 16)
                combined_spec[:, :(end_col - start_col)] = i_specgram[:, start_col:end_col]
            elif start_hex[:5] == i_hex:
                start_col = int(start_hex, 16) - int(make_hex8(start_hex[:5]), 16)
                end_col = i_specgram[:, start_col:].shape[1]
                combined_spec[:, 0:end_col] = i_specgram[:, start_col:]
            elif end_hex[:5] == i_hex:
                start_col = int(make_hex8(i_hex), 16) - int(start_hex, 16)
                end_col = int(end_hex, 16) - int(make_hex8(i_hex), 16)
                combined_spec[:, start_col:] = i_specgram[:, :end_col]
            else:
                start_col = int(make_hex8(i_hex), 16) - int(start_hex, 16)
                end_col = i_specgram.shape[1]
                combined_spec[:, start_col:start_col + end_col] = i_specgram[:, :]
        print combined_spec.shape
        return combined_spec


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
        os.remove("Gui_files\\" + f)
    os.rmdir("Gui_files")
    ftp.close()
    app.destroy()
    plt.close()


def main():
    if not os.path.isdir("Gui_files"):
        os.mkdir("Gui_files")
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
    except TypeError as e:
        print e.message
        return

if __name__ == "__main__":
    main()
