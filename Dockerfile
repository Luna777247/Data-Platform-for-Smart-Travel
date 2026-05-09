# Smart Tourism Data Platform - Docker Image
# ==========================================
# Multi-stage build cho production-ready FastAPI application
#
# Build:
#   docker build -t smart-tourism-api .
#
# Run:
#   docker run -p 8000:8000 smart-tourism-api
#
# Stages:
# 1. Builder: Install dependencies và compile requirements
# 2. Production: Final image với chỉ necessary files

# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.11-slim as builder

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Ngăn Python ghi .pyc files
# PYTHONUNBUFFERED: Force stdout/stderr không buffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies cho building Python packages
# gcc: C compiler (cho packages có C extensions)
# libpq-dev: PostgreSQL client libraries
# curl: HTTP client cho health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
# Virtual env giúp isolate dependencies và reduce image size
RUN python -m venv /opt/venv

# Activate virtual environment
# Các lệnh sau sẽ sử dụng Python và pip từ venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements file trước để leverage Docker layer caching
# Nếu requirements không thay đổi, Docker sẽ skip rebuild layer này
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Không lưu pip cache để giảm image size
# --upgrade pip: Upgrade pip lên version mới nhất
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 2: Production
# ============================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # APP_HOME: Thư mục chứa application trong container
    APP_HOME=/app \
    # PORT: Port mà Uvicorn sẽ listen
    PORT=8000 \
    # WORKERS: Số worker processes (auto = CPU cores * 2 + 1)
    WORKERS=4 \
    # LOG_LEVEL: Logging level cho production
    LOG_LEVEL=info

# Create non-root user cho security
# Chạy app dưới user không có root privileges giảm attack surface
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR $APP_HOME

# Install runtime system dependencies (nhẹ hơn build dependencies)
# curl: Cho health checks
# libpq5: PostgreSQL runtime library
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    # Clean apt cache để giảm image size
    && apt-get clean

# Copy virtual environment từ builder stage
# Chỉ copy đã compile packages, không copy build tools
COPY --from=builder /opt/venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
# --chown=appuser:appuser: Set ownership cho non-root user
COPY --chown=appuser:appuser src/ ./src/

# Copy storage directory (nếu có seed data)
COPY --chown=appuser:appuser storage/ ./storage/

# Create logs directory
RUN mkdir -p logs && chown -R appuser:appuser logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE $PORT

# Health check
# Docker sẽ kiểm tra endpoint này để xác định container health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Labels cho metadata
LABEL maintainer="Smart Tourism Team" \
      description="Smart Tourism Data Platform API" \
      version="1.0.0"

# Start application với Uvicorn
# --host 0.0.0.0: Listen trên tất cả interfaces (cần thiết cho Docker)
# --port $PORT: Dynamic port từ env var
# --workers $WORKERS: Multiple worker processes
# --access-log: Enable access logging
# --proxy-headers: Trust proxy headers (cho reverse proxy)
CMD exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers $WORKERS \
    --access-log \
    --proxy-headers \
    --forwarded-allow-ips="*"
