#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-30 12:21:48

import os
import hashlib
import urlparse

debug = True
gzip = True
bind = '0.0.0.0'
port = int(os.getenv('PORT', 8923))
https = bool(os.getenv('ENABLE_HTTPS', False))
cookie_days = 5
mysql_url = urlparse.urlparse(os.getenv('JAWSDB_MARIA_URL', ''))
redis_url = urlparse.urlparse(os.getenv('REDISCLOUD_URL', ''))

class mysql(object):
    host = mysql_url.hostname or 'localhost'
    port = mysql_url.port or '3306'
    database = mysql_url.path[1:] or 'qiandao'
    user = mysql_url.username or 'qiandao'
    passwd = mysql_url.password or None

class sqlite3(object):
    path = './database.db'

db_type = os.getenv('DB_TYPE', 'sqlite3')

class redis(object):
    host = redis_url.hostname or 'localhost'
    port = redis_url.port or 6379
    passwd = redis_url.password or None
    db = int(os.getenv('REDIS_DB_INDEX', 1))
evil = 100

pbkdf2_iterations = 400
aes_key = hashlib.sha256(os.getenv('AES_KEY', 'binux')).digest()
cookie_secret = hashlib.sha256(os.getenv('COOKIE_SECRET', 'binux')).digest()
check_task_loop = 10000
download_size_limit = 1*1024*1024
proxies = []

mail_domain = "mail.qiandao.today"
mailgun_key = ""
ga_key = ""

try:
    from local_config import *
except ImportError:
    pass
