"""
Gunicorn configuration for production deployment.
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8080"

# Workers
workers = multiprocessing.cpu_count() * 2 + 1

# Timeout for encoding operations (5 minutes)
timeout = 300

# Worker connections
worker_connections = 1000

# Max requests per worker before restart
max_requests = 1000

# Graceful timeout
graceful_timeout = 30

# Logging
accesslog = "/var/log/mp4-optimizer/access.log"
errorlog = "/var/log/mp4-optimizer/error.log"
loglevel = "info"

# Process naming
proc_name = "mp4-optimizer"

# Worker class
worker_class = "sync"

# Threads per worker
threads = 2

# Keepalive
keepalive = 5

# Max requests jitter
max_requests_jitter = 100

# Preload app
preload_app = True

# Sendfile
sendfile = True

# Retry logic
retry_timeout = 30

# Environment
raw_env = [
    f"PYTHONPATH={os.path.dirname(os.path.abspath(__file__))}",
    "FLASK_ENV=production"
]