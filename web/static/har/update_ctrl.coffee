# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-06 21:12:48

define (require, exports, module) ->
  analysis = require '/static/har/analysis'

  angular.module('upload_ctrl', []).
    controller('UploadCtrl', ($scope, $rootScope) ->
      element = angular.element('#upload-har')

      element.modal('show').on('hide.bs.modal', -> $scope.uploaded?)

      element.find('input[type=file]').on('change', (ev) ->
        $scope.file = this.files[0]
      )

      $scope.alert = (message) ->
        element.find('.alert').text(message).show()

      $scope.loaded = (data) ->
        loaded =
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
            $scope.loaded(angular.fromJson(ev.target.result))
          catch error
            console.log error
            $scope.alert 'HAR 格式错误'
          finally
            element.find('button').button('reset')
        reader.readAsText $scope.file
    )
