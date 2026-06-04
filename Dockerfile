FROM python:3.11-slim
WORKDIR /app
# 更换国内debian源+安装依赖，规避源超时、包找不到
RUN sed -i '/deb。debian.org/mirror.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
        libffi-dev shared-mime-info fonts-noto-cjk \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt gunicorn
COPY . .
# 先用原生python启动，输出完整运行报错
CMD python -u app.py
