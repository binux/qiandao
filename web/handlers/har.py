#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-01 10:35:08

import json
import umsgpack
from tornado import gen
from jinja2 import Environment, meta

from base import *
from libs.fetcher import Fetcher

class HAREditor(BaseHandler):
    def get(self, id):
        return self.render('har/editor.html')

class HARTest(BaseHandler):
    @gen.coroutine
    def post(self):
        data = json.loads(self.request.body)
        ret = yield Fetcher().fetch(data)

        result = {
                'success': ret['success'],
                'har': Fetcher.response2har(ret['response']),
                'env': {
                    'variables': ret['env']['variables'],
                    'session': ret['env']['session'].to_json(),
                    }
                }

        self.finish(result)

class HARSave(BaseHandler):
    @staticmethod
    def get_variables(tpl):
        variables = set()
        extracted = set()
        env = Environment()
        for entry in tpl:
            req = entry['request']
            rule = entry['rule']
            var = set()

            def _get(obj, key):
                if not obj.get(key):
                    return
                ast = env.parse(obj[key])
                var.update(meta.find_undeclared_variables(ast))

            _get(req, 'method')
            _get(req, 'url')
            _get(req, 'data')
            for header in req['headers']:
                _get(header, 'name')
                _get(header, 'value')
            for cookie in req['cookies']:
                _get(cookie, 'name')
                _get(cookie, 'value')

            variables.update(var - extracted)
            extracted.update(set(x['name'] for x in rule.get('extract_variables', [])))
        return variables

    @tornado.web.authenticated
    def post(self):
        userid = self.current_user['id']
        data = json.loads(self.request.body)

        har = self.db.user.encrypt(userid, data['har'])
        tpl = self.db.user.encrypt(userid, data['tpl'])
        variables = json.dumps(list(self.get_variables(data['tpl'])))

        if data.get('id'):
            id = data['id']
            self.db.tpl.mod(id, har=har, tpl=tpl, variables=variables)
        else:
            id = self.db.tpl.add(userid, har, tpl, variables)
            if not id:
                raise Exception('create tpl error')
        self.db.tpl.mod(id, sitename=data.get('sitename'), siteurl=data.get('siteurl'))
        self.redirect('/har/edit/%d' % id)

handlers = [
        (r'/har/edit/?(\d+)?', HAREditor),
        (r'/har/test', HARTest),
        (r'/har/save', HARSave),
        ]
