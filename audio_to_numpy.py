__author__ = 'lukestack'

import os
from scipy.signal import resample
from scipy.io.wavfile import read
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tempfile
from pydub import AudioSegment
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
        temp.close()
        if path.endswith(".flac"):
            sound = AudioSegment.from_file(path, "flac")
            sound.export(temp.name, format="wav")
        elif path.endswith(".mp3"):
            sound = AudioSegment.from_file(path, "mp3")
            sound.export(temp.name, format="wav")
        bee_rate, bee_data = read(temp.name)
        os.remove(temp.name)
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
    plt.title(date + "T" + file_time)
    plt.ylim(0, 600)
    plt.yticks(np.arange(0, 601, 50.0))
    plt.xlabel("Time (sec)")
    plt.ylabel("Frequencies (hz)")
    plt.show()
    plt.close()


def save_specgram_pkl(data, date, file_time, recording, output_dir, show=False):
    sample_rate = 2048
    data = resample(data, len(data) / 44100.0 * sample_rate)
    if show:
        show_spectrogram(data, date, file_time)
    specgram, freqs, time, img = plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
    specgram = abs(specgram)
    hex_num, hex_dir = Dates.to_hex(date, file_time)
    print (date, file_time, hex_num)
    for i in range(-1, specgram.shape[1] + 1):
        start_date, start_time = Dates.add_seconds_to_date(date, file_time, i)
        end_date, end_time = Dates.add_seconds_to_date(start_date, start_time, 1)
        start_datetime = start_date + 'T' + start_time
        end_datetime = end_date + 'T' + end_time
        hex_num, hex_dir = Dates.to_hex(start_date, start_time)
        if not os.path.isdir(output_dir + hex_dir):
            os.makedirs(output_dir + hex_dir)
        if "left" in recording:
            output = output_dir + hex_dir + hex_num + "_" + start_date + "T" + start_time + "_left.spec.npy"
        else:
            output = output_dir + hex_dir + hex_num + "_" + start_date + "T" + start_time + "_right.spec.npy"
        if i == -1:
            intensities = specgram[:, 0]
        elif i == specgram.shape[1]:
            intensities = specgram[:, specgram.shape[1] - 1]
        else:
            intensities = specgram[:, i]	
        data = {"intensities": intensities.astype(np.float32).tolist(), "sample_rate": sample_rate,
                "start_datetime": start_datetime, "end_datetime": end_datetime}
        if not os.path.isfile(output):
            np.save(output, data)
        plt.clf()


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
                    temp_date, temp_time = Dates.add_seconds_to_date(date, file_time, 30)
                    hex_num, hex_dir = Dates.to_hex(temp_date, temp_time)
                    if "left" in rec:
                        output = output_dir + hex_dir + hex_num + "_" + temp_date + "T" + temp_time + "_left.spec.npy"
                    else:
                        output = output_dir + hex_dir + hex_num + "_" + temp_date + "T" + temp_time + "_right.spec.npy"
                    if not os.path.isfile(output):
                        try:
                            (bee_rate, bee_data) = get_data(audio_dir + rec)
                            save_specgram_pkl(bee_data, date, file_time, rec, output_dir)
                        except:
                            print ("Error thrown when file was read")

if __name__ == "__main__":
    import sys
    main("/Users/lukestack/PycharmProjects/BeeVisualization", "/Users/lukestack/PycharmProjects/BeeVisualization/Seconds")
