__author__ = 'lukestack'

import time
import pytz
from dateutil.tz import tzlocal
from datetime import datetime, timedelta


utc = pytz.timezone('UTC')
START_DATE = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0, tzinfo=utc)
# Program will stop working on 2480-05-19T20:15:00Z


def to_hex(date, file_time):
    date = date.split("-")
    file_time = file_time.split(":")
    d2 = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                  hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=utc)
    d1_ts = time.mktime(START_DATE.timetuple())
    d2_ts = time.mktime(d2.timetuple())
    minutes = int((d2_ts-d1_ts) / 60)
    return '{:07x}'.format(minutes), '/'.join('{:07x}'.format(minutes)[:-1]) + "/"


def to_date(hex_num):
    minutes = int(hex_num, 16)
    date = (START_DATE + timedelta(minutes=minutes)).date()
    file_time = (START_DATE + timedelta(minutes=minutes)).time()
    return str(date), str(file_time)


def convert_to_utc(date, file_time):
    date = date.split("-")
    file_time = file_time.split(":")
    date = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                    hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=tzlocal())
    date.replace(tzinfo=tzlocal()).astimezone(tz=utc)
    date = utc.normalize(date)
    return str(date.date()), str(date.time())