#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 11:55:41

import re
import base64
import logging
import urlparse
from tornado import gen, concurrent, httpclient

from datetime import datetime
from jinja2 import Template
from libs import cookie_utils

logger = logging.getLogger('qiandao.fetcher')

class Fetcher(object):
    def __init__(self):
        httpclient.AsyncHTTPClient.configure(
                "tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.client = httpclient.AsyncHTTPClient()

    @staticmethod
    def render(request, env):
        def _render(obj, key):
            if obj.get(key):
                obj[key] = Template(obj[key]).render(**env)

        _render(request, 'method')
        _render(request, 'url')
        for header in request['headers']:
            _render(header, 'name')
            _render(header, 'value')
        for cookie in request['cookies']:
            _render(cookie, 'name')
            _render(cookie, 'value')
        _render(request, 'data')
        return request

    @staticmethod
    def build_request(obj):
        """
        obj = {
          request: {
            method: 
            url: 
            headers: [{name: , value: }, ]
            cookies: [{name: , value: }, ]
            data:
          }
          rule: {
            success_asserts: [{re: , from: 'content'}, ]
            failed_asserts: [{re: , from: 'content'}, ]
            extract_variables: [{name: , re:, from: 'content'}, ]
          }
          env: {
            variables: {
              name: value
            }
            session: [
            ]
          }
        }
        """

        env = obj['env']
        rule = obj['rule']
        request = Fetcher.render(obj['request'], env['variables'])

        method = request['method']
        url = request['url']
        headers = dict((e['name'], e['value']) for e in request['headers'])
        cookies = dict((e['name'], e['value']) for e in request['cookies'])
        data = request.get('data')

        req = httpclient.HTTPRequest(
                url = url,
                method = method,
                headers = headers,
                body = data,
                follow_redirects = False,
                max_redirects = 0,
                decompress_response = True,
                allow_nonstandard_methods = True,
                allow_ipv6 = True,
                )

        session = cookie_utils.CookieSession()
        session.from_json(obj['env']['session'])
        session.update(cookies)
        cookie_header = session.get_cookie_header(req)
        if cookie_header:
            req.headers['Cookie'] = cookie_header

        env['session'] = session

        return req, rule, env

    @staticmethod
    def response2har(response):
        request = response.request

        def build_headers(headers):
            result = []
            for k, v in headers.get_all():
                result.append(dict(name=k, value=v))
            return result

        def build_request(request):
            url = urlparse.urlparse(request.url)
            ret = dict(
                    method = request.method,
                    url = request.url,
                    httpVersion = 'HTTP/1.1',
                    headers = build_headers(request.headers),
                    queryString = [
                        {'name': n, 'value': v} for n, v in\
                                urlparse.parse_qsl(url.query)],
                    cookies = [
                        {'name': n, 'value': v} for n, v in \
                                urlparse.parse_qsl(request.headers.get('cookie', ''))],
                    headersSize = -1,
                    bodySize = len(request.body) if request.body else 0,
                    )
            if request.body:
                ret['postData'] = dict(
                        mimeType = request.headers.get('content-type'),
                        text = request.body,
                        )
                if ret['postData']['mimeType'] == 'application/x-www-form-urlencoded':
                    ret['postData']['params'] = [
                            {'name': n, 'value': v} for n, v in \
                                urlparse.parse_qsl(request.body)]

            return ret


        def build_response(response):
            cookies = cookie_utils.CookieSession()
            cookies.extract_cookies_to_jar(response.request, response)

            return dict(
                    status = response.code,
                    statusText = response.reason,
                    headers = build_headers(response.headers),
                    cookies = cookies.to_json(),
                    content = dict(
                        size = len(response.body),
                        mimeType = response.headers.get('content-type'),
                        text = base64.b64encode(response.body),
                        ),
                    redirectURL = response.headers.get('Location'),
                    headersSize = -1,
                    bodySize = -1,
                    )

        entry = dict(
            startedDateTime = datetime.now().isoformat(),
            time = response.request_time,
            request = build_request(request),
            response = build_response(response),
            cache = {},
            timings = response.time_info,
            connections = "0",
            pageref = "page_0",
            )
        return entry

    @staticmethod
    def run_rule(response, rule, env):
        success = True

        def getdata(_from):
            if _from == 'content':
                return response.body
            elif _from == 'status':
                return '%s' % response.code
            elif _from.startswith('header-'):
                _from = _from[7:]
                return response.headers.get(_from, '')
            else:
                return ''

        for r in rule.get('success_asserts') or '':
            if not re.search(r['re'], getdata(r['from'])):
                success = False
                break

        for r in rule.get('failed_asserts') or '':
            if re.search(r['re'], getdata(r['from'])):
                success = False
                break

        for r in rule.get('extract_variables') or '':
            m = re.search(r['re'], getdata(r['from']))
            if m:
                m = m.groups()
                if len(m) > 1:
                    m = m[1]
                else:
                    m = m[0]
                env['variables'][r['name']] = m

        return success

    @gen.coroutine
    def fetch(self, obj):
        req, rule, env = self.build_request(obj)

        try:
            response = yield self.client.fetch(req)
        except httpclient.HTTPError as e:
            if not e.response:
                raise
            response = e.response

        env['session'].extract_cookies_to_jar(response.request, response)
        success = self.run_rule(response, rule, env)

        raise gen.Return({
            'success': success,
            'response': response,
            'env': env,
            })
