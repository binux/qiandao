FROM daocloud.io/python:2-onbuild
MAINTAINER fangzhengjin "fangzhengjin@gmail.com"
EXPOSE 8923
CMD ["python","/usr/src/app/run.py"]
