__author__ = 'lukestack'

import os
import pickle
import numpy as np
import math

def combine_specgrams(data1, data2):
    data1 = (data1[::, ::2] + data1[::, 1::2]) / 2.0
    data2 = (data2[::, ::2] + data2[::, 1::2]) / 2.0
    return np.hstack((data1, data2))


def save_pickle(spectrum, freqs, file_name):
    if not os.path.isfile(file_name):
        with open(file_name, 'wb') as outfile:
            pickle.dump((spectrum, freqs), outfile)


def create_combined_pickles(input_dir):
    spectrum = os.listdir(input_dir)
    spectrum.sort()
    combined_specgram_left = None
    combined_specgram_right = None
    hex_values = []
    freqs = None
    for spec in spectrum: 
        if ".spec.pkl" in spec:
            hex_values.append(spec[:8])
            with open(input_dir + spec, 'rb') as f:
                spectrum, freq, time = pickle.load(f)
            if freqs is None:
                freqs = freq
            if "left" in spec:
                if combined_specgram_left is None:
                    combined_specgram_left = spectrum
                else:
                    combined_specgram_left = np.vstack((combined_specgram_left, spectrum))
            else:    
                if combined_specgram_right is None:
                    combined_specgram_right = spectrum
                else:
                    combined_specgram_right = np.vstack((combined_specgram_right, spectrum)) 
    log = (math.ceil(math.log10(int(hex_values[len(hex_values) - 1], 16) - int(hex_values[0], 16)) / math.log10(16)))
    if log == 0:
        hex_num = (hex_values[0][:8 - 1])
    else:
        hex_num = (hex_values[0][:8 - log])
    print (combined_specgram_left.shape) 
    if combined_specgram_left.shape[0] == 16:
        save_pickle(np.mean(combined_specgram_left[:2], axis=0), freqs, input_dir + hex_num + "_000_left.spec.pkl")
        save_pickle(np.mean(combined_specgram_left[2:4], axis=0), freqs, input_dir + hex_num + "_001_left.spec.pkl")
        save_pickle(np.mean(combined_specgram_left[:4], axis=0), freqs, input_dir + hex_num + "_00_left.spec.pkl")
        save_pickle(np.mean(combined_specgram_left[4:8], axis=0), freqs, input_dir + hex_num + "_01_left.spec.pkl")
        save_pickle(np.mean(combined_specgram_left[0:8], axis=0), freqs, input_dir + hex_num + "_0_left.spec.pkl")
        save_pickle(np.mean(combined_specgram_left[8:16], axis=0), freqs, input_dir + hex_num + "_1_left.spec.pkl")
        save_pickle(np.mean(combined_specgram_left, axis=0), freqs, input_dir + hex_num + "_left.spec.pkl")
    else:
        print (hex_num + "is not a full directory")
    
    if combined_specgram_right.shape[0] == 16:
        save_pickle(np.mean(combined_specgram_right[:2], axis=0), freqs, input_dir + hex_num + "_000_right.spec.pkl")
        save_pickle(np.mean(combined_specgram_right[2:4], axis=0), freqs, input_dir + hex_num + "_001_right.spec.pkl")
        save_pickle(np.mean(combined_specgram_right[:4], axis=0), freqs, input_dir + hex_num + "_00_right.spec.pkl")
        save_pickle(np.mean(combined_specgram_right[4:8], axis=0), freqs, input_dir + hex_num + "_01_right.spec.pkl")
        save_pickle(np.mean(combined_specgram_right[0:8], axis=0), freqs, input_dir + hex_num + "_0_right.spec.pkl")
        save_pickle(np.mean(combined_specgram_right[8:16], axis=0), freqs, input_dir + hex_num + "_1_right.spec.pkl")
        save_pickle(np.mean(combined_specgram_right, axis=0), freqs, input_dir + hex_num + "_right.spec.pkl")
    else:
        print (hex_num + "is not a full directory")
        

def main(input_dir):
    if not input_dir.endswith("/"):
        input_dir += "/"
    create_combined_pickles(input_dir)


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
