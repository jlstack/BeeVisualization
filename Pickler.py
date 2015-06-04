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


fs = 1225
nfft = 1024
noverlap = 512


def get_data(path):
    temp = tempfile.NamedTemporaryFile(suffix=".wav")
    if path.endswith(".flac"):
        sound = AudioSegment.from_file(path, "flac")
        sound.export(temp.name, format="wav")
    if path.endswith(".mp3"):
        sound = AudioSegment.from_file(path, "mp3")
        sound.export(temp.name, format="wav")
    bee_rate, bee_data = read(temp.name)
    temp.close()
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
    data, freqs, bins, img = plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    with open(name, 'wb') as outfile:
        pickle.dump((data, freqs), outfile)
    plt.close()


def create_directories(output_dir):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    if not os.path.isdir(output_dir + "left/"):
        os.makedirs(output_dir + "left/")
    if not os.path.isdir(output_dir + "right/"):
        os.makedirs(output_dir + "right/")
    if not os.path.isdir(output_dir + "single_channel/"):
        os.makedirs(output_dir + "single_channel/")


def main(input_dir, output_dir):
    if not input_dir.endswith("/"):
        input_dir += "/"
    if not output_dir.endswith("/"):
        output_dir += "/"
    create_directories(output_dir)
    for dir in os.listdir(input_dir):
        if os.path.isdir(input_dir + dir + "/audio/"):
            audio_dir = input_dir + dir + "/audio/"
            date = dir.split("-")
            date.reverse()
            date = "-".join(date)
            for rec in os.listdir(audio_dir):
                if rec.endswith(".wav") or rec.endswith(".flac") or rec.endswith(".mp3"):
                    (bee_rate, bee_data) = read(audio_dir + rec)
                else:
                    print ("not an audio file")
                    continue
                bee_data = decimate(bee_data, 36)
                if "left" in rec:
                    output = output_dir + "left/" + date + "_" + os.path.splitext(rec)[0] + ".spec.pkl"
                elif "right" in rec:
                    output = output_dir + "right/" + date + "_" + os.path.splitext(rec)[0] + ".spec.pkl"
                else:
                    output = output_dir + "single_channel/" + date + "_" + os.path.splitext(rec)[0] + ".spec.pkl"
                print (output)
                save_specgram_pkl(bee_data, os.path.splitext(rec)[0], output, show=False)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])
