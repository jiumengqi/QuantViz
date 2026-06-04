FROM python:3.11-slim
WORKDIR /app

# 修正sed，全部英文符号，阿里debian源
RUN sed -i '/deb。debian.org/mirror.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
        libffi-dev shared-mime-info fonts-noto-cjk \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 清华pip源安装依赖
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
COPY . .

# 前台启动，输出完整报错
CMD ["python","-u","app.py"]
