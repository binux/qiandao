# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 21:12:48

define (require, exports, module) ->
  analysis = require '/static/har/analysis'
  utils = require '/static/utils'

  angular.module('upload_ctrl', []).
    controller('UploadCtrl', ($scope, $rootScope) ->
      element = angular.element('#upload-har')

      element.modal('show').on('hide.bs.modal', -> $scope.uploaded?)

      element.find('input[type=file]').on('change', (ev) ->
        $scope.file = this.files[0]
      )

      $scope.local_har = utils.storage.get('har_filename') if utils.storage.get('har_har')?

      $scope.alert = (message) ->
        element.find('.alert').text(message).show()

      $scope.loaded = (data) ->
        loaded =
          filename: $scope.file.name
          har: analysis.analyze(data, {
                username: $scope.username
                password: $scope.password
              })
          env:
            username: $scope.username
            password: $scope.password
        $scope.uploaded = true
        $rootScope.$emit('har-loaded', loaded)
        angular.element('#upload-har').modal('hide')
        return true

      $scope.load_local_har = () ->
        loaded =
          filename: utils.storage.get('har_filename')
          har: utils.storage.get('har_har')
          env: utils.storage.get('har_env')
        $scope.uploaded = true
        $rootScope.$emit('har-loaded', loaded)
        angular.element('#upload-har').modal('hide')
        return true

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
              $scope.loaded(angular.fromJson(ev.target.result))
            catch error
              console.log error
              $scope.alert 'HAR 格式错误'
            finally
              element.find('button').button('reset')
        reader.readAsText $scope.file
    )
