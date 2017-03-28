#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-09 14:43:13

import time
import datetime
import logging
import tornado.log
import tornado.ioloop
from tornado import gen

import config
from libs import utils
from libs.fetcher import Fetcher

logger = logging.getLogger('qiandao.worker')
class MainWorker(object):
    def __init__(self):
        self.running = False

        if config.db_type == 'sqlite3':
            import sqlite3_db as db
        else:
            import db

        class DB(object):
            user = db.UserDB()
            tpl = db.TPLDB()
            task = db.TaskDB()
            tasklog = db.TaskLogDB()
        self.db = DB
        self.fetcher = Fetcher()

    def __call__(self):
        if self.running:
            return
        self.running = self.run()
        def done(future):
            self.running = None
            success, failed = future.result()
            if success or failed:
                logger.info('%d task done. %d success, %d failed' % (success+failed, success, failed))
            return
        self.running.add_done_callback(done)

    @gen.coroutine
    def run(self):
        running = []
        success = 0
        failed = 0
        try:
            for task in self.scan():
                running.append(self.do(task))
                if len(running) > 50:
                    logging.debug('scaned %d task, waiting...', len(running))
                    result = yield running[:10]
                    for each in result:
                        if each:
                            success += 1
                        else:
                            failed += 1
                    running = running[10:]
            logging.debug('scaned %d task, waiting...', len(running))
            result = yield running
            for each in result:
                if each:
                    success += 1
                else:
                    failed += 1
        except Exception as e:
            logging.exception(e)
        raise gen.Return((success, failed))

    scan_fields = ('id', 'tplid', 'userid', 'init_env', 'env', 'session', 'last_success', 'last_failed', 'success_count', 'failed_count', 'last_failed_count', 'next', 'disabled', )
    def scan(self):
        return self.db.task.scan(fields=self.scan_fields)

    @staticmethod
    def failed_count_to_time(last_failed_count, interval=None):
        if last_failed_count == 0:
            next = 10 * 60
        elif last_failed_count == 1:
            next = 110 * 60
        elif last_failed_count == 2:
            next = 240 * 60
        elif last_failed_count == 3:
            next = 360 * 60
        elif last_failed_count < 8:
            next = 11 * 60 * 60
        else:
            next = None

        if interval is None:
            interval = 24 * 60 * 60
        if next and next > interval / 2:
            next = interval / 2
        return next

    @staticmethod
    def fix_next_time(next, gmt_offset=-8*60):
        date = datetime.datetime.utcfromtimestamp(next)
        local_date = date - datetime.timedelta(minutes=gmt_offset)
        if local_date.hour < 2:
            next += 2 * 60 * 60
        if local_date.hour > 21:
            next -= 3 * 60 * 60
        return next

    @staticmethod
    def is_tommorrow(next, gmt_offset=-8*60):
        date = datetime.datetime.utcfromtimestamp(next)
        now = datetime.datetime.utcnow()
        local_date = date - datetime.timedelta(minutes=gmt_offset)
        local_now = now - datetime.timedelta(minutes=gmt_offset)
        local_tomorrow = local_now + datetime.timedelta(hours=24)

        if local_date.day == local_tomorrow.day and not now.hour > 22:
            return True
        elif local_date.hour > 22:
            return True
        else:
            return False

    @gen.coroutine
    def do(self, task):
        user = self.db.user.get(task['userid'], fields=('id', 'email', 'email_verified', 'nickname'))
        tpl = self.db.tpl.get(task['tplid'], fields=('id', 'userid', 'sitename', 'siteurl', 'tpl',
            'interval', 'last_success'))

        if task['disabled']:
            self.db.tasklog.add(task['id'], False, msg='task disabled.')
            self.db.task.mod(task['id'], next=None, disabled=1)
            raise gen.Return(False)

        if not user:
            self.db.tasklog.add(task['id'], False, msg='no such user, disabled.')
            self.db.task.mod(task['id'], next=None, disabled=1)
            raise gen.Return(False)

        if not tpl:
            self.db.tasklog.add(task['id'], False, msg='tpl missing, task disabled.')
            self.db.task.mod(task['id'], next=None, disabled=1)
            raise gen.Return(False)

        if tpl['userid'] and tpl['userid'] != user['id']:
            self.db.tasklog.add(task['id'], False, msg='no permission error, task disabled.')
            self.db.task.mod(task['id'], next=None, disabled=1)
            raise gen.Return(False)

        start = time.time()
        try:
            fetch_tpl = self.db.user.decrypt(0 if not tpl['userid'] else task['userid'], tpl['tpl'])
            env = dict(
                    variables = self.db.user.decrypt(task['userid'], task['init_env']),
                    session = [],
                    )

            new_env = yield self.fetcher.do_fetch(fetch_tpl, env)

            variables = self.db.user.encrypt(task['userid'], new_env['variables'])
            session = self.db.user.encrypt(task['userid'],
                    new_env['session'].to_json() if hasattr(new_env['session'], 'to_json') else new_env['session'])

            # todo next not mid night
            next = time.time() + max((tpl['interval'] if tpl['interval'] else 24 * 60 * 60), 30*60)
            if tpl['interval'] is None:
                next = self.fix_next_time(next)

            # success feedback
            self.db.tasklog.add(task['id'], success=True, msg=new_env['variables'].get('__log__'))
            self.db.task.mod(task['id'],
                    last_success=time.time(),
                    last_failed_count=0,
                    success_count=task['success_count']+1,
                    env=variables,
                    session=session,
                    mtime=time.time(),
                    next=next)
            self.db.tpl.incr_success(tpl['id'])

            logger.info('taskid:%d tplid:%d successed! %.4fs', task['id'], task['tplid'], time.time()-start)
        except Exception as e:
            # failed feedback
            next_time_delta = self.failed_count_to_time(task['last_failed_count'], tpl['interval'])
            if next_time_delta:
                disabled = False
                next = time.time() + next_time_delta
            else:
                disabled = True
                next = None

            self.db.tasklog.add(task['id'], success=False, msg=unicode(e))
            self.db.task.mod(task['id'],
                    last_failed=time.time(),
                    failed_count=task['failed_count']+1,
                    last_failed_count=task['last_failed_count']+1,
                    disabled = disabled,
                    mtime = time.time(),
                    next=next)
            self.db.tpl.incr_failed(tpl['id'])

            if task['success_count'] and task['last_failed_count'] and user['email_verified'] and user['email']\
                    and self.is_tommorrow(next):
                try:
                    _ = yield utils.send_mail(to=user['email'], subject=u"%s - 签到失败%s" % (
                        tpl['sitename'], u' 已停止' if disabled else u""),
                    text=u"""
您的 %(sitename)s [ %(siteurl)s ] 签到任务，执行 %(cnt)d次 失败。%(disable)s

下一次重试在一天之后，为防止签到中断，给您发送这份邮件。

访问： http://%(domain)s/task/%(taskid)s/log 查看日志。
                    """ % dict(
                        sitename=tpl['sitename'] or u'未命名',
                        siteurl=tpl['siteurl'] or u'',
                        cnt=task['last_failed_count'] + 1,
                        disable=u"因连续多次失败，已停止。" if disabled else u"",
                        domain=config.domain,
                        taskid=task['id'],
                        ), async=True)
                except Exception as e:
                    logging.error('send mail error: %r', e)

            logger.error('taskid:%d tplid:%d failed! %r %.4fs', task['id'], task['tplid'], e, time.time()-start)
            raise gen.Return(False)
        raise gen.Return(True)

    def task_failed(self, task, user, tpl, e):
        pass
        #if user['email'] and user['email_verified']:
            #return utils.send_mail(to=user['email'],
                    #subject=u"%s - 签到失败提醒" % (tpl['sitename']),
                    #text=u"""
                    #您在 签到.today ( http://qiandao.today )
                    #""")

if __name__ == '__main__':
    tornado.log.enable_pretty_logging()
    worker = MainWorker()
    io_loop = tornado.ioloop.IOLoop.instance()
    tornado.ioloop.PeriodicCallback(worker, config.check_task_loop, io_loop).start()
    worker()
    io_loop.start()
