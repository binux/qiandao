# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 21:14:54

define (require, exports, module) ->
  analysis = require '/static/har/analysis'
  utils = require '/static/utils'

  angular.module('entry_list', []).
    controller('EntryList', ($scope, $rootScope, $http) ->
      $scope.filter = {}

      # on uploaded event
      $rootScope.$on('har-loaded', (ev, data) ->
        console.info(data)

        $scope.filename = data.filename
        $scope.har = data.har
        $scope.init_env = data.env
        $scope.env = utils.dict2list(data.env)
        $scope.session = []
        $scope.setting = data.setting
        $scope.readonly = data.readonly or not HASUSER

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
          console.debug('local saved')
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

      $scope.download = () ->
        $scope.pre_save()
        tpl = btoa(unescape(encodeURIComponent(angular.toJson(har2tpl($scope.har)))))
        angular.element('#download-har').attr('download', $scope.setting.sitename+'.har').attr('href', 'data:application/json;base64,'+tpl)
        return true

      $scope.pre_save = () ->
        alert_elem = angular.element('#save-har .alert-danger').hide()
        alert_info_elem = angular.element('#save-har .alert-info').hide()

        first_entry = (() ->
          for entry in $scope.har.log.entries when entry.checked
            variables = analysis.variables_in_entry(entry)
            if ('cookies' in variables or 'cookie' in variables)
              return entry
        )()
        if not first_entry
          first_entry ?= (() ->
            for entry in $scope.har.log.entries when entry.checked
              return entry)()

        try
          $scope.setting ?= {}
          $scope.setting.sitename ?= first_entry and utils.get_domain(first_entry.request.url).split('.')[0]
          parsed_url = first_entry and utils.url_parse(first_entry.request.url)
          $scope.setting.siteurl ?= parsed_url.protocol == 'https:' and "#{parsed_url.protocol}//#{parsed_url.host}" or parsed_url.host
        catch error
          console.error(error)

      har2tpl = (har) ->
        return ({
            request:
              method: entry.request.method
              url: entry.request.url
              headers: ({name: h.name, value: h.value} for h in entry.request.headers when h.checked)
              cookies: ({name: c.name, value: c.value} for c in entry.request.cookies when c.checked)
              data: entry.request.postData?.text
              mimeType: entry.request.postData?.mimeType
            rule:
              success_asserts: entry.success_asserts
              failed_asserts: entry.failed_asserts
              extract_variables: entry.extract_variables
          } for entry in har.log.entries when entry.checked)

      $scope.save = () ->
        data = {
          id: $scope.id,
          har: $scope.har
          tpl: har2tpl($scope.har)
          setting: $scope.setting
        }

        save_btn = angular.element('#save-har .btn').button('loading')
        alert_elem = angular.element('#save-har .alert-danger').hide()
        alert_info_elem = angular.element('#save-har .alert-info').hide()
        $http.post(location.pathname.replace('edit', 'save'), data)
        .success((data, status, headers, config) ->
          utils.storage.del('har_filename')
          utils.storage.del('har_har')
          utils.storage.del('har_env')
          save_btn.button('reset')
          pathname = "/tpl/#{data.id}/edit"
          if pathname != location.pathname
            location.pathname = pathname
          alert_info_elem.text('保存成功').show()
        )
        .error((data, status, headers, config) ->
          alert_elem.text(data).show()
          save_btn.button('reset')
        )

      $scope.test = () ->
        data =
          env:
            variables: utils.list2dict($scope.env)
            session: []
          tpl: har2tpl($scope.har)

        result = angular.element('#test-har .result').hide()
        btn = angular.element('#test-har .btn').button('loading')
        $http.post('/tpl/run', data)
        .success((data) ->
          result.html(data).show()
          btn.button('reset')
        )
        .error((data) ->
          result.html('<h1 class="alert alert-danger text-center">签到失败</h1><div class="well"></div>').show().find('div').text(data)
          btn.button('reset')
        )
    )
