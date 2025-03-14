# 构建阶段
FROM python:3.11-slim as builder
WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/

# 安装构建依赖
# RUN apt-get update && apt-get install -y \
#     gcc \
#     python3-dev \
#     && rm -rf /var/lib/apt/lists/*

# 安装生产依赖
RUN pip install --user --no-cache-dir .[celery]

# 运行时阶段
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH

# 应用端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "wecom.main:app", "--host", "0.0.0.0", "--port", "8000"]