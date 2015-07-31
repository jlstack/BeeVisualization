"""
NMFSpec.py

This file contains functions to get the audio files
and perform nonnegative matrix factorization on them.  It also contains
functions that enable the user to plot the results of the NMF.
"""

__author__ = "Chris Smith"

import sys
from scipy.io.wavfile import read as read_wav
from sklearn import decomposition
import numpy as np
import wave
from scipy import signal
from scipy import stats
from matplotlib import pyplot as plt
import os
from time import time
from pydub import AudioSegment
import pickle
import tempfile
from mpl_toolkits.mplot3d import Axes3D

'''
This function looks on the path provided for data from
the date given pertaining to the pit that is passed in.

The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The day parameter is the day to get data from.
The limit parameter is the number of files to include.
'''
def audiolist_getter(path, pit, date=None, limit=None):
    dates = []
    #If using the mp3 structure
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
    #If not using the mp3 structure
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
    return dates, parsefiles, limited, path

'''
This method gets the data from the audio.  It does the correct transformations
if the file is not a .wav file (i.e. a .mp3 or a .flac file).

The path parameter is the directory that has the wav files.
The date parameter is the day to get data from.
The filedate parameter is the list of dates that are in the dataset.
The filename parameter is the file's name.
The index parameter is the index of the file in the list of files.
'''
def audiodata_getter(path, date, filedate, filename, index):
    #Check to see if it's a wav file. If not, convert in a temp file.
    splitname = os.path.splitext(filename)[0]
    if os.path.splitext(filename)[1] != ".wav":
        temp = tempfile.NamedTemporaryFile(suffix=".wav")
        if os.path.splitext(filename)[1] == ".mp3":
            if "mp3" in path and date is None:
                sound = AudioSegment.from_file(path + filedate[index] + "/" + filename, "mp3")
            else:
                sound = AudioSegment.from_file(path + filename, "mp3")
            sound.export(temp.name, format = "wav")
        if os.path.splitext(filename)[1] == ".flac":
            if "mp3" in path and date is None:
                sound = AudioSegment.from_file(path + filedate[index] + "/" + filename, "flac")
            else:
                sound = AudioSegment.from_file(path + filename, "flac")
            sound.export(temp.name, format = "flac")
        try:
            wav = wave.open(temp, 'r')
            return wav
        except:
            print(filename + " corrupted or not audio file.")
    else:
        try:
            #Open the .wav file and get the vital information
            wav = wave.open(path + "/audio/" + filename, 'r')
            return wav
        except:
            print(filename + " corrupted or not audio file.")

'''
This function gets the files to be factorized, and
then does nonnegative matrix factorization on the periodograms of the wav file specgrams.

The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The day parameter is the day to get data from.
The limit parameter is the number of files to include.
'''
def NMF_dir(path, pit, date=None, limit=None):
    t0 = time()
    #Get the current directory for data storage, as well as getting the audio path based on input
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + str(date) + "/"
    dates = []
    data = []
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
    dates, parsefiles, limit, path = audiolist_getter(path, pit, date, limit)

    print("Files to parse: " + str(limit))
    #Get the recordings and parse them for clustering
    for recording in range(len(parsefiles)):
        if count % int(limit/5) == 0:
            print(str(count) + " out of " + str(limit) + " audio files read!")
        if count >= limit:
            break
        try:
            wav = audiodata_getter(path, date, dates, parsefiles[recording], recording)
        except:
            continue
        frames = wav.readframes(-1)
        sig = np.fromstring(frames, "Int16")
        #Decimate the wav signal for parsing
        dsarray = signal.decimate(sig, 36)
        #pxx is the periodograms, freqs is the frequencies
        pxx, freqs, times, img = plt.specgram(dsarray, NFFT = 1024, noverlap = 512, Fs = 1225)
        #Save the data for later use.
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
    #Actually do the NMF computation
    t2 = time()
    print("Data gathering complete. Doing nonnegative matrix factorization.")
    estimator = decomposition.NMF(init = 'nndsvd', max_iter=10000, random_state = 327)
    print("Fitting the model to your data...")
    print("This may take some time...")
    w = estimator.fit_transform(data)
    h = estimator.components_
    t3 = time()
    print(t3 - t2)
    #Save the dot product of the 2 matrices, the reconstruction error, the transformed data matrix, and the component matrix into a file called "NMFdata_xxx.npy"
    saveddata = [np.dot(w,h), estimator.reconstruction_err_, w, h]
    print("Saving results...")
    pickle.dump(saveddata, open(save_dir + "/NMFdata_" + str(limit) + ".pkl", "wb"), protocol = 2)
    print("Done.")
    print(time() - t0)

'''
Visualize the components of the factorized matrix in 3D space.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.
'''
def NMF_plot3d(path):
    t0 = time()
    #Load the multiplied matrix
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[0]
    fig = plt.figure()
    ax = fig.add_subplot(111, projection = '3d')
    #Plot the 3D figure using the first 3 dimensions
    ax.scatter(components[:, 0], components[:, 1], components[:, 2])
    #Set the axis to scientific notation
    ax.xaxis.get_major_formatter().set_powerlimits((0,1))
    ax.yaxis.get_major_formatter().set_powerlimits((0,1))
    fig.suptitle("3D Visualization of Data")
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()

'''
Visualize the components of the factorized matrix in 2D space.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.

The dims parameter is the number of dimensions to visualize.
'''
def NMF_plot2d(path, dims = 2):
    t0 = time()
    #Load the multiplied matrix
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[0]
    fig = plt.figure()
    pos = 1
    dims = int(dims)
    #Plot the number of dimensions, from dim 1 to provided parameter.
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
    fig.suptitle("2D Visualization of Data")
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()

'''
Visualize the W matrix using 2D histograms.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.

The dims parameter is the number of dimensions to visualize.
'''
def NMF_plotW(path, dims = 2):
     t0 = time()
     #Load the multiplied matrix
     pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
     components = pickledData[2]
     fig = plt.figure()
     pos = 1
     dims = int(dims)
     #Plot the number of dimensions, from dim 1 to provided parameter.
     for y in range(dims):
         print("Loading dimension " + str(y + 1) + ".")
         for x in range(dims):
             ax = fig.add_subplot(dims, dims, pos)
             pos += 1
             if x != y:
                 #Plot data for 2D histogram
                 a, b, c = np.histogram2d(components[:,x], components[:,y], bins = 40)
                 a = np.flipud(np.rot90(a))
                 mesh = plt.pcolormesh(b,c,np.ma.masked_where(a == 0, a))
             else:
                 plt.hist(components[:,x], bins = 50)
             #Set the axis to scientific notation
             ax.xaxis.get_major_formatter().set_powerlimits((0,1))
             ax.yaxis.get_major_formatter().set_powerlimits((0,1))
     print("Time to graph items: " + str(time() - t0) + " sec.")
     fig.subplots_adjust(right = 0.8)
     fig.suptitle("2D Histograms of W")
     cax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
     fig.colorbar(mesh, cax = cax)
     plt.show()
     plt.close()

'''
Visualize the H matrix of the NMF using a density plot.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.

The dims parameter is the number of dimensions to visualize.
'''
def NMF_plotH(path, dims = 2):
    t0 = time()
    #Load the multiplied matrix
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[3]
    fig = plt.figure()
    pos = 1
    dims = int(dims)
    factors = [num for num in range(1, int(dims / 2) + 1) if not dims % num] + [dims]
    #Plot the number of dimensions, from dim 1 to provided parameter.
    for x in range(dims):
        print("Loading dimension " + str(x + 1) + ".")
        ax = fig.add_subplot(dims/factors[int(len(factors)/2) - 1], dims/factors[int(len(factors) / 2)], pos)
        pos += 1
        #Plot density plots
        den = stats.kde.gaussian_kde(components[:,x])
        den.covariance_factor = lambda : .25
        den._compute_covariance()
        #lin = np.linspace(0, int(np.max(components[:,x])), 200)
        lin = range(0, len(components))
        plt.plot(lin, components[:,x])
        #plt.plot(lin, den(lin))
        #Set the axis to scientific notation
        ax.xaxis.get_major_formatter().set_powerlimits((0,1))
        ax.yaxis.get_major_formatter().set_powerlimits((0,1))
    fig.suptitle("Density Plots of H")
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()


'''
Used to run through command prompt instead of python console.
'''
if __name__ == "__main__":
    passed = True
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
        print("Third parameter is the date to analyze (OPTIONAL)")
        print("Fourth parameter is the number of files desired (OPTIONAL)")


