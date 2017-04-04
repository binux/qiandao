FROM python:2-onbuild
MAINTAINER fangzhengjin <fangzhengjin@gmail.com>
ENV PORT 80
EXPOSE $PORT
ENTRYPOINT ["python","/usr/src/app/run.py"]
