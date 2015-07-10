__author__ = 'lukestack'
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
import Tkinter as tk
import pickle
import matplotlib.pyplot as plt
import numpy as np
import Dates
import ftplib
from StringIO import StringIO
from scipy.io.wavfile import read
from pydub import AudioSegment
import tempfile
import thread
import pyaudio

user = 'stackjl'
password = ''
ftp = ftplib.FTP('cs.appstate.edu', user, password)
input_dir = "/usr/local/bee/beemon/beeW/Luke/specgrams2/pit2/"
start = "5/5/9/3/c/f/3/"
mp3_dirs = ["/usr/local/bee/beemon/mp3/pit2/%s/", "/usr/local/bee/beemon/pit2/%s/audio/"]
ftp.cwd(input_dir + start)


class BeeApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.input_dir = input_dir
        self.current_input = input_dir + start
        self.mp3_dirs = mp3_dirs
        self.leftmost = make_hex8("".join(start.split("/")))
        self.center = format(int(self.leftmost, 16) + 8, 'x')
        self.zoom = 1
        self.cax = self.fig = self.ax = None
        self.get_next_16(self.center)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        def on_key_event(event):
            print('you pressed %s'%event.key)
            key_press_handler(event, self.canvas, toolbar)

        self.canvas.mpl_connect('key_press_event', on_key_event)

        self.zoom_out = tk.Button(self, text="-", command=self.on_zoom_out)
        self.zoom_out.pack(side=tk.LEFT)

        self.zoom_in = tk.Button(self, text="+", command=self.on_zoom_in)
        self.zoom_in.pack(side=tk.LEFT)

        self.play = tk.Button(self, text="Play", command=self.on_play)
        self.play.pack(side=tk.LEFT, expand=tk.YES)

        self.right = tk.Button(self, text=">", command=self.on_right)
        self.right.pack(side=tk.RIGHT)

        self.left = tk.Button(self, text="<", command=self.on_left)
        self.left.pack(side=tk.RIGHT)

    def on_zoom_out(self):
        if self.zoom < 28:
            self.zoom += 1
            self.get_next_16(self.center)

    def on_zoom_in(self):
        if self.zoom != 1:
            self.zoom -= 1
            self.get_next_16(self.center)

    def on_play(self):
        audio_dir = None
        audio_file = None
        for i in range(0, 60):
            sec = int(self.center, 16)
            sec -= i
            sec = format(sec, 'x')
            date, time = Dates.to_date(sec)
            date, time = Dates.convert_to_local(date, time)
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
            temp = tempfile.NamedTemporaryFile(suffix=".wav")
            with open(temp.name, 'wb') as r:
                ftp.retrbinary('RETR ' + audio_dir + audio_file, r.write)
            rate, wav = get_data(temp.name)
            temp.close()
            thread.start_new_thread(play, (rate, wav))

    def on_right(self):
        cen = int(self.center, 16)
        cen += 2**(3 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.get_next_16(self.center)

    def on_left(self):
        cen = int(self.center, 16)
        cen -= 2**(3 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.get_next_16(self.center)

    def get_next_16(self, hex_num):
        print ("Zoom: ", self.zoom)
        combined_spec = None
        num = int(hex_num, 16)
        num -= 2**(3 + self.zoom) / 2
        for i in range(0, 2**(3 + self.zoom), 2**(self.zoom - 1)):
            i_hex = '{:08x}'.format(int(num + i))
            i_hex = i_hex[:int(len(i_hex) - ((self.zoom - 1) / 4))]
            i_dir = "/".join(i_hex[:-1]) + "/"
            i_file = None
            try:
                ftp.cwd(input_dir + i_dir)
                files = ftp.nlst()
                for f in files:
                    if "left" in f:
                        if 4 - (self.zoom - 1) % 4 == 4:
                            if i_hex in f:
                                i_file = f
                                break
                        else:
                            bi = "{0:04b}".format(int(i_hex[-1], 16))[:(4 - (self.zoom - 1) % 4)]
                            if i_hex[:-1] + "_" + bi + "_" in f:
                                i_file = f
                                break
            except ftplib.error_perm:
                pass
            if i_file is not None:
                print (i_file)
                r = StringIO()
                ftp.retrbinary('RETR ' + self.input_dir + i_dir + i_file, r.write)
                data = pickle.loads(r.getvalue())
                r.close()
                if combined_spec is None:
                    combined_spec = data[0]
                else:
                    combined_spec = np.vstack((combined_spec, data[0]))
            else:
                if combined_spec is None:
                    combined_spec = [0] * 2049
                else:
                    combined_spec = np.vstack((combined_spec, [0] * 2049))
        hex_time1 = '{:08x}'.format(int(num))
        hex_time2 = '{:08x}'.format(int(num + 2**(3 + self.zoom) - 1))
        self.leftmost = make_hex8(hex_time1)
        self.create_fig(combined_spec, hex_time1, hex_time2)

    def create_fig(self, combined_spec, hex_time1, hex_time2):
        print combined_spec.shape
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
            if self.cax is None:
                self.cax = ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
            cax = ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
            ax.set_ylim((0, 1024))
            ax.set_title(title)
            labels = [item.get_text() for item in ax.get_xticklabels()]
            labels[0] = file_time1
            labels[8] = Dates.to_date(self.center)[1]
            labels[len(labels) - 1] = file_time2
            ax.set_xticklabels(labels)
            cax.set_clim(self.cax.get_clim())
            fig.colorbar(cax)
            self.fig = fig
            self.ax = ax
        else:
            self.ax.clear()
            self.ax.set_xticks(np.arange(0, combined_spec.shape[0], 1.0))
            self.ax.set_xticklabels(["" for x in range(combined_spec.shape[0])])
            cax = self.ax.imshow(20 * np.log10(combined_spec.T), origin='lower', aspect='auto')
            self.ax.set_ylim((0, 1024))
            self.ax.set_title(title)
            labels = [item.get_text() for item in self.ax.get_xticklabels()]
            labels[0] = file_time1
            labels[8] = Dates.to_date(self.center)[1]
            labels[len(labels) - 1] = file_time2
            self.ax.set_xticklabels(labels)
            cax.set_clim(self.cax.get_clim())
            self.canvas.draw()


def get_data(path):
    if path.endswith(".wav"):
        bee_rate, bee_data = read(path)
    else:
        temp = tempfile.NamedTemporaryFile(suffix=".wav")
        if path.endswith(".flac"):
            sound = AudioSegment.from_file(path, "flac")
            sound.export(temp.name, format="wav")
        elif path.endswith(".mp3"):
            sound = AudioSegment.from_file(path, "mp3")
            sound.export(temp.name, format="wav")
        bee_rate, bee_data = read(temp.name)
        temp.close()
    return bee_rate, bee_data


def make_hex8(hex_num):
    for i in range(0, 8 - len(hex_num)):
        hex_num += "0"
    return hex_num


def play(rate, wav):
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(2), channels=1, rate=rate, output=True)
    stream.write(wav.tostring())
    stream.close()
    p.terminate()


def on_closing():
    ftp.close()
    app.destroy()
    plt.close()

app = BeeApp()
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()