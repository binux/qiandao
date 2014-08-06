# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-01 11:02:45

define (require, exports, module) ->
  require 'jquery'
  require 'bootstrap'
  require 'angular'
  require '/static/har/contenteditable'
  require '/static/har/editablelist'

  analysis = require '/static/har/analysis'
  utils = require '/static/utils'

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

  editor = angular.module('HAREditor', ['contenteditable', 'editablelist'])

  # upload har controller
  editor.controller('UploadCtrl', ($scope, $rootScope) ->
    element = angular.element('#upload-har')

    element.modal('show').on('hide.bs.modal', -> $scope.uploaded?)

    element.find('input[type=file]').on('change', (ev) ->
      $scope.file = this.files[0]
    )

    $scope.alert = (message) ->
      element.find('.alert').text(message).show()

    $scope.loaded = (data) ->
      console.log data
      $scope.uploaded = true
      $rootScope.$emit('har-loaded', data)
      angular.element('#upload-har').modal('hide')

    $scope.upload = ->
      if not $scope.file?
        return false

      if $scope.file.size > 50*1024*1024
        $scope.alert '文件大小超过50M'
        return false

      element.find('button').button('loading')
      reader = new FileReader()
      reader.onload = (ev) ->
        $scope.uploaded = true
        try
          $scope.loaded(
            har: analysis.analyze(angular.fromJson(ev.target.result), {
              username: $scope.username
              password: $scope.password
            })
            env: {
              username: $scope.username
              password: $scope.password
            }
          )
        catch error
          console.log error
          $scope.alert 'HAR 格式错误'
        finally
          element.find('button').button('reset')
      reader.readAsText $scope.file
  )

  # har list controller
  editor.controller('EditorCtrl', ($scope, $rootScope) ->
    $rootScope.$on('har-loaded', (ev, data) ->
      $scope.$apply ->
        console.log data
        $scope.har = data.har
        $scope.env = utils.dict2list(data.env)
        $scope.session = []
    )

    $scope.status_label = (status) ->
      if status // 100 == 2
        'label-success'
      else if status // 100 == 3
        'label-info'
      else if status == 0
        'label-danger'
      else
        'label-warning'

    $scope.variables_in_entry = analysis.variables_in_entry

    $scope.filter = {}
    $scope.badge_filter = (update) ->
      filter = angular.copy($scope.filter)
      for key, value of update
        filter[key] = value
      return filter

    $scope.track_item = () ->
      $scope.filted = []
      (item) ->
        $scope.filted.push(item)
        return true

    $scope.edit = (entry) ->
      $scope.$broadcast('edit-entry', entry)
      return false

    $scope.recommend = () ->
      analysis.recommend($scope.har)
  )

  # entry edit
  editor.controller('EntryCtrl', ($scope, $rootScope, $sce, $http) ->
    $scope.$on('edit-entry', (ev, entry) ->
      console.log entry
      $scope.entry = entry
      angular.element('#edit-entry').modal('show')
      $scope.alert_hide()
    )

    angular.element('#edit-entry').on('hidden.bs.modal', (ev) ->
      if $scope.panel in ['preview-headers', 'preview']
        $scope.$apply ->
            $scope.panel = 'test'
      $scope.$apply ->
        $scope.preview = undefined
    )

    $scope.alert = (message) ->
      angular.element('.panel-test .alert').text(message).show()
    $scope.alert_hide = () ->
      angular.element('.panel-test .alert').hide()

    $scope.$watch('entry.request.url', () ->
      if not $scope.entry?
        return
      queryString = ({name: key, value: value} for key, value of utils.url_parse($scope.entry.request.url, true).query)

      if not angular.equals(queryString, $scope.entry.request.queryString)
        $scope.entry.request.queryString = queryString
    )

    $scope.$watch('entry.request.queryString', (() ->
      if not $scope.entry?
        return
      url = utils.url_parse($scope.entry.request.url)
      query = {}
      for each in $scope.entry.request.queryString
        query[each.name] = each.value
      query = utils.querystring_unparse_with_variables(query)
      url.search = "?#{query}" if query
      url = utils.url_unparse(url)

      if url != $scope.entry.request.url
        $scope.entry.request.url = url
    ), true)

    $scope.$watch('entry.request.postData.params', (() ->
      if not $scope.entry?.postData?
        return
      obj = {}
      for param in $scope.entry.request.postData.params
        obj[param.name] = param.value
      $scope.entry.request.postData.text = utils.querystring_unparse_with_variables(obj)
    ), true)

    $scope.panel = 'request'

    $scope.delete = (hashKey, array) ->
      for each, index in array
        if each.$$hashKey == hashKey
          array.splice(index, 1)
          return

    $scope.variables_wrapper = (string, place_holder='') ->
      string = string or place_holder
      re = /{{\s*([\w]+?)\s*}}/g
      $sce.trustAsHtml(string.replace(re, '<span class="label label-primary">$&</span>'))

    $scope.do_test = () ->
      $http.post('/har/test', {
        request:
          method: $scope.entry.request.method
          url: $scope.entry.request.url
          headers: ({name: h.name, value: h.value} for h in $scope.entry.request.headers when h.checked)
          cookies: ({name: c.name, value: c.value} for c in $scope.entry.request.cookies when c.checked)
          data: $scope.entry.request.postData?.text
        env: utils.list2dict($scope.env)
        session: $scope.session
      }).
      success((data, status, headers, config) ->
        console.log 'success', data, status
        if (status != 200)
          $scope.alert(data)
          return
        $scope.preview = data.har
        $scope.env = utils.dict2list(data.env)
        $scope.session = data.session
        $scope.panel = 'preview'

        if data.har.response?.content?.text?
          setTimeout((() ->
            angular.element('.panel-preview iframe').attr("src",
              "data:#{data.har.response.content.mimeType};\
              base64,#{data.har.response.content.text}")), 0)
      ).
      error((data, status, headers, config) ->
        console.log 'error', data, status, headers, config
        $scope.alert(data)
      )
  )

  init: -> angular.bootstrap(document.body, ['HAREditor'])
  analysis: analysis
