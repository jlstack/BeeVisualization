"""
KMeansSpec.py

This program opens up a connection to SSH into the cs.appstate.edu
server.  It will be utilized to get the bee videos for later parsing.

The KMeans_dir(path) function is used to get the audio files
and perform KMeans clustering on them.  It then displays the closest
and farthest tuples of points in the same cluster, and displays how
many points are in each cluster.
"""

#import matplotlib
#matplotlib.use("Agg")
import sys
from ftplib import FTP
import getpass
import StringIO
from scipy.io.wavfile import read as read_wav
import tempfile
from sklearn import cluster
import numpy as np
import wave
from scipy.spatial import distance as d
import sklearn.preprocessing as p
from scipy import signal
from matplotlib import pyplot as plt
import os

'''
This function opens the connection and gets the files to be clustered.
The path parameter is the directory that has the wav files.
The n parameter is the number of clusters.
The limit parameter is the number of files to include.
'''
def KMeans_dir(path, n=None, limit=None):
    #Connect to the cs server with the proper credentials. 
    session = FTP()
    session.connect("cs.appstate.edu")
    user = raw_input("Type your username.")
    passwd = getpass.getpass("Type your password.")
    session.login(user, passwd)
    try:
        session.cwd(path)
        #Set the current directory to the one passed in's audio folder
        audio_dir = session.pwd() + "/audio/"
        session.cwd(audio_dir)
        data = []
        names = []
        match = "*.wav"
        count = 0
        print "Login successful. Reading wav files..."
        #Make sure the storage directories are there
        if not os.path.isdir("../SpecgramData/"):
            os.makedirs("../SpecgramData/")
        if not os.path.isdir("../SpecgramData/Left/"):
            os.makedirs("../SpecgramData/Left/")
        if not os.path.isdir("../SpecgramData/Right/"):
            os.makedirs("../SpecgramData/Right/")
        #Make sure the limit is set
        if limit is None:
            limit = len(session.nlst(match))
        limit = int(limit)
        #Get the recordings and parse them for clustering
        for recording in session.nlst(match):
            if count >= limit:
                break
            #Get the wav file from server, and put it in temp file.
            read = StringIO.StringIO()
            temp = tempfile.NamedTemporaryFile(suffix=".wav")
            file = open(temp.name, 'wb')
            session.retrbinary("RETR " + recording, read.write)
            values = read.getvalue()
            file.write(values)
            file.close()
            #Open the .wav file and get the vital information
            wav = wave.open(file.name, 'r')
            frames = wav.readframes(-1)
            sig = np.fromstring(frames, "Int16")
            #Decimate the wav signal for parsing
            dsarray = signal.decimate(sig, 36)
            #pxx is the periodograms, freqs is the frequencies
            pxx, freqs, times, img = plt.specgram(dsarray, NFFT = 1024, noverlap = 512, Fs = 1225)
            #Plot against the time. Then, title it and limit the y-axis to 600
            plt.plot(np.linspace(0, len(freqs)/1225, num=len(freqs)), freqs)
            plt.title(recording)
            plt.ylim((0,600))
            #Show and save the periodograms
            #plt.show()
            if "left" in recording:
                np.save("../SpecgramData/Left/" + recording, pxx)
            elif "right" in recording:
                np.save("../SpecgramData/Right/" + recording, pxx)
            count += 1
            temp.close()
            #Append it to the list of data
            data.append(pxx.ravel())
            names.append(recording)
            if count % 25 == 0:
                print str(count) + " out of " + str(limit) + " wav files read!"
        #Close the FTP connection
        session.quit()
        #Make sure the number of clusters is set
        if n is None:
            n = 10
        n = int(n)
        #Actually do the KMeans clustering
        print "Data gathering complete. Initializing KMeans..."
        estimator = cluster.KMeans(n_clusters=n, n_init = 1, max_iter=100, verbose=1, n_jobs=1)
        estimator.fit(data)
        #Print the inertia
        print estimator.inertia_
        finals = []
        for i in range(len(estimator.labels_)):
            if i % 25 == 0:
                print "Finding distances between files, where i = " + str(i) + "."
            for j in range(i, len(estimator.labels_)):
                #Store the distance between points in the same cluster
                if estimator.labels_[i] == estimator.labels_[j] and i != j:
                    finals.append([d.euclidean(np.array(data[i]), np.array(data[j])), i, j])
        finals.sort()
        #Save the labels, names, overall inertia, and the final distances into a file called "clusterdata.npy"
        saveddata = [estimator.labels_, names, estimator.inertia_, finals]
        np.save("clusterdata.npy", saveddata)
        #Print the closest 25 pairs of wav files, as well as the farthest
        print "Closest {0:.3f}% of wav file tuples that are in the same cluster: ".format(1/(float(limit)/2)*100)
        for result in finals[:(limit+1)]:
            print result
        print "Farthest {0:.3f}% of wav file tuples that are in the same cluster: ".format(1/(float(limit)/2)*100)
        for result in finals[-(limit+1):]:
            print result
        total_counts(saveddata, n)
        print "Done."
    except Exception,e:
        print e

'''
Used to count the number of points in a given cluster.
Returns the count for a given cluster number.
'''
def find(dataset, x):
    count = 0
    for i in range(len(dataset[0])):
        if dataset[0][i] == x:
            count += 1
    return count

'''
Used to return the counts for each cluster.
Prints this out to the console.
'''
def total_counts(dataset, n):
    for x in range(n):
        print "Number of points in cluster " + str(x) + ": " + str(find(dataset, x))

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
            if 'y' in decision or 'Y' in decision:
                passed = False
            else:
                KMeans_dir(sys.argv[1], limit=sys.argv[2])
        else:
            print "Error. Answer must contain y for yes, or n for no."
        if not passed:
            print "Cannot contain both."
    elif len(sys.argv) == 4:
        KMeans_dir(sys.argv[1], n=sys.argv[2], limit=sys.argv[3])
    else:
        print "Called with wrong number of parameters."
        print "First parameter is the path to the files (REQUIRED)"
        print "Second parameter is the number of clusters (OPTIONAL)"
        print "Third parameter is the number of files desired (OPTIONAL)"

