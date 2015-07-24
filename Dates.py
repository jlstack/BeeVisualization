__author__ = 'lukestack'

import pytz
from dateutil import tz
from datetime import datetime, timedelta


utc = pytz.timezone('UTC')
START_DATE = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0, tzinfo=utc)
# Program will stop working on 2106-02-07T06:28:15Z


def to_hex(date, file_time):
    """
    Date and time should be in the user's local time and will be converted into UTC time when necessary.
    :param date: a specified date on or after epoch(1970-01-01) UTC (YYYY-MM-DD)
    :param file_time: a specified time(HH:MM:SS)
    :return: corresponding hex value for specified date and time and the directory it should be located in
    """
    date, file_time = convert_to_utc(date, file_time)  # converts to UTC to make time calculations easier
    date = date.split("-")
    file_time = file_time.split(":")
    d = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                 hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=utc)
    seconds = int((d - START_DATE).total_seconds())
    return '{:08x}'.format(seconds), '/'.join('{:08x}'.format(seconds)[:-1]) + "/"


def to_date(hex_num):
    """
    The hex value is the number of seconds since epoch.
    This number of seconds is added to epoch, giving you the corresponding date and time.
    :param hex_num: hex value in range 0 - FFFFFFFF
    :return: local date and time for hex value
    """
    seconds = int(hex_num, 16)
    date = str((START_DATE + timedelta(seconds=seconds)).date())
    file_time = str((START_DATE + timedelta(seconds=seconds)).time())
    date, file_time = convert_to_local(str(date), str(file_time))  # converts back to local time
    return date, file_time


def convert_to_utc(date, file_time):
    """
    Converts a local date and time to the equivalent UTC date and time.
    :param date: specified date in local time (YYYY-MM-DD)
    :param file_time: specified date in local time
    :return: utc date and time equivalent for specified local date and time
    """
    date = date.split("-")
    file_time = file_time.split(":")
    date = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                    hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=tz.tzlocal())
    date.replace(tzinfo=tz.tzlocal()).astimezone(tz=utc)
    date = utc.normalize(date)
    return str(date.date()), str(date.time())


def convert_to_local(date, file_time):
    """
    Converts a UTC date and time to the equivalent local date and time.
    :param date: specified date in UTC time (YYYY-MM-DD)
    :param file_time: specified date in UTC time
    :return: local date and time equivalent for specified UTC date and time
    """
    local = tz.tzlocal()
    date = date.split("-")
    file_time = file_time.split(":")
    date = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                    hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=utc)
    date.replace(tzinfo=utc)
    date = date.astimezone(tz=local)
    return str(date.date()), str(date.time())


def add_seconds_to_date(date, file_time, seconds):
    """
    Adds a specified number of seconds to a given date and time.
    Local time is assumed.
    :param date: a specified date(YYYY-MM-DD)
    :param file_time: a specified time(HH:MM:SS)
    :param seconds: number of seconds to be added to input date and time
    :return: date and time after seconds have been added
    """
    date = date.split("-")
    file_time = file_time.split(":")
    d = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]),
                 hour=int(file_time[0]), minute=int(file_time[1]), second=int(file_time[2]), tzinfo=tz.tzlocal())
    date = str((d + timedelta(seconds=seconds)).date())
    file_time = str((d + timedelta(seconds=seconds)).time())
    return date, file_time


def get_current_date():
    """
    Retrieves current local date and time.
    :return: current local date and time
    """
    now = datetime.now()
    curr_time = str(now.time())
    curr_time = curr_time[:curr_time.rfind('.')]
    curr_date = str(now.date())
    return curr_date, curr_time


def time_diff(date1, file_time1, date2, file_time2):
    """
    Finds the total number of seconds between two date/times
    :param date1: a specified date(YYYY-MM-DD)
    :param file_time1: a specified time(HH:MM:SS)
    :param date2: a specified date(YYYY-MM-DD)
    :param file_time2: a specified time(HH:MM:SS)
    :return: total number of seconds between two times
    """
    date1 = date1.split("-")
    file_time1 = file_time1.split(":")
    d1 = datetime(year=int(date1[0]), month=int(date1[1]), day=int(date1[2]),
                  hour=int(file_time1[0]), minute=int(file_time1[1]), second=int(file_time1[2]), tzinfo=tz.tzlocal())
    date2 = date2.split("-")
    file_time2 = file_time2.split(":")
    d2 = datetime(year=int(date2[0]), month=int(date2[1]), day=int(date2[2]),
                  hour=int(file_time2[0]), minute=int(file_time2[1]), second=int(file_time2[2]), tzinfo=tz.tzlocal())
    diff = d2 - d1
    return int(diff.total_seconds())