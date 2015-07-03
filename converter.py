__author__ = 'lukestack'
import os
import pickle
import Dates
from datetime import datetime
import json
import numpy as np


def to_json(input_dir):
    start, stop = get_start_and_stop()
    for i in range(start, stop):
        hex_date = '{:08x}'.format(i)
        date_dir = '/'.join(hex_date[:-1]) + "/"
        date, time = Dates.to_date(hex_date)
        left = input_dir + date_dir + hex_date + "_" + date + 'T' + time + 'Z_left.spec.pkl'
        right = input_dir + date_dir + hex_date + "_" + date + 'T' + time + 'Z_right.spec.pkl'
        if os.path.isfile(left):
            with open(left, 'rb') as f:
                u = pickle._Unpickler(f)
                u.encoding = 'latin1'
                data = u.load()
                # data = pickle.load(f)
            data = [data[0].tolist(), data[1].tolist(), data[2].tolist()]
            with open(left + '.json', 'w') as outfile:
                json.dump(data, outfile)
            os.remove(left)
            print(left)
        if os.path.isfile(right):
            with open(right, 'rb') as f:
                u = pickle._Unpickler(f)
                u.encoding = 'latin1'
                data = u.load()
                # data = pickle.load(f)
            data = [data[0].tolist(), data[1].tolist(), data[2].tolist()]
            with open(right + '.json', 'w') as outfile:
                json.dump(data, outfile)
            os.remove(right)
            print(right)


def to_pickle(input_dir):
    start, stop = get_start_and_stop()
    for i in range(start, stop):
        hex_date = '{:08x}'.format(i)
        date_dir = '/'.join(hex_date[:-1]) + "/"
        date, time = Dates.to_date(hex_date)
        left = input_dir + date_dir + hex_date + "_" + date + 'T' + time + 'Z_left.spec.pkl.json'
        right = input_dir + date_dir + hex_date + "_" + date + 'T' + time + 'Z_right.spec.pkl.json'
        if os.path.isfile(left):
            with open(left, 'rb') as f:
                data = json.load(pic)
            data = np.array(data[0]), np.array(data[1]), np.array(data[2])
            l_pkl = left[:left.index('.json')]
            with open(l_pkl, 'w') as outfile:
                pickle.dump(data, outfile)
            os.remove(left)
            print(left)
        if os.path.isfile(right):
            with open(right, 'rb') as f:
                data = json.load(pic)
            data = np.array(data[0]), np.array(data[1]), np.array(data[2])
            r_pkl = left[:right.index('.json')]
            with open(r_pkl, 'w') as outfile:
                pickle.dump(data, outfile)
            os.remove(right)
            print(right)


def get_start_and_stop():
    start, start_dir = Dates.to_hex('2015-04-14', '00:00:00')
    start = int(start, 16)
    now = datetime.now()
    curr_time = str(now.time())
    curr_time = curr_time[:curr_time.rfind('.')]
    curr_date = str(now.date())
    curr_date, curr_time = Dates.convert_to_utc(curr_date, curr_time)
    stop_date, stop_time = Dates.add_seconds_to_date(curr_date, curr_time, 24 * 60 * 60)  # adds one extra day
    stop, stop_dir = Dates.to_hex(stop_date, stop_time)
    stop = int(stop, 16)
    return start, stop


if __name__ == '__main__':
    import sys
    to_json(sys.argv[1])

