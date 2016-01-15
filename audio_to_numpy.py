import Dates
import os
import numpy as np
import tempfile
from scipy.signal import resample
from scipy.io.wavfile import read
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tempfile
from pydub import AudioSegment

# rate that is used during resampling 
sample_rate = 2048

# parameters for specgram
fs = 2048
nfft = 4096
noverlap = 2048


def get_data(path):
    """
    Gets the data associated with an audio file, converting to wav when necessary.
    :param path: path to audio file
    :return: sample rate, audio data
    """
    if path.endswith(".wav"):
        bee_rate, bee_data = read(path)
    else:
        temp = tempfile.NamedTemporaryFile(suffix=".wav")
        temp.close()
        if path.endswith(".flac"):
            sound = AudioSegment.from_file(path, "flac")
            sound.export(temp.name, format="wav")
        elif path.endswith(".mp3"):
            sound = AudioSegment.from_file(path, "mp3")
            sound.export(temp.name, format="wav")
        bee_rate, bee_data = read(temp.name)
        os.remove(temp.name)
    data_type = np.iinfo(bee_data.dtype)
    dmin = data_type.min
    dmax = data_type.max
    bee_data = bee_data.astype(np.float64)
    bee_data = 2.0 * ((bee_data - dmin) / (dmax - dmin)) - 1.0
    bee_data = bee_data.astype(np.float32)
    return bee_rate, bee_data


def get_specgram(fname):
    """
    Generates spectrogram for given file.
    :param fname: path to audio file
    :return: spectrogram for audio file
    """
    try:
        rate, data = get_data(fname)
        data = resample(data, len(data) / float(rate) * sample_rate)
        specgram, freqs, time, img = plt.specgram(data,  pad_to=nfft, NFFT=nfft, noverlap=noverlap, Fs=fs)
        specgram = abs(specgram)
        return specgram 
    except ValueError as e:
        print(e.message, '\n', fname)


def make_hex8(hex_num):
    """
    Pads end of hex with 0s to make it length 8.
    :param hex_num: Number to be padded
    :return: padded hex number
    """
    for i in range(0, 8 - len(hex_num)):
        hex_num += "0"
    return hex_num


def get_starting_cols(start, channel, mp3_dirs): 
    """
    Sometimes audio files span multiple time frames and consequently, 
    multiple spectrogram files. This function looks for an audio file 
    directly before the start time and takes columns from the specrogram 
    that fall after the starting time.
    :param start: beginning time for the spectrogram being generated
    :param channel: left or right (microphone for hive)
    :param mp3_dirs: list of directories where file may be located
    :return: columns falling after start time
    """
    file_start = None
    for i in range(0, -60, -1):
        i_hex = '{:08x}'.format(int(start, 16) + i) 
        date, time = Dates.to_date('{:08x}'.format(int(start, 16) + i))
        fname = get_fname(date, time, channel, mp3_dirs)
        if fname is not None:
            file_start = i_hex
            break
    if fname is not None:
        col = int(start, 16) - int(file_start, 16) 
        spec = get_specgram(fname)
        if spec is not None:
            return spec[:, col:]


def get_fname(date, time, channel, mp3_dirs):
    """
    Locates file name for desired time and date.
    :param date: date of desired file (YYYY-MM-DD)
    :param time: time of desired file (HH:MM:SS) 
    :param channel: left or right (microphone for hive)
    :param mp3_dirs: list of directories where file may be located
    """
    '''date = date.split("-")
    date.reverse()
    date = "-".join(date)'''
    fname = None
    for d in mp3_dirs:
        if os.path.isdir(d % date):
            file_list = os.listdir(d % date)
            if len(file_list) == 0 and os.path.isdir(d % (date + "Org")):
                date = date + "Org"
                file_list = os.listdir(d % date)
            if file_list is not None:
                file_list.sort()
                fname = binary_search(time, channel, file_list)
                if fname is not None:
                    fname = d % date + fname
                    break
    return fname


def binary_search(time, channel, file_list):
    """
    Searches list of files from directory for the file 
    associated with a desired time.
    :param time: time of desired file (HH:MM:SS) 
    :param channel: left or right (microphone for hive)
    :param file_list: a sorted list of files from a directory.
    :return: name of file for desired time
    """
    first = 0
    last = len(file_list) - 1
    fname = None
    time = '-'.join(time.split(':'))
    while first <= last:
        midpoint = int((first + last) / 2)
        if time in file_list[midpoint] and channel in file_list[midpoint]:
            print(time)
            fname = file_list[midpoint]
            break
        else:
            if time == ''.join(file_list[midpoint].split('-')[0:3]):
                print(time)
                try:
                    if time in file_list[midpoint - 1] and channel in file_list[midpoint - 1]:
                        fname = file_list[midpoint - 1]
                        break
                except IndexError:
                    pass
                try:
                    if time in file_list[midpoint + 1] and channel in file_list[midpoint + 1]:
                        fname = file_list[midpoint + 1]
                        break
                except IndexError:
                    pass    
                break 
            elif time < ''.join(file_list[midpoint].split('-')[0:3]):
                last = midpoint - 1
            else:
                first = midpoint + 1
    return fname


def main(start_date, start_time, pit, channel):
    start = make_hex8(Dates.to_hex(start_date, start_time)[0][:5])
    mp3_dirs = ["/usr/local/bee/beemon/" + pit + "/%s/audio/", "/usr/local/bee/beemon/beeW/Luke/mp3s/" + pit + "/%s/audio/"]
    curr_date, curr_time = Dates.get_current_date()
    curr_hex = Dates.to_hex(curr_date, curr_time)[0]
    n = int(curr_hex[:5], 16) - int(start[:5], 16) + 1 
    remaining_cols = get_starting_cols(start, channel, mp3_dirs)
    for i in range(0, n): # All 4096 time blocks between start_date/start_time and current_date/current_time
        intensities = np.empty((2049, 4096))
        intensities[:] = np.NAN
        if remaining_cols is not None:
            intensities[:, :remaining_cols.shape[1]] = remaining_cols
            remaining_cols = None
        start_datetime = None
        file_dir = None
        for j in range(0, 4096):  # There are 4096 seconds for each specgram
            date, time = Dates.to_date('{:08x}'.format(int(start, 16) + (i * 4096) + j))
            if start_datetime is None:
                file_dir = Dates.to_hex(date, time)[1]
                start_datetime = date + "T" + time
            fname = get_fname(date, time, channel, mp3_dirs)
            if fname is not None:
                print(fname)
                spec = get_specgram(fname)
                if spec is not None:
                    if j + spec.shape[1] <= intensities.shape[1]:
                        intensities[:, j:j + spec.shape[1]] = spec
                    else:
                        cols = intensities[:, j:].shape[1]
                        intensities[:, j:j + cols] = spec[:, :cols]
                        remaining_cols = spec[:, cols:]
                        print(spec.shape, spec[:, :cols].shape, remaining_cols.shape)
        end_date, end_time = Dates.add_seconds_to_date(start_datetime.split('T')[0], start_datetime.split('T')[1], 4095)
        end_datetime = end_date + "T" + end_time
        # only creates file if audio files were found. (there are entries in intensities that are not equal to np.NaN)
        print(intensities.shape)
        if np.count_nonzero(~np.isnan(intensities)) > 0:
            out_dir =  "/usr/local/bee/beemon/beeW/Luke/numpy_specs/%s/" % pit + file_dir
            if not os.path.isdir(out_dir): 
                os.makedirs(out_dir)
            print(out_dir + '{:08x}'.format(int(start, 16) + (i * 4096))[:5] + "_" + channel + ".npz")
            print("Time frame:", start_datetime, "-", end_datetime, "\n")
            print(intensities.shape)
            np.savez_compressed(out_dir + '{:08x}'.format(int(start, 16) + (i * 4096))[:5] + "_" + channel + ".npz", intensities=intensities, sample_rate=sample_rate, start_datetime=start_datetime, end_datetime=end_datetime)

if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
