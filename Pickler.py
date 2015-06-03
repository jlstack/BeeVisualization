__author__ = 'lukestack'

import os
from scipy.signal import decimate
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import tempfile
from pydub import AudioSegment
import pickle


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


def save_specgram_pkl(data, title=None, name=None, show=False):
    if show:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
        if title is not None:
            ax.set_title(title)
        # ax.set_ylim(0, 600)
        # ax.set_yticks(np.arange(0, 601, 50.0))
        ax.set_xlabel("Time (sec)")
        ax.set_ylabel("Frequencies (hz)")
        plt.show()
        plt.close()
    data, freqs, bins, img = plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    with open(name, 'w') as outfile:
        pickle.dump((data, freqs), outfile)
    plt.close()


def main(input_dir, output_dir):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    for dir in os.listdir(input_dir):
        print input_dir + dir + "/audio/"
        if os.path.isdir(input_dir + dir + "/audio/"):
            date = dir.split("-")
            date.reverse()
            date = "-".join(date)
            print date
            audio_dir = input_dir + dir + "/audio/"
            file_index = 1
            for rec in os.listdir(audio_dir):
                if rec.endswith(".wav") or rec.endswith(".flac") or rec.endswith(".mp3"):
                    (bee_rate, bee_data) = read(audio_dir + rec)
                else:
                    print "not an audio file"
                    continue

                bee_data = decimate(bee_data, 36)
                output = output_dir + date + "_" + os.path.splitext(rec)[0] + ".spec.pkl"
                save_specgram_pkl(bee_data, os.path.splitext(rec)[0], output, show=False)

                print "file", file_index, "completed"
                file_index += 1


if __name__ == "__main__":
    import sys
main("/Users/lukestack/PycharmProjects/BeeVisualization/", "/Users/lukestack/PycharmProjects/BeeVisualization/Pickles/")
