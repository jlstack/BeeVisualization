__author__ = 'lukestack'

import time
import pytz
from dateutil import tz
from datetime import datetime, timedelta


utc = pytz.timezone('UTC')
START_DATE = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0, tzinfo=utc)
# Program will stop working on 2106-02-07T06:28:15Z


def to_hex(date, file_time):
    date = date.split("-")
    file_time = file_time.split(":")
    d2 = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                  hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=utc)
    d1_ts = time.mktime(START_DATE.timetuple())
    d2_ts = time.mktime(d2.timetuple())
    seconds = int(d2_ts - d1_ts)
    return '{:08x}'.format(seconds), '/'.join('{:08x}'.format(seconds)[:-1]) + "/"


def to_date(hex_num):
    seconds = int(hex_num, 16)
    date = (START_DATE + timedelta(seconds=seconds)).date()
    file_time = (START_DATE + timedelta(seconds=seconds)).time()
    return str(date), str(file_time)


def convert_to_utc(date, file_time):
    date = date.split("-")
    file_time = file_time.split(":")
    date = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                    hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=tz.tzlocal())
    date.replace(tzinfo=tz.tzlocal()).astimezone(tz=utc)
    date = utc.normalize(date)
    return str(date.date()), str(date.time())


def add_seconds_to_date(date, file_time, seconds):
    date = date.split("-")
    file_time = file_time.split(":")
    d = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                 hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=utc)
    date = (d + timedelta(seconds=seconds)).date()
    file_time = (d + timedelta(seconds=seconds)).time()
    return str(date), str(file_time)


def convert_to_local(date, file_time):
    local = tz.tzlocal()


    date = date.split("-")
    file_time = file_time.split(":")
    date = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                    hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=utc)
    date.replace(tzinfo=utc)
    date = date.astimezone(tz=local)
    return str(date.date()), str(date.time())
