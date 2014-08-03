# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-03 07:42:45

define (require) ->
  require '/static/node_components'

  url = node_url
  tough = node_tough
  querystring = node_querystring

  exports =
    cookie_parse: (cookie_string) ->
      cookie = {}
      for each in cookie_string?.split(';')
        index = each.indexOf('=')
        index = if index < 0 then each.length else index
        key = each[..index]
        value = each[index+1..]
        cookie[decodeURIComponent(key)] = decodeURIComponent(value)
      return cookie

    cookie_unparse: (cookie) ->
      (encodeURIComponent(key)+'='+encodeURIComponent(value) for key, value in cookie).join(';')

    url_parse: node_url.parse
    url_unparse: node_url.format

    querystring_parse: node_querystring.parse
    querystring_unparse: node_querystring.stringify

    CookieJar: node_tough.CookieJar
    Cookie: node_tough.Cookie

  return exports
