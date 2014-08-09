#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-07 22:00:27

import socket
import struct

def ip2int(addr):                                                               
    return struct.unpack("!I", socket.inet_aton(addr))[0]                       

def int2ip(addr):                                                               
    return socket.inet_ntoa(struct.pack("!I", addr))                            


import umsgpack
import functools

def func_cache(f):
    _cache = {}

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        key = umsgpack.packb((args, kwargs))
        if key not in _cache:
            _cache[key] = f(*args, **kwargs)
        return _cache[key]

    return wrapper

import datetime

def format_date(date, gmt_offset=-8*60, relative=True, shorter=False, full_format=False):
    """Formats the given date (which should be GMT).

    By default, we return a relative time (e.g., "2 minutes ago"). You
    can return an absolute date string with ``relative=False``.

    You can force a full format date ("July 10, 1980") with
    ``full_format=True``.

    This method is primarily intended for dates in the past.
    For dates in the future, we fall back to full format.
    """
    if not date:
        return '-'
    if isinstance(date, float) or isinstance(date, int):
        date = datetime.datetime.utcfromtimestamp(date)
    now = datetime.datetime.utcnow()
    if date > now:
        #if relative and (date - now).seconds < 60:
            ## Due to click skew, things are some things slightly
            ## in the future. Round timestamps in the immediate
            ## future down to now in relative mode.
            #date = now
        #else:
            ## Otherwise, future dates always use the full format.
            full_format = True
    local_date = date - datetime.timedelta(minutes=gmt_offset)
    local_now = now - datetime.timedelta(minutes=gmt_offset)
    local_yesterday = local_now - datetime.timedelta(hours=24)
    difference = now - date
    seconds = difference.seconds
    days = difference.days

    format = None
    if not full_format:
        if relative and days == 0:
            if seconds < 50:
                return ("1 second ago" if seconds == 1 else \
                        "%(seconds)d seconds ago") % {"seconds": seconds}

            if seconds < 50 * 60:
                minutes = round(seconds / 60.0)
                return ("1 minute ago" if minutes == 1 else \
                        "%(minutes)d minutes ago") % {"minutes": minutes}

            hours = round(seconds / (60.0 * 60))
            return ("1 hour ago" if hours else \
                    "%(hours)d hours ago" ) % {"hours": hours}

        if days == 0:
            format = "%(time)s"
        elif days == 1 and local_date.day == local_yesterday.day and \
                relative:
            format = "yesterday" if shorter else "yesterday at %(time)s"
        elif days < 5:
            format = "%(weekday)s" if shorter else "%(weekday)s at %(time)s"
        elif days < 334:  # 11mo, since confusing for same month last year
            format = "%(month_name)s-%(day)s" if shorter else \
                "%(month_name)s-%(day)s at %(time)s"

    if format is None:
        format = "%(month_name)s %(day)s, %(year)s" if shorter else \
            "%(month_name)s %(day)s, %(year)s at %(time)s"

    str_time = "%d:%02d" % (local_date.hour, local_date.minute)

    return format % {
        "month_name": local_date.month - 1,
        "weekday": local_date.weekday(),
        "day": str(local_date.day),
        "year": str(local_date.year),
        "time": str_time
    }

