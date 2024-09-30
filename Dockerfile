# 使用官方 Python 基础镜像作为起点
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录下的所有文件到容器内的 /app 目录下
COPY . .

# 安装应用程序的依赖，使用国内镜像源加速
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

EXPOSE 8000
# 指定容器启动时要运行的命令
CMD ["python", "src/main.py"]
