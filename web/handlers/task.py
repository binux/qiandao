#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-09 11:39:25

import json
import time
from base import *

class TaskNewHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, tplid):
        user = self.current_user
        fields = ('id', 'sitename', )

        tpls = sorted(self.db.tpl.list(userid=user['id'], fields=fields), key=lambda t: -t['id'])
        tpls += list(self.db.tpl.list(userid=None, fields=fields))

        if not tplid:
            tplid = tpls[0]['id']
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
            self.db.task.mod(taskid, next=time.time() + 2*60)

        referer = self.request.headers.get('referer', '/my/')
        self.redirect(referer)

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
        ('/task/del/(\d+)', TaskDelHandler),
        ]
