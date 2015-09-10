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
            try:
                audiofiles = os.listdir(path)
            except:
                audiofiles = []
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
            try:
                audiofiles= os.listdir(path + "/audio/")
            except:
                audiofiles = []
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
        parsefiles = sorted(parsefiles)
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
    new_spec = np.zeros((len(a),math.ceil(len(a[0])/2)))
    newColumns = range(0,math.floor(len(a[0])/2)*2, 2)
    for i in newColumns:
        b=np.mean(a[:,i:i+2], axis=1)
        b = b.reshape((1,len(b)))
        b = b.T
        new_spec[:,i/2] = b.ravel()
    if len(a[0]) % 2 != 0:
        new_spec[:,-1] = a[:,-1].ravel()
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
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + str(date) + "/"
    if not os.path.isdir(save_dir + "Left/"):
        os.makedirs(save_dir + "Left/")
    if not os.path.isdir(save_dir + "Right/"):
        os.makedirs(save_dir + "Right/")
    count = 0
    data = []
    start = time()
    numFiles = range(33)
    for recording in numFiles:
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
        columns = range(pxx.shape[1])
        for index in columns:
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
    spec1 = np.asarray(create_specgrams(newdate, "00:00:00", newdate, "00:59:59", pit, "left"))
    print("Got first specgram set")
    spec2 = np.asarray(specgramdata_getter(parsefiles, path, pit, date, dates, newdate))
    print("Got second specgram set")
    fig = plt.figure()
    for x in range(2):
        ax = fig.add_subplot(1, 2, x)
        if x == 0:
            ax.plot(spec1[:,0])
        else:
            ax.plot(spec2[:,0])
    plt.show()
    plt.close()

'''
This function gets the files to be factorized, and
then does nonnegative matrix factorization on the periodograms of the wav file specgrams.

The path parameter is the directory that has the wav files.
The pit parameter is the pit to choose from.
The hour parameter is the hour to get the data from.
The components parameter is the number of components for NMF.
The date parameter is the day to get data from.
The limit parameter is the number of files to include.
'''
def NMF_dir(path, pit, hour, components = 5, date = None, limit = None):
    t0 = time()
    hour = str(hour)
    components = int(components)
    #Get the current directory for data storage, as well as getting the audio path based on input
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + str(date) + "/" + str(components) + "comp/"
    print("Reading audio files...")
    #Make sure the storage directories are there
    if not os.path.isdir("usr/local/bee/beemon/beeW/Chris/" + pit):
        os.makedirs("usr/local/bee/beemon/beeW/Chris/" + pit)
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    if date is not None:
        date = str(date)
        newdate = date.split('-')[::-1]
        newdate = '-'.join(newdate)
    dates, parsefiles, limit, path = audiolist_getter(path, pit, date, limit)
    specgram_viewer(parsefiles, path, pit, date, dates, newdate)
    #Get the recordings and parse them for clustering
    if path == "/usr/local/bee/beemon/beeW/Luke/mp3s/" + pit + "/" + date:
        data = create_specgrams(newdate, hour + ":00:00", newdate, hour + ":59:59", pit, "left")
    else:
        data = specgramdata_getter(parsefiles, path, pit, date, dates, newdate)
    #Actually do the NMF computation
    t2 = time()
    print("Data gathering complete. Doing nonnegative matrix factorization.")
    estimator = decomposition.NMF(n_components = components, init = 'nndsvdar', max_iter = 1000, nls_max_iter = 50000, random_state = 327, tol = 0.002)
    print("Fitting the model to your data...")
    print("This may take some time...")
    w = estimator.fit_transform(data)
    h = estimator.components_
    t3 = time()
    print(t3 - t2)
    #Save the dot product of the 2 matrices, the reconstruction error, the transformed data matrix, and the component matrix into a file called "NMFdata_xxx.npy"
    saveddata = [np.dot(w,h), estimator.reconstruction_err_, w, h]
    print("Saving results...")
    pickle.dump(saveddata, open(save_dir + "NMFdata" + hour + "_" + str(components) + ".pkl", "wb"), protocol = 2)
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
def NMF_plotW(pit, date, hour, comp, dims = 2):
     t0 = time()
     path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + date + "/" + comp + "comp/NMFdata" + hour + "_" + comp + ".pkl"
     #date = path.split("/")[8]
     #t = (path.split("/")[10])[7:9]
     #Load the multiplied matrix
     pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
     components = pickledData[2]
     print(components.shape)
     fig = plt.figure()
     ax = fig.add_subplot(111)
     lin = range(0, len(components))
     plt.plot(lin, components[:, :dims])
     ax.xaxis.set_ticks(np.arange(0, len(components), 250))
     ax.xaxis.set_label_text("Time in Seconds")
     ax.yaxis.set_label_text("Intensity")
     plt.xlim((0, len(components)))
     #Limit the y-axis to the same scale for each subplot
     maxht = np.amax(components[:, :dims])
     if np.amax(maxht) < .002:
         plt.ylim((0, maxht))
     else:
         plt.ylim((0, .002))
     plt.title("Density Plots of W for " + str(date) + " Hour " + str(t), fontsize = 20)
     print("Time to graph items: " + str(time() - t0) + " sec.")
     plt.show()
     plt.close()

'''
Visualize the H matrix of the NMF using a density plot.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.
The dims parameter is the number of dimensions to visualize.
'''
def NMF_plotH(path, dims = 2):
    t0 = time()
    date = path.split("/")[8]
    t = (path.split("/")[10])[7:9]
    #Load the multiplied matrix
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[3]
    components = np.asarray(components)
    components = components.T
    print(components.shape)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    lin = range(0, len(components))
    plt.plot(lin, components[:, :dims])
    ax.xaxis.set_ticks([0, 200, 400, 600, 800, 1000])
    ax.xaxis.set_label_text("Frequencies in Hertz")
    ax.yaxis.set_label_text("Intensity")
    plt.xlim((0, len(components)))
    #Limit the y-axis to the same scale for each subplot
    maxht = np.amax(components[:, :dims])
    if np.amax(maxht) < .005:
        plt.ylim((0, maxht))
    else:
        plt.ylim((0, .005))
    plt.title("Density Plots of H for " + str(date) + " Hour " + str(t), fontsize = 20)
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()


'''
Used to run through command prompt instead of python console.
'''
if __name__ == "__main__":
    passed = True
    if len(sys.argv) == 4:
        NMF_dir(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 5:
        if '-' in sys.argv[4]:
            NMF_dir(sys.argv[1], sys.argv[2], sys.argv[3], date=sys.argv[4])
        else:
            NMF_dir(sys.argv[1], sys.argv[2], sys.argv[3], components=sys.argv[4])
    elif len(sys.argv) == 6:
        NMF_dir(sys.argv[1], sys.argv[2], sys.argv[3], components=sys.argv[4], date=sys.argv[5])
    else:
        print("Called with wrong number of parameters.")
        print("First parameter is the path to the files (REQUIRED)")
        print("Second parameter is the pit to analyze (REQUIRED)")
        print("Third parameter is the hour to get data from (REQUIRED)")
        print("Fourth parameter is the number of components (OPTIONAL)")
        print("Fifth parameter is the date (OPTIONAL)")


