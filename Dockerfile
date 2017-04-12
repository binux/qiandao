# 基础镜像
FROM python:2.7-alpine

# 维护者信息
MAINTAINER fangzhengjin <fangzhengjin@gmail.com>

RUN apk update
RUN apk add bash autoconf g++

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app

# 基础镜像已经包含pip组件
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT 80
EXPOSE $PORT/tcp

CMD ["python","/usr/src/app/run.py"]
