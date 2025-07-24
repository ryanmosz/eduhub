# Multi-stage Dockerfile for EduHub
# Python 3.13 base image with slim variant for smaller size
FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Set work directory
WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY pyproject.toml tox.ini ./

# Change ownership to app user
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Default command for development
CMD ["uvicorn", "src.eduhub.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production dependencies stage
FROM base as prod-deps

# Install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM prod-deps as production

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Install the application
RUN pip install -e .

# Create non-root user
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command with gunicorn
CMD ["gunicorn", "src.eduhub.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Testing stage
FROM development as testing

# Run tests
RUN python -m pytest tests/ -v

# Linting stage  
FROM development as linting

# Run code quality checks
RUN black --check src tests && \
    isort --check-only src tests && \
    mypy src 