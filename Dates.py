__author__ = 'lukestack'

from datetime import datetime, timedelta
import time
import pytz

utc = pytz.timezone('UTC')
START_DATE = datetime(year=2015, month=1, day=1, hour=0, minute=0, second=0, tzinfo=utc)
# Program will stop working on 2046-11-24 at 20:15:00


def to_hex(date, file_time):
    date = date.split("-")
    file_time = file_time.split(":")
    d2 = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                  hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=utc)
    d1_ts = time.mktime(START_DATE.timetuple())
    d2_ts = time.mktime(d2.timetuple())
    minutes = int(d2_ts-d1_ts) / 60
    return '{:06x}'.format(minutes), '/'.join('{:06x}'.format(minutes)[:-1]) + "/"


def to_date(hex_num):
    minutes = int(hex_num, 16)
    date = (START_DATE + timedelta(minutes=minutes)).date()
    file_time = (START_DATE + timedelta(minutes=minutes)).time()
    return str(date), str(file_time)
