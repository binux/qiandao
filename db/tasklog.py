#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-08 20:18:29

import time
import logging
import mysql.connector

import config
from libs import utils
from basedb import BaseDB

class TaskLogDB(BaseDB):
    '''
    task log db

    id, taskid, success, ctime, msg
    '''
    __tablename__ = 'tasklog'

    def __init__(self, host=config.mysql.host, port=config.mysql.port,
            database=config.mysql.database, user=config.mysql.user, passwd=config.mysql.passwd):
        self.conn = mysql.connector.connect(user=user, password=passwd, host=host, port=port, database=database)

    @property
    def dbcur(self):
        return self.conn.cursor()

    def add(self, taskid, success, msg=''):
        now = time.time()

        insert = dict(
                taskid = taskid,
                success = success,
                msg = msg,
                ctime = now,
                )
        return self._insert(**insert)
