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
from matplotlib import ticker
import os
from time import time
from pydub import AudioSegment
import pickle
import tempfile
from mpl_toolkits.mplot3d import Axes3D
import Dates
import math

'''
This function looks on the path provided for data from
the date given pertaining to the pit that is passed in.

The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The date parameter is the day to get data from.
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
        #Make sure the limit is set
        if limit is None:
            limit = len(audiofiles)
        limit = int(limit)
        parsefiles = audiofiles[:limit]
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
        if limit is None:
            limit = len(audiofiles)
        limit = int(limit)
        parsefiles = audiofiles[:limit]
    return dates, parsefiles, limit, path

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
            if "mp3s" in path:
                sound = AudioSegment.from_file(path +  "/audio/" + filename, "mp3")
            elif "mp3" in path and date is None:
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
This function is designed to get the specgrams from Luke's database of specgrams.
Then, the function combines them into one 2D numpy array for factorization.
This array is returned.

The start_date parameter is the date of the first file.
The start_time parameter is the start time of the first file.
The end_date parameter is the date of the last file.
The end_time parameter is the start time of the last file.
The pit parameter is the pit to choose from.
The channel parameter is left or right mic (ALWAYS left for pit2).
'''
def create_specgrams(start_date, start_time, end_date, end_time, pit, channel):
    """
    Ex: python create_specgram.py 2015-05-05 00:00:00 2015-05-05 00:00:00 pit1 left
    """
    spec_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs2/"
    timer = time()
    combined_spec = []
    start_hex, start_dir = Dates.to_hex(start_date, start_time)
    end_hex, end_dir = Dates.to_hex(end_date, end_time)
    start_int = int(start_hex, 16)
    end_int = int(end_hex, 16)
    for i in range(start_int, end_int+1):
        i_hex = '{:08x}'.format(i)
        i_dir = "/".join(i_hex[:-1]) + "/"
        hex_date, hex_time = Dates.to_date(i_hex)
        fname = spec_dir + pit + "/" + i_dir + i_hex + "_" + hex_date + "T" + hex_time + "_" + channel + ".spec.npy"
        if os.path.isfile(fname):
            data = np.load(fname).item()
            combined_spec.append(data["intensities"])
    a = np.asarray(combined_spec)
    new_spec = np.zeros((len(a),math.ceil(len(a[0])/3)))
    for i in range(0,math.floor(len(a[0])/3)*3, 3):
        b=np.mean(a[:,i:i+3], axis=1)
        b = b.reshape((1,len(b)))
        b = b.T
        new_spec[:,i/3] = b.ravel()
    if len(a[0]) % 3 == 1:
        new_spec[:,-1] = a[:,-1].ravel()
    elif len(a[0]) % 3 == 2:
        b=np.mean(a[:,-2:], axis=1)
        b = b.reshape((1,len(b)))
        b = b.T
        new_spec[:,-1] = b.ravel()
    print(new_spec.shape)
    print(time() - timer)
    return new_spec

'''
This function reads each file from the parsefiles list and gets the data
for the specgrams for each file.  It does this through the wav file itself.
A list of the columns of the specgrams is returned.

The parsefiles parameter is a list of the files to read in.
The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The date parameter is the day to get data from in the form DD-MM-YYYY.
The dates parameter is the list of dates if one day was not chosen.
The newdate parameter is the date in the format YYYY-MM-DD.
'''
def specgramdata_getter(parsefiles, path, pit, date, dates, newdate):
    count = 0
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + str(date) + "/"
    data = []
    start = time()
    for recording in range(len(parsefiles)):
        if count % 100 == 0:
            print(str(count) + " audio files read!")
        try:
            if path == "/usr/local/bee/beemon/beeW/Luke/mp3s/" + pit + "/" + date:
                wav = audiodata_getter(path, newdate, dates, parsefiles[recording], recording)
            else:
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
    print(time() - start)
    print("Number of periodograms: " + str(len(data)))
    return data

'''
This function gets the specgrams and plots them side by side for
comparison.

The parsefiles parameter is a list of the files to read in.
The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The date parameter is the day to get data from in the form DD-MM-YYYY.
The dates parameter is the list of dates if one day was not chosen.
The newdate parameter is the date in the format YYYY-MM-DD.

'''
def specgram_viewer(parsefiles, path, pit, date, dates, newdate):
    spec1 = np.asarray(create_specgrams(newdate, "00:00:00", newdate, "23:59:59", pit, "left"))
    print("Got first specgram set")
    spec2 = np.asarray(specgramdata_getter(parsefiles, path, pit, date, dates, newdate))
    print("Got second specgram set")
    fig = plt.figure(2)
    for x in range(2):
        ax = fig.add_subplot(1, 2, x)
        plt.plot("spec" + str(x+1))
    plt.show()
    plt.close()

'''
This function gets the files to be factorized, and
then does nonnegative matrix factorization on the periodograms of the wav file specgrams.

The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The date parameter is the day to get data from.
The limit parameter is the number of files to include.
'''
def NMF_dir(path, pit, date=None, limit=None):
    t0 = time()
    #Get the current directory for data storage, as well as getting the audio path based on input
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + str(date) + "/"
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
    if date is not None:
        date = str(date)
        newdate = date.split('-')[::-1]
        newdate = '-'.join(newdate)
    dates, parsefiles, limit, path = audiolist_getter(path, pit, date, limit)
    print("Files to parse: " + str(limit))
    #specgram_viewer(parsefiles, path, pit, date, dates, newdate)
    #Get the recordings and parse them for clustering
    if path == "/usr/local/bee/beemon/beeW/Luke/mp3s/" + pit + "/" + date:
        data = create_specgrams(newdate, "00:00:00", newdate, "23:59:59", pit, "left")
    else:
        data = specgramdata_getter(parsefiles, path, pit, date, dates, newdate)
    #Actually do the NMF computation
    t2 = time()
    print("Data gathering complete. Doing nonnegative matrix factorization.")
    estimator = decomposition.NMF(n_components = 10, init = 'nndsvdar', max_iter = 1000, nls_max_iter = 10000, random_state = 327)
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
    fig.suptitle("3D Visualization of Data", fontsize = 20)
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
    dims = int(dims)
    #Load the multiplied matrix
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[0]
    fig = plt.figure(dims + 1)
    pos = 1
    #Plot the number of dimensions, from dim 1 to provided parameter.
    for y in range(dims):
        print("Loading dimension " + str(y + 1) + ".")
        for x in range(dims):
            ax = fig.add_subplot(dims + 1, dims , pos)
            pos += 1
            if x != y:
                #Plot data
                plt.scatter(components[:, x], components[:, y], linewidth = 0.15)
            else:
                plt.hist(components[:,x], bins = 50)
            yticks = ax.get_yticks()
            ax.set_yticks(yticks[::2])
            #Set the axis to scientific notation
            ax.xaxis.get_major_formatter().set_powerlimits((0,1))
            ax.yaxis.get_major_formatter().set_powerlimits((0,1))
            plt.xticks(rotation = 40)
    #Modify the layout so title is on bottom and graph size is maximized
    plt.tight_layout(pad = 0, w_pad = -1, h_pad = -1)
    fig.get_axes()[0].annotate('2D Visualization of Data', (0.5, 0.05), xycoords='figure fraction', ha='center', fontsize=20)
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
     dims = int(dims)
     fig = plt.figure(dims + 1)
     pos = 1
     #Plot the number of dimensions, from dim 1 to provided parameter.
     for y in range(dims):
         print("Loading dimension " + str(y + 1) + ".")
         for x in range(dims):
             ax = fig.add_subplot(dims + 1, dims, pos)
             pos += 1
             if x != y:
                 #Plot data for 2D histogram
                 a, xlims, ylims = np.histogram2d(components[:,x], components[:,y], bins = 500)
                 a = np.flipud(np.rot90(a))
                 mesh = plt.pcolormesh(xlims, ylims, np.ma.masked_where(a == 0, a))
             else:
                 plt.hist(components[:,x], bins = 50)
             yticks = ax.get_yticks()
             ax.set_yticks(yticks[::2])
             #Set the axis to scientific notation
             ax.xaxis.get_major_formatter().set_powerlimits((0,1))
             ax.yaxis.get_major_formatter().set_powerlimits((0,1))
             plt.xticks(rotation = 40)
     plt.tight_layout(pad = 0, w_pad = -1, h_pad = -1)
     print("Time to graph items: " + str(time() - t0) + " sec.")
     fig.get_axes()[0].annotate('2D Histograms of W', (0.5, 0.05), xycoords='figure fraction', ha='center', fontsize=20)
     fig.subplots_adjust(right = 0.8)
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
    dims = int(dims)
    fig = plt.figure(dims + 1)
    pos = 1
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
        #Limit the y-axis to the same scale for each subplot
        plt.ylim((0, 2500))
    #Modify the layout so title is on bottom and graph size is maximized
    plt.tight_layout(pad = 0, w_pad = -1, h_pad = -1)
    fig.get_axes()[0].annotate('Density Plots of H', (0.5, 0.02), xycoords='figure fraction', ha='center', fontsize=20)
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


