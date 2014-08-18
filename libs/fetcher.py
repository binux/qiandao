#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 11:55:41

import re
import json
import urllib
import base64
import logging
import urlparse
from datetime import datetime

import pycurl
from jinja2 import Template
from tornado import gen, concurrent, httpclient

try:
    import config
except ImportError:
    class config:
        debug = False
        download_size_limit = 1*1024*1024

from libs import cookie_utils, utils

logger = logging.getLogger('qiandao.fetcher')

class Fetcher(object):
    def __init__(self, download_size_limit=config.download_size_limit):
        httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        self.client = httpclient.AsyncHTTPClient()
        self.download_size_limit = download_size_limit

    @staticmethod
    def render(request, env, session={}):
        request = dict(request)

        def _render(obj, key):
            if not obj.get(key):
                return
            obj[key] = Template(obj[key]).render(_cookies=session, **env)

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
    def build_request(obj, download_size_limit=config.download_size_limit):
        env = obj['env']
        rule = obj['rule']
        request = Fetcher.render(obj['request'], env['variables'], env['session'])

        method = request['method']
        url = request['url']
        headers = dict((e['name'], e['value']) for e in request['headers'])
        cookies = dict((e['name'], e['value']) for e in request['cookies'])
        data = request.get('data')
        if method == 'GET':
            data = None
        elif method == 'POST':
            data = request.get('data', '')

        def set_size_limit_callback(curl):
            def size_limit(download_size, downloaded, upload_size, uploaded):
                if download_size and download_size > download_size_limit:
                    return 1
                if downloaded > download_size_limit:
                    return 1
                return 0
            curl.setopt(pycurl.NOPROGRESS, 0)
            curl.setopt(pycurl.PROGRESSFUNCTION, size_limit)
            return curl

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
                prepare_curl_callback = set_size_limit_callback,
                )

        session = cookie_utils.CookieSession()
        if req.headers.get('Cookie'):
            session.update(dict(urlparse.parse_qsl(req.headers['Cookie'])))
        if isinstance(env['session'], cookie_utils.CookieSession):
            session.from_json(env['session'].to_json())
        else:
            session.from_json(env['session'])
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
                    try:
                        _ = json.dumps(ret['postData']['params'])
                    except UnicodeDecodeError:
                        logger.error('params encoding error')
                        del ret['postData']['params']

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
                        decoded = utils.decode(response.body, response.headers),
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

        content = [-1, ]
        def getdata(_from):
            if _from == 'content':
                if content[0] == -1:
                    content[0] = utils.decode(response.body)
                return content[0]
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
                if m.groups():
                    m = m.groups()[0]
                else:
                    m = m.group(0)
                env['variables'][r['name']] = m

        return success

    @staticmethod
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
                    bodySize = len(en['request'].get('data')) if en['request'].get('data') else 0,


                    )
            if en['request'].get('data'):
                request['postData'] = dict(
                        mimeType = en['request'].get('mimeType'),
                        text = en['request'].get('data'),
                        )
                if en['request'].get('mimeType') == 'application/x-www-form-urlencoded':
                    params = [{'name': x[0], 'value': x[1]} \
                        for x in urlparse.parse_qsl(en['request']['data'], True)]
                    request['postData']['params'] = params
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


    @gen.coroutine
    def fetch(self, obj):
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
        req, rule, env = self.build_request(obj, self.download_size_limit)

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

    @gen.coroutine
    def do_fetch(self, tpl, env):
        """
        do a fetch of hole tpl
        """
        for i, entry in enumerate(tpl):
            try:
                result = yield self.fetch(dict(
                    request = entry['request'],
                    rule = entry['rule'],
                    env = env,
                    ))
                env = result['env']
            except Exception as e:
                if config.debug:
                    logging.exception(e)
                raise Exception('failed at %d/%d request, error:%r, %s' % (
                    i+1, len(tpl), e, entry['request']['url']))
            if not result['success']:
                raise Exception('failed at %d/%d request, code:%s, %s' % (
                    i+1, len(tpl), result['response'].code, entry['request']['url']))
        raise gen.Return(env)

