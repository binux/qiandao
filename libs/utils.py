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
        later = u"后"
        date, now = now, date
    else:
        later = u"前"
    local_date = date - datetime.timedelta(minutes=gmt_offset)
    local_now = now - datetime.timedelta(minutes=gmt_offset)
    local_yesterday = local_now - datetime.timedelta(hours=24)
    local_tomorrow = local_now + datetime.timedelta(hours=24)
    difference = now - date
    seconds = difference.seconds
    days = difference.days

    format = None
    if not full_format:
        if relative and days == 0:
            if seconds < 50:
                return u"%(seconds)d 秒" % {"seconds": seconds} + later

            if seconds < 50 * 60:
                minutes = round(seconds / 60.0)
                return u"%(minutes)d 分钟" % {"minutes": minutes} + later

            hours = round(seconds / (60.0 * 60))
            return u"%(hours)d 小时" % {"hours": hours} + later

        if days == 0:
            format = "%(time)s"
        elif days == 1 and local_date.day == local_yesterday.day and \
                relative:
            format = u"昨天" if shorter else u"昨天 %(time)s"
        elif days == 1 and local_date.day == local_tomorrow.day and \
                relative:
            format = u"明天" if shorter else u"明天 %(time)s"
        #elif days < 5:
            #format = "%(weekday)s" if shorter else "%(weekday)s %(time)s"
        elif days < 334:  # 11mo, since confusing for same month last year
            format = "%(month_name)s-%(day)s" if shorter else \
                "%(month_name)s-%(day)s %(time)s"

    if format is None:
        format = "%(year)s-%(month_name)s-%(day)s" if shorter else \
            "%(year)s-%(month_name)s-%(day)s %(time)s"

    str_time = "%d:%02d:%02d" % (local_date.hour, local_date.minute, local_date.second)

    return format % {
        "month_name": local_date.month - 1,
        "weekday": local_date.weekday(),
        "day": str(local_date.day),
        "year": str(local_date.year),
        "time": str_time
    }

def utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf8')
    return string

import urllib
import config
from tornado import httpclient

def send_mail(to, subject, text=None, html=None, async=False, _from=u"签到提醒 <noreply@qiandao.today>"):
    if not config.mailgun_key:
        return

    httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
    if async:
        client = httpclient.AsyncHTTPClient()
    else:
        client = httpclient.HTTPClient()

    body = {
            'from': utf8(_from),
            'to': utf8(to),
            'subject': utf8(subject),
            }

    if text:
        body['text'] = utf8(text)
    elif html:
        body['html'] = utf8(html)
    else:
        raise Exception('nedd text or html')

    req = httpclient.HTTPRequest(
            method = "POST",
            url = "https://api.mailgun.net/v2/qiandao.today/messages",
            auth_username = "api",
            auth_password = config.mailgun_key,
            body = urllib.urlencode(body)
            )
    return client.fetch(req)
