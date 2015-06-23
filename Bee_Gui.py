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

input_dir = "/Users/lukestack/PycharmProjects/BeeVisualization/Pickles/5/5/2/e/d/e/d/"
print input_dir


class BeeApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.current_input = input_dir

        self.gran = tk.Scale(self, label="", from_=1, to=4, tickinterval=1, orient='vertical', length=300)
        self.gran.grid(row=1, rowspan=2, column=7)

        self.img1 = Image.open(self.get_image(input_dir))
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

        self.left = tk.Button(self, text="<", command=self.on_zoom_out)
        self.left.grid(row=4, column=4)

        self.right = tk.Button(self, text=">", command=self.on_zoom_in)
        self.right.grid(row=4, column=5)

        self.zoom_value = tk.Scale(self, label="Zoom", from_=0, to= 15, tickinterval=1, orient='horizontal', length=500)
        self.zoom_value.grid(row=5, columnspan=7)

        self.messages = tk.Message(self, text="Current Directory: " + self.current_input, relief='raised', width=600)
        self.messages.grid(row=6, column=0, columnspan=7)

    def on_zoom_out(self):
        new_dir = self.current_input[:-2]
        if os.path.isdir(new_dir):
            if not self.update_image(new_dir):
                self.messages.config(text="Current Directory: " + self.current_input +
                                     "\nCan not zoom out any farther.")

    def on_zoom_in(self):
        new_dir = self.current_input + '{:01x}'.format(self.zoom_value.get()) + "/"
        if os.path.isdir(new_dir):
                if not self.update_image(new_dir):
                    self.messages.config(text="Current Directory: " + self.current_input +
                                         "\nCan not zoom in here.")
        else:
            self.messages.config(text="Current Directory: " + self.current_input +
                                 "\nDirectory does not exist.")

    def update_image(self, new_dir):
        image = self.get_image(new_dir)
        if image is not None:
            self.img1 = Image.open(image)
            self.img1.thumbnail((800, 800), Image.ANTIALIAS)
            self.pic1 = ImageTk.PhotoImage(self.img1)
            self.panel1.config(image=self.pic1)
            self.current_input = new_dir
            print self.current_input
            self.messages.config(text="Current Directory: " + self.current_input)
            return True
        return False

    def on_change_gran(self):
        if not self.update_image(self.current_input):
            print "poop"

    def get_image(self, input_dir):
        combined_spectrum = None
        pickles = os.listdir(input_dir)
        pickles.sort()
        used = []
        used_pickles = []
        for pic in pickles:
            if self.gran.get() == 1:
                pattern = r"[0-9a-fA-F]*_[0-1]{1}_left.spec.pkl"
            elif self.gran.get() == 2:
                pattern = r"[0-9a-fA-F]*_[0-1]{2}_left.spec.pkl"
            elif self.gran.get() == 3:
                pattern = r"[0-9a-fA-F]*_[0-1]{3}_left.spec.pkl"
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
                if combined_spectrum is None:
                    combined_spectrum = data[0]
                else:
                    combined_spectrum = np.vstack((combined_spectrum, data[0]))
        if combined_spectrum is None:
            return
        file_name = "/Users/lukestack/PycharmProjects/BeeVisualization/Images/" + used_pickles[0] + "_" + \
                    used_pickles[len(used_pickles) - 1] + "_gran_" + str(self.gran.get()) + ".png"
        if not os.path.isfile(file_name):
            hex_date1 = used_pickles[0]
            self.get_16(hex_date1)
            hex_date2 = used_pickles[len(used_pickles) - 1]
            if len(used_pickles) > 0:
                for i in range(0, 8 - len(hex_date1)):
                    hex_date1 += "0"
                for i in range(0, 8 - len(hex_date2)):
                    hex_date2 += "0"
            print (used)
            print (used_pickles[0], used_pickles[len(used_pickles) - 1])
            date1, file_time1 = Dates.to_date(hex_date1)
            date2, file_time2 = Dates.to_date(hex_date2)
            try:
                fig, ax = plt.subplots()
                fig.canvas.draw()
                ax.set_xticks(np.arange(0, combined_spectrum.shape[0], 1.0))
                ax.imshow(np.log(combined_spectrum.T), origin='lower', aspect='auto')
                ax.set_ylim((0, 1024))
                ax.set_title(date1)
                labels = [item.get_text() for item in ax.get_xticklabels()]
                labels[0] = file_time1
                print len(labels)
                labels[len(labels) - 1] = file_time2
                ax.set_xticklabels(labels)
                plt.savefig(file_name)
            except TypeError:
                return
        return file_name

    def get_16(self, hex_num):
        for i in range(0, 8 - len(hex_num)):
                    hex_num += "0"
        num = int(hex_num, 16)
        for i in range(0, 16):
            print format(num + i, 'x')

app = BeeApp()
app.mainloop()