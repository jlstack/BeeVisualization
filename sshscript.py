"""
sshscript.py

This program opens up a connection to SSH into the cs.appstate.edu
server.  It will be utilized to get the bee videos for later parsing.

The get_file(filename) function is used to get the audio file
that is to be visualized.
"""

from ftplib import FTP
import getpass
import StringIO
import SpectrogramVideo as s
'''
This function opens the connection and gets the files to be parsed.
The path parameter is the directory that has the mp3 files.
'''
def get_file(path):
    #Connect to the cs server with the proper credentials.
    session = FTP()
    session.connect("cs.appstate.edu")
    user = raw_input("Type your username.")
    passwd = getpass.getpass("Type your password.")
    session.login(user, passwd)
    session.cwd(path)
    #Gets the mp3 files in the passed in directory
    match = "*.mp3"
    count = 1
    #Print the total number of .mp3 files that are in the directory,
    #and go through them all
    print "Total number of files: " + str(len(session.nlst(match)))
    for name in session.nlst(match):
        read = StringIO.StringIO()
        session.retrbinary("RETR " + name, read.write)
        #In order to print the data, change print name to
        #print read.getvalue()
        print name
        print "File number: " + str(count)
        count += 1
        #Close the StringIO
        read.close()
    s.create_specgrams(path)
    #Close the FTP connection
    session.quit()
    print "Done."
