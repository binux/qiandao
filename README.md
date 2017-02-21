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

设置管理员

```
./chrole.py your@email.address admin
```

qiandao.py
==========

```
pip install tornado u-msgpack-python jinja2 chardet requests
./qiandao.py tpl.har [--key=value]* [env.json]
```

鸣谢
====

+[雪月秋水](https://plus.google.com/u/0/+%E9%9B%AA%E6%9C%88%E7%A7%8B%E6%B0%B4%E9%85%B1) [GetCookies项目](https://github.com/acgotaku/GetCookies)

许可
====

MIT
