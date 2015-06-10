__author__ = 'lukestack'

import os
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import tempfile
from pydub import AudioSegment
import subprocess
import numpy as np

fs = 44100.0
nfft = 32768
noverlap = 16384


def create_spectrum(data, title=None, name=None, save=True, show=False):
    Pxx, freqs, bins, img = plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    plt.close()
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(freqs, np.mean(np.abs(Pxx), axis=1))
    if title is not None:
        ax.set_title(title)
    ax.set_xlim(0, 600)
    ax.set_xticks(np.arange(0, 601, 50.0))
    ax.set_ylim(0, 40000)
    ax.set_xlabel("Frequencies (hz)")
    ax.set_ylabel("Count")
    if show:
        plt.show()
    if save and name is not None:
        plt.savefig(name)
    plt.close()

def create_spectrogram(data, title=None, name=None, save=True, show=False):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    if title is not None:
        ax.set_title(title)
    ax.set_ylim(0, 600)
    ax.set_yticks(np.arange(0, 601, 50.0))
    ax.set_xlabel("Time (sec)")
    ax.set_ylabel("Frequencies (hz)")
    if show:
        plt.show()
    if save and name is not None:
        plt.savefig(name)
    plt.close()

def get_data(path):
    if path.endswith(".wav"):
        bee_rate, bee_data = read(path)
        return bee_rate, bee_data
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


def create_videos(input_dir):
    wd = os.getcwd()
    os.chdir(input_dir + "/Specgrams/")
    subprocess.Popen("ffmpeg -r 24 -i %05d_left.jpeg left.mp4", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.Popen("ffmpeg -r 24 -i %05d_right.jpeg right.mp4", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.chdir(input_dir + "/Spectrums/")
    subprocess.Popen("ffmpeg -r 24 -i %05d_left.jpeg left.mp4", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.Popen("ffmpeg -r 24 -i %05d_right.jpeg right.mp4", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.chdir(wd)


def main(input_dir):
    if os.path.isdir(input_dir + "/audio/"):
        audio_dir = input_dir + "/audio/"
        specgram_dir = input_dir + "/Specgrams/"
        spec_dir = input_dir + "/Spectrums/"
        left_index = 1
        right_index = 1
        file_index = 1
        for rec in os.listdir(audio_dir):
            if rec.endswith(".wav"):
                (bee_rate, bee_data) = read(audio_dir + rec)
            elif rec.endswith(".flac"):
                (bee_rate, bee_data) = get_data(audio_dir + rec)
            else:
                print "not an audio file"
                continue

            if not os.path.isdir(specgram_dir):
                os.makedirs(specgram_dir)
            if not os.path.isdir(spec_dir):
                os.makedirs(spec_dir)

            if "left" in rec:
                output = "%05d_left.jpeg" % left_index
                create_spectrum(bee_data, os.path.splitext(rec)[0], spec_dir + output)
                create_spectrogram(bee_data, os.path.splitext(rec)[0], specgram_dir + output)
                left_index += 1
            else:
                output = "%05d_right.jpeg" % right_index
                create_spectrum(bee_data, os.path.splitext(rec)[0], spec_dir + output)
                create_spectrogram(bee_data, os.path.splitext(rec)[0], specgram_dir + output)
                right_index += 1

            print "file", file_index, "completed"
            file_index += 1
        create_videos(input_dir)


if __name__ == "__main__":
    import sys
    main(sys.argv[1])