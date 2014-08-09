#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-07 22:27:07

import time
import logging
import umsgpack
import mysql.connector

import config
from libs import utils
from basedb import BaseDB

class TPLDB(BaseDB):
    '''
    tpl db

    id, userid, siteurl, sitename, banner, disabled, public, fork, har, tpl, variables, interval, ctime, mtime, atime, last_success
    '''
    __tablename__ = 'tpl'

    def __init__(self, host=config.mysql.host, port=config.mysql.port,
            database=config.mysql.database, user=config.mysql.user, passwd=config.mysql.passwd):
        self.conn = mysql.connector.connect(user=user, password=passwd, host=host, port=port, database=database)

    @property
    def dbcur(self):
        return self.conn.cursor()

    def add(self, userid, har, tpl, variables, interval=None):
        now = time.time()

        insert = dict(
                userid = userid,
                siteurl = None,
                sitename = None,
                banner = None,
                disabled = 0,
                public = 0,
                fork = None,
                har = har,
                tpl = tpl,
                variables = variables,
                interval = interval,
                ctime = now,
                mtime = now,
                atime = now,
                last_success = None,
                )
        return self._insert(**insert)

    def mod(self, id, **kwargs):
        return self._update(where="id=%s", where_values=(id, ), **kwargs)

    def get(self, id, fields=None):
        for tpl in self._select2dic(what=fields, where='id=%s', where_values=(id, )):
            return tpl

    def list(self, fields=None, **kwargs):
        where = '1=1'
        where_values = []
        for key, value in kwargs.iteritems():
            if value is None:
                where += ' and %s is %%s' % self.escape(key)
            else:
                where += ' and %s = %%s' % self.escape(key)
            where_values.append(value)
        for tpl in self._select2dic(what=fields, where=where, where_values=where_values):
            yield tpl
