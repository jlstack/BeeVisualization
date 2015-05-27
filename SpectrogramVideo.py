__author__ = 'lukestack'

import os
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import tempfile
from pydub import AudioSegment
import subprocess

fs = 44100.0
nfft = 2048
noverlap = 1024


def create_specgrams(input_dir):
    if os.path.isdir(input_dir + "/audio/"):
        audio_dir = input_dir + "/audio/"
        spec_dir = input_dir + "/Specgrams/"
        left_index = 1
        right_index = 1
        file_index = 1
        for recording in os.listdir(audio_dir).sort():
            if recording.endswith(".wav"):
                (bee_rate, bee_data) = read(audio_dir + recording)
            elif recording.endswith(".mp3"):
                (bee_rate, bee_data) = get_data(audio_dir + recording)
            else:
                print "not an audio file"
                continue

            if not os.path.isdir(spec_dir):
                os.makedirs(spec_dir)

            plt.specgram(bee_data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
            plt.title(os.path.splitext(recording)[0])
            if "left" in recording:
                plt.savefig(spec_dir + "%05d_left.jpeg" % left_index)
                plt.close()
                left_index += 1
            else:
                plt.savefig(spec_dir + "%05d_right.jpeg" % right_index)
                plt.close()
                right_index += 1
            print "file",file_index,"completed"
        create_videos(input_dir)


def get_data(path):
    if path.endswith(".mp3"):
        temp = tempfile.NamedTemporaryFile(suffix=".wav")
        sound = AudioSegment.from_mp3(path)
        sound.export(temp.name, format="wav")
        (bee_rate, bee_data) = read(temp.name)
        temp.close()
        return (bee_rate, bee_data)


def create_videos(input_dir):
    wd = os.getcwd()
    os.chdir(input_dir + "/Specgrams/")
    subprocess.Popen("ffmpeg -r 24 -i %05d_left.jpeg left.mp4", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.Popen("ffmpeg -r 24 -i %05d_right.jpeg right.mp4", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.chdir(wd)
