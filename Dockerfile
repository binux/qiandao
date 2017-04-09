FROM python:2-onbuild
MAINTAINER fangzhengjin <fangzhengjin@gmail.com>
ENV PORT 80
EXPOSE $PORT/tcp
ENTRYPOINT ["python","/usr/src/app/run.py"]
