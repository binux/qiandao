#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-09 17:52:49

import json
from base import *
from libs import utils

class TPLPushHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, tplid):
        user = self.current_user
        tpl = self.db.tpl.get(tplid, fields=('id', 'userid', 'sitename'))
        if tpl['userid'] != user['id']:
            self.finish(u'<span class="alert alert-danger">没有权限</span>')
            return
        tpls = self.db.tpl.list(None, fields=('id', 'sitename'))
        self.render('tpl_push.html', tpl=tpl, tpls=tpls)

    @tornado.web.authenticated
    def post(self, tplid):
        user = self.current_user
        tplid = int(tplid)
        tpl = self.db.tpl.get(tplid, fields=('userid', ))
        if tpl['userid'] != user['id']:
            self.finish(u'<span class="alert alert-danger">没有权限</span>')
            return

        to_tplid = int(self.get_argument('totpl'))
        msg = self.get_argument('msg')
        if to_tplid == 0:
            to_tplid = None
            to_userid = None
        else:
            totpl = self.db.tpl.get(to_tplid, fields=('userid', ))
            if not totpl:
                self.finish(u'<span class="alert alert-danger">模板不存在</span>')
                return
            to_userid = totpl['userid']

        self.db.push_request.add(from_tplid=tplid, from_userid=user['id'],
                to_tplid=to_tplid, to_userid=to_userid, msg=msg)
        self.db.tpl.mod(tplid, lock=True)

        referer = self.request.headers.get('referer', '/my/')
        self.redirect(referer)

class PushListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, status=0):
        user = self.current_user
        admin = 'admin' in (user.get('role', '') or '')
        status = status or 0

        @utils.func_cache
        def get_user(userid):
            if not userid:
                return { 'nickname': u'公开' }
            user = self.db.user.get(userid, fields='nickname, email, email_verified')
            if not user:
                return { 'nickname': u'查无此人' }
            return user

        @utils.func_cache
        def get_tpl(tplid):
            if not tplid:
                return {}
            tpl = self.db.tpl.get(tplid, fields=('sitename', 'siteurl', 'ctime', 'mtime', 'last_success'))
            return tpl or {}

        def join(pr):
            from_user = get_user(pr['from_userid'])
            pr['from_user_name'] = from_user['nickname']
            if admin:
                pr['from_user_email'] = from_user.get('email')
                pr['from_user_email_verified'] = from_user.get('email_verified')
            to_user = get_user(pr['to_userid'])
            pr['to_user_name'] = to_user['nickname']
            if admin:
                pr['to_user_email'] = to_user.get('email')
                pr['to_user_email_verified'] = to_user.get('email_verified')

            pr['from_tpl'] = get_tpl(pr['from_tplid'])
            pr['to_tpl'] = get_tpl(pr['to_tplid'])
            return pr

        pushs = []
        for each in self.db.push_request.list(from_userid = user['id'], status=status):
            pushs.append(join(each))
        if admin:
            for each in self.db.push_request.list(from_userid = None, status=status):
                pushs.append(join(each))

        pulls = []
        for each in self.db.push_request.list(to_userid = user['id'], status=status):
            pulls.append(join(each))
        if admin:
            for each in self.db.push_request.list(to_userid = None, status=status):
                pulls.append(join(each))

        self.render('push_list.html', pushs=pushs, pulls=pulls)

class TPLVarHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, tplid):
        user = self.current_user
        tpl = self.db.tpl.get(tplid, fields=('userid', 'variables'))
        if tpl['userid'] and tpl['userid'] != user['id']:
            self.finish('<span class="alert alert-danger">没有权限</span>')
            return
        self.render('task_new_var.html', variables=json.loads(tpl['variables']))

handlers = [
        ('/tpl/pushs/?(\d+)?', PushListHandler),
        ('/tpl/push/(\d+)', TPLPushHandler),
        ('/tpl/push/view/(\d+)', TPLPushHandler),
        ('/tpl/var/?(\d+)?', TPLVarHandler),
        ]
