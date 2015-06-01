__author__ = 'lukestack'
from scipy.io.wavfile import read
from numpy import mean, log10, sqrt, array_split, float32, square, hstack
import tempfile
from pydub import AudioSegment
import matplotlib.pyplot as plt
import os
import pickle


def get_data(path):
    if path.endswith(".wav"):
        bee_rate, bee_data = read(path)
        return bee_rate, bee_data
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

def get_data_for_hour(audio_dir, keyword):
    title = None
    combined_wav = None
    last_recording = None
    for rec in os.listdir(audio_dir):
        if keyword in rec:
            samprate, wav_data = get_data(audio_dir + rec)
            if title is None:
                title = os.path.splitext(rec)[0]
            if combined_wav is None:
                combined_wav = wav_data
            else:
                combined_wav = hstack((combined_wav, wav_data))
            last_recording = rec
    title += " " + os.path.splitext(last_recording)[0]
    return combined_wav, title

def create_decibel_plot(data, title=None, name=None, save=False, show=True):
    xs, dbs = get_decibels(data)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(xs, dbs)
    if title is not None:
        ax.set_title(title)
    ax.set_xlabel("Time (Minutes)")
    ax.set_ylabel("Decibel (dB)")
    if show:
        plt.show()
    if save and name is not None:
        plt.savefig(name)
    plt.close()

def get_decibels(data, path=None, name=None, save=False):
    if path is not None and name is not None:
        if os.path.isfile(path + name + ".pkl"):
            pkl = open(path + name + ".pkl", "r")
            return pickle.load(pkl)
    data = float32(data)
    minutes = len(data) / 44100 / 60
    num_chunks = 1000.0
    chunks = array_split(data, num_chunks)
    dbs = [20 * log10(sqrt(mean(chunk**2))) for chunk in chunks]
    xs = [i / num_chunks * minutes for i in range(int(num_chunks))]
    if save and name is not None and path is not None:
        with open(path + name + ".pkl", 'w') as outfile:
            pickle.dump((xs, dbs), outfile)
    return xs, dbs

def main():
    """
    audio_dir = "/Users/lukestack/PycharmProjects/BeeVisualization/15-04-2015Org/audio/"
    for rec in os.listdir(audio_dir):
        if ".flac" in rec:
            wav = audio_dir + rec
            samprate, wav_data = get_data(wav)
            xs, dbs = get_decibels(wav_data, path="/Users/lukestack/PycharmProjects/BeeVisualization/15-04-2015Org/Decibels/",
                         name=os.path.splitext(rec)[0], save=True)
            print dbs
    """
    # wav_data, title = get_data_for_hour(audio_dir, "left")
    # create_decibel_plot(wav_data, title=title, show=True)
    flac = "/Users/lukestack/PycharmProjects/BeeVisualization/15-04-2015Org/audio/17:48:01_left.flac"
    samprate, wav_data = get_data(flac)
    create_decibel_plot(wav_data, show=True)

if __name__ == "__main__":
    main()

