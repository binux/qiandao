#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-09 14:43:13

import logging
import tornado.log
import tornado.ioloop
from tornado import gen

import db
import time
import config
from libs.fetcher import Fetcher

tornado.log.enable_pretty_logging()
logger = logging.getLogger('qiandao.worker')
class MainWorker(object):
    def __init__(self):
        self.running = False
        class DB(object):
            user = db.UserDB()
            tpl = db.TPLDB()
            task = db.TaskDB()
            tasklog = db.TaskLogDB()
        self.db = DB

    def __call__(self):
        if self.running:
            return
        self.running = self.run()
        def done(future):
            self.running = None
            return future.result()
        self.running.add_done_callback(done)

    @gen.coroutine
    def run(self):
        running = []
        try:
            for task in self.scan():
                running.append(self.do(task))
                if len(running) > 50:
                    logging.info('scaned %d task, waiting...', len(running))
                    _ = yield running[:10]
                    running = running[10:]
            logging.info('scaned %d task, waiting...', len(running))
            _ = yield running
        except Exception as e:
            logging.exception(e)
        raise gen.Return(None)

    scan_fields = ('id', 'tplid', 'userid', 'init_env', 'env', 'session', 'last_success', 'last_failed', 'success_count', 'failed_count', 'last_failed_count', 'next')
    def scan(self):
        return self.db.task.scan(fields=self.scan_fields)

    @staticmethod
    def failed_count_to_time(last_failed_count):
        if last_failed_count == 0:
            next = 10 * 60
        elif last_failed_count == 1:
            next = 110 * 60
        elif last_failed_count == 2:
            next = 240 * 60
        elif last_failed_count == 3:
            next = 360 * 60
        elif last_failed_count < 8:
            next = 12 * 60 * 60
        else:
            next = None
        return next

    @gen.coroutine
    def do(self, task):
        if task['next'] > time.time():
            raise gen.Return(False)
        if task['disabled']:
            self.db.task.mod(task['id'], next=None)
            raise gen.Return(False)
        start = time.time()
        taskid = task['id']
        tplid = task['tplid']
        userid = task['userid']
        init_env = task['init_env']
        env = task['env']
        session = task['session']
        last_success = task['last_success']
        last_failed = task['last_failed']
        success_count = task['success_count']
        failed_count = task['failed_count']
        last_failed_count = task['last_failed_count']
        next = task['next']

        try:

            tplobj = self.db.tpl.get(tplid, fields=('userid', 'tpl', 'interval', 'last_success'))
            if not tplobj:
                self.db.task.mod(task['id'], next=None, disabled=1)
                raise gen.Return(False)

            if tplobj['userid'] and tplobj['userid'] != userid:
                raise Exception('cannot decrypt the tpl, user may not the owner.')

            tpl = self.db.user.decrypt(0 if not tplobj['userid'] else userid, tplobj['tpl'])
            variables = self.db.user.decrypt(userid, init_env)
            session = []
            env = dict(
                    variables = variables,
                    session = session
                    )

            env = yield self.fetch(tpl, env)

            variables = self.db.user.encrypt(userid, env['variables'])
            session = self.db.user.encrypt(userid,
                    env['session'] if isinstance(env['session'], basestring) else env['session'].to_json())

            # todo next not mid night
            failed_time_delta = 0
            for i in range(last_failed_count):
                failed_time_delta += self.failed_count_to_time(last_failed_count)
            next = time.time() + (tplobj['interval'] if tplobj['interval'] else 24 * 60 * 60) - failed_time_delta

            self.db.tasklog.add(taskid, True)
            self.db.task.mod(taskid, last_success=time.time(),
                    last_failed_count=0, success_count=success_count+1,
                    env=variables, session=session, next=next)
            if time.time() - (tplobj['last_success'] or 0) > 60 * 60:
                self.db.tpl.mod(tplid, last_success=time.time())
            logger.info('taskid:%d tplid:%d successed! %.4fs', task['id'], task['tplid'], time.time()-start)
        except Exception as e:
            logger.error('taskid:%d tplid:%d failed! %s %.4fs', task['id'], task['tplid'], e, time.time()-start)
            self.db.tasklog.add(task['id'], False, msg=repr(e))

            next_time_delta = self.failed_count_to_time(last_failed_count)
            if next_time_delta:
                next = time.time() + next_time_delta
            else:
                next = None
                self.task_failed(task)

            self.db.task.mod(task['id'],
                    last_failed=time.time(),
                    failed_count=task['failed_count']+1, last_failed_count=last_failed_count+1,
                    next=next)
        raise gen.Return(None)

    def task_failed(self, task):
        self.db.task.mod(task['id'], disabled=1)

    @staticmethod
    @gen.coroutine
    def fetch(tpl, env):
        fetcher = Fetcher()
        for i, entry in enumerate(tpl):
            try:
                result = yield fetcher.fetch(dict(
                    request = entry['request'],
                    rule = entry['rule'],
                    env = env,
                    ))
                env = result['env']
            except Exception as e:
                raise Exception('failed at %d request, %r', i, e)
            if not result['success']:
                raise Exception('failed at %d request, code:%s', i, result['response'].code)
        raise gen.Return(env)

if __name__ == '__main__':
    worker = MainWorker()
    io_loop = tornado.ioloop.IOLoop.instance()
    tornado.ioloop.PeriodicCallback(worker, config.check_task_loop, io_loop).start()
    worker()
    io_loop.start()
