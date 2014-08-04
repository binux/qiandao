# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-02 10:07:33

define (require, exports, module) ->
  utils = require('/static/utils')

  xhr = (har) ->
    for entry in har.log.entries
      if (h for h in entry.request.headers when h.name == 'X-Requested-With' and h.value == 'XMLHttpRequest').length > 0
        entry.filter_xhr = true
    return har

  mime_type = (har) ->
    for entry in har.log.entries
      mt = entry.response.content?.mimeType

      entry.filter_mimeType = switch
        when mt.indexOf('audio') == 0 then 'media'
        when mt.indexOf('image') == 0 then 'image'
        when mt.indexOf('javascript') != -1 then 'javascript'
        when mt in ['text/html', ] then 'document'
        when mt in ['text/css', 'application/x-pointplus', ] then 'style'
        when mt.indexOf('application') == 0 then 'media'
        else 'other'
    return har

  analyze_cookies = (har) ->
    # analyze where cookie from
    cookie_jar = new utils.CookieJar()
    for entry in har.log.entries
      cookies = {}
      for cookie in cookie_jar.getCookiesSync(entry.request.url, {now: new Date(entry.startedDateTime)})
        cookies[cookie.key] = cookie.value
      for cookie in entry.request.cookies
        cookie.checked = false
        if cookie.name of cookies
          if cookie.value == cookies[cookie.name]
            cookie.from_session = true
            entry.filter_from_session = true
          else
            cookie.cookie_changed = true
            entry.filter_cookie_changed = true
            #cookie_jar.setCookieSync(utils.Cookie.fromJSON(angular.toJson({
              #key: cookie.name
              #value: cookie.value
              #path: '/'
            #})), entry.request.url)
        else
          cookie.cookie_added = true
          entry.filter_cookie_added = true
          #cookie_jar.setCookieSync(utils.Cookie.fromJSON(angular.toJson({
            #key: cookie.name
            #value: cookie.value
            #path: '/'
          #})), entry.request.url)

      # update cookie from response
      for header in (h for h in entry.response.headers when h.name.toLowerCase() == 'set-cookie')
        entry.filter_set_cookie = true
        cookie_jar.setCookieSync(header.value, entry.request.url, {now: new Date(entry.startedDateTime)})
    return har

  sort = (har) ->
    har.log.entries = har.log.entries.sort((a, b) ->
      if a.pageref > b.pageref
        1
      else if a.pageref < b.pageref
        -1
      else if a.startedDateTime > b.startedDateTime
        1
      else if a.startedDateTime < b.startedDateTime
        -1
      else
        0
    )
    return har

  headers = (har) ->
    to_remove_headers = ['x-devtools-emulate-network-conditions-client-id', 'cookie']
    for entry in har.log.entries
      for header in entry.request.headers
        if header.name.toLowerCase() not in to_remove_headers
          header.checked = true
        else
          header.checked = false
    return har

  exports =
    analyze: (har) ->
      xhr mime_type analyze_cookies headers sort har
    recommend: (har) ->
      for entry in har.log.entries
        entry.recommend = if entry.checked then true else false

      checked = (e for e in har.log.entries when e.checked)
      related_cookies = []
      for entry in checked
        for cookie in entry.request.cookies
          related_cookies.push(cookie.name)
      for entry in har.log.entries
        for cookie in entry.response.cookies
          if cookie.name in related_cookies
            entry.recommend = true
            break

  return exports
