import re
import os
import pickle
from datetime import datetime
import Dates


def save_pickle(data, file_name):
    if not os.path.isfile(file_name):
        with open(file_name, 'wb') as outfile:
            pickle.dump(data, outfile)


def other_levels(input_dir, hex_digits, binary_digits):
    pickles = os.listdir(input_dir)
    pickles.sort()
    spectrum = {"left": {}, "right": {}}
    hex_num = None
    for pic in pickles:
        m = re.search(r"[0-9a-fA-F]{" + str(hex_digits) + "}_[0-1]{" + str(binary_digits) + "}", pic)
        if m:
            hex_num = re.search(r"[0-9a-fA-F]{" + str(hex_digits) + "}", pic).group()
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
    if hex_num is not None:
        save_combined_pickles_other_levels(spectrum, hex_num, input_dir)


def save_combined_pickles_other_levels(spectrum, hex_num, output_dir):
    if len(spectrum[list(spectrum)[0]].keys()) > 0:
        binary_len = len(list(spectrum[list(spectrum)[0]])[0])
    elif len(spectrum[list(spectrum)[1]].keys()) > 0:
        binary_len = len(list(spectrum[list(spectrum)[1]])[0])
    else:
        return
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


def lowest_level(input_dir, hex_digits):
    pickles = os.listdir(input_dir)
    pickles.sort()
    spectrum = {"left": {}, "right": {}}
    for pic in pickles:
        spec = freq = None
        m = re.search(r"[0-9a-fA-F]{" + str(hex_digits) + "}", pic)
        if m:
            hex_num = re.search(r"[0-9a-fA-F]{" + str(hex_digits) + "}", pic).group()
            if "left" in pic:
                if hex_num not in spectrum["left"].keys():
                    try:
                        with open(input_dir + pic, 'rb') as f:
                            spec, freq, time = pickle.load(f)
                        spectrum["left"][hex_num] = (spec, freq, None)
                    except EOFError:
                        spectrum["left"][hex_num] = (spec, freq, None)
            else:
                if hex_num not in spectrum["right"].keys():
                    try:
                        with open(input_dir + pic, 'rb') as f:
                            spec, freq, time = pickle.load(f)
                        spectrum["right"][hex_num] = (spec, freq, None)
                    except EOFError:
                        spectrum["left"][hex_num] = (spec, freq, None)
    save_combined_pickles_lowest_level(spectrum, input_dir)


def save_combined_pickles_lowest_level(spectrum, output_dir):
    if len(spectrum[list(spectrum)[0]].keys()) > 0:
        hex_num = list(spectrum[list(spectrum)[0]])[0][:-1]
    elif len(spectrum[list(spectrum)[1]].keys()) > 0:
        hex_num = list(spectrum[list(spectrum)[1]])[0][:-1]
    else:
        return
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

    m_date, m_time = Dates.convert_to_utc("2015-03-01", "00:00:00")  # started recording in march 2015
    m_hex, m_dir = Dates.to_hex(m_date, m_time)
    i = int(m_hex[:-1], 16)
    while i < 16**7:
        if os.path.isdir(input_dir + '/'.join('{:07x}'.format(i)) + "/"):
            while os.path.isdir(input_dir + '/'.join('{:07x}'.format(i)) + "/"):
                i -= 1
            i += 1
            break
        i += 1

    now = datetime.now()
    curr_time = str(now.time())
    curr_time = curr_time[:curr_time.rfind('.')]
    curr_date = str(now.date())
    curr_date, curr_time = Dates.convert_to_utc(curr_date, curr_time)
    stop_date, stop_time = Dates.add_seconds_to_date(curr_date, curr_time, 24 * 60 * 60)  # adds one extra day
    stop_hex, stop_dir = Dates.to_hex(stop_date, stop_time)
    hex_num = '{:07x}'.format(i)
    for hd in range(7, 0, -1):
        i = int(hex_num[:hd], 16)
        stop = int(stop_hex[:hd], 16)
        hex_form = "{:0" + str(hd) + "x}"
        while i <= stop:
            if os.path.isdir(input_dir + '/'.join(hex_form.format(i)[:hd]) + "/"):
                print (input_dir + '/'.join(hex_form.format(i)[:hd + 1]) + "/")
                lowest_level(input_dir + '/'.join(hex_form.format(i)[:hd]) + "/", hd + 1)
                for bd in range(3, 0, -1):
                    other_levels(input_dir+ '/'.join(hex_form.format(i)[:hd]) + "/", hd, bd)
            i += 1


if __name__ == "__main__":
    import sys
    main(sys.argv[1])