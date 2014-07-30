#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-30 12:38:34

import logging
import tornado.log
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer

import config
from web.app import Application

if __name__ == "__main__":
    http_server = HTTPServer(Application(), xheaders=True)
    http_server.bind(config.port, config.bind)
    http_server.start()

    tornado.log.enable_pretty_logging()

    logging.info("http server started on %s:%s", config.bind, config.port)
    IOLoop.instance().start()
