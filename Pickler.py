__author__ = 'lukestack'

import os
from scipy.signal import resample
from scipy.io.wavfile import read
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tempfile
from pydub import AudioSegment
import pickle
import numpy as np
import Dates


fs = 2048
nfft = 4096
noverlap = 2048


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


def show_spectrogram(data, date, file_time):
    plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    plt.title(date + "T" + file_time + "Z")
    plt.ylim(0, 600)
    plt.yticks(np.arange(0, 601, 50.0))
    plt.xlabel("Time (sec)")
    plt.ylabel("Frequencies (hz)")
    plt.show()
    plt.close()


def save_specgram_pkl(data, date, file_time, recording, output_dir, show=False):
    data = resample(data, len(data) / 44100.0 * 2048)
    if show:
        show_spectrogram(data, date, file_time)
    specgram, freqs, time, img = plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    specgram = abs(specgram)
    hex_num, hex_dir = Dates.to_hex(date, file_time)
    print (date, file_time, hex_num)
    for i in range(-1, specgram.shape[1] + 1):
        temp_date, temp_time = Dates.add_seconds_to_date(date, file_time, i)
        hex_num, hex_dir = Dates.to_hex(temp_date, temp_time)
        if not os.path.isdir(output_dir + hex_dir):
            os.makedirs(output_dir + hex_dir)
        if "left" in recording:
            output = output_dir + hex_dir + hex_num + "_" + temp_date + "T" + temp_time + "Z_left.spec.pkl"
        else:
            output = output_dir + hex_dir + hex_num + "_" + temp_date + "T" + temp_time + "Z_right.spec.pkl"
        if i == -1:
            spectrum = specgram[:, 0]
        elif i == specgram.shape[1]:
            spectrum = specgram[:, specgram.shape[1] - 1]
        else:
            spectrum = specgram[:, i]
        if not os.path.isfile(output):
            with open(output, 'wb') as outfile:
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
    for d in directories:
        if os.path.isdir(input_dir + d + "/audio/"):
            audio_dir = input_dir + d + "/audio/"
            date = d.split("-")
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
                    temp_date, temp_time = Dates.add_seconds_to_date(date, file_time, 30)
                    hex_num, hex_dir = Dates.to_hex(temp_date, temp_time)
                    if "left" in rec:
                        output = output_dir + hex_dir + hex_num + "_" + temp_date + "T" + temp_time + "Z_left.spec.pkl"
                    else:
                        output = output_dir + hex_dir + hex_num + "_" + temp_date + "T" + temp_time + "Z_right.spec.pkl"
                    if not os.path.isfile(output):
                        (bee_rate, bee_data) = get_data(audio_dir + rec)
                        save_specgram_pkl(bee_data, date, file_time, rec, output_dir)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])
