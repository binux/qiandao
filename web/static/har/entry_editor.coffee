# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 21:16:15

define (require, exports, module) ->
  utils = require '/static/utils'

  angular.module('entry_editor', []).
    controller('EntryCtrl', ($scope, $rootScope, $sce, $http) ->
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
