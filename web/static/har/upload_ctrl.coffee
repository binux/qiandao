# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 21:12:48

define (require, exports, module) ->
  analysis = require '/static/har/analysis'
  utils = require '/static/utils'

  angular.module('upload_ctrl', []).
    controller('UploadCtrl', ($scope, $rootScope, $http) ->
      element = angular.element('#upload-har')

      element.modal('show').on('hide.bs.modal', -> $scope.is_loaded?)

      element.find('input[type=file]').on('change', (ev) ->
        $scope.file = this.files[0]
      )

      $scope.local_har = utils.storage.get('har_filename') if utils.storage.get('har_har')?

      $scope.alert = (message) ->
        element.find('.alert').text(message).show()

      $scope.loaded = (loaded) ->
        $scope.is_loaded = true
        $rootScope.$emit('har-loaded', loaded)
        angular.element('#upload-har').modal('hide')
        return true

      $scope.load_remote = (id) ->
        element.find('button').button('loading')
        $http.post("/har/edit/#{id}")
        .success((data, status, headers, config) ->
          element.find('button').button('reset')
          $scope.loaded(data)
        )
        .error((data, status, headers, config) ->
          $scope.alert(data)
          element.find('button').button('reset')
        )
      if not $scope.local_har and m = location.pathname.match(/\/har\/edit\/(\d+)/)
        $scope.load_remote(m[1])

      $scope.load_file = (data) ->
        loaded =
          filename: $scope.file.name
          har: analysis.analyze(data, {
                username: $scope.username
                password: $scope.password
              })
          env:
            username: $scope.username
            password: $scope.password
          upload: true
        $scope.loaded(loaded)

      $scope.load_local_har = () ->
        loaded =
          filename: utils.storage.get('har_filename')
          har: utils.storage.get('har_har')
          env: utils.storage.get('har_env')
          upload: true
        $scope.loaded(loaded)

      $scope.delete_local = () ->
        utils.storage.del('har_har')
        utils.storage.del('har_env')
        utils.storage.del('har_filename')

        $scope.local_har = undefined
        if not $scope.local_har and m = location.pathname.match(/\/har\/edit\/(\d+)/)
          $scope.load_remote(m[1])

      $scope.upload = ->
        if not $scope.file?
          $scope.alert '还没选择文件啊，亲'
          return false

        if $scope.file.size > 50*1024*1024
          $scope.alert '文件大小超过50M'
          return false

        element.find('button').button('loading')
        reader = new FileReader()
        reader.onload = (ev) ->
          $scope.$apply ->
            $scope.uploaded = true
            try
              $scope.load_file(angular.fromJson(ev.target.result))
            catch error
              console.log error
              $scope.alert 'HAR 格式错误'
            finally
              element.find('button').button('reset')
        reader.readAsText $scope.file
    )
