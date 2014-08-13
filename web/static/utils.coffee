# vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-03 07:42:45

define (require) ->
  require '/static/node_components'

  url = node_url
  tough = node_tough
  querystring = node_querystring

  exports =
    cookie_parse: (cookie_string) ->
      cookie = {}
      for each in cookie_string?.split(';')
        index = each.indexOf('=')
        index = if index < 0 then each.length else index
        key = each[..index]
        value = each[index+1..]
        cookie[decodeURIComponent(key)] = decodeURIComponent(value)
      return cookie

    cookie_unparse: (cookie) ->
      (encodeURIComponent(key)+'='+encodeURIComponent(value) for key, value in cookie).join(';')

    url_parse: node_url.parse
    url_unparse: node_url.format

    querystring_parse: node_querystring.parse
    querystring_unparse: node_querystring.stringify
    querystring_unparse_with_variables: (obj) ->
      query = node_querystring.stringify(obj)

      replace_list = {}
      for key, value of obj
        re = /{{\s*([\w]+)[^}]*?\s*}}/g
        while m = re.exec(key)
          replace_list[encodeURIComponent(m[0])] = m[0]
        re = /{{\s*([\w]+)[^}]*?\s*}}/g
        while m = re.exec(value)
          replace_list[encodeURIComponent(m[0])] = m[0]
      for key, value of replace_list
        query = query.replace(key, value, 'g')
      return query
    querystring_parse_with_variables: (query) ->
      obj = {}

    CookieJar: node_tough.CookieJar
    Cookie: node_tough.Cookie

    dict2list: (dict) ->
      ({name: k, value: v} for k, v of dict)
    list2dict: (list) ->
      dict = {}
      for each in list
        dict[each.name] = each.value
      return dict

    get_public_suffix: node_tough.getPublicSuffix
    get_domain: (url) ->
      exports.get_public_suffix exports.url_parse(url).hostname

    debounce: (func, wait, immediate) ->
      timestamp = 0
      timeout = 0

      later = () ->
        last = (new Date().getTime()) - timestamp

        if 0 < last < wait
          timeout = setTimeout(later, wait - last)
        else
          timeout = null
          if not immediate
            result = func.apply(context, args)
            if not timeout
              context = args = null

      return () ->
        context = this
        args = arguments
        timestamp = (new Date().getTime())
        callNow = immediate and not timeout
        if not timeout
          timeout = setTimeout(later, wait)
        if callNow
          result = func.apply(context, args)
          context = args = null

        return result

    storage:
      set: (key, value) ->
        if not window.localStorage?
          return false
        try
          return window.localStorage.setItem(key, angular.toJson(value))
        catch error
          return null
      get: (key) ->
        if not window.localStorage?
          return null
        try
          return angular.fromJson(window.localStorage.getItem(key))
        catch error
          return null
      del: (key) ->
        if not window.localStorage?
          return false
        try
          return window.localStorage.removeItem(key)
        catch error
          return null

  return exports
