import re
import os
import pickle
import numpy as np


def save_pickle(data, file_name):
    if not os.path.isfile(file_name):
        with open(file_name, 'wb') as outfile:
            pickle.dump(data, outfile)


def other_levels(input_dir, binary_digits):
    pickles = os.listdir(input_dir)
    pickles.sort()
    spectrum = {"left": {}, "right": {}}
    for pic in pickles:
        m = re.search(r"[0-9a-fA-F]{7}_[0-1]{" + str(binary_digits) + "}", pic)
        if m:
            hex_num = re.search(r"[0-9a-fA-F]{7}", pic).group()
            binary_num = re.search(r"[0-1]{" + str(binary_digits) + "}", pic).group()
            if "left" in pic:
                if binary_num not in spectrum["left"].keys():
                    with open(input_dir + pic, 'rb') as f:
                        spec, freq, time = pickle.load(f)
                    spectrum["left"][binary_num] = (spec, freq, time)
            else:
                if binary_num not in spectrum["right"].keys():
                    with open(input_dir + pic, 'rb') as f:
                        spec, freq, time = pickle.load(f)
                    spectrum["right"][binary_num] = (spec, freq, time)
    save_combined_pickles_other_levels(spectrum, hex_num, input_dir)


def save_combined_pickles_other_levels(spectrum, hex_num, output_dir):
    binary_len = len(spectrum[spectrum.keys()[0]].keys()[0])
    for key in spectrum.keys():
        for i in range(0, 2**binary_len, 2):
            binary_form = "{:0" + str(binary_len) + "b}"
            if binary_len == 1:
                file_name = output_dir + "../" + hex_num + "_" + key + ".spec.pkl"
            else:
                file_name = output_dir + hex_num + "_" + binary_form.format(i)[:binary_len - 1] + "_" + key + ".spec.pkl"
            try:
                s1, s1_freqs, s1_time = spectrum[key][binary_form.format(i)]
            except KeyError:
                s1 = s1_freqs = s1_time = None
            try:
                s2, s2_freqs, s2_time = spectrum[key][binary_form.format(i + 1)]
            except KeyError:
                s2 = s2_freqs = s2_time = None
            if s1 is None and s2 is None:
                continue
            elif s1 is None:
                save_pickle((s2, s2_freqs, None), file_name)
            elif s2 is None:
                save_pickle((s1, s1_freqs, None), file_name)
            else:
                save_pickle(((s1 + s2) / 2, s1_freqs, None), file_name)


def lowest_level(input_dir):
    pickles = os.listdir(input_dir)
    pickles.sort()
    spectrum = {"left": {}, "right": {}}
    for pic in pickles:
        m = re.search(r"[0-9a-fA-F]{8}_[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", pic)
        if m:
            hex_num = re.search(r"[0-9a-fA-F]{8}", pic).group()
            if "left" in pic:
                if hex_num not in spectrum["left"].keys():
                    with open(input_dir + pic, 'rb') as f:
                        spec, freq, time = pickle.load(f)
                    spectrum["left"][hex_num] = (spec, freq, None)
            else:
                if hex_num not in spectrum["right"].keys():
                    with open(input_dir + pic, 'rb') as f:
                        spec, freq, time = pickle.load(f)
                    spectrum["right"][hex_num] = (spec, freq, None)
    save_combined_pickles_lowest_level(spectrum, input_dir)


def save_combined_pickles_lowest_level(spectrum, output_dir):
    hex_num = spectrum[spectrum.keys()[0]].keys()[0][:-1]
    for key in spectrum.keys():
        for i in range(0, 16, 2):
            file_name = output_dir + hex_num + "_" + "{0:04b}".format(i)[:3] + "_" + key + ".spec.pkl"
            try:
                s1, s1_freqs, s1_time = spectrum[key][hex_num + '{:01x}'.format(i)]
            except KeyError:
                s1 = s1_freqs = s1_time = None
            try:
                s2, s2_freqs, s2_time = spectrum[key][hex_num + '{:01x}'.format(i + 1)]
            except KeyError:
                s2 = s2_freqs = s2_time = None

            if s1 is None and s2 is None:
                continue
            elif s1 is None:
                save_pickle((s2, s2_freqs, None), file_name)
            elif s2 is None:
                save_pickle((s1, s1_freqs, None), file_name)
            else:
                save_pickle(((s1 + s2) / 2, s1_freqs, None), file_name)


def main(input_dir):
    if not input_dir.endswith("/"):
        input_dir += "/"
    lowest_level(input_dir)
    for i in range(3, 0, -1):
        other_levels(input_dir, i)


if __name__ == "__main__":
    import sys
    main(sys.argv[1])