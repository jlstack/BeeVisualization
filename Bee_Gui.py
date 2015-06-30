__author__ = 'lukestack'
import Tkinter as tk
from PIL import ImageTk, Image
import pickle
import matplotlib.pyplot as plt
import numpy as np
import os
import Dates

input_dir = "/Users/lukestack/PycharmProjects/BeeVisualization/Pickles/"
start = "5/5/2/e/c/3/6/"
img_dir = "/Users/lukestack/PycharmProjects/BeeVisualization/Images/"

class BeeApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.input_dir = input_dir
        self.current_input = input_dir + start
        self.img_dir = img_dir
        self.leftmost = self.make_hex8("".join(start.split("/")))
        self.center = format(int(self.leftmost, 16) + 8, 'x')
        self.zoom = 1
        self.cax = None
        self.panel1 = None

        self.img1 = Image.open(self.get_next_16(self.center))
        self.img1.thumbnail((800, 800), Image.ANTIALIAS)
        self.pic1 = ImageTk.PhotoImage(self.img1)
        self.panel1 = tk.Label(self, image=self.pic1)
        self.panel1.grid(row=0, rowspan=4, columnspan=7)

        self.zoom_out = tk.Button(self, text="-", command=self.on_zoom_out)
        self.zoom_out.grid(row=4, column=1)

        self.zoom_in = tk.Button(self, text="+", command=self.on_zoom_in)
        self.zoom_in.grid(row=4, column=2)

        self.left = tk.Button(self, text="<", command=self.on_left)
        self.left.grid(row=4, column=4)

        self.right = tk.Button(self, text=">", command=self.on_right)
        self.right.grid(row=4, column=5)

    def on_zoom_out(self):
        if self.zoom < 28:
            self.zoom += 1
            self.update_image(self.get_next_16(self.center))

    def on_zoom_in(self):
        if self.zoom != 1:
            self.zoom -= 1
            self.update_image(self.get_next_16(self.center))

    def update_image(self, image):
        if image is not None:
            self.img1 = Image.open(image)
            self.img1.thumbnail((800, 800), Image.ANTIALIAS)
            self.pic1 = ImageTk.PhotoImage(self.img1)
            self.panel1.config(image=self.pic1)
            return True
        return False

    def on_right(self):
        cen = int(self.center, 16)
        cen += 2**(3 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.get_next_16(self.center, 'right')

    def on_left(self):
        cen = int(self.center, 16)
        cen -= 2**(3 + self.zoom) / 2
        self.center = format(cen, 'x')
        self.get_next_16(self.center, 'left')

    def get_next_16(self, hex_num, direction=None):
        print "\nZoom: ", self.zoom
        combined_spec = None
        num = int(hex_num, 16)
        num -= 2**(3 + self.zoom) / 2
        for i in range(0, 2**(3 + self.zoom), 2**(self.zoom - 1)):
            i_hex = format(num + i, 'x')
            i_hex = i_hex[:len(i_hex) - ((self.zoom - 1) / 4)]
            i_dir = "/".join(i_hex[:-1]) + "/"
            i_file = None
            if os.path.isdir(self.input_dir + i_dir):
                for f in os.listdir(self.input_dir + i_dir):
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
            if i_file is not None:
                print i_file
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
        hex_time2 = format(num + 2**(3 + self.zoom) - 1, 'x')
        file_name = self.img_dir + hex_time1 + "_" + \
                hex_time2 + "_zoom_" + str(self.zoom) + ".png"
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
            title = date1 + "  -  " + date2
        else:
            title = date1
        fig, ax = plt.subplots()
        fig.canvas.draw()
        ax.set_xticks(np.arange(0, combined_spec.shape[0], 1.0))
        if self.cax is None:
            self.cax = ax.imshow(np.log(combined_spec.T), origin='lower', aspect='auto')
        ax.imshow(np.log(combined_spec.T), origin='lower', aspect='auto')
        ax.set_ylim((0, 1024))
        ax.set_title(title)
        labels = [item.get_text() for item in ax.get_xticklabels()]
        labels[0] = file_time1
        labels[len(labels) - 1] = file_time2
        ax.set_xticklabels(labels)
        fig.colorbar(self.cax)
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
