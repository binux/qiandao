#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-09 21:34:01

import json
import time
import urlparse
from datetime import datetime

from base import *

def tpl2har(tpl):
    def build_request(en):
        url = urlparse.urlparse(en['request']['url'])
        request = dict(
                method = en['request']['method'],
                url = en['request']['url'],
                httpVersion = 'HTTP/1.1',
                headers = [
                    {'name': x['name'], 'value': x['value'], 'checked': True} for x in\
                            en['request'].get('headers', [])],
                queryString = [
                    {'name': n, 'value': v} for n, v in\
                            urlparse.parse_qsl(url.query)],
                cookies = [
                    {'name': x['name'], 'value': x['value'], 'checked': True} for x in\
                            en['request'].get('cookies', [])],
                headersSize = -1,
                bodySize = len(en['request'].get('body')) if en['request'].get('body') else 0,


                )
        if en['request'].get('body'):
            request['postdata'] = dict(
                    text = en['request'].get('body'),
                    )
        return request

    entries = []
    for en in tpl:
        entry = dict(
                checked = True,
                startedDateTime = datetime.now().isoformat(),
                time = 1,
                request = build_request(en),
                response = {},
                cache = {},
                timings = {},
                connections = "0",
                pageref = "page_0",

                success_asserts = en.get('rule', {}).get('success_asserts', []),
                failed_asserts = en.get('rule', {}).get('failed_asserts', []),
                extract_variables = en.get('rule', {}).get('extract_variables', []),
                )
        entries.append(entry)
    return dict(
            log = dict(
                creator = dict(
                    name = 'binux',
                    version = 'qiandao'
                    ),
                entries = entries,
                pages = [],
                version = '1.2'
                )
            )

class PushListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, status=None):
        user = self.current_user
        admin = 'admin' in (user.get('role', '') or '')

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
        _f = {}
        if status is not None:
            _f['status'] = status
        for each in self.db.push_request.list(from_userid = user['id'], **_f):
            pushs.append(join(each))
        if admin:
            for each in self.db.push_request.list(from_userid = None, **_f):
                pushs.append(join(each))
        pushs.reverse()

        pulls = []
        for each in self.db.push_request.list(to_userid = user['id'], **_f):
            pulls.append(join(each))
        if admin:
            for each in self.db.push_request.list(to_userid = None, **_f):
                pulls.append(join(each))
        pulls.reverse()

        self.render('push_list.html', pushs=pushs, pulls=pulls)

class PushActionHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, prid, action):
        user = self.current_user
        pr = self.db.push_request.get(prid)

        if action in ('accept', 'refuse'):
            if pr['to_userid']:
                if user['id'] != pr['to_userid']:
                    raise HTTPError(401)
            elif not user['isadmin']:
                raise HTTPError(401)
        elif action in ('cancel', ):
            if not user['isadmin'] and user['id'] != pr['from_userid']:
                raise HTTPError(401)

        getattr(self, action)(pr)

        tpl_lock = len(list(self.db.push_request.list(from_tplid=pr['from_tplid'],
            status=self.db.push_request.PENDING, fields='1')))
        print tpl_lock
        if not tpl_lock:
            self.db.tpl.mod(pr['from_tplid'], lock=False)

        self.redirect('/pushs')

    def accept(self, pr):
        tplobj = self.db.tpl.get(pr['from_tplid'], fields=('id', 'userid', 'tpl', 'variables', 'sitename', 'siteurl', 'banner', 'interval'))
        if not tplobj:
            raise Exception('from tpl missing.')
        # re-encrypt
        tpl = self.db.user.decrypt(pr['from_userid'], tplobj['tpl'])
        har = self.db.user.encrypt(pr['to_userid'], tpl2har(tpl))
        tpl = self.db.user.encrypt(pr['to_userid'], tpl)

        if not pr['to_tplid']:
            tplid = self.db.tpl.add(
                    userid = pr['to_userid'],
                    har = har,
                    tpl = tpl,
                    variables = tplobj['variables'],
                    interval = tplobj['interval'],
                    )
            self.db.tpl.mod(tplid,
                    sitename = tplobj['sitename'],
                    siteurl = tplobj['siteurl'],
                    banner = tplobj['banner'],
                    fork = pr['from_tplid'],
                    )
        else:
            tplid = pr['to_tplid']
            self.db.tpl.mod(tplid,
                    har = har,
                    tpl = tpl,
                    variables = tplobj['variables'],
                    interval = tplobj['interval'],
                    sitename = tplobj['sitename'],
                    siteurl = tplobj['siteurl'],
                    banner = tplobj['banner'],
                    fork = pr['from_tplid'],
                    )
        self.db.push_request.mod(pr['id'], status=self.db.push_request.ACCEPT)

    def cancel(self, pr):
        self.db.push_request.mod(pr['id'], status=self.db.push_request.CANCEL)

    def refuse(self, pr):
        self.db.push_request.mod(pr['id'], status=self.db.push_request.REFUSE)

class PushViewHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, prid):
        return self.render('har/editor.html')

    @tornado.web.authenticated
    def post(self, prid):
        user = self.current_user
        pr = self.db.push_request.get(prid, fields=('id', 'from_tplid', 'from_userid', 'to_tplid', 'to_userid'))
        if pr['to_userid']:
            if user['id'] != pr['to_userid']:
                raise HTTPError(401)
        elif not user['isadmin']:
            raise HTTPError(401)

        tpl = self.db.tpl.get(pr['from_tplid'], fields=('id', 'userid', 'sitename', 'siteurl', 'tpl', 'variables', ))
        if not tpl:
            self.set_status(404)
            self.finish('模板不存在')
            return

        tpl['har'] = tpl2har(self.db.user.decrypt(pr['from_userid'], tpl['tpl']))
        tpl['variables'] = json.loads(tpl['variables'])
        self.finish(dict(
            filename = tpl['sitename'] or '未命名模板',
            har = tpl['har'],
            env = dict((x, '') for x in tpl['variables']),
            sitename = tpl['sitename'],
            siteurl = tpl['siteurl'],
            readonly = True,
            ))

handlers = [
        ('/pushs/?(\d+)?', PushListHandler),
        ('/push/(\d+)/(cancel|accept|refuse)', PushActionHandler),
        ('/push/(\d+)/view', PushViewHandler),
        ]
