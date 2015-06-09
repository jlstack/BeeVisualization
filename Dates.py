__author__ = 'lukestack'

from datetime import datetime, timedelta
import time

START_DATE = datetime.strptime('2015-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
# Program will stop working on 2046-11-24 at 20:15:00

def to_hex(date, file_time):
    d2 = datetime.strptime(date + " " + file_time, '%Y-%m-%d %H:%M:%S')
    d1_ts = time.mktime(START_DATE.timetuple())
    d2_ts = time.mktime(d2.timetuple())
    minutes = int(d2_ts-d1_ts) / 60
    return '{:06x}'.format(minutes), '/'.join('{:06x}'.format(minutes)[:-1]) + "/"


def to_date(hex_num):
    minutes = int(hex_num, 16)
    date = (START_DATE + timedelta(minutes=minutes)).date()
    file_time = (START_DATE + timedelta(minutes=minutes)).time()
    return str(date), str(file_time)