#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-09 11:39:25

import json
import time
from tornado import gen

from base import *
from libs.fetcher import Fetcher

class TaskNewHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, tplid):
        user = self.current_user
        fields = ('id', 'sitename', )

        tpls = sorted(self.db.tpl.list(userid=user['id'], fields=fields), key=lambda t: -t['id'])
        tpls.append({})
        tpls += list(self.db.tpl.list(userid=None, fields=fields))

        if not tplid:
            for tpl in tpls:
                if tpl.get('id'):
                    tplid = tpl['id']
                    break
        tplid = int(tplid)

        tpl = self.db.tpl.get(tplid, fields=('userid', 'variables'))
        if tpl['userid'] and tpl['userid'] != user['id']:
            raise HTTPError(401)
        variables = json.loads(self.db.tpl.get(tplid, fields='variables')['variables'])

        self.render('task_new.html', tpls=tpls, tplid=tplid, variables=variables)

    @tornado.web.authenticated
    def post(self, tplid):
        user = self.current_user
        tplid = int(self.get_body_argument('_binux_tplid'))
        tested = int(self.get_body_argument('_binux_tested'))

        env = {}
        for key, value in self.request.body_arguments.iteritems():
            if key.startswith('_binux_'):
                continue
            if not value:
                continue
            env[key] = value[0]
        env = self.db.user.encrypt(user['id'], env)

        taskid = self.db.task.add(tplid, user['id'], env)
        if tested:
            self.db.task.mod(taskid, next=time.time() + 24*60*60)
        else:
            self.db.task.mod(taskid, next=time.time() + 15)

        referer = self.request.headers.get('referer', '/my/')
        self.redirect(referer)

class TaskRunHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, taskid):
        user = self.current_user
        task = self.db.task.get(taskid, fields=('id', 'tplid', 'userid', 'init_env',
            'env', 'session', 'last_success', 'last_failed', 'success_count',
            'failed_count', 'last_failed_count', 'next', 'disabled'))
        if task['userid'] != user['id']:
            raise HTTPError(401)
        if not task:
            raise HTTPError(404)

        tpl = self.db.tpl.get(task['tplid'], fields=('id', 'userid', 'sitename',
            'siteurl', 'tpl', 'interval', 'last_success'))
        if not tpl:
            raise HTTPError(403)
        if tpl['userid'] and tpl['userid'] != user['id']:
            raise HTTPError(401)

        fetch_tpl = self.db.user.decrypt(
                0 if not tpl['userid'] else task['userid'], tpl['tpl'])
        env = dict(
                variables = self.db.user.decrypt(task['userid'], task['init_env']),
                session = [],
                )

        try:
            fetcher = Fetcher()
            new_env = yield fetcher.do_fetch(fetch_tpl, env)
        except Exception as e:
            self.finish('<h1 class="alert alert-danger text-center">签到失败</h1><div class="well">%s</div>' % e)
            return

        self.db.task.mod(task['id'],
                last_success = time.time(),
                last_failed_count = 0,
                success_count = task['success_count'] + 1,
                mtime = time.time(),
                next = time.time() + (tpl['interval'] if tpl['interval'] else 24 * 60 * 60))
        self.finish('<h1 class="alert alert-success text-center">签到成功</h1>')
        return

class TaskLogHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, taskid):
        user = self.current_user
        task = self.db.task.get(taskid, fields=('id', 'tplid', 'userid', 'disabled'))
        if task['userid'] != user['id']:
            raise HTTPError(401)

        tasklog = self.db.tasklog.list(taskid = taskid, fields=('success', 'ctime', 'msg'))

        self.render('tasklog.html', task=task, tasklog=tasklog)

class TaskDelHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, taskid):
        user = self.current_user
        task = self.db.task.get(taskid, fields=('userid', ))
        if task['userid'] == user['id']:
            self.db.task.delete(taskid)
        else:
            raise HTTPError(401)

        referer = self.request.headers.get('referer', '/my/')
        self.redirect(referer)

handlers = [
        ('/task/new/?(\d+)?', TaskNewHandler),
        ('/task/(\d+)/del', TaskDelHandler),
        ('/task/(\d+)/log', TaskLogHandler),
        ('/task/(\d+)/run', TaskRunHandler),
        ]
