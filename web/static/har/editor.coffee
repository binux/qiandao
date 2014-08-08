# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-01 11:02:45

define (require, exports, module) ->
  require 'jquery'
  require 'bootstrap'
  require 'angular'

  require '/static/har/contenteditable'
  require '/static/har/upload_ctrl'
  require '/static/har/entry_list'
  require '/static/har/entry_editor'

  # contentedit-wrapper
  $(document).on('click', '.contentedit-wrapper', (ev) ->
    editable = $(this).hide().next('[contenteditable]').show().focus()
  )
  $(document).on('blur', '.contentedit-wrapper + [contenteditable]', (ev) ->
    $(this).hide().prev('.contentedit-wrapper').show()
  )
  $(document).on('focus', '[contenteditable]', (ev) ->
    if this.childNodes[0]
      range = document.createRange()
      sel = window.getSelection()
      range.setStartBefore(this.childNodes[0])
      range.setEndAfter(this)
      sel.removeAllRanges()
      sel.addRange(range)
  )

  editor = angular.module('HAREditor', [
    'editablelist'
    'upload_ctrl'
    'entry_list'
    'entry_editor'
  ])

  init: -> angular.bootstrap(document.body, ['HAREditor'])
