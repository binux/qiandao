qiandao
=======

签到 —— 一个自动签到框架 base on an HAR editor

HAR editor 使用指南：https://github.com/binux/qiandao/blob/master/docs/har-howto.md

qiandao.py
==========

```
pip install tornado u-msgpack-python jinja2 chardet requests
./qiandao.py tpl.har [--key=value]* [env.json]
```

Web
===

需要 Mysql
可选 redis

```
apt-get install python-dev
pip install http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#md5=3df394d89300db95163f17c843ef49df
pip install tornado u-msgpack-python jinja2 chardet requests mysql-connector-python redis pbkdf2 pycrypto
mysql < qiandao.sql
./worker.py &
./web.py
```

设置管理员

在数据库中，将用户的 role 改为 admin

鸣谢
====

+[雪月秋水](https://plus.google.com/u/0/+%E9%9B%AA%E6%9C%88%E7%A7%8B%E6%B0%B4%E9%85%B1) [GetCookies项目](https://github.com/acgotaku/GetCookies)

许可
====

MIT
