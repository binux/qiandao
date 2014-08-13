#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-09 17:52:49

import json
from tornado import gen
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
    def get(self, tplid):
        user = self.current_user
        tpl = self.db.tpl.get(tplid, fields=('id', 'note', 'userid', 'variables'))
        if tpl['userid'] and (not user or tpl['userid'] != user['id']):
            self.finish('<span class="alert alert-danger">没有权限</span>')
            return
        self.render('task_new_var.html', note=tpl['note'], variables=json.loads(tpl['variables']))

class TPLDelHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, tplid):
        user = self.current_user
        tpl = self.db.tpl.get(tplid, fields=('id', 'userid'))
        if tpl['userid']:
            if user['id'] != tpl['userid']:
                raise HTTPError(401)
        else:
            if not user['isadmin']:
                raise HTTPError(401)

        self.db.tpl.delete(tplid)
        referer = self.request.headers.get('referer', '/my/')
        self.redirect(referer)

class TPLRunHandler(BaseHandler):
    @gen.coroutine
    def post(self, tplid):
        user = self.current_user
        tplid = tplid or self.get_argument('_binux_tplid', None)
        if tplid:
            tpl = self.db.tpl.get(tplid, fields=('id', 'userid', 'sitename',
                'siteurl', 'tpl', 'interval', 'last_success'))
            if tpl['userid'] and (not user or tpl['userid'] != user['id']):
                raise HTTPError(401)
            fetch_tpl = self.db.user.decrypt(tpl['userid'], tpl['tpl'])
        else:
            try:
                fetch_tpl = json.loads(self.get_argument('tpl'))
            except:
                raise HTTPError(400)
        try:
            env = dict(
                    variables = json.loads(self.get_argument('env')),
                    session = []
                    )
        except:
            raise HTTPError(400)

        try:
            result = yield self.fetcher.do_fetch(fetch_tpl, env)
        except Exception as e:
            self.finish('<h1 class="alert alert-danger text-center">签到失败</h1><div class="well">%s</div>' % e)
            return

        self.finish('<h1 class="alert alert-success text-center">签到成功</h1>')
        return

class PublicTPLHandler(BaseHandler):
    def get(self):
        tpls = self.db.tpl.list(userid=None, limit=None, fields=('id', 'siteurl', 'sitename', 'banner', 'note', 'disabled', 'lock', 'last_success', 'ctime', 'mtime', 'fork'))

        self.render('tpls_public.html', tpls=tpls)

handlers = [
        ('/tpl/(\d+)/push', TPLPushHandler),
        ('/tpl/(\d+)/var', TPLVarHandler),
        ('/tpl/(\d+)/del', TPLDelHandler),
        ('/tpl/?(\d+)?/run', TPLRunHandler),
        ('/tpls/public', PublicTPLHandler),
        ]
