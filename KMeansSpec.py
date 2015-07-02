"""
KMeansSpec.py

This program opens up a connection to SSH into the cs.appstate.edu
server.  It will be utilized to get the bee videos for later parsing.

The KMeans_dir(path) function is used to get the audio files
and perform KMeans clustering on them.  It then displays the closest
and farthest tuples of points in the same cluster, and displays how
many points are in each cluster.
"""

import sys
from scipy.io.wavfile import read as read_wav
from sklearn import cluster
import numpy as np
import wave
from scipy.spatial import distance as d
import sklearn.preprocessing as p
from scipy import signal
from matplotlib import pyplot as plt
import os
from time import time
from collections import Counter
from sklearn import metrics
from pydub import AudioSegment
import pickle
import tempfile

'''
This function opens the connection & gets the files to be clustered.
Then, it performs KMeans clustering on the periodograms
of the wav file specgrams.

The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The day parameter is the day to get data from.
The n parameter is the number of clusters.
The limit parameter is the number of files to include.
'''
def KMeans_dir(path, pit, date=None, n=None, limit=None):
    t0 = time()
    #Set seed for consistent cluster center initialization
    np.random.seed(327)
    #Get the current directory for data storage, as well as getting the audio path based on input
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + date + "/"
    data = []
    count = 0
    print("Reading wav files...")
    #Make sure the storage directories are there
    if not os.path.isdir("usr/local/bee/beemon/beeW/Chris/" + pit):
        os.makedirs("usr/local/bee/beemon/beeW/Chris/" + pit)
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    if not os.path.isdir(save_dir + "Left/"):
        os.makedirs(save_dir + "Left/")
    if not os.path.isdir(save_dir + "Right/"):
        os.makedirs(save_dir + "Right/")
    if path == "/usr/local/bee/bee-mp3/":
        audiofiles = os.listdir(path)
        audiofiles.sort()
        parsefiles = []
        #Make sure the limit is set
        if limit is None:
            limit = len(audiofiles)
        limited = 0
        for rec in audiofiles:
            name = os.path.splitext(rec)[1]
            if pit == str(rec.split('_')[0]):
                if str(rec.split('_')[1]) == date or date is None:
                    if name == ".wav" or name == ".mp3" or name == ".flac":
                            parsefiles.append(rec)
                            limited += 1
                            if len(parsefiles) == limit:
                                break
    else:
        path = path + pit + "/" + date
        audiofiles= os.listdir(path + "/audio/")
        audiofiles.sort()
        parsefiles = []
        if limit is None:
            limit = len(audiofiles)
        limited = 0
        for rec in audiofiles:
            parsefiles.append(rec)
            limited += 1
            if limit == len(parsefiles):
                break
    limit = limited
    print("Files to parse: " + str(limit))
    #Get the recordings and parse them for clustering
    for recording in parsefiles:
        if count % int(limit/5) == 0:
            print(str(count) + " out of " + str(limit) + " audio files read!")
        if count >= limit:
            break
        filename = os.path.splitext(recording)[0]
        if os.path.splitext(recording)[1] != ".wav":
            temp = tempfile.NamedTemporaryFile(suffix=".wav")
            if os.path.splitext(recording)[1] == ".mp3":
                sound = AudioSegment.from_file(path + recording, "mp3")
                sound.export(temp.name, format = "wav")
            if os.path.splitext(recording)[1] == ".flac":
                sound = AudioSegment.from_file(path + recording, "flac")
                sound.export(temp.name, format = "flac")
            wav = wave.open(temp, 'r')
        else:
            #Open the .wav file and get the vital information
            wav = wave.open(path + "/audio/" + recording, 'r')
        frames = wav.readframes(-1)
        sig = np.fromstring(frames, "Int16")
        #Decimate the wav signal for parsing
        dsarray = signal.decimate(sig, 36)
        #pxx is the periodograms, freqs is the frequencies
        pxx, freqs, times, img = plt.specgram(dsarray, NFFT = 1024, noverlap = 512, Fs = 1225)
        #Plot against the time. Then, title it and limit the y-axis to 600
        if "left" in recording:
            np.save(save_dir + "Left/" + recording, pxx)
        elif "right" in recording:
            np.save(save_dir + "Right/" + recording, pxx)
        count += 1
        #Append it to the list of data
        for index in range(pxx.shape[1]):
            data.append(pxx[:,index])
    print("Number of periodograms: " + str(len(data)))
    #Make sure the number of clusters is set
    if n is None:
        n = 10
    n = int(n)
    #Actually do the KMeans clustering
    t2 = time()
    print("Data gathering complete. Initializing KMeans...")
    estimator = cluster.KMeans(n_clusters=n, n_init = 1, max_iter=10000, verbose=1, n_jobs=1)
    estimator.fit(data)
    t3 = time()
    print(t3 - t2)
    #Save the labels, cluster centers, overall inertia, and the cluster counts into a file called "clusterdata.npy"
    counts = total_counts(estimator.labels_, n)
    print(counts)
    saveddata = [estimator.labels_, estimator.cluster_centers_, estimator.inertia_, counts]
    print("Saving results...")
    pickle.dump(saveddata, open(save_dir + "/clusterdata_" + str(n) + "_" + str(limit) + ".pkl", "wb"), protocol = 2)
    print("Done.")
    print(time() - t0)

'''
Used to return the counts for each cluster.
Prints this out to the console.
'''
def total_counts(dataset, n):
    c = Counter(dataset)
    return c.most_common(n)
'''
Used to run through command prompt instead of python console.
'''
if __name__ == "__main__":
    passed = True
    import sys
    if len(sys.argv) == 2:
        KMeans_dir(sys.argv[1])
    elif len(sys.argv) == 3:
        decision = raw_input("Is the second parameter the number of clusters?")
        if 'y' in decision or 'Y' in decision:
            if 'n' in decision or 'N' in decision:
                passed = False
            else:
                KMeans_dir(sys.argv[1], n=sys.argv[2])
        elif 'n' in decision or 'N' in decision:
            KMeans_dir(sys.argv[1], limit=sys.argv[2])
        else:
            print("Error. Answer must contain y for yes, or n for no.")
        if not passed:
            print("Cannot contain both.")
    elif len(sys.argv) == 4:
        KMeans_dir(sys.argv[1], n=sys.argv[2], limit=sys.argv[3])
    else:
        print("Called with wrong number of parameters.")
        print("First parameter is the path to the files (REQUIRED)")
        print("Second parameter is the number of clusters (OPTIONAL)")
        print("Third parameter is the number of files desired (OPTIONAL)")

