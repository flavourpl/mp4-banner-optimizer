FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libx264-164 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mp4_optimizer/ ./mp4_optimizer/
COPY templates/ ./templates/
COPY web_app_prod.py ./web_app.py
COPY wsgi.py .

# Create directories for file storage
RUN mkdir -p uploads outputs reports

# Create non-root user for security
RUN useradd -m -u appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()"

# Run application
CMD ["gunicorn", "--config", "gunicorn_config.py", "wsgi:app"]