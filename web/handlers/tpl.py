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
        tpls = self.db.tpl.list(userid=None, fields=('id', 'sitename'))
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

        #referer = self.request.headers.get('referer', '/my/')
        self.redirect('/pushs')

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
        ('/tpl/(\d+)/push', TPLPushHandler),
        ('/tpl/(\d+)/var', TPLVarHandler),
        ]
