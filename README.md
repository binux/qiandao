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
pip install mysql-connector-python-rf==2.1.3
```

可选数据库：sqlite, Mysql
可选启用 redis 功能

```
将
db_type = os.getenv('DB_TYPE', 'sqlite3')
修改为
db_type = os.getenv('DB_TYPE', 'mysql')
```


选用Mysql的先运行`qiandao.sql`来初始化数据库：
```
mysql -u root -p < qiandao.sql
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
mail_smtp = ""       # 邮件smtp 地址
mail_method = ""     # 邮件加密方法，目前仅支持ssl
mail_user = ""       # 邮件账户
mail_port = 465      # SMPT端口
mail_passowrd = ""   # 邮件密码
mail_domain = ""     # 使用mailgun发送邮件时设置项：发送域名
mailgun_key = ""     # 使用mailgun发送邮件时设置项：API接入密钥
```

如果需要开启HTTPS，请使用本机反向代理
Apache2反向代理教程可以查看我的博文 [在ubuntu 16.04下配置apache2的反向代理功能](https://www.elfive.cn/how-to-setup-apache2-proxy-function/) 

鸣谢
====

+[雪月秋水](https://plus.google.com/u/0/+%E9%9B%AA%E6%9C%88%E7%A7%8B%E6%B0%B4%E9%85%B1) [GetCookies项目](https://github.com/acgotaku/GetCookies)

许可
====

MIT
