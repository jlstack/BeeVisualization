__author__ = 'lukestack'
import Tkinter as tk
from PIL import ImageTk, Image
import pickle
import matplotlib.pyplot as plt
import numpy as np
import os
import re
import Dates
import sys

input_dir = "/Users/lukestack/PycharmProjects/BeeVisualization/Pickles/"
start = "5/5/2/e/c/3/6/"
img_dir = "/Users/lukestack/PycharmProjects/BeeVisualization/Images/"


class BeeApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.input_dir = input_dir
        self.current_input = input_dir + start
        self.img_dir = img_dir
        self.cax = None
        self.panel1 = None

        self.gran = tk.Scale(self, label="", from_=1, to=4, tickinterval=1, orient='vertical', length=300)
        self.gran.set(4)
        self.gran.grid(row=1, rowspan=2, column=7)

        self.img1 = Image.open(self.get_image(self.current_input))
        self.img1.thumbnail((800, 800), Image.ANTIALIAS)
        self.pic1 = ImageTk.PhotoImage(self.img1)
        self.panel1 = tk.Label(self, image=self.pic1)
        self.panel1.grid(row=0, rowspan=4, columnspan=7)

        self.change_gran = tk.Button(self, text="Change", command=self.on_change_gran)
        self.change_gran.grid(row=3, column=7)

        self.zoom_out = tk.Button(self, text="-", command=self.on_zoom_out)
        self.zoom_out.grid(row=4, column=1)

        self.zoom_in = tk.Button(self, text="+", command=self.on_zoom_in)
        self.zoom_in.grid(row=4, column=2)

        self.left = tk.Button(self, text="<", command=self.on_left)
        self.left.grid(row=4, column=4)

        self.right = tk.Button(self, text=">", command=self.on_right)
        self.right.grid(row=4, column=5)

        self.zoom_value = tk.Scale(self, label="Zoom", from_=0, to= 15, tickinterval=1, orient='horizontal', length=500)
        self.zoom_value.grid(row=5, columnspan=7)

        self.messages = tk.Message(self, text="Current Directory: " + self.current_input, relief='raised', width=600)
        self.messages.grid(row=6, column=0, columnspan=7)

    def on_zoom_out(self):
        new_dir = self.current_input[:-2]
        if os.path.isdir(new_dir):
            if not self.update_image(self.get_image(new_dir)):
                self.messages.config(text="Current Directory: " + self.current_input +
                                     "\nCan not zoom out any farther.")
            else:
                self.current_input = new_dir
                print self.current_input
                self.messages.config(text="Current Directory: " + self.current_input)

    def on_zoom_in(self):
        new_dir = self.current_input + '{:01x}'.format(self.zoom_value.get()) + "/"
        if os.path.isdir(new_dir):
                if not self.update_image(self.get_image(new_dir)):
                    self.messages.config(text="Current Directory: " + self.current_input +
                                         "\nCan not zoom in here.")
                else:
                    self.current_input = new_dir
                    print self.current_input
                    self.messages.config(text="Current Directory: " + self.current_input)
        else:
            self.messages.config(text="Current Directory: " + self.current_input +
                                 "\nDirectory does not exist.")

    def update_image(self, image):
        if image is not None:
            self.img1 = Image.open(image)
            self.img1.thumbnail((800, 800), Image.ANTIALIAS)
            self.pic1 = ImageTk.PhotoImage(self.img1)
            self.panel1.config(image=self.pic1)
            return True
        return False

    def on_change_gran(self):
        if not self.update_image(self.current_input):
            print "poop"

    def get_image(self, input_dir):
        combined_spec = None
        pickles = os.listdir(input_dir)
        pickles.sort()
        used = []
        used_pickles = []
        for pic in pickles:
            if self.gran.get() < 4:
                pattern = r"[0-9a-fA-F]*_[0-1]{" + str(self.gran.get()) + "}_left.spec.pkl"
            else:
                pattern = r"[0-9a-fA-F]*_left.spec.pkl"
            m = re.match(pattern, pic)
            if m is None and self.gran.get() == 4:
                m = re.match(r"[0-9a-fA-F]{8}_[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z_left.spec.pkl", pic)
            if m:
                used.append(m.group())
                used_pickles.append(re.search(r"[0-9a-fA-F]*", pic).group())
                with open(input_dir + pic) as f:
                    data = pickle.load(f)
                if combined_spec is None:
                    combined_spec = data[0]
                else:
                    combined_spec = np.vstack((combined_spec, data[0]))
        if combined_spec is None:
            return
        self.leftmost = self.make_hex8(used_pickles[0])
        file_name = self.img_dir + used_pickles[0] + "_" + \
                    used_pickles[len(used_pickles) - 1] + "_gran_" + str(self.gran.get()) + ".png"
        if not os.path.isfile(file_name):
            hex_time1 = used_pickles[0]
            hex_time2 = used_pickles[len(used_pickles) - 1]
            try:
                self.create_fig(combined_spec, hex_time1, hex_time2, file_name)
            except TypeError:
                return
        return file_name

    def on_right(self):
        self.get_next_16(self.leftmost, 'right')
        print self.leftmost, self.leftmost[-1], "{0:04b}".format(int(self.leftmost[-1], 16))

    def on_left(self):
        self.get_next_16(self.leftmost, 'left')
        print self.leftmost, self.leftmost[-1], "{0:04b}".format(int(self.leftmost[-1], 16))

    def get_next_16(self, hex_num, direction=None):
        combined_spec = None
        num = int(hex_num, 16)
        if direction == 'right':
            num += 8
        elif direction == 'left':
            num -= 8
        for i in range(0, 16):
            i_hex = format(num + i, 'x')
            i_dir = "/".join(i_hex[:-1]) + "/"
            i_file = None
            if os.path.isdir(self.input_dir + i_dir):
                for f in os.listdir(self.input_dir + i_dir):
                    if i_hex in f:
                        i_file = f
                        break
            if i_file is not None:
                with open(self.input_dir + i_dir + i_file) as f:
                    data = pickle.load(f)
                if combined_spec is None:
                    combined_spec = data[0]
                else:
                    combined_spec = np.vstack((combined_spec, data[0]))
            else:
                if combined_spec is None:
                    combined_spec = [0] * 2049
                else:
                    combined_spec = np.vstack((combined_spec, [0] * 2049))
        hex_time1 = format(num, 'x')
        hex_time2 = format(num + 15, 'x')
        file_name = self.img_dir + hex_time1 + "_" + \
                hex_time2 + "_gran_" + str(self.gran.get()) + ".png"
        self.leftmost = self.make_hex8(hex_time1)
        self.create_fig(combined_spec, hex_time1, hex_time2, file_name)
        if self.panel1 is not None:
            self.update_image(file_name)
        return file_name

    def create_fig(self, combined_spec, hex_time1, hex_time2, file_name):
        hex_time1 = self.make_hex8(hex_time1)
        hex_time2 = self.make_hex8(hex_time2)
        date1, file_time1 = Dates.to_date(hex_time1)
        date2, file_time2 = Dates.to_date(hex_time2)
        if not date1 == date2:
            title = date1 + "-" + date2
        else:
            title = date1
        fig, ax = plt.subplots()
        fig.canvas.draw()
        ax.set_xticks(np.arange(0, combined_spec.shape[0], 1.0))
        if self.cax is None:
            self.cax = ax.imshow(np.log(combined_spec.T), origin='lower', aspect='auto')
        else:
            ax.imshow(np.log(combined_spec.T), origin='lower', aspect='auto')
        ax.set_ylim((0, 1024))
        ax.set_title(title)
        labels = [item.get_text() for item in ax.get_xticklabels()]
        labels[0] = file_time1
        labels[len(labels) - 1] = file_time2
        ax.set_xticklabels(labels)
        plt.savefig(file_name)
        plt.close()

    def make_hex8(self, hex_num):
        for i in range(0, 8 - len(hex_num)):
            hex_num += "0"
        return hex_num


def on_closing():
    app.destroy()
    for the_file in os.listdir(img_dir):
        file_path = os.path.join(img_dir, the_file)
        if os.path.isfile(file_path):
            os.remove(file_path)

app = BeeApp()
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
