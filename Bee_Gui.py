__author__ = 'lukestack'
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
import matplotlib.ticker as tkr
import Tkinter as Tk
import tkSimpleDialog
import matplotlib.pyplot as plt
import Dates
import ftplib
from scipy.io.wavfile import read
from pydub import AudioSegment
import tempfile
import thread
import pyaudio
import os
import math
import numpy as np

user = 'stackjl'
password = ''
ftp = ftplib.FTP('cs.appstate.edu', user, password)


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
        self.withdraw()
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
        self.mp3_dirs = ["/usr/local/bee/beemon/mp3/" + self.pit + "/%s/",
                         "/usr/local/bee/beemon/" + self.pit + "/%s/audio/"]
        start_hex, start_dir = Dates.to_hex(date, time)
        self.current_input = self.input_dir + start_dir
        self.channel = channel
        self.leftmost = make_hex8("".join(start_dir.split("/")))
        self.center = format(int(self.leftmost, 16) + 8, 'x')
        self.zoom = 1
        self.files = self.audio_files = {'pit1': {}, 'pit2': {}}
        self.cax = self.fig = self.ax = self.stream = self.combined_spec = None
        self.current_view = "spec"
        self.get_next_16(self.center)

        self.option_add('*tearOff', False)
        self.menubar = Tk.Menu(self)
        self.config(menu=self.menubar)
        pit = Tk.Menu(self.menubar)
        channel = Tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=pit, label="pit")
        self.menubar.add_cascade(menu=channel, label="channel")
        self.menubar.add_command(label="Search Time", command=self.search_date)
        pit.add_radiobutton(label="pit1", command=lambda: self.change_pit("pit1"))
        pit.add_radiobutton(label="pit2", command=lambda: self.change_pit("pit2"))
        channel.add_radiobutton(label="left", command=lambda: self.change_channel("left"))
        channel.add_radiobutton(label="right", command=lambda: self.change_channel("right"))

        self.matplotlib_plot = Tk.Frame(self)  # Frame that holds the matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.matplotlib_plot)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.canvas.mpl_connect('key_press_event', self.toolbox_event)
        self.matplotlib_plot.pack(fill=Tk.BOTH, expand=True)

        self.control_frame = Tk.Frame(self, width=400)  # Frame that holds the navigational buttons
        self.zoom_out = Tk.Button(self.control_frame, text="-", command=self.on_zoom_out)
        self.zoom_out.grid(row=0, column=0)
        self.zoom_in = Tk.Button(self.control_frame, text="+", command=self.on_zoom_in)
        self.zoom_in.grid(row=0, column=1)
        if self.zoom == 1:
            self.zoom_in['state'] = 'disabled'  # Makes zoom in button unclickable
        self.play = Tk.Button(self.control_frame, text="Play", command=self.on_play)
        self.play.grid(row=0, column=2)
        self.plot = Tk.Button(self.control_frame, text="Plot Frequencies", command=self.on_plot)
        self.plot.grid(row=0, column=3)
        self.left = Tk.Button(self.control_frame, text="<", command=self.on_left)
        self.left.grid(row=0, column=4)
        self.right = Tk.Button(self.control_frame, text=">", command=self.on_right)
        self.right.grid(row=0, column=5)
        self.control_frame.pack()

        self.message_frame = Tk.LabelFrame(self, height=50, width=400)  # Frame that holds the message
        self.message = Tk.Label(self.message_frame, text="Last Played:")
        self.message.pack()
        self.message_frame.pack()

    def toolbox_event(self, event):
            key_press_handler(event, self.canvas, self.toolbar)

    def search_date(self):
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
            self.get_next_16(self.center)
        except:
            pass

    def change_pit(self, pit):
        self.pit = pit
        self.input_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs2/%s/" % self.pit
        self.mp3_dirs = ["/usr/local/bee/beemon/mp3/" + self.pit + "/%s/",
                         "/usr/local/bee/beemon/" + self.pit + "/%s/audio/"]
        self.get_next_16(self.center)

    def change_channel(self, channel):
        self.channel = channel
        self.get_next_16(self.center)

    def on_zoom_out(self):
        """
        Zooms out one level and calls self.get_next_16 to update the spectrogram.
        :return: None
        """
        if self.zoom < 28:
            self.zoom += 1
            self.get_next_16(self.center)
        if self.zoom > 1:
            self.zoom_in['state'] = 'normal'

    def on_zoom_in(self):
        """
        Zooms in one level and calls self.get_next_16 to update the spectrogram.
        :return: None
        """
        if self.zoom != 1:
            self.zoom -= 1
            self.get_next_16(self.center)
        if self.zoom == 1:
            self.zoom_in['state'] = 'disabled'

    def on_plot(self):
        """
        Creates plot of frequencies.
        :return: None
        """
        print self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T.shape, self.combined_spec.shape
        if self.current_view == "spec":
            self.ax.clear()
            freqs = np.arange(0, self.combined_spec.shape[1] / 2.0, .5)
            if not math.isnan(np.mean(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T)):
                self.ax.set_ylim((0, np.amax(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T[2:, :])))
                # Takes max after column 2 because there is often an outlier at the first two columns
                self.ax.plot(freqs, np.mean(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T, axis=1))
            else:
                self.ax.plot(freqs, [0] * len(freqs))
            self.canvas.draw()
            self.plot.config(text="Spectrogram")
            self.current_view = "plot"
        else:
            self.get_next_16(self.center)

    def on_play(self):
        """
        Callback for play button. Locates the file associated with given time if the file exists.
        Then calls the play function to play the located file.
        :return: None
        """
        global stop_playing
        if self.play.config('text')[-1] == "Stop":
            stop_playing = True
        else:
            stop_playing = False
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
                                if time in f or '-'.join(time.split(':')) in f:
                                    audio_dir = self.mp3_dirs[j] % date
                                    audio_file = f
                                    break
                    except ftplib.error_perm:
                        pass
                if audio_file is not None:
                    break
            if audio_file is not None:
                print audio_dir + audio_file
                if audio_file not in self.audio_files[self.pit]:
                    filename, file_extension = os.path.splitext(audio_file)
                    temp = tempfile.NamedTemporaryFile(suffix=file_extension)
                    temp.close()
                    with open(temp.name, 'wb') as r:
                        ftp.retrbinary('RETR ' + audio_dir + audio_file, r.write)
                    rate, wav = get_data(temp.name)
                    self.audio_files[self.pit][audio_file] = (rate, wav)
                else:
                    rate, wav = self.audio_files[self.pit][audio_file]
                self.message.config(text="Last Played:" + audio_file)
                thread.start_new_thread(player, (self.play, rate, wav))
            else:
                self.message.config(text="No audio file.")

    def on_right(self):
        """
        Moves the center time to the right and updates the plot.
        :return: None
        """
        cen = int(self.center, 16)
        cen += 2 ** (3 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.get_next_16(self.center)

    def on_left(self):
        """
        Moves the center time to the left and updates the plot.
        :return: None
        """
        cen = int(self.center, 16)
        cen -= 2 ** (3 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.get_next_16(self.center)

    def get_next_16(self, hex_num):
        """
        Gets the next 16 files surrounding the specified hex time stamp.
        :param hex_num: hex time stamp that will be the center of the data
        :return: None
        """
        print ("Zoom: ", self.zoom)
        combined_spec = None
        num = int(hex_num, 16)
        num -= 2 ** (3 + self.zoom) / 2
        for i in range(0, 2 ** (3 + self.zoom), 2 ** (self.zoom - 1)):
            i_hex = '{:08x}'.format(int(num + i))
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
            except ftplib.error_perm:
                pass
            if i_file is not None:
                print (i_file)
                if i_file not in self.files[self.pit]:
                    r = open("from_server.npy", 'wb')
                    ftp.retrbinary('RETR ' + self.input_dir + i_dir + i_file, r.write)
                    r.close()
                    data = np.load("from_server.npy").item()
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
        self.combined_spec = combined_spec
        hex_time1 = '{:08x}'.format(int(num))
        hex_time2 = '{:08x}'.format(int(num + 2 ** (3 + self.zoom) - 1))
        self.leftmost = make_hex8(hex_time1)
        self.create_fig(combined_spec, hex_time1, hex_time2)
        if self.current_view != "spec":
            self.plot.config(text="Frequencies")
            self.current_view = "spec"

    def create_fig(self, combined_spec, hex_time1, hex_time2):
        """
        Creates the current spectrogram.
        :param combined_spec: spectrogram to be displayed
        :param hex_time1: start time of spectrogram
        :param hex_time2: end time of spectrogram
        :return: None
        """
        date1, file_time1 = Dates.to_date(hex_time1)
        date2, file_time2 = Dates.to_date(hex_time2)
        if not date1 == date2:
            title = date1 + "  -  " + date2
        else:
            title = date1
        if self.fig is None:
            fig, ax = plt.subplots()
            fig.canvas.draw()
            ax.set_xticks(np.arange(0, combined_spec.shape[0], 1.0))
            ax.set_xticklabels(["" for x in range(combined_spec.shape[0])])
            if self.cax is None and np.count_nonzero(combined_spec) != 0:
                self.cax = ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
            cax = ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
            ax.set_title(title)
            labels = [item.get_text() for item in ax.get_xticklabels()]
            labels[0] = file_time1
            center_date, center_time = Dates.to_date(self.center)
            labels[8] = center_time
            labels[len(labels) - 1] = file_time2
            ax.set_xticklabels(labels)
            yfmt = tkr.FuncFormatter(numfmt)
            ax.yaxis.set_major_formatter(yfmt)
            if self.cax is not None:
                cax.set_clim(self.cax.get_clim())
                fig.colorbar(cax)
            self.fig = fig
            self.ax = ax
        else:
            self.ax.clear()
            self.ax.set_xticks(np.arange(0, combined_spec.shape[0], 1.0))
            self.ax.set_xticklabels(["" for x in range(combined_spec.shape[0])])
            cax = self.ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
            self.ax.set_title(title)
            labels = [item.get_text() for item in self.ax.get_xticklabels()]
            labels[0] = file_time1
            center_date, center_time = Dates.to_date(self.center)
            labels[8] = center_time
            labels[len(labels) - 1] = file_time2
            labels[len(labels) - 1] = file_time2
            self.ax.set_xticklabels(labels)
            yfmt = tkr.FuncFormatter(numfmt)
            self.ax.yaxis.set_major_formatter(yfmt)
            if self.cax is None and np.count_nonzero(combined_spec) != 0:
                self.cax = self.ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
                self.fig.colorbar(cax)
            if self.cax is not None:
                cax.set_clim(self.cax.get_clim())
            self.canvas.draw()


def numfmt(y, pos):
    """
    Divides each y label by 2.
    :param x:
    :param pos:
    :return:
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


def player(play_button, rate, wav):
    """
    Plays audio clip.
    :param play_button: Button that was pressed to play. (Will configure it to be a stop button.)
    :param rate: sample rate of the wave file
    :param wav: audio file data
    :return: None
    """
    play_button.config(text="Stop")
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(2), channels=1, rate=rate, output=True)
    stream.start_stream()
    start = 0
    end = 1024
    while start < len(wav) and not stop_playing:
        stream.write(wav[start:end].tostring())
        start += 1024
        end = start + 1024
    stream.close()
    p.terminate()
    play_button.config(text="Play")


def on_closing(app):
    """
    Callback for the closing of the application.
    :return: None
    """
    if os.path.isfile("from_server.npy"):
        os.remove("from_server.npy")
    ftp.close()
    app.destroy()
    plt.close()


def main():
    root = Tk.Tk()
    root.withdraw()
    d = DateDialog(root)
    try:
        date, time, pit, channel = d.result
        root.destroy()
        app = BeeApp(date, time, pit, channel)
        app.protocol("WM_DELETE_WINDOW", lambda: on_closing(app))
        app.mainloop()
    except TypeError:
        pass

if __name__ == "__main__":
    main()
