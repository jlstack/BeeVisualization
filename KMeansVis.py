"""

KMeansVis.py

File that visualizes the results gotten from the KMeansSpec.py file.

Saves a file that is the 2D representation of the clusters, as well as
their points.

"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
from sklearn.decomposition import PCA

'''
Method that visualizes the cluster centers, as well as the points in question.
The path1 parameter is the path to the data that was used.
'''
def visualizer(path1):
    print "Getting data..."
    pxx = np.load(path1)
    pxx = pxx[1]
    results = []
    listL = os.listdir(os.getcwd() + "/SpecgramData/Left/")
    listR = os.listdir(os.getcwd() + "/SpecgramData/Right/")
    finalList = listL + listR
    list.sort(finalList)
    num1 = int((path1.split('.')[0]).split('_')[1])
    num2 = int((path1.split('.')[0]).split('_')[2])
    for i in range(num2):
        if "left" in finalList[i]:
            results.append(np.load(os.getcwd() + "/SpecgramData/Left/" + finalList[i]))
        if "right" in finalList[i]:
            results.append(np.load(os.getcwd() + "/SpecgramData/Right/" + finalList[i]))
    pca = PCA(n_components = 2)
    pxx = np.asarray(pxx)
    print len(results)
    results = np.asarray(results)
    newRes = []
    for k in range(len(results[0][0])):
        for i in range(len(results)):
            newRes.append(results[i,:,k])
    for i in pxx:
        newRes.append(i)
    newRes = np.asarray(newRes)
    print newRes.shape
    print "Reducing dimensionality of the data..."
    reducedRes = pca.fit_transform(newRes)
    path1 = path1.split('.')[0]
    print "Plotting data..."
    #fig = plt.figure()
    #ax = fig.add_subplot(111, projection = '3d')
    plt.scatter(reducedRes[:len(reducedRes)-num1,0], reducedRes[:len(reducedRes)-20,1], c='b')
    plt.scatter(reducedRes[-num1:, 0], reducedRes[-num1:, 1], c='r')
    #ax.scatter(reducedRes[:len(reducedRes)-20,0], reducedRes[:len(reducedRes)-20,1], reducedRes[:len(reducedRes)-20,2], c = 'b')
    #ax.scatter(reducedRes[-20:,0], reducedRes[-20:,1], reducedRes[-20:,2], c = 'r')
    plt.title("Image of " + path1)
    #Show and save the periodograms
    plt.show()
    #plt.gcf().savefig(path1 + ".png")


