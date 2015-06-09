__author__ = 'lukestack'

from datetime import datetime, timedelta
import time

START_DATE = datetime.strptime('2015-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')


def to_hex(date, file_time):
    d2 = datetime.strptime(date + " " + file_time, '%Y-%m-%d %H:%M:%S')

    d1_ts = time.mktime(START_DATE.timetuple())
    d2_ts = time.mktime(d2.timetuple())

    minutes = int(d2_ts-d1_ts) / 60
    return '{:024x}'.format(minutes)


def to_date(num):
    minutes = int(num, 16)
    date = (START_DATE + timedelta(minutes=minutes)).date()
    file_time = (START_DATE + timedelta(minutes=minutes)).time()
    return str(date), str(file_time)

