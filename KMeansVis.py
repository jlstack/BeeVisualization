"""

KMeansVis.py

File that visualizes the results gotten from the KMeansSpec.py file.
There is also a plotter function to display the interactive figure.

Saves a file that is the dimension reduction of the data, using PCA.

The plotter_2d function loads a pickle of an interactive plot created
from pyplot.

"""

__author__ = "Chris Smith"

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
from mpl_toolkits.mplot3d import Axes3D
import os
from sklearn.decomposition import PCA
import pickle
import time
from sklearn.metrics import silhouette_samples

'''
Method that reduces the dimensionality of the data.

The pit parameter is the pit to use.

The day parameter is the day whose data you want to parse.

The num1 parameter is the number of clusters.

The num2 parameter is the number of files that was read.

The dims parameter is the number of dimensions to visualize.*OPTIONAL
'''
def dim_red(pit, day, num1, num2, dims=50):
    t0 = time.time()
    print("Getting data...")
    #Load the centroids (should be equivalent to num1)
    dims = int(dims)
    pxx = pickle.load(open("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/clusterdata_" + str(num1) + "_" + str(num2) + ".pkl", "rb"), encoding = 'bytes')
    pxx = np.asarray(pxx[1])
    results = []
    #Get all possible data points
    listL = os.listdir("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/Left/")
    listR = os.listdir("/usr/local/bee/beemon/beeW/Chris/" + pit + "/"       + day + "/Right/")
    finalList = listL + listR
    list.sort(finalList)
    #Get the specified number of files' data (from num2)
    for i in range(num2):
        if "left" in finalList[i]:
            results.append(np.load("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/Left/" + finalList[i]))
        if "right" in finalList[i]:
            results.append(np.load("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/Right/" + finalList[i]))
    #Reduce dimensionality through principal component analysis
    pxx = np.asarray(pxx)
    #Get each column, instead of groups of columns
    newRes = []
    for i in range(len(results)):
        for k in range(len(results[i][0])):
            newRes.append(results[i][:,k])
    for i in pxx:
        newRes.append(i)
    newRes = np.asarray(newRes)
    print("Shape: " + str(newRes.shape))
    print("Reducing dimensionality of the data...")
    pca = PCA(n_components = dims)
    reducedRes = pca.fit_transform(newRes)
    pickle.dump(reducedRes, open("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/clusterdata_" + str(num1) + "_" + str(num2) +  "_reduced.p", "wb"), protocol = 2)
    print("Time to run: " + str(time.time() - t0))

'''
Method that plots the data in a matrix of dimensional plots.

Example for 3D data: (1,1) (2,1) (3,1)
                     (1,2) (2,2) (3,2)
                     (1,3) (2,3) (3,3)

Used as a helper fucntion for plotter.

***DO NOT CALL THIS FUNCTION DIRECTLY. USE PLOTTER_2D TO DO SO.***
'''
def graph_2d(dataArray, lim, name, labels, dims):
    t0 = time.time()
    lim = int(lim)
    dims = int(dims)
    nums = labels[3]
    nums = sorted(nums)
    #Reshape for appending
    labels = labels[0].reshape(len(labels[0]), 1)
    fig = plt.figure()
    fig.suptitle("Image of " + name)
    pos = 1
    #Get the cluster colors for later plotting
    clu_colors = plt.get_cmap("gist_rainbow")
    norm = colors.Normalize(vmin = 0, vmax = lim)
    scalarMap = cm.ScalarMappable(cmap = clu_colors, norm = norm)
    #Organize data points through their cluster numbers
    data = np.append(dataArray[0:len(dataArray)-lim], labels, 1)
    data = data[np.argsort(data[:, -1], kind = 'quicksort')]
    for y in range(dims):
        print("Loading dimension " + str(y + 1) + ".")
        for x in range(dims):
            ax = fig.add_subplot(dims, dims, pos)
            pos += 1
            if x != y:
                index = 0
                #Plot data
                for i in range(lim):
                    plt.scatter(data[index:index + nums[i][1], x], data[index:index + nums[i][1], y], c = scalarMap.to_rgba(i), linewidth = 0.15)
                    index += nums[i][1]
                #If centroid is a data point, it's the cluster color.  Else, it's white.
                for i in range(1, lim + 1):
                    if dataArray[-i] in dataArray[:len(dataArray)-lim]:
                        plt.scatter(dataArray[-i, x], dataArray[-i, y], c = scalarMap.to_rgba(i-1), marker = '^', s = 35)
                    else:
                        plt.scatter(dataArray[-i, x], dataArray[-i, y], c='#ffffff', marker = '^', s = 35)
            else:
                histData, bins, patches = plt.hist(dataArray[:len(dataArray)-lim,x], bins = 10)
                for bin in range(len(bins)-1):
                    if histData[bin] < 100:
                        ax.text(bins[bin] + (bins[bin + 1] - bins[bin])/2, histData[bin] * 1.02, '%d'%int(histData[bin]), fontsize = 10)
                    else:
                        ax.text(bins[bin], histData[bin] * 1.02, '%d'%int(histData[bin]), fontsize = 10)
            ax.xaxis.get_major_formatter().set_powerlimits((0,1))
            ax.yaxis.get_major_formatter().set_powerlimits((0,1))
    print("Time to graph items: " + str(time.time() - t0) + " sec.")
    #Save the interactive visual as a pickle
    plt.show()
    plt.close()

'''
Method that plots the data in a 3D scatter plot.

Used as a helper fucntion for plotter_3d.

***DO NOT CALL THIS FUNCTION DIRECTLY. USE PLOTTER_3D TO DO SO.***
'''
def graph_3d(dataArray, lim, name, labels):
    t0 = time.time()
    lim = int(lim)
    nums = labels[3]
    nums = sorted(nums)
    #Reshape for appending
    labels = labels[0].reshape(len(labels[0]), 1)
    fig = plt.figure()
    fig.suptitle("Image of " + name)
    pos = 1
    #Get the cluster colors for later plotting
    clu_colors = plt.get_cmap("gist_rainbow")
    norm = colors.Normalize(vmin = 0, vmax = lim)
    scalarMap = cm.ScalarMappable(cmap = clu_colors, norm = norm)
    #Organize data points through their cluster numbers
    data = np.append(dataArray[0:len(dataArray)-lim], labels, 1)
    data = data[np.argsort(data[:, -1], kind = 'quicksort')]
    ax = fig.add_subplot(111, projection = '3d')
    index = 0
    for i in range(lim):
        ax.scatter(data[index:index + nums[i][1], 0], data[index:index + nums[i][1], 1], data[index:index + nums[i][1], 2], c=scalarMap.to_rgba(i))
        index += nums[i][1]
    for i in range(1, lim + 1):
        if dataArray[-i] in dataArray[:len(dataArray)-lim]:
            ax.scatter(dataArray[-i, 0], dataArray[-i, 1], dataArray[-i, 2], c = scalarMap.to_rgba(i-1), marker = '^', s = 35)
        else:
            ax.scatter(dataArray[-i, 0], dataArray[-i, 1], dataArray[-i, 2], c='#ffffff', marker = '^', s = 35)
    print("Time to graph items: " + str(time.time() - t0) + " sec.")
    #Save the interactive visual as a pickle
    plt.show()
    plt.close()


'''
Method that helps load the data to be graphed into many 2D plots.

The pit parameter is the pit to choose.

The day parameter is the day to plot.

The clusters parameter is the number of clusters to plot.

The files parameter is the number of files to cluster.

The dims parameter is the number of dimensions to visualize.*OPTIONAL
'''
def plotter_2d(pit, day, clusters, files, dims = 2):
    data = pickle.load(open("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/clusterdata_" + str(clusters) + "_" + str(files) + "_reduced.p", 'rb'), encoding = 'bytes')
    labels = pickle.load(open("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/clusterdata_" + str(clusters) + "_" + str(files) + ".pkl", 'rb'), encoding = 'bytes')
    try:
        if len(labels[0]) < 400:
            silhouettes = silhouette_samples(data, labels[0])
            print(silhouettes)
            print(np.mean(silhouettes))
    except Exception:
        print("Silhouette scoring cannot be done.")
    num1 = int(clusters)
    path1 = "Pit:" + pit + " Day:" + day + " Clusters:" + str(clusters) + " Files:" + str(files)
    graph_2d(data, num1, path1, labels, dims)
    plt.close()

'''
Method that helps load the data to be graphed into a 3D plot.

The pit parameter is the pit to choose.

The day parameter is the day to plot.

The clusters parameter is the number of clusters to plot.

The files parameter is the number of files to cluster.
'''
def plotter_3d(pit, day, clusters, files):
    data = pickle.load(open("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/clusterdata_" + str(clusters) + "_" + str(files) + "_reduced.p", 'rb'), encoding = 'bytes')
    labels = pickle.load(open("/usr/local/bee/beemon/beeW/Chris/" + pit + "/" + day + "/clusterdata_" + str(clusters) + "_" + str(files) + ".pkl", 'rb'), encoding = 'bytes')
    try:
        if len(labels[0]) < 400:
            silhouettes = silhouette_samples(data, labels[0])
            print(silhouettes)
            print(np.mean(silhouettes))
    except Exception:
        print("Silhouette scoring cannot be done.")
    num1 = int(clusters)
    path1 = "Pit:" + pit + " Day:" + day + " Clusters:" + str(clusters) + " Files:" + str(files)
    graph_3d(data, num1, path1, labels)
    plt.close()

