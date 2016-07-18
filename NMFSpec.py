"""
NMFSpec.py

This file contains functions to get the audio files
and perform nonnegative matrix factorization on them.  It also contains
functions that enable the user to plot the results of the NMF, as well
as do some analysis on the results, such as finding average intensity over
specified frequency ranges of interest.
"""

__author__ = "Chris Smith"

#Imports for current functions
from sklearn import decomposition
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import os
from time import time
import pickle
import Dates
import math
from datetime import datetime
#Imports for old functions
import wave
from scipy import signal
from pydub import AudioSegment
import tempfile


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
    #Get 4096 seconds of specgram data
    for i in range(int(start_hex[:5], 16), int(end_hex[:5], 16) + 1):
        i_hex = '{:05x}'.format(i)
        d = '/'.join(i_hex[-5:-1]) + '/'
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
    #Take the average of each pair of rows
    for i in newRows:
        b = np.mean(a[i:i+2, :], axis=0)
        b = b.reshape((len(b), 1))
        b = b.T
        new_spec[i/2, :] = b.ravel()
    if len(a) % 2 != 0:
        new_spec[-1,:] = a[-1,:].ravel()
    #new_spec = new_spec[:, ~np.all(np.isnan(new_spec), axis=0)]
    #Normalize the data
    new_spec = np.nan_to_num(new_spec)
    new_spec = (new_spec - np.amin(new_spec)) / (np.amax(new_spec) - np.amin(new_spec))
    #Set the intensity of 0 Hz to 0, as there is an odd spike that throws the NMF off at 0 Hz
    new_spec[0] = 0
    #new_spec[:123] = 0
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
    #Time the function, and put the date in the right format
    t0 = time()
    newstart_date = start_date.split('-')[::-1]
    newstart_date = '-'.join(newstart_date)
    newend_date = end_date.split('-')[::-1]
    newend_date = '-'.join(newend_date)
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + newstart_date + "/" + components + "comp/"
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    components = int(components)
    #Get the spectrograms and do nonnegative matrix factorization on it
    data = create_specgrams(start_date, start_time, end_date, end_time, pit, channel)
    data = data.T
    print(data.shape)
    t1 = time()
    print("Data gathering complete. Doing nonnegative matrix factorization.")
    estimator = decomposition.NMF(n_components = components, init = 'nndsvdar', max_iter = 1000, nls_max_iter = 50000, random_state = 327, tol = 0.01)
    print("Fitting the model to your data...")
    print("This may take some time...")
    #Get the W and H matrices
    w = estimator.fit_transform(data)
    #w = (w - np.amin(w)) / (np.amax(w) - np.amin(w))
    h = estimator.components_
    #h = (h - np.amin(h)) / (np.amax(h) - np.amin(h))
    t2 = time()
    print(t2 - t1)
    saveddata = [np.dot(w,h), estimator.reconstruction_err_, w, h]
    #Save the data if wanted
    if save is True:
        print("Saving results...")
        pickle.dump(saveddata, open(save_dir + "NMFdata_" + start_time + "_" + newend_date + "_" + end_time + ".pkl", "wb"), protocol = 2)
    print("Done.")
    print(time() - t0)

"""
This function computes NMF on a time interval.  The 2D matrix of data used to compute NMF is returned.

The date parameter is the date of the desired analysis.
The start_time parameter is the start time of the desired interval.
The pit parameter is the pit to choose from.
The channel parameter is left or right mic (ALWAYS left for pit2).
The components parameter is the number of components for the nonnegative matrix factorization.
The save parameter is whether or not to save. Default is false.
"""
def implemented_NMF(date, start_time, pit, channel, components, save = False):
    new_date = date.split('-')[::-1]
    new_date = '-'.join(new_date)
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + new_date + "/" + components + "comp/"
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    components = int(components)
    end_time = start_time.split(':')[0] + ":59:59"
    #Get the spectrograms as a 2D array, and transpose it so the ind. sound sources are found with NMF
    data = create_specgrams(date, start_time, date, end_time, pit, channel).T
    print("Data has shape: " + str(data.shape))
    t0 = time()
    #NMF algorithm
    a = 0.0002
    b = 0.02
    thres = 3000
    np.random.seed(327)
    w = np.random.rand(len(data), components)
    h = np.random.rand(components, len(data[0]))
    for iteration in range(100):
        print("Iteration " + str(iteration))
        error = 0
        estimated = np.dot(w, h)
        for i in range(len(data)):
            for j in range(len(data[0])):
                if data[i][j] != 0:
                    ind_error = data[i][j] - estimated[i][j]
                    error += math.pow(ind_error, 2)
                    for k in range(components):
                        w[i][k] += a * (2 * ind_error * h[k][j] - b * w[i][k])
                        h[k][j] += a * (2 * ind_error * w[i][k] - b * h[k][j])
                        
                        if w[i][k] < 0:
                            w[i][k] = 0
                        if h[k][j] < 0:
                            h[k][j] = 0
                       
                        error += ((b / 2) * (math.pow(w[i][k], 2) + math.pow(h[k][j], 2)))
        print("Error: %.3f" % error)
        if error < thres:
            break
    print("NMF complete.")
    saveddata = [estimated, error, w, h]
    #Save if wanted to be saved
    if save is True:
        print("Saving results...")
        pickle.dump(saveddata, open(save_dir + "NMFdata_" + start_time + "_" + new_date + "_" + end_time + ".pkl", "wb"), protocol = 2)
    print("Done in " + str("%.3f" % float(time() - t0)) + " seconds")
    return estimated


"""
This function takes the two 'clusters' of data at approximately 180-369 Hz and 370-559 Hz, and averages the
intensities for the two 'clusters'.  Then, the two lines are plotted for the time interval given.

The pit parameter is the pit to choose from.
The start_date parameter is the date of the first file. (DD-MM-YYYY)
The start_time parameter is the start time of the first file.
The end_date parameter is the date of the last file. (DD-MM-YYYY)
The end_time parameter is the start time of the last file.
The channel parameter is left or right mic (ALWAYS left for pit2).
The components parameter is the number of components.
The pic parameter is whether or not to show the graph afterwards (default is False).
"""
def avg_intensities(pit, start_date, start_time, end_date, end_time, channel, components, pic=False):
    #Put the dates in the right format
    newstart_date = start_date.split('-')[::-1]
    newstart_date = '-'.join(newstart_date)
    newend_date = end_date.split('-')[::-1]
    newend_date = '-'.join(newend_date)
    graph_date = '-'.join(list(reversed(start_date.split("-")[0:2])))+"-"+"".join(start_date.split("-")[2])
    graph_time = start_time
    end_date = '-'.join(list(reversed(end_date.split("-")[0:2])))+"-"+"".join(end_date.split("-")[2])
    #Get the elapsed time
    elapsed_time = Dates.time_diff(newstart_date, start_time, newend_date, end_time)
    hours_elapsed = math.ceil(elapsed_time / 3600)
    save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + start_date + "/" + components + "comp/"
    first_hour = int(start_time.split(':')[0])
    days_elapsed = math.ceil((hours_elapsed + first_hour) / 24)
    avg_freqs = np.zeros((hours_elapsed + first_hour, 2))
    #Get data for each hour, and add it to the figure
    for i in range(first_hour, hours_elapsed + first_hour):
        intstr = "%02d" % (i % 24)
        path = save_dir + "NMFdata_" + intstr + ":00:00_" + start_date + "_" + intstr + ":59:59" + ".pkl"
        try:
            if not os.path.isfile(path) or os.path.isfile(path):
                NMF_interval(newstart_date, intstr + ":00:00", newstart_date, intstr + ":59:59", pit, channel, components, True)
            pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
            H = pickledData[3]
            H = np.asarray(H)
            H = H.T
            #Get frequency ranges 180-369 Hz and 370-559 Hz
            avg_freqs[i, 0] = np.mean(H[180:370, :])
            avg_freqs[i, 1] = np.mean(H[370:560, :])
        except:
            print("Invalid data for " + newstart_date + " " + intstr + " hour")
        #Increments date for one day, and sets time to 00:00:00
        if(i % 24 == 23):
            print("Success for " + newstart_date)
            if(i == 23):
                newstart_date, start_time = Dates.add_seconds_to_date(newstart_date, start_time, 86400 - first_hour * 3600)
            else:
                newstart_date, start_time = Dates.add_seconds_to_date(newstart_date, start_time, 86400)
            start_date = newstart_date.split('-')[::-1]
            start_date = '-'.join(start_date)
            save_dir = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + start_date + "/" + components + "comp/"
    fig = plt.figure()
    ax = plt.subplot(111)
    #Print out information pertaining to day/night for each day
    try:
        for i in range(days_elapsed):
            #8 AM of day i, 10 PM of day i, 12 AM of day i, and 12 AM for day i+1
            ei = 24 * i + 8
            tti = 24 * i + 22
            zi = 24 * i
            tfi = 24 * (i + 1)
            print('-----TIME SENSITIVE INTENSITIES FOR DAY ' + str(i) + '-----')
            print('Low freqs day: ' + '{:.7f}'.format(np.average(avg_freqs[ei:tti, 0], weights = avg_freqs[ei:tti, 0].astype(bool))))
            print('High freqs day: ' + '{:.7f}'.format(np.average(avg_freqs[ei:tti, 1], weights = avg_freqs[ei:tti, 1].astype(bool))))
            night0 = np.hstack((avg_freqs[zi:ei, 0], avg_freqs[tti:tfi, 0]))
            night1 = np.hstack((avg_freqs[zi:ei, 1], avg_freqs[tti:tfi, 1]))
            try:
                lownight = np.average(night0[:], weights = night0[:].astype(bool))
                hinight = np.average(night1[:], weights = night1[:].astype(bool))
            except:
                lownight = 0
                hinight = 0
            print('Low freqs night: ' + '{:.7f}'.format(lownight))
            print('High freqs night: ' + '{:.7f}'.format(hinight))
        print('-----INTENSITY TOTALS-----')
        print('Low freqs total: ' + '{:.7f}'.format(np.average(avg_freqs[:, 0], weights = avg_freqs[:,0].astype(bool))))
        print('High freqs total: ' + '{:.7f}'.format(np.average(avg_freqs[:, 1], weights = avg_freqs[:,1].astype(bool))))
    except:
        continue
    #Plot both frequency ranges
    plt.plot(avg_freqs[:,0], color = '#ff8800', label = '180 - 369 Hz')
    plt.plot(avg_freqs[:,1], color = '#0088ff', label = '370 - 559 Hz')
    ax.xaxis.set_label_text("Time in Hours")
    ax.yaxis.set_label_text("Average Intensities")
    plt.title("Average Intensities for " + graph_date + " " + graph_time + " to " + end_date + " " + end_time)
    ax.legend(loc = 'upper center', bbox_to_anchor = (.5, -.1), ncol = avg_freqs.shape[1])
    current = ax.get_position()
    ax.set_position([current.x0, current.y0 + current.width * .05, current.width, current.height * .95])
    #Show if pic is True
    if(pic):
        plt.show()
    plt.close()

'''
Visualize the W matrix using 2D histograms.

The pit parameter is the pit to choose from.
The start_date parameter is the date of the first file. (DD-MM-YYYY)
The start_time parameter is the start time of the first file.
The end_date parameter is the date of the last file. (DD-MM-YYYY)
The end_time parameter is the last second desired.
The comp parameter is the number of components.
The dims parameter is the number of dimensions to visualize.
'''
def NMF_intplotW(pit, start_date, start_time, end_date, end_time, comp, dims = 2):
     t0 = time()
     path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + start_date + "/" + comp + "comp/NMFdata_" + start_time + '_' + end_date + "_" + end_time + ".pkl"
     #Load the multiplied matrix
     pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
     components = pickledData[2]
     print(components.shape)
     fig = plt.figure()
     ax = plt.subplot(111)
     lin = range(0, len(components))
     #Make a colormap for the lines, so that each dimension gets a unique color
     linecolors = colormap_lines(dims)
     for i in range(dims):
         ax.plot(lin, components[:, i], label = 'Spec. ' + str(i), color = linecolors[i])
     ax.xaxis.set_ticks(np.arange(0, len(components)+1, int((len(components)-(len(components)%100))/5)))
     ax.xaxis.set_label_text("Time in Seconds")
     ax.yaxis.set_label_text("Intensity")
     #Get the current position of the axes, and set the axes to be higher up for the legend
     current = ax.get_position()
     ax.set_position([current.x0, current.y0 + current.width * .15, current.width, current.height * .9])
     #Plot the legend underneath the x-axis
     ax.legend(loc = 'upper center', bbox_to_anchor = (.5, -.1), ncol = math.floor(math.sqrt(dims)+1))
     plt.xlim((0, len(components)))
     #Limit the y-axis to the same scale for each subplot
     maxht = np.amax(components[:, :dims])
     if np.amax(maxht) < 1:
         plt.ylim((0, maxht))
     else:
         plt.ylim((0, 1))
     plt.title("Density Plots of W for " + start_date + " " + start_time + " to " + end_date + " " + end_time, fontsize = 20)
     print("Time to graph items: " + str(time() - t0) + " sec.")
     plt.show()
     plt.close()

'''
Visualize the H matrix of the NMF using a density plot.

The pit parameter is the pit to choose from.
The start_date parameter is the date of the first file. (DD-MM-YYYY)
The start_time parameter is the start time of the first file.
The end_date parameter is the date of the last file. (DD-MM-YYYY)
The end_time parameter is the last second desired.
The comp parameter is the number of components.
The dims parameter is the number of dimensions to visualize.
'''
def NMF_intplotH(pit, start_date, start_time, end_date, end_time, comp, dims = 2):
    t0 = time()
    path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + start_date + "/" + comp + "comp/NMFdata_" + start_time + '_' + end_date + "_" + end_time + ".pkl"
    #Load the multiplied matrix
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    components = pickledData[3]
    components = np.asarray(components)
    components = components.T
    print(components.shape)
    fig = plt.figure()
    ax = plt.subplot(111)
    lin = range(0, len(components))
    #Make a colormap for the lines, so that each dimension gets a unique color
    linecolors = colormap_lines(dims)
    for i in range(dims):
        ax.plot(lin, components[:, i], label = 'Spec. ' + str(i), color = linecolors[i])
    ax.xaxis.set_ticks([0, 200, 400, 600, 800, 1000])
    ax.xaxis.set_label_text("Frequencies in Hertz")
    ax.yaxis.set_label_text("Intensity")
    #Get the current position of the axes, and set the axes to be higher up for the legend
    current = ax.get_position()
    ax.set_position([current.x0, current.y0 + current.width * .15, current.width, current.height * .9])
    #Plot the legend underneath the x-axis
    ax.legend(loc = 'upper center', bbox_to_anchor = (.5, -.1), ncol = math.floor(math.sqrt(dims)+1))
    plt.xlim((0, len(components)))
    #Limit the y-axis to the same scale for each subplot
    maxht = np.amax(components[:, :dims])
    if np.amax(maxht) < 1:
        plt.ylim((0, maxht))
    else:
        plt.ylim((0, 1))
    plt.title("Density Plots of H for " + start_date + " " + start_time + " to " + end_date + " " + end_time, fontsize = 20)
    print("Time to graph items: " + str(time() - t0) + " sec.")
    plt.show()
    plt.close()

'''
This function creates and returns a normalized array based on the number of dimensions requested.
It uses the spectral colormap from matplotlib's database of colormaps.  This allows the map to be
diverse in the actual mapped colors.

The lim parameter is the number of spectra being plotted.
'''
def colormap_lines(lim):
    clu_colors = plt.get_cmap("spectral")
    norm = colors.Normalize(vmin = 0, vmax = lim)
    scalarMap = cm.ScalarMappable(cmap = clu_colors, norm = norm)
    linecolors = scalarMap.to_rgba(range(lim))
    return linecolors

'''
This function plots both H and W side by side.  This becomes useful for comparative purposes.

The pit parameter is the pit to choose from.
The start_date parameter is the date of the first file.
The start_time parameter is the start time of the first file.
The end_date parameter is the date of the last file.
The end_time parameter is the last second desired.
The comp parameter is the number of components.
The dims parameter is the number of dimensions to visualize.
'''
def plotInterval(pit, start_date, start_time, end_date, end_time, comp, dims = 2):
    path = "/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + start_date + "/" + comp + "comp/NMFdata_" + start_time + '_' + end_date + "_" + end_time + ".pkl"
    pickledData = pickle.load(open(path, 'rb'), encoding = 'bytes')
    h = pickledData[3]
    h = np.asarray(h)
    h = h.T
    lin = range(0, len(h))
    #Plot H
    ax = plt.subplot(121)
    ax.set_title("H", fontsize = 10)
    linecolors = colormap_lines(dims)
    for i in range(dims):
        ax.plot(lin, h[:, i], label = 'Spec. ' + str(i), color = linecolors[i])
    ax.xaxis.set_ticks([0, 200, 400, 600, 800, 1000])
    ax.xaxis.set_label_text("Frequencies in Hertz")
    ax.yaxis.set_label_text("Intensity")
    #Get the current position of the axes, and set the axes to be higher up for the legend
    current = ax.get_position()
    ax.set_position([current.x0, current.y0 + current.width * .3, current.width, current.height * .9])
    ax.set_xlim([0, len(h)])
    if np.amax(h[:,:dims]) > 1:
        ax.set_ylim([0, 1])
    #Plot W
    ax = plt.subplot(122)
    ax.set_title("W", fontsize = 10)
    w = pickledData[2]
    lin = range(0, len(w))
    #Make a colormap for the lines, so that each dimension gets a unique color
    for i in range(dims):
        ax.plot(lin, w[:, i], label = 'Spec. ' + str(i), color = linecolors[i])
    ax.xaxis.set_ticks(np.arange(0, len(w)+1, int((len(w)-(len(w)%100))/5)))
    ax.xaxis.set_label_text("Time in Seconds")
    ax.tick_params(labelright = True, labelleft = False)
    ax.yaxis.set_label_text("Intensity", rotation = 270)
    ax.yaxis.set_label_position("right")
    #Get the current position of the axes, and set the axes to be higher up for the legend
    current = ax.get_position()
    ax.set_position([current.x0, current.y0 + current.width * .3, current.width, current.height * .9])
    ax.set_xlim([0, len(w)])
    if np.amax(w[:,:dims]) > 1:
        ax.set_ylim([0, 1])
    #Plot the legend underneath the x-axis
    plt.legend(loc = 'upper center', bbox_to_anchor = (-.1, -.08), ncol = math.floor(math.sqrt(dims)+1))
    plt.suptitle("Graph of " + start_date + " " + start_time + " to " + end_date + " " + end_time , fontsize = 12)
    plt.show()
    #plt.savefig(start_date + 'T' + start_time + '.png', format='png', dpi = 500)
    plt.close()

'''
Used to run through command prompt instead of python console.
'''
def main():
    params = input("Put in your parameters, separated by spaces.")
    params = params.split()
    if len(params) == 7:
        done = False
        answer = input("Do you want to save the results?")
        while not done:
            answer = input("")
            if ('n' in answer or 'N' in answer) and not ('y' in answer or 'Y' in answer):
                NMF_interval(params[0], params[1], params[2], params[3], params[4], params[5], params[6], False)
                done = True
            elif ('y' in answer or 'Y' in answer) and not ('n' in answer or 'N' in answer):
                NMF_interval(params[0], params[1], params[2], params[3], params[4], params[5], params[6], True)
                done = True
            else:
                print("UNCLEAR. Please type an answer with a 'y' in it for yes, or a 'n' in it for no.")
                print("But, do not do both.")
        answer = input("Do you want to run NMF on more data?")
        if ('y' in answer or 'Y' in answer):
            main()
        else:
            print("Exiting.")
    else:
        print("Called with wrong number of parameters.")
        print("First parameter is the start date")
        print("Second parameter is the start time")
        print("Third parameter is end date")
        print("Fourth parameter is end time")
        print("Fifth parameter is the pit")
        print("Sixth parameter is the channel")
        print("Seventh parameter is the number of components")
        main()

if __name__ == "__main__":
    main()

'''
-----------OLD FUNCTIONS-----------

These functions were used at one time, but are not used anymore.
Some of these functions are handled more efficiently above, or
are done through the use of Luke's functions in a more efficient
manner.
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
    #new_spec = (combined_spec - np.amin(combined_spec)) / (np.amax(combined_spec) - np.amin(combined_spec))
    #print(np.amin(new_spec))
    #print(np.amax(new_spec))
    return combined_spec

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
    spec1 = np.asarray(old_create_specgrams(newdate, "00:00:00", newdate, "00:59:59", pit, "left"))
    print("Got first specgram set")
    spec2 = np.asarray(specgramdata_getter(parsefiles, path, pit, date, dates, newdate))
    print("Got second specgram set")
    fig = plt.figure()
    for x in range(2):
        ax = fig.add_subplot(1, 2, x)
        if x == 0:
            ax.plot(spec1[:])
        else:
            ax.plot(spec2[:])
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
The OLD main
DO NOT USE!
'''
def oldmain():
    answer = input("Are you using a time interval?")
    if 'n' in answer or 'N' in answer:
        params = input("Put in your parameters.")
        params = params.split()
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

