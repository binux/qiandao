# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-02 10:07:33

define (require, exports, module) ->
  first_request = (har) ->
    # mark first request of each page
    current_page = null
    for entry in har.log.entries
      if entry.pageref != current_page
        entry.first_request = true
        current_page = entry.pageref
    return har

  checked = (har) ->
    # mark can been checked
    for entry in har.log.entries
      if entry.response.status in [0, 304]
        entry.checked = false
      else if entry.response.content?.mimeType.indexOf('image') == 0
        entry.checked = false
      else if entry.response.content?.mimeType in ['text/css', ]
        entry.checked = false
      else
        entry.checked = true
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
    checked first_request sort har
  
  return exports
