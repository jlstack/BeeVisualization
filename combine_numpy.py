import re
import os
from datetime import datetime
import Dates
import numpy as np


def other_levels(input_dir, hex_digits, binary_digits):
    """
    Collects all of the files containing binary digits and places their data
    in a dictionary using their binary value as the key.
    :param input_dir: starting directory that holds the hierarchy
    :param hex_digits: number of hex digits in the filename
    :return: nothing is returned; files are being created
    """
    numpy_files = os.listdir(input_dir)
    numpy_files.sort()
    spectrum = {"left": {}, "right": {}}
    hex_num = None
    for nf in numpy_files:
        if not os.path.isdir(input_dir + nf):
            m = re.search(r"[0-9a-fA-F]{" + str(hex_digits) + "}_[0-1]{" + str(binary_digits) + "}" + "_", nf)
            if m:
                hex_num = re.search(r"[0-9a-fA-F]{" + str(hex_digits) + "}", nf).group()
                binary_num = re.search(r"[0-1]{" + str(binary_digits) + "}", nf).group()
                if "left" in nf:
                    if binary_num not in spectrum["left"].keys():
                        data = np.load(input_dir + nf).item()
                        spectrum["left"][binary_num] = data
                else:
                    if binary_num not in spectrum["right"].keys():
                        data = np.load(input_dir + nf).item()
                        spectrum["right"][binary_num] = data
    save_combined_pickles_other_levels(spectrum, hex_num, input_dir)


def save_combined_pickles_other_levels(spectrum, hex_num, output_dir):
    if len(spectrum[list(spectrum)[0]].keys()) > 0:
        binary_len = len(list(spectrum[list(spectrum)[0]])[0])
    elif len(spectrum[list(spectrum)[1]].keys()) > 0:
        binary_len = len(list(spectrum[list(spectrum)[1]])[0])
    else:
        return
    for key in spectrum.keys():
        for i in range(0, 2 ** binary_len, 2):
            binary_form = "{:0" + str(binary_len) + "b}"
            if binary_len == 1:
                file_name = output_dir + "../" + hex_num + "_" + key + ".spec.npy"
            else:
                file_name = output_dir + hex_num + "_" + binary_form.format(i)[:binary_len - 1] + "_" + key + ".spec.npy"
            try:
                d1 = spectrum[key][binary_form.format(i)]
            except KeyError:
                d1 = None
            try:
                d2 = spectrum[key][binary_form.format(i + 1)]
            except KeyError:
                d2 = None
            combine_data(d1, d2, file_name)


def lowest_level(input_dir, hex_digits):
    """
    Collects all of the files and places their data
    in a dictionary using their hex value as the key.
    :param input_dir: starting directory that holds the hierarchy
    :param hex_digits: number of hex digits in the filename
    :return: nothing is returned; files are being created
    """
    numpy_files = os.listdir(input_dir)
    numpy_files.sort()
    spectrum = {"left": {}, "right": {}}
    for nf in numpy_files:
        if not os.path.isdir(input_dir + nf):
            pattern = r"[0-9a-fA-F]{" + str(hex_digits) + "}" + "_"
            m = re.search(pattern, nf)
            pattern2 = r"_[0-9a-fA-F]{" + str(hex_digits) + "}" + "_"
            n = re.search(pattern2, nf)
            if m and not n:
                hex_num = re.search(pattern, nf).group()
                hex_num = hex_num[:-1]  # removes underscore
                if "left" in nf:
                    if hex_num not in spectrum["left"].keys():
                        try:
                            data = np.load(input_dir + nf).item()
                            spectrum["left"][hex_num] = data
                        except EOFError:
                            spectrum["left"][hex_num] = None
                else:
                    if hex_num not in spectrum["right"].keys():
                        try:
                            data = np.load(input_dir + nf).item()
                            spectrum["right"][hex_num] = data
                        except EOFError:
                            spectrum["left"][hex_num] = None
    save_combined_lowest_level(spectrum, input_dir)


def save_combined_lowest_level(spectrum, output_dir):
    # Since all files in dictionary are from the same directory, they share the same first hex digits.
    # These common hex digits are selected in the condition below if there are any keys present.
    if len(spectrum[list(spectrum)[0]].keys()) > 0:
        hex_num = list(spectrum[list(spectrum)[0]])[0][:-1]
    elif len(spectrum[list(spectrum)[1]].keys()) > 0:
        hex_num = list(spectrum[list(spectrum)[1]])[0][:-1]
    else:
        return

    for key in spectrum.keys():  # done for both left and right
        for i in range(0, 16, 2):
            file_name = output_dir + hex_num + "_" + "{0:04b}".format(i)[:3] + "_" + key + ".spec.npy"
            # tries to gather data from both files in present range
            try:
                d1 = spectrum[key][hex_num + '{:01x}'.format(i)]
            except KeyError:
                d1 = None
            try:
                d2 = spectrum[key][hex_num + '{:01x}'.format(i + 1)]
            except KeyError:
                d2 = None
            combine_data(d1, d2, file_name)


def combine_data(data1, data2, file_name):
    """
    Takes two data objects and combines them into one,
    saving the combined data in the specified filename.
    :param data1: dictionary containing the contents from the first npy file
    :param data2: dictionary containing the contents from the second npy file
    :param file_name: specified name for file that is generated
    :return: None
    """
    if data1 is None and data2 is None:
        return
    elif data1 is None:
        end_date = data2["end_datetime"].split("T")[0]
        end_time = data2["end_datetime"].split("T")[1]
        start_date = data2["start_datetime"].split("T")[0]
        start_time = data2["start_datetime"].split("T")[1]
        diff = Dates.time_diff(start_date, start_time, end_date, end_time)
        start_date, start_time = Dates.add_seconds_to_date(start_date, start_time, -1 * diff)
        data2["start_datetime"] = start_date + "T" + start_time
        np.save(file_name, data2)
    elif data2 is None:
        end_date = data1["end_datetime"].split("T")[0]
        end_time = data1["end_datetime"].split("T")[1]
        start_date = data1["start_datetime"].split("T")[0]
        start_time = data1["start_datetime"].split("T")[1]
        diff = Dates.time_diff(start_date, start_time, end_date, end_time)
        end_date, end_time = Dates.add_seconds_to_date(end_date, end_time, diff)
        data1["end_datetime"] = end_date + "T" + end_time
        np.save(file_name, data1)
    else:
        intensities = np.array(data1["intensities"]) + np.array(data2["intensities"]) / 2.0
        combined_data = {"intensities": intensities.tolist(),
                         "start_datetime": data1["start_datetime"], "end_datetime": data2["end_datetime"]}
        if data1["sample_rate"] == data2["sample_rate"]:
            combined_data["sample_rate"] = data1["sample_rate"]
        else:
            combined_data["sample_rate"] = None
            np.save(file_name, combined_data)
    print file_name


def make_hex8(hex_num):
    """
    Pads the end of a hex number with 0s to make it of length 8.
    :param hex_num: specified hex number
    :return: padded hex number
    """
    for i in range(0, 8 - len(hex_num)):
        hex_num += "0"
    return hex_num


def main(input_dir):
    if not input_dir.endswith("/"):
        input_dir += "/"
    m_hex, m_dir = Dates.to_hex("2015-03-01", "00:00:00")  # started recording in march 2015
    i = int(m_hex[:-1], 16)
    while i < 16 ** 7:
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
    stop_date, stop_time = Dates.add_seconds_to_date(curr_date, curr_time, 24 * 60 * 60)  # adds one extra day
    stop_hex, stop_dir = Dates.to_hex(stop_date, stop_time)
    hex_num = '{:07x}'.format(i)
    for hd in range(7, 0, -1):
        i = int(hex_num[:hd], 16)
        stop = int(stop_hex[:hd], 16)
        hex_form = "{:0" + str(hd) + "x}"
        while i <= stop:
            if os.path.isdir(input_dir + '/'.join(hex_form.format(i)[:hd]) + "/"):
                lowest_level(input_dir + '/'.join(hex_form.format(i)[:hd]) + "/", hd + 1)
                for bd in range(3, 0, -1):
                    other_levels(input_dir + '/'.join(hex_form.format(i)[:hd]) + "/", hd, bd)
            i += 1


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
