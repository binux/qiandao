#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-30 16:02:08

import json
from base import *

class IndexHandlers(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/my/')
            return

        tplid = self.get_argument('tplid', None)
        fields = ('id', 'sitename', )
        tpls = sorted(self.db.tpl.list(userid=None, fields=fields), key=lambda t: t['sitename'])
        if not tpls:
            raise HTTPError(404)

        if not tplid:
            for tpl in tpls:
                if tpl.get('id'):
                    tplid = tpl['id']
                    break
        tplid = int(tplid)
        tpl = self.db.tpl.get(tplid, fields=('id', 'userid', 'note', 'variables'))
        if tpl['userid']:
            raise HTTPError(401)
        variables = json.loads(self.db.tpl.get(tplid, fields='variables')['variables'])
        
        return self.render('index.html', tpls=tpls, tplid=tplid, note=tpl['note'], variables=variables)

handlers = [
        ('/', IndexHandlers),
        ]
