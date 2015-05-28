"""
sametime.py

This program opens up a connection to SSH into the cs.appstate.edu
server.  It will be utilized to get the bee videos for later parsing.

The main(path, time) function is used to get the audio files
that will be visualized given a certain time desired.
"""

from ftplib import FTP
import getpass
import StringIO
'''
This function opens the connection and gets the files to be parsed.
The path parameter is the directory that has the directories of mp3 files.
The time parameter is the time that you want, in military time.
Ex. 19:50 is 7:50 PM.
'''
def main(path, time):
    #Connect to the cs server with the proper credentials.
    session = FTP()
    session.connect("cs.appstate.edu")
    user = raw_input("Type your username.")
    passwd = getpass.getpass("Type your password.")
    session.login(user, passwd)
    #Set the current directory to the one passed in
    session.cwd(path)
    #Gets the mp3 file for a certain time every day in the passed in directory
    count = 1
    #Print the total number of .mp3 files that are in the directory,
    #and go through them all
    print "Total number of files: " + str(len(session.nlst('*-*-*')))
    filelist = []
    for name in session.nlst('*-*-*'):
        session.cwd(name + '/audio')
        read = StringIO.StringIO()
        print name
        try:
            for hit in session.nlst('*' + time + '*'):
                #session.retrbinary("RETR " + hit, read.write)
                #In order to print the data, change print name to
                #print read.getvalue()
                #print hit
                filelist.append(name + '/audio/' + hit)
                print "File number: " + str(count)
                count += 1
                #Close the StringIO
        except Exception, e:
            print "No file matched in this directory."
        read.close()
        session.cwd('../../')
    print filelist
    #Close the FTP connection
    session.quit()
    print "Done."

if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])
