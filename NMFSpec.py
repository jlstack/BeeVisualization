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
from sklearn import preprocessing
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
from datetime import datetime

"""
Pads end of hex with 0s to make it length 8.  The padded number is returned.

The hex_num parameter is the number to be padded
"""
def make_hex8(hex_num):
    for i in range(0, 8 - len(hex_num)):
        hex_num += "0"
    return hex_num

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
    Ex: 2015-05-05 00:00:00 2015-05-05 00:00:00 pit1 left
    """
    start_datetime = datetime.now()
    spec_dir = "/usr/local/bee/beemon/beeW/Luke/numpy_specs/%s/"
    start_hex, start_dir = Dates.to_hex(start_date, start_time)
    end_hex, end_dir = Dates.to_hex(end_date, end_time)
    cols = int(end_hex, 16) - int(start_hex, 16)
    combined_spec = np.empty((2049, cols))
    combined_spec[:] = 0
    for i in range(int(start_hex[:5], 16), int(end_hex[:5], 16) + 1):
        i_hex = '{:05x}'.format(i)
        d = '/'.join(i_hex) + '/'
        if os.path.isfile(spec_dir % pit + d + i_hex + '_' + channel + '.npz'):
            print(spec_dir % pit + d + i_hex + '_' + channel + '.npz')
            npz_file = np.load(spec_dir % pit + d + i_hex + '_' + channel + '.npz')
            if start_hex[:5] == end_hex[:5] and start_hex[:5] == i_hex:
                start_col = int(start_hex, 16) - int(make_hex8(start_hex[:5]), 16)
                end_col = int(end_hex, 16) - int(make_hex8(start_hex[:5]), 16)
                npz_file['intensities'][:, start_col:end_col + 1]
                combined_spec[:, :(end_col - start_col)] = npz_file['intensities'][:, start_col:end_col]
            elif start_hex[:5] == i_hex:
                start_col = int(start_hex, 16) - int(make_hex8(start_hex[:5]), 16)
                end_col = npz_file['intensities'][:, start_col:].shape[1]
                combined_spec[:, 0:end_col] = npz_file['intensities'][:, start_col:]
            elif end_hex[:5] == i_hex:
                start_col = int(make_hex8(i_hex), 16) - int(start_hex, 16)
                end_col = int(end_hex, 16) - int(make_hex8(i_hex), 16)
                combined_spec[:, start_col:] = npz_file['intensities'][:, :end_col]
            else:
                start_col = int(make_hex8(i_hex), 16) - int(start_hex, 16)
                end_col = npz_file['intensities'].shape[1]
                combined_spec[:, start_col:start_col + end_col] = npz_file['intensities'][:, :]
            npz_file.close()
    print("time to retrieve data:", datetime.now() - start_datetime)
    a = np.asarray(combined_spec)
    new_spec = np.zeros((math.ceil(len(a)/2), len(a[0])))
    newRows = range(0,math.floor(len(a)/2)*2, 2)
    for i in newRows:
        b = np.mean(a[i:i+2, :], axis=0)
        b = b.reshape((len(b), 1))
        b = b.T
        new_spec[i/2, :] = b.ravel()
    if len(a) % 2 != 0:
        new_spec[-1,:] = a[-1,:].ravel()
    #new_spec = new_spec[:, ~np.all(np.isnan(new_spec), axis=0)]
    #new_spec = np.nan_to_num(new_spec)
    new_spec = (new_spec - np.amin(new_spec)) / (np.amax(new_spec) - np.amin(new_spec))
    print(np.amin(new_spec))
    print(np.amax(new_spec))
    return new_spec

"""
This function computes NMF on a time interval.  The 2D matrix of data used to compute NMF is returned.

The start_date parameter is the date of the first file.
The start_time parameter is the start time of the first file.
The end_date parameter is the date of the last file.
The end_time parameter is the start time of the last file.
The pit parameter is the pit to choose from.
The channel parameter is left or right mic (ALWAYS left for pit2).
The components parameter is the number of components for the nonnegative matrix factorization.
The save parameter is whether or not to save. Default is false.
"""
def NMF_interval(start_date, start_time, end_date, end_time, pit, channel, components, save = False):
    t0 = time()
    newstart_date = start_date.split('-')[::-1]
    newstart_date = '-'.join(newstart_date)
    newend_date = end_date.split('-')[::-1]
    newend_date = '-'.join(newend_date)
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + newstart_date + "/" + components + "comp/"
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    components = int(components)
    data = create_specgrams(start_date, start_time, end_date, end_time, pit, channel)
    data = data.T
    print(data.shape)
    t1 = time()
    print("Data gathering complete. Doing nonnegative matrix factorization.")
    estimator = decomposition.NMF(n_components = components, init = 'nndsvdar', max_iter = 1000, nls_max_iter = 50000, random_state = 327, tol = 0.002)
    print("Fitting the model to your data...")
    print("This may take some time...")
    w = estimator.fit_transform(data)
    h = estimator.components_
    t2 = time()
    print(t2 - t1)
    saveddata = [np.dot(w,h), estimator.reconstruction_err_, w, h]
    if save is True:
        print("Saving results...")
        pickle.dump(saveddata, open(save_dir + "NMFdata_" + start_time+ "_" + newend_date + "_" + end_time + ".pkl", "wb"), protocol = 2)
    print("Done.")
    print(time() - t0)

"""
This function takes the two 'clusters' of data at approximately - Hz and - Hz, and averages the intensities
for the two 'clusters'.  Then, the two lines are plotted for the time interval given.

The pit parameter is the pit to choose from.
The start_date parameter is the date of the first file.
The start_time parameter is the start time of the first file.
The end_date parameter is the date of the last file.
The end_time parameter is the start time of the last file.
The channel parameter is left or right mic (ALWAYS left for pit2).
The components parameter is the number of components.
"""
def avg_frequencies(pit, start_date, start_time, end_date, end_time, channel, components):
    newstart_date = start_date.split('-')[::-1]
    newstart_date = '-'.join(newstart_date)
    newend_date = end_date.split('-')[::-1]
    newend_date = '-'.join(newend_date)
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + start_date + "/" + components + "comp/"
    avg_freqs = np.zeros((24, 2))
    for i in range(24):
        intstr = "%02d" % i
        path = save_dir + "NMFdata_" + intstr + ":00:00_" + end_date + "_" + intstr + ":59:59" + ".pkl"
        if not os.path.isfile(path):
            NMF_interval(newstart_date, intstr + ":00:00", newstart_date, intstr + ":59:59", pit, channel, components, True)
        pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
        H = pickledData[3]
        H = np.asarray(H)
        H = H.T
        avg_freqs[i, 0] = np.mean(H[180:370, :])
        avg_freqs[i, 1] = np.mean(H[370:560, :])
    print(avg_freqs)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.plot(avg_freqs)
    ax.xaxis.set_label_text("Time in Hours")
    ax.yaxis.set_label_text("Average Intensities")
    plt.title("Average Frequencies for " + start_date)
    plt.show()
    plt.close()

'''
Visualize the W matrix using 2D histograms.

The pit parameter is the pit to choose from.
The st_date parameter is the date of the first file.
The end_date parameter is the date of the last file.
The end_time parameter is the start time of the last file.
The comp parameter is the number of components.
The dims parameter is the number of dimensions to visualize.
'''
def NMF_intplotW(pit, st_date, st_time, end_date, end_time, comp, dims = 2):
     t0 = time()
     path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + st_date + "/" + comp + "comp/NMFdata_" + st_time + '_' + end_date + "_" + end_time + ".pkl"
     #Load the multiplied matrix
     pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
     components = pickledData[2]
     print(components.shape)
     fig = plt.figure()
     ax = fig.add_subplot(111)
     lin = range(0, len(components))
     plt.plot(lin, components[:, :dims])
     ax.xaxis.set_ticks(np.arange(0, len(components)+1, int((len(components)-(len(components)%100))/5)))
     ax.xaxis.set_label_text("Time in Seconds")
     ax.yaxis.set_label_text("Intensity")
     plt.xlim((0, len(components)))
     #Limit the y-axis to the same scale for each subplot
     maxht = np.amax(components[:, :dims])
     if np.amax(maxht) < .002:
         plt.ylim((0, maxht))
     else:
         plt.ylim((0, .002))
     plt.title("Density Plots of W for " + st_date + " " + st_time + " to " + end_date + " " + end_time, fontsize = 20)
     print("Time to graph items: " + str(time() - t0) + " sec.")
     plt.show()
     plt.close()

'''
Visualize the H matrix of the NMF using a density plot.

The pit parameter is the pit to choose from.
The st_date parameter is the date of the first file.
The end_date parameter is the date of the last file.
The end_time parameter is the start time of the last file.
The comp parameter is the number of components.
The dims parameter is the number of dimensions to visualize.
'''
def NMF_intplotH(pit, st_date, st_time, end_date, end_time, comp, dims = 2):
    t0 = time()
    path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + st_date + "/" + comp + "comp/NMFdata_" + st_time + '_' + end_date + "_" + end_time + ".pkl"
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
    plt.title("Density Plots of H for " + st_date + " " + st_time + " to " + end_date + " " + end_time, fontsize = 20)
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()

'''
-----------OLD FUNCTIONS-----------
'''

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
        print(path)
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
def old_create_specgrams(start_date, start_time, end_date, end_time, pit, channel):
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
    new_spec = (combined_spec - np.amin(combined_spec)) / (np.amax(combined_spec) - np.amin(combined_spec))
    print(np.amin(new_spec))
    print(np.amax(new_spec))
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
    #specgram_viewer(parsefiles, path, pit, date, dates, newdate)
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
def NMF_oldplotW(pit, date, hour, comp, dims = 2):
     t0 = time()
     path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + date + "/" + comp + "comp/NMFdata" + hour + "_" + comp + ".pkl"
     #Load the multiplied matrix
     pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
     components = pickledData[2]
     print(components.shape)
     fig = plt.figure()
     ax = fig.add_subplot(111)
     lin = range(0, len(components))
     plt.plot(lin, components[:, :dims])
     ax.xaxis.set_ticks(np.arange(0, len(components), int((len(components)-(len(components)%100))/5)))
     ax.xaxis.set_label_text("Time in Seconds")
     ax.yaxis.set_label_text("Intensity")
     plt.xlim((0, len(components)))
     #Limit the y-axis to the same scale for each subplot
     maxht = np.amax(components[:, :dims])
     if np.amax(maxht) < .002:
         plt.ylim((0, maxht))
     else:
         plt.ylim((0, .002))
     plt.title("Density Plots of W for " + str(date) + " Hour " + str(hour), fontsize = 20)
     print("Time to graph items: " + str(time() - t0) + " sec.")
     plt.show()
     plt.close()

'''
Visualize the H matrix of the NMF using a density plot.

The path parameter is the path to the NMFdata_xx.pkl file to visualize.
The dims parameter is the number of dimensions to visualize.
'''
def NMF_oldplotH(pit, date, hour, comp, dims = 2):
    t0 = time()
    path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + date + "/" + comp + "comp/NMFdata" + hour + "_" + comp + ".pkl"
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
    plt.title("Density Plots of H for " + str(date) + " Hour " + str(hour), fontsize = 20)
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()

'''
Used to run through command prompt instead of python console.
'''
def main():
    answer = input("Are you using a time interval?")
    if 'n' in answer or 'N' in answer:
        params = input("Put in your parameters.")
        if len(params) == 3:
            NMF_dir(params[0], params[1], params[2])
        elif len(params) == 4:
            if '-' in params[3]:
                NMF_dir(params[0], params[1], params[2], date=params[3])
            else:
                NMF_dir(params[0], params[1], params[2], components=params[3])
        elif len(params) == 5:
            NMF_dir(params[0], params[1], params[2], components=params[3], date=params[4])
        elif len(params) == 6:
            NMF_dir(params[0], params[1], params[2], components=params[3], date=params[4], limit=params[5])
        else:
            print("Called with wrong number of parameters.")
            print("First parameter is the path to the files (REQUIRED)")
            print("Second parameter is the pit to analyze (REQUIRED)")
            print("Third parameter is the hour to get data from (REQUIRED)")
            print("Fourth parameter is the number of components (OPTIONAL)")
            print("Fifth parameter is the date (OPTIONAL)")
            print("Sixth parameter is the limit for number of files (OPTIONAL)")
            main()
    elif 'y' in answer or 'Y' in answer:
        print("PARAMETERS ARE: Start Date, Start Time, End Date, End Time, Pit, Channel, and Components")
        print("Dates are in the format: YYYY-MM-DD, Times are in the format: HH:MM:SS")
        print("Pit is in the format: pitX, where X is the pit no., Channel is left or right, Components is an int")
        params = input("Put in the 7 parameters separated by spaces.")
        sd, st, ed, et, pit, chan, comp = params.split()
        NMF_interval(sd, st, ed, et, pit, chan, comp, True)
    else:
        print("UNCLEAR. Please type an answer with a 'y' in it for yes, or a 'n' in it for no.")
        print("But, do not do both.")
        main()

if __name__ == "__main__":
    main()

