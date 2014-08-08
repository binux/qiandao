#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-08 20:38:51

import umsgpack

from base import *

class LoginHandler(BaseHandler):
    def get(self):
        return self.render('login.html')

    def post(self):
        email = self.get_argument('email')
        password = self.get_argument('password')
        if self.db.user.challenge(email, password):
            user = self.db.user.get(email=email, fields=('id', 'email', 'nickname', 'role'))
            self.set_secure_cookie('user', umsgpack.packb(user))
        else:
            self.db.redis.evil(self.ip, +5)

def RegisterHandler(BaseHandler):
    def get(self):
        return self.render('register.html')

    def post(self):
        email = self.get_argument('email')
        password = self.get_argument('password')
        try:
            self.db.user.add(email=email, password=password, ip=self.ip2int)
            user = self.db.user.get(email=email, fields=('id', 'email', 'nickname', 'role'))
            self.set_secure_cookie('user', umsgpack.packb(user))
            self.redirect('/')
        except self.db.user.DeplicateUser as e:
            self.render('register.html', error='email地址已注册')

handlers = [
        ('/login', LoginHandler),
        ('/register', RegisterHandler),
        ]
