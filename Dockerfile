# 使用 Python 官方带环境的镜像
FROM python:3.10-slim

# 安装 Playwright 运行所需的系统依赖和 Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpangoft2-1.0-0 \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
RUN pip install --no-cache-dir playwright fastapi uvicorn
RUN playwright install chromium

# 复制你的服务代码
COPY . /app

EXPOSE 8000

# 启动 API 服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
