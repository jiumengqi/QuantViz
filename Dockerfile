# QuantViz 量化投资平台 - Render 适配 Dockerfile
FROM python:3.11-slim

# 1. 安装 weasyprint 系统依赖 + 中文字体
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 分层缓存：先装依赖
COPY requirements.txt .

# 3. pip 清华源安装全部依赖 + gunicorn
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt && \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    gunicorn gevent

# 4. 复制项目代码
COPY . .

# 5. 创建运行时目录
RUN mkdir -p logs instance uploads

# 6. Render 自动注入 $PORT（默认 10000）
#    使用 gunicorn + gevent，工作进程数根据 Render 免费配额设为 2
CMD gunicorn app:app \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 2 \
    --worker-class gevent \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
