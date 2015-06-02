"""
KMeansSpec.py

This program opens up a connection to SSH into the cs.appstate.edu
server.  It will be utilized to get the bee videos for later parsing.

The KMenas_dir(path) function is used to get the audio files
and perform KMeans clustering on them.
"""

from ftplib import FTP
import getpass
import StringIO
import os
from scipy.io.wavfile import read as read_wav
import matplotlib.pyplot as plt
import tempfile
from sklearn import cluster
import numpy as np
import wave
from scipy.spatial import distance as d
import sklearn.preprocessing as p

'''
This function opens the connection and gets the files to be clustered.
The path parameter is the directory that has the wav files.
'''
def KMeans_dir(path):
    #Connect to the cs server with the proper credentials. 
    session = FTP()
    session.connect("cs.appstate.edu")
    user = raw_input("Type your username.")
    passwd = getpass.getpass("Type your password.")
    session.login(user, passwd)
    try:
        session.cwd(path)
        #Set the current directory to the one passed in
        audio_dir = session.pwd() + "/audio/"
        spec_dir = session.pwd() + "/Specgrams/"
        session.cwd(audio_dir)
        data = []
        names = []
        match = "*.wav"
        count = 0
        #Get the recordings and parse them for clustering
        for recording in session.nlst(match):
            if count >= 50:
                break
            read = StringIO.StringIO()
            temp = tempfile.NamedTemporaryFile(suffix=".wav")
            file = open(temp.name, 'w')
            session.retrbinary("RETR " + recording, read.write)
            values = read.getvalue()
            file.write(values)
            file.close()
            #Open the .wav file and get the vital information
            wav = wave.open(file.name)
            #rate = wav.getframerate()
            nframes = wav.getnframes()
            datum = wav.readframes(nframes)
            #normalized = [float(int(i))/np.max(datum) for i in datum]
            #frames = []
            #for chunk in range(0, int(rate / 1024*60)):
                #num_getting = chunk * 1024
                #frame_data = datum[num_getting:num_getting + 1024]
                #frames.append(np.fromstring(frame_data, dtype = np.int16))
            #print rate
            #print nframes
            arraydata = np.fromstring(datum, dtype = np.int64)
            data.append(arraydata)
            #print np.fromstring(datum, dtype = np.int64).shape
            names.append(recording)
            temp.close()
            count += 1
            print str(count) + " out of " + str(len(session.nlst(match)))
        #Close the FTP connection
        session.quit()
        data = np.asarray(data)
        row_sums = data.sum(axis=1)
        min = float(data.min())
        max = float(data.max())
        normalized = []
        for i in range(len(data)):
            normalized.append((data[i] / max) - (min / max))
        #print names
        #Actually do the KMeans clustering
        estimator = cluster.KMeans(n_clusters=10, n_init = 1, max_iter=100, verbose=1, n_jobs=1)
        estimator.fit(normalized)
        #Save the labels, their associated names, and the inertia
        saveddata = [estimator.labels_, names, estimator.inertia_]
        print estimator.inertia_
        np.save("clusterdata.npy", saveddata)
        for i in range(len(saveddata[0])):
            for j in range(i, len(saveddata[0])):
                #Print the distance between points in the same cluster
                if estimator.labels_[i] == estimator.labels_[j] and i != j:
                    print str(d.euclidean(np.array(normalized[i]), np.array(normalized[j])))+ " " + str(i) + " " + str(j)
        print "Done."
    except Exception,e:
        print e

if __name__ == "__main__":
    import sys
    KMeans_dir(sys.argv[1])

