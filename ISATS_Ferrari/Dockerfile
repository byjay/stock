# 🐳 ISATS v7.0 Docker Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Base Image: Python 3.11 (slim)
FROM python:3.11-slim

# Metadata
LABEL maintainer="ISATS Neural Swarm"
LABEL version="7.0"
LABEL description="ISATS Ferrari - Standardized Trading Intelligence"

# Environment Variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Seoul

# Working Directory
WORKDIR /app

# System Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy Requirements
COPY requirements.txt .

# Install Python Dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy Application
COPY . .

# Create Directories
RUN mkdir -p \
    /app/data/KR \
    /app/data/US \
    /app/logs \
    /app/brain \
    /app/config

# Expose Ports
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start Command (Multi-process)
CMD ["sh", "-c", "redis-server --daemonize yes && python api_server.py & python main.py"]
