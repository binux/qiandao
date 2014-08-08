#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-08 20:38:51

import re
import time
import umsgpack

from base import *

class LoginHandler(BaseHandler):
    def get(self):
        return self.render('login.html')

    def post(self):
        email = self.get_argument('email')
        password = self.get_argument('password')
        next = self.get_argument('next', None)
        if self.db.user.challenge(email, password):
            user = self.db.user.get(email=email, fields=('id', 'email', 'nickname', 'role'))
            if not user:
                self.render('login.html', password_error=u'不存在此邮箱或密码错误')
                return

            self.set_secure_cookie('user', umsgpack.packb(user))
            self.db.user.mod(user['id'], atime=time.time(), aip=self.ip2int)
            if not next:
                self.redirect('/my')
        else:
            self.db.redis.evil(self.ip, +5)
            self.render('login.html', password_error=u'不存在此邮箱或密码错误')

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('/')

class RegisterHandler(BaseHandler):
    def get(self):
        return self.render('register.html')

    def post(self):
        email = self.get_argument('email')
        password = self.get_argument('password')

        if not email:
            self.render('register.html', email_error=u'请输入邮箱')
            return
        if email.count('@') != 1 or email.count('.') == 0:
            self.render('register.html', email_error=u'邮箱格式不正确')
            return
        if len(password) < 6:
            self.render('register.html', password_error=u'密码需要大于6位')
            return

        try:
            self.db.user.add(email=email, password=password, ip=self.ip2int)
            user = self.db.user.get(email=email, fields=('id', 'email', 'nickname', 'role'))
            self.set_secure_cookie('user', umsgpack.packb(user))
            self.redirect('/my')
        except self.db.user.DeplicateUser as e:
            self.render('register.html', email_error=u'email地址已注册')

handlers = [
        ('/login', LoginHandler),
        ('/logout', LogoutHandler),
        ('/register', RegisterHandler),
        ]
