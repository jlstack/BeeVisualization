"""
sshscript.py
This program opens up a connection to SSH into the cs.appstate.edu
server.  It will be utilized to get the bee videos for later parsing.

The get_file(filename) function is used to get the audio file
that is to be visualized.
"""

from ftplib import FTP, error_perm
import getpass
import StringIO
import tempfile
from pydub import AudioSegment
from scipy.io.wavfile import read as read_wav
import matplotlib.pyplot as plt


fs = 44100.0
nfft = 2048
noverlap = 1024


def get_data_from_flac(data):
    flac_temp = tempfile.NamedTemporaryFile(suffix=".flac")

    # writes data from server to local tempfile
    flac = open(flac_temp.name, 'w')
    flac.write(data)
    flac.close()

    wav_temp = tempfile.NamedTemporaryFile(suffix=".wav")
    sound = AudioSegment.from_file(flac_temp.name, "flac")
    sound.export(wav_temp.name, format="wav")
    bee_rate, bee_data = read_wav(wav_temp.name)
    flac_temp.close()
    wav_temp.close()
    return bee_rate, bee_data


def main(path):
    # Connect to the cs server with the proper credentials.
    session = FTP()
    session.connect("cs.appstate.edu")
    user = raw_input("Type your username.")
    passwd = getpass.getpass("Type your password.")
    session.login(user, passwd)
    session.cwd(path)
    try:
        session.mkd("../Spectrograms")
    except error_perm:
        pass

    # Gets the flac files in the passed in directory
    match = "*.flac"
    count = 1

    # Print the total number of .mp3 files that are in the directory,
    # and go through them all
    print "Total number of files: " + str(len(session.nlst(match)))

    left_index = 1
    right_index = 1
    for name in session.nlst(match):
        read = StringIO.StringIO()
        session.retrbinary("RETR " + name, read.write)

        data = read.getvalue()
        bee_rate, bee_data = get_data_from_flac(data)

        plt.specgram(bee_data, pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
        plt.title(name)
        jpeg_temp = tempfile.NamedTemporaryFile(suffix=".jpeg")
        plt.savefig(jpeg_temp.name)
        plt.close()

        spec = open(jpeg_temp.name, 'r')
        if "left" in name:
            session.storbinary("STOR ../Spectrograms/%05d_left.jpeg" % left_index, spec)
            left_index += 1
        if "right" in name:
            session.storbinary("STOR ../Spectrograms/%05d_right.jpeg" % right_index, spec)
            right_index += 1
        spec.close()
        jpeg_temp.close()

        print "File number: " + str(count)
        count += 1

        # Close the StringIO
        read.close()

    # Close the FTP connection
    session.quit()
    print "Done."

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
