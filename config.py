#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-30 12:21:48

from Crypto.Hash import SHA256

debug = True
gzip = True
bind = '0.0.0.0'
port = 8923

class mysql(object):
    host = 'localhost'
    port = '3306'
    database = 'qiandao'
    user = 'root'
    passwd = None

pbkdf2_iterations = 400
aes_key = SHA256.new('binux').digest()
cookie_secret = SHA256.new('binux').digest()
check_task_loop = 10000
