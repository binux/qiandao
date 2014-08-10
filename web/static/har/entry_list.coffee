# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 21:14:54

define (require, exports, module) ->
  require 'jquery'
  require 'bootstrap'
  require 'angular'

  analysis = require '/static/har/analysis'
  utils = require '/static/utils'

  angular.module('entry_list', []).
    controller('EntryList', ($scope, $rootScope, $http) ->
      $scope.filter = {}

      # on uploaded event
      $rootScope.$on('har-loaded', (ev, data) ->
        console.log data
        $scope.filename = data.filename
        $scope.har = data.har
        $scope.env = utils.dict2list(data.env)
        $scope.session = []

        $scope.sitename = data.sitename
        $scope.siteurl = data.siteurl
        $scope.readonly = data.readonly

        $scope.recommend()
        if (x for x in $scope.har.log.entries when x.recommend).length > 0
          $scope.filter.recommend = true

        if not $scope.readonly
          utils.storage.set('har_filename', data.filename)
          utils.storage.set('har_env', data.env)
          if data.upload
            utils.storage.set('har_har', data.har)
          else
            utils.storage.del('har_har')
      )
      $scope.$on('har-change', () ->
        $scope.save_change()
      )
      $scope.save_change = utils.debounce((() ->
        if ($scope.filename and not $scope.readonly)
          console.log 'local saved'
          utils.storage.set('har_har', $scope.har)
      ), 1000)

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

      $scope.pre_save = () ->
        first_entry = (() ->
          for entry in $scope.har.log.entries when entry.checked
            return entry)()

        try
          $scope.sitename ?= first_entry and utils.get_domain(first_entry.request.url).split('.')[0]
          $scope.siteurl ?= first_entry and utils.url_parse(first_entry.request.url).host
        catch error
          null

      $scope.save = () ->
        data = {
          id: $scope.id,
          har: $scope.har
          tpl: ({
            request:
              method: entry.request.method
              url: entry.request.url
              headers: ({name: h.name, value: h.value} for h in entry.request.headers when h.checked)
              cookies: ({name: c.name, value: c.value} for c in entry.request.cookies when c.checked)
              data: entry.request.postData?.text
            rule:
              success_asserts: entry.success_asserts
              failed_asserts: entry.failed_asserts
              extract_variables: entry.extract_variables
          } for entry in $scope.har.log.entries when entry.checked)
          sitename: $scope.sitename
          siteurl: $scope.siteurl
        }

        save_btn = angular.element('#save-har .btn').button('loading')
        alert_elem = angular.element('#save-har .alert').hide()
        $http.post(location.pathname.replace('edit', 'save'), data)
        .success((data, status, headers, config) ->
          utils.storage.del('har_filename')
          utils.storage.del('har_har')
          utils.storage.del('har_env')
          save_btn.button('reset')
          pathname = "/har/edit/#{data.id}"
          if pathname != location.pathname
            location.pathname = pathname
        )
        .error((data, status, headers, config) ->
          alert_elem.text(data).show()
          save_btn.button('reset')
        )
    )
