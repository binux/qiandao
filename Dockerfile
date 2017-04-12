#基础镜像 此镜像会自动从项目中读取requirements.txt文件并安装文件中声明的依赖组件
FROM python:2-onbuild

#维护者信息
MAINTAINER fangzhengjin <fangzhengjin@gmail.com>

#设置环境变量 在Dockerfile中设置的环境变量可以在启动的时候被覆盖
ENV PORT 80

#使用环境变量 设置容器暴露端口
EXPOSE $PORT/tcp

#设置进入点
ENTRYPOINT ["python","/usr/src/app/run.py"]
