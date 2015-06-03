"""
KMeansSpec.py

This program opens up a connection to SSH into the cs.appstate.edu
server.  It will be utilized to get the bee videos for later parsing.

The KMenas_dir(path) function is used to get the audio files
and perform KMeans clustering on them.
"""

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

'''
This function opens the connection and gets the files to be clustered.
The path parameter is the directory that has the wav files.
'''
def KMeans_dir(path, limit=None):
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
        #Get the recordings and parse them for clustering
        if limit is None:
            limit = len(session.nlst(match))
        limit = int(limit)
        for recording in session.nlst(match):
            if count >= limit:
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
            nframes = wav.getnframes()
            datum = wav.readframes(nframes)
            #Convert the data from a UTF-8 string to an int64 NumPy array
            arraydata = np.fromstring(datum, dtype = np.int64)
            #Append it to the list of data
            data.append(arraydata)
            names.append(recording)
            #Close the local temp file
            temp.close()
            count += 1
            if count % 25 == 0:
                print str(count) + " out of " + str(len(session.nlst(match))) + " wav files read!"
        #Close the FTP connection
        session.quit()
        data = np.asarray(data)
        min = float(data.min())
        max = float(data.max())
        #Normalize the data, so overflow is not experienced
        normalized = []
        for i in range(len(data)):
            normalized.append((data[i] / (max - min)) - (min / (max - min)))
        #Actually do the KMeans clustering
        print "Data gathering complete. Initializing KMeans..."
        estimator = cluster.KMeans(n_clusters=10, n_init = 1, max_iter=100, verbose=1, n_jobs=1)
        estimator.fit(normalized)
        #Print the inertia
        print estimator.inertia_
        finals = []
        for i in range(len(estimator.labels_)):
            if i % 25 == 0:
                print "Finding distances between files, where i = " + str(i) + "."
            for j in range(i, len(estimator.labels_)):
                #Store the distance between points in the same cluster
                if estimator.labels_[i] == estimator.labels_[j] and i != j:
                    finals.append([d.euclidean(np.array(normalized[i]), np.array(normalized[j])), i, j])
        finals.sort()
        #Save the labels, names, overall inertia, and the final distances into a file called "clusterdata.npy"
        saveddata = [estimator.labels_, names, estimator.inertia_, finals]
        np.save("clusterdata.npy", saveddata)
        #Print the closest 25 pairs of wav files, as well as the farthest
        print "Closest 25 wav files that are in the same cluster: "
        for result in finals[:25]:
            print result
        print "Farthest 25 wav files that are in the same cluster: "
        for result in finals[-25:]:
            print result
        print "Done."
    except Exception,e:
        print e

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        KMeans_dir(sys.argv[1])
    elif len(sys.argv) == 3:
        KMeans_dir(sys.argv[1], limit=sys.argv[2])
    else:
        print "Called with wrong number of parameters."
        print "First parameter is the path to the files (REQUIRED)"
        print "Second parameter is the number of files desired (OPTIONAL)"

