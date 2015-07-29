__author__ = 'lukestack'
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
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
password = 'sta.44,ck'
ftp = ftplib.FTP('cs.appstate.edu', user, password)
pit = "pit2"
channel = 'left'
input_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs2/%s/" % pit
mp3_dirs = ["/usr/local/bee/beemon/mp3/" + pit + "/%s/", "/usr/local/bee/beemon/" + pit + "/%s/audio/"]
temp_dir = "/Users/lukestack/PycharmProjects/BeeVisualization/"

if not os.path.isdir(temp_dir):
    os.mkdir(temp_dir)


class DateDialog(tkSimpleDialog.Dialog):
    def body(self, master):
        self.withdraw()
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
        date = self.date.get()
        time = self.time.get()
        self.result = date, time


class BeeApp(Tk.Tk):
    def __init__(self, date, time):
        Tk.Tk.__init__(self)
        self.title("Bee App")
        self.input_dir = input_dir
        start_hex, start_dir = Dates.to_hex(date, time)
        self.current_input = input_dir + start_dir
        self.channel = channel
        self.mp3_dirs = mp3_dirs
        self.temp_dir = temp_dir
        self.leftmost = make_hex8("".join(start_dir.split("/")))
        self.center = format(int(self.leftmost, 16) + 8, 'x')
        self.zoom = 1
        self.files = self.audio_files = {}
        self.cax = self.fig = self.ax = self.stream = self.combined_spec = None
        self.current_view = "spec"
        self.get_next_16(self.center)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        def on_key_event(event):
            key_press_handler(event, self.canvas, toolbar)

        self.canvas.mpl_connect('key_press_event', on_key_event)

        self.zoom_out = Tk.Button(self, text="-", command=self.on_zoom_out)
        self.zoom_out.pack(side=Tk.LEFT)

        self.zoom_in = Tk.Button(self, text="+", command=self.on_zoom_in)
        self.zoom_in.pack(side=Tk.LEFT)

        self.play = Tk.Button(self, text="Play", command=self.on_play)
        self.play.pack(side=Tk.LEFT, expand=Tk.YES)

        self.plot = Tk.Button(self, text="Plot Frequencies", command=self.on_plot)
        self.plot.pack(side=Tk.LEFT, expand=Tk.YES)

        self.right = Tk.Button(self, text=">", command=self.on_right)
        self.right.pack(side=Tk.RIGHT)

        self.left = Tk.Button(self, text="<", command=self.on_left)
        self.left.pack(side=Tk.RIGHT)

    def on_zoom_out(self):
        if self.zoom < 28:
            self.zoom += 1
            self.get_next_16(self.center)

    def on_zoom_in(self):
        if self.zoom != 1:
            self.zoom -= 1
            self.get_next_16(self.center)

    def on_plot(self):
        if self.current_view == "spec":
            self.combined_spec[~np.all(self.combined_spec == 0, axis=1)]
            self.ax.clear()
            freqs = np.arange(0, self.combined_spec.shape[1] / 2.0, .5)
            if not math.isnan(np.mean(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T)):
                self.ax.set_ylim((0, np.amax(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T[2:, :])))
                self.ax.plot(freqs, np.mean(self.combined_spec[~np.all(self.combined_spec == 0, axis=1)].T, axis=1))
            else:
                self.ax.plot(freqs, [0] * len(freqs))
            self.canvas.draw()
            self.plot.config(text="Spectragram")
            self.current_view = "plot"
        else:
            self.get_next_16(self.center)

    def on_play(self):
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
                if audio_file not in self.audio_files:
                    filename, file_extension = os.path.splitext(audio_file)
                    temp = tempfile.NamedTemporaryFile(suffix=file_extension)
                    temp.close()
                    with open(temp.name, 'wb') as r:
                        ftp.retrbinary('RETR ' + audio_dir + audio_file, r.write)
                    rate, wav = get_data(temp.name)
                    self.audio_files[audio_file] = (rate, wav)
                else:
                    rate, wav = self.audio_files[audio_file]
                thread.start_new_thread(player, (self.play, rate, wav))

    def on_right(self):
        cen = int(self.center, 16)
        cen += 2 ** (3 + self.zoom) / 4
        self.center = format(cen, 'x')
        self.get_next_16(self.center)

    def on_left(self):
        cen = int(self.center, 16)
        cen -= 2 ** (3 + self.zoom) / 4
        self.center = format(cen, 'x')
        self.get_next_16(self.center)

    def get_next_16(self, hex_num):
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
                if fname in self.files:
                    i_file = fname
                else:
                    ftp.cwd(input_dir + i_dir)
                    files = ftp.nlst()
                    for f in files:
                        if f == fname:
                            i_file = f
                            break
            except ftplib.error_perm:
                pass
            if i_file is not None:
                print (i_file)
                if i_file not in self.files:
                    r = open(temp_dir + "from_server.npy", 'wb')
                    ftp.retrbinary('RETR ' + self.input_dir + i_dir + i_file, r.write)
                    r.close()
                    data = np.load(temp_dir + "from_server.npy").item()
                    self.files[i_file] = data
                else:
                    data = self.files[i_file]
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
            # print ax.get_yticklabels()[0].get_label(), "here"
            # ax.set_yticklabels([str(int(str(l)) / 2) for l in ax.get_yticklabels()])
            ax.set_title(title)
            labels = [item.get_text() for item in ax.get_xticklabels()]
            labels[0] = file_time1
            center_date, center_time = Dates.to_date(self.center)
            labels[8] = center_time
            labels[len(labels) - 1] = file_time2
            ax.set_xticklabels(labels)
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
            if self.cax is None and np.count_nonzero(combined_spec) != 0:
                self.cax = self.ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
                self.fig.colorbar(cax)
            if self.cax is not None:
                cax.set_clim(self.cax.get_clim())
            self.canvas.draw()


def get_data(path):
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
    for i in range(0, 8 - len(hex_num)):
        hex_num += "0"
    return hex_num


def player(play_button, rate, wav):
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


def on_closing():
    ftp.close()
    app.destroy()
    plt.close()


root = Tk.Tk()
root.withdraw()
d = DateDialog(root)
date, time = d.result
root.destroy()

app = BeeApp(date, time)
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()