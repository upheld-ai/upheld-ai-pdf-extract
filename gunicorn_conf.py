import multiprocessing
import os

bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8020')}"
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
keepalive = 5

# Memory management: restart workers after handling N requests to prevent MuPDF C leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s µs'
