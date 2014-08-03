# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-02 10:07:33

define (require, exports, module) ->
  utils = require('/static/utils')

  checked = (har) ->
    # mark can been checked
    for entry in har.log.entries
      entry.check_tag = []
      if entry.response.cookies.length > 0
        entry.check_tag.push('response-cookie')
        entry.checked = true
      else if (c for c in entry.request.cookies when c.cookie_changed or c.cookie_added).length > 0
        entry.check_tag.push('request-cookie-changed')
        entry.checked = true
      else if entry.response.status in [0, 304]
        entry.checked = false
      else if entry.response.content?.mimeType.indexOf('image') == 0
        entry.checked = false
      else if entry.response.content?.mimeType in ['text/css', ]
        entry.checked = false
      else
        entry.checked = true
    return har

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
    cookies = {}
    for entry in har.log.entries
      for cookie in entry.request.cookies
        if cookie.name of cookies
          if cookie.value == cookies[cookie.name]
            cookie.from_session = true
          else
            cookie.cookie_changed = true
            entry.filter_cookie_changed = true
        else
          cookie.cookie_added = true
          entry.filter_cookie_added = true
        cookies[cookie.name] = cookie.value

      # update cookie from response
      for cookie in entry.response.cookies
        entry.filter_set_cookie = true
        cookies[cookie.name] = cookie.value
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

  exports.analyze = (har) ->
    mime_type analyze_cookies sort har
  
  return exports
