#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-09-12 22:39:57
# form requests&tornado

import http.cookiejar as cookielib
from requests.cookies import RequestsCookieJar, get_cookie_header, extract_cookies_to_jar
from collections import UserDict
from urllib.parse import urlparse
from tornado import httpclient, httputil

def dump_cookie(cookie):
    result = {}
    for key in ('name', 'value', 'expires', 'secure', 'port', 'domain', 'path',
            'discard', 'comment', 'comment_url', 'rfc2109'):
        result[key] = getattr(cookie, key)
    result['rest'] = cookie._rest
    return result

class CookieSession(RequestsCookieJar):
    def extract_cookies_to_jar(self, request, response):
        return extract_cookies_to_jar(self, response, request)

    def from_json(self, data):
        for cookie in data:
            self.set(**cookie)

    def to_json(self):
        result = []
        for cookie in iter(self):
            result.append(dump_cookie(cookie))
        return result

    def __getitem__(self, name):
        if isinstance(name, cookielib.Cookie):
            return name.value
        return super().__getitem__(name)

    def to_dict(self):
        result = {}
        for key in self.keys():
            result[key] = self.get(key)
        return result

    def get_cookie_header(self, req):
        get_cookie_header(self, req)
