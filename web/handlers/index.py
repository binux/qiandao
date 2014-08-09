#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-30 16:02:08

from base import *

class IndexHandlers(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/my/')
            return
        return self.render('index.html')

handlers = [
        ('/', IndexHandlers),
        ]
