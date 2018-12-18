# 基础镜像
FROM python:2.7-alpine
# 维护者信息
LABEL maintainer "fangzhengjin <fangzhengjin@gmail.com>"
ADD . /usr/src/app
WORKDIR /usr/src/app
# 基础镜像已经包含pip组件
RUN apk update \
    && apk add bash autoconf g++ \
    && pip install --no-cache-dir -r requirements.txt
ENV PORT 80
EXPOSE $PORT/tcp
# 添加挂载点
VOLUME ["/usr/src/app/"]
CMD ["python","/usr/src/app/run.py"]
