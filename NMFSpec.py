"""
NMFSpec.py

The NMF_dir function is used to get the audio files
and perform nonnegative matrix factorization on them.  it then displays the closest
and farthest tuples of points in the same cluster, and displays how
many points are in each cluster.
"""

import sys
from scipy.io.wavfile import read as read_wav
from sklearn import decomposition
import numpy as np
import wave
#from scipy.spatial import distance as d
#import sklearn.preprocessing as p
from scipy import signal
from matplotlib import pyplot as plt
import os
from time import time
#from collections import Counter
#from sklearn import metrics
from pydub import AudioSegment
import pickle
import tempfile
from mpl_toolkits.mplot3d import Axes3D


'''
This file contains functions to get the files to be factorized, and
then does it on the periodograms of the wav file specgrams.

The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The day parameter is the day to get data from.
The limit parameter is the number of files to include.
'''
def NMF_dir(path, pit, date=None, limit=None):
    t0 = time()
    #Set seed for consistent cluster center initialization
    #Get the current directory for data storage, as well as getting the audio path based on input
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + str(date) + "/"
    data = []
    dates = []
    count = 0
    print("Reading audio files...")
    #Make sure the storage directories are there
    if not os.path.isdir("usr/local/bee/beemon/beeW/Chris/" + pit):
        os.makedirs("usr/local/bee/beemon/beeW/Chris/" + pit)
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    if not os.path.isdir(save_dir + "Left/"):
        os.makedirs(save_dir + "Left/")
    if not os.path.isdir(save_dir + "Right/"):
        os.makedirs(save_dir + "Right/")
    if path == "/usr/local/bee/beemon/mp3/":
        if date is not None:
            path = path + pit + "/" + date + "/"
            audiofiles = os.listdir(path)
        else:
            path = path + pit + "/"
            audiofiles = []
            for dir in os.listdir(path):
                for d in os.listdir(path + dir):
                    audiofiles.append(d)
                    dates.append(dir)
                if limit is not None and int(limit) <= len(audiofiles):
                    break
        parsefiles = []
        #Make sure the limit is set
        if limit is None:
            limit = len(audiofiles)
        limit = int(limit)
        limited = 0
        for rec in audiofiles:
            name = os.path.splitext(rec)[1]
            if name == ".wav" or name == ".mp3" or name == ".flac":
                parsefiles.append(rec)
                limited += 1
                if len(parsefiles) == limit:
                    break
    else:
        if date is not None:
            path = path + pit + "/" + date
            audiofiles= os.listdir(path + "/audio/")
        else:
            path = path + pit + "/"
            audiofiles = []
            for dir in os.listdir(path):
                audiofiles.append(os.listdir(path + dir))
                if limit is not None and int(limit) <= len(audiofiles):
                    break
        parsefiles = []
        if limit is None:
            limit = len(audiofiles)
        limit = int(limit)
        limited = 0
        for rec in audiofiles:
            parsefiles.append(rec)
            limited += 1
            if limit == len(parsefiles):
                break
    limit = limited
    print("Files to parse: " + str(limit))
    #Get the recordings and parse them for clustering
    for recording in range(len(parsefiles)):
        if count % int(limit/5) == 0:
            print(str(count) + " out of " + str(limit) + " audio files read!")
        if count >= limit:
            break
        filename = os.path.splitext(parsefiles[recording])[0]
        if os.path.splitext(parsefiles[recording])[1] != ".wav":
            temp = tempfile.NamedTemporaryFile(suffix=".wav")
            if os.path.splitext(parsefiles[recording])[1] == ".mp3":
                if "mp3" in path and date is None:
                    sound = AudioSegment.from_file(path + dates[recording] + "/" + parsefiles[recording], "mp3")
                else:
                    sound = AudioSegment.from_file(path + parsefiles[recording], "mp3")
                sound.export(temp.name, format = "wav")
            if os.path.splitext(parsefiles[recording])[1] == ".flac":
                if "mp3" in path and date is None:
                    sound = AudioSegment.from_file(path + dates[recording] + "/" + recording, "flac")
                else:
                    sound = AudioSegment.from_file(path + parsefiles[recording], "flac")
                sound.export(temp.name, format = "flac")
            wav = wave.open(temp, 'r')
        else:
            #Open the .wav file and get the vital information
            wav = wave.open(path + "/audio/" + parsefiles[recording], 'r')
        frames = wav.readframes(-1)
        sig = np.fromstring(frames, "Int16")
        #Decimate the wav signal for parsing
        dsarray = signal.decimate(sig, 36)
        #pxx is the periodograms, freqs is the frequencies
        pxx, freqs, times, img = plt.specgram(dsarray, NFFT = 1024, noverlap = 512, Fs = 1225)
        #Plot against the time. Then, title it and limit the y-axis to 600
        if "left" in parsefiles[recording] and not os.path.isfile(save_dir + "Left/" + parsefiles[recording] + ".npy"):
            if date is not None:
                np.save(save_dir + "Left/" + parsefiles[recording], pxx)
            else:
                np.save(save_dir + "Left/" + dates[recording] + '_' + parsefiles[recording], pxx)
        elif "right" in parsefiles[recording] and not os.path.isfile(save_dir + "Right/" + parsefiles[recording] + ".npy"):
            if date is not None:
                np.save(save_dir + "Right/" + parsefiles[recording], pxx)
            else:
                np.save(save_dir + "Right/" + dates[recording] + '_' + parsefiles[recording], pxx)
        count += 1
        #Append it to the list of data
        for index in range(pxx.shape[1]):
            data.append(pxx[:,index])
    print("Number of periodograms: " + str(len(data)))
    #Make sure the number of clusters is set
    #if n is None:
    #    n = 10
    #n = int(n)
    #Actually do the KMeans clustering
    t2 = time()
    print("Data gathering complete. Doing nonnegative matrix factorization.")
    estimator = decomposition.NMF(init = 'nndsvdar', max_iter=10000, random_state = 327)
    print("Fitting the model to your data...")
    print("This may take some time...")
    estimator.fit(data)
    t3 = time()
    print(t3 - t2)
    #Save the labels, cluster centers, overall inertia, and the cluster counts into a file called "clusterdata.npy"
    saveddata = [estimator.components_, estimator.reconstruction_err_]
    print("Saving results...")
    pickle.dump(saveddata, open(save_dir + "/NMFdata_" + str(limit) + ".pkl", "wb"), protocol = 2)
    print("Done.")
    print(time() - t0)

'''
Visualize the components of the factorized matrix in 3D space.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.
'''
def NMF_vis3d(path):
    t0 = time()
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[0]
    fig = plt.figure()
    ax = fig.add_subplot(111, projection = '3d')
    ax.scatter(components[:, 0], components[:, 1], components[:, 2])
    ax.xaxis.get_major_formatter().set_powerlimits((0,1))
    ax.yaxis.get_major_formatter().set_powerlimits((0,1))
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()

'''
Visualize the components of the factorized matrix in 3D space.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.

The dims parameter is the number of dimensions to visualize.
'''
def NMF_vis2d(path, dims = 2):
    t0 = time()
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[0]
    fig = plt.figure()
    pos = 1
    dims = int(dims)
    for y in range(dims):
        print("Loading dimension " + str(y + 1) + ".")
        for x in range(dims):
            ax = fig.add_subplot(dims, dims, pos)
            pos += 1
            if x != y:
                #Plot data
                plt.scatter(components[:, x], components[:, y], linewidth = 0.15)
            else:
                plt.hist(components[:,x], bins = 50)
            #Set the axis to scientific notation
            ax.xaxis.get_major_formatter().set_powerlimits((0,1))
            ax.yaxis.get_major_formatter().set_powerlimits((0,1))
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()



'''
Used to run through command prompt instead of python console.
'''
if __name__ == "__main__":
    passed = True
    import sys
    if len(sys.argv) == 3:
        NMF_dir(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        if '-' in sys.argv[3]:
            NMF_dir(sys.argv[1], sys.argv[2], date=sys.argv[3])
        else:
            NMF_dir(sys.argv[1], sys.argv[2], limit=sys.argv[3])
    elif len(sys.argv) == 5:
        NMF_dir(sys.argv[1], sys.argv[2], date=sys.argv[3], limit=sys.argv[4])
    else:
        print("Called with wrong number of parameters.")
        print("First parameter is the path to the files (REQUIRED)")
        print("Second parameter is the pit to analyze (REQUIRED)")
        print("Second parameter is the date to analyze (OPTIONAL)")
        print("Third parameter is the number of files desired (OPTIONAL)")


