FROM python:3.11-slim

# Set metadata
LABEL maintainer="Exploratory QA POC Team"
LABEL description="Exploratory QA Test Case Generator POC"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    libxss1 \
    libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/
COPY tests/ ./tests/
COPY docs/ ./docs/
COPY CLAUDE.md README.md ./

# Create necessary directories
RUN mkdir -p outputs logs config

# Set environment variables
ENV PYTHONPATH=/app
ENV BROWSER_USE_SETUP_LOGGING=true
ENV BROWSER_USE_TELEMETRY=false
ENV POC_HEADLESS=true

# Create non-root user for security
RUN useradd -m -u 1000 pocuser && \
    chown -R pocuser:pocuser /app
USER pocuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import src.test_models; print('POC Health Check: OK')" || exit 1

# Default command
CMD ["python3", "examples/basic_usage.py"]

# Expose port for potential web interface
EXPOSE 8000