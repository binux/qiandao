qiandao
=======

签到 —— 一个自动签到框架 base on an HAR editor

HAR editor 使用指南：https://github.com/binux/qiandao/blob/master/docs/har-howto.md

Web
===

需要 python2.7, 虚拟主机无法安装

```
apt-get install python-dev autoconf g++ python-pbkdf2
pip install tornado u-msgpack-python jinja2 chardet requests pbkdf2 pycrypto
```

可选 redis, Mysql

```
mysql < qiandao.sql
```

启动

```
./run.py
```

数据不随项目分发，去 [https://qiandao.today/tpls/public](https://qiandao.today/tpls/public) 查看你需要的模板，点击下载。
在你自己的主页中 「我的模板+」 点击 + 上传。模板需要发布才会在「公开模板」中展示，你需要管理员权限在「我的发布请求」中审批通过。


设置管理员

```
./chrole.py your@email.address admin
```

使用Docker部署站点
==========

可参考 Wiki [Docker部署签到站教程](https://github.com/binux/qiandao/wiki/Docker%E9%83%A8%E7%BD%B2%E7%AD%BE%E5%88%B0%E7%AB%99%E6%95%99%E7%A8%8B)

qiandao.py
==========

```
pip install tornado u-msgpack-python jinja2 chardet requests
./qiandao.py tpl.har [--key=value]* [env.json]
```

config.py
=========
优先用`mailgun`方式发送邮件，如果要用smtp方式发送邮件，请填写mail_smtp, mail_user, mail_password
```python
mail_smtp = ""     # 邮件smtp 地址
mail_user = ""    # 邮件账户
mail_passowrd = ""   # 邮件密码
mail_domain = "mail.qiandao.today"
mailgun_key = ""
```

鸣谢
====

+[雪月秋水](https://plus.google.com/u/0/+%E9%9B%AA%E6%9C%88%E7%A7%8B%E6%B0%B4%E9%85%B1) [GetCookies项目](https://github.com/acgotaku/GetCookies)

许可
====

MIT
