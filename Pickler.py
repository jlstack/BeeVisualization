__author__ = 'lukestack'

import os
from scipy.signal import decimate
from scipy.io.wavfile import read
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tempfile
from pydub import AudioSegment
import pickle
import numpy as np
import Dates


fs = 1225
nfft = 1024
noverlap = 512


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
    data_type = np.iinfo(bee_data.dtype)
    dmin = data_type.min
    dmax = data_type.max
    bee_data = bee_data.astype(np.float32)
    bee_data = 2 * ((bee_data - dmin) / (dmax - dmin)) - 1
    return bee_rate, bee_data


def combine_specgrams(data1, data2):
    data1 = (data1[::, ::2] + data1[::, 1::2]) / 2.0
    data2 = (data2[::, ::2] + data2[::, 1::2]) / 2.0
    return np.hstack((data1, data2))


def save_specgram_pkl(data, title=None, name=None, show=False):
    if show:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
        if title is not None:
            ax.set_title(title)
        ax.set_ylim(0, 600)
        ax.set_yticks(np.arange(0, 601, 50.0))
        ax.set_xlabel("Time (sec)")
        ax.set_ylabel("Frequencies (hz)")
        plt.show()
        plt.close()
    data = decimate(data, 36)
    spectrum, freqs, time, img = plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    spectrum = abs(spectrum)
    with open(name, 'wb') as outfile:
        pickle.dump((spectrum, freqs, time), outfile)
    plt.close()


def main(input_dir, output_dir):
    if not input_dir.endswith("/"):
        input_dir += "/"
    if not output_dir.endswith("/"):
        output_dir += "/"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    directories = os.listdir(input_dir)
    directories.sort()
    for dir in directories:
        if os.path.isdir(input_dir + dir + "/audio/"):
            audio_dir = input_dir + dir + "/audio/"
            date = dir.split("-")
            date.reverse()
            date = "-".join(date)
            if "Org" in date:
                index = date.index("Org")
                date = date[:index] + date[index + 3:]
            recordings = os.listdir(audio_dir)
            recordings.sort()
            for rec in recordings:
                if rec.endswith(".wav") or rec.endswith(".flac") or rec.endswith(".mp3"):
                    print (audio_dir + rec)
                    file_time = os.path.splitext(rec)[0][:os.path.splitext(rec)[0].index("_")]
                    date, file_time = Dates.convert_to_utc(date, file_time)
                    hex_num, hex_dir = Dates.to_hex(date, file_time)
                    if not os.path.isdir(output_dir + hex_dir):
                        os.makedirs(output_dir + hex_dir)
                    if "left" in rec:
                        output = output_dir + hex_dir + hex_num + "_" + date + "T" + file_time + "Z_left.spec.pkl"
                    else:
                        output = output_dir + hex_dir + hex_num + "_" + date + "T" + file_time + "Z_right.spec.pkl"
                    if not os.path.isfile(output):
                        (bee_rate, bee_data) = get_data(audio_dir + rec)
                        save_specgram_pkl(bee_data, os.path.splitext(rec)[0], output, show=False)
                else:
                    continue


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])
