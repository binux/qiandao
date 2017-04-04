FROM python:2-onbuild
MAINTAINER fangzhengjin <fangzhengjin@gmail.com>
ENV PORT 80
EXPOSE $PORT
CMD ["python","/usr/src/app/run.py"]
