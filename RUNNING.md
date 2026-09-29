# Running `upheld-ai-pdf-extract` (Local & Production Guide)

This guide provides instructions for running **`upheld-ai-pdf-extract`** locally and in production without Docker.

---

## Quick Reference

| Environment | Purpose | Command |
| :--- | :--- | :--- |
| **Local Dev** | Hot reload on port 8020 | `uvicorn app.main:app --host 0.0.0.0 --port 8020 --reload` |
| **Local Legacy** | Direct Python runner | `python app.py` |
| **Tests** | Automated test suite | `pytest -v` |
| **Production** | Multi-worker Gunicorn | `gunicorn -c gunicorn_conf.py app.main:app` |
| **Production Service** | Background daemon | `sudo systemctl start upheld-pdf-extract` |

---

## 1. Local Development Setup

### Prerequisites
- Python 3.9+ (Python 3.11 recommended)
- `pip` and `virtualenv`

### Step 1: Virtual Environment Setup
```bash
# Navigate to the project root
cd upheld-ai-pdf-extract

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest httpx
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `.env` contains your `API_TOKEN`:
```dotenv
API_TOKEN=TESTAPIKEK
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8020
MAX_FILE_SIZE_MB=50
MAX_PAGES=500
DEFAULT_RENDER_DPI=150
LOG_LEVEL=DEBUG
```

### Step 4: Start Local Server

#### Option A: FastAPI Uvicorn with Hot Reload (Recommended)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8020 --reload
```

#### Option B: Direct Python Execution
```bash
python app.py
```

#### Option C: Makefile Shortcut
```bash
make dev
```

Once started:
- **Interactive OpenAPI Documentation**: `http://localhost:8020/docs`
- **ReDoc Documentation**: `http://localhost:8020/redoc`
- **Liveness Probe**: `http://localhost:8020/health/live`
- **Legacy Endpoint**: `http://localhost:8020/extract-text`

---

## 2. Testing Your Local Server

Verify the service from another terminal using `curl`:

### Health Check (No Auth Required)
```bash
curl -s http://localhost:8020/health/live
# Response: {"status":"alive"}
```

### Legacy Endpoint (`upheld-ai-statements` Compatible)
```bash
curl -X POST http://localhost:8020/extract-text \
  -H "Authorization: Bearer TESTAPIKEK" \
  -F "file=@/path/to/statement.pdf"
```

### Modern v1 Multimodal Extraction
```bash
curl -X POST http://localhost:8020/api/v1/extract \
  -H "Authorization: Bearer TESTAPIKEK" \
  -F "file=@/path/to/statement.pdf" \
  -F "mode=full" \
  -F "extract_tables=true"
```

### Dedicated Table Extraction
```bash
curl -X POST http://localhost:8020/api/v1/tables \
  -H "Authorization: Bearer TESTAPIKEK" \
  -F "file=@/path/to/statement.pdf"
```

### Run Automated Tests
```bash
pytest -v
```

### Import into Postman
You can test all endpoints visually using the provided Postman collection:
1. Import [`postman_collection.json`](postman_collection.json) and [`postman_environment.json`](postman_environment.json) into Postman.
2. Select the **Upheld AI PDF Extract (Local)** environment.
3. Requests for Legacy (`/extract-text`), Health (`/health/*`), and v1 (`/api/v1/extract`, `/api/v1/tables`, `/api/v1/render-pages`, `/api/v1/inspect`) are pre-populated with authorization headers and multipart form presets.

---

## 3. Production Deployment (Native / Bare-Metal / VM)

In production, run the service with **Gunicorn** managing a pool of **UvicornWorker** processes. This provides multi-core utilization, worker recycling to prevent MuPDF memory fragmentation, and graceful reloads.

### Step 1: Install Production Dependencies
```bash
# In your server's application directory
cd /opt/upheld-ai-pdf-extract

# Create production virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Configure Production Environment (`.env`)
```dotenv
API_TOKEN=your-high-entropy-production-secret-token-here
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8020
REQUEST_TIMEOUT_SECONDS=120
WEB_CONCURRENCY=4
MAX_FILE_SIZE_MB=50
MAX_PAGES=500
DEFAULT_RENDER_DPI=150
LOG_LEVEL=INFO
```

### Step 3: Run Gunicorn Directly
```bash
source .venv/bin/activate
gunicorn -c gunicorn_conf.py app.main:app
```
`gunicorn_conf.py` automatically configures:
- Worker count: `(2 * CPU_CORES) + 1` (or via `WEB_CONCURRENCY`)
- Worker class: `uvicorn.workers.UvicornWorker`
- Request timeout: 120 seconds
- Worker recycling (`max_requests = 1000` with jitter) to prevent MuPDF C-heap fragmentation.

---

### Step 4: Run as a Systemd Service (Linux Auto-Restart)

To ensure the service runs on system boot and auto-restarts upon unexpected exit:

1. Create `/etc/systemd/system/upheld-pdf-extract.service`:

```ini
[Unit]
Description=Upheld AI PDF Extract Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/upheld-ai-pdf-extract
EnvironmentFile=/opt/upheld-ai-pdf-extract/.env
ExecStart=/opt/upheld-ai-pdf-extract/.venv/bin/gunicorn -c gunicorn_conf.py app.main:app
Restart=always
RestartSec=5s
LimitNOFILE=65536

# Resource limits (adjust based on server capacity)
MemoryHigh=2G
MemoryMax=3G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable upheld-pdf-extract
sudo systemctl start upheld-pdf-extract
```

3. Check service status and logs:
```bash
sudo systemctl status upheld-pdf-extract
journalctl -u upheld-pdf-extract -f
```

---

### Step 5: (Alternative) Supervisor Process Manager

If your infrastructure uses Supervisor:

Create `/etc/supervisor/conf.d/upheld_pdf_extract.conf`:

```ini
[program:upheld-pdf-extract]
directory=/opt/upheld-ai-pdf-extract
command=/opt/upheld-ai-pdf-extract/.venv/bin/gunicorn -c gunicorn_conf.py app.main:app
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
redirect_stderr=true
stdout_logfile=/var/log/upheld-pdf-extract.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/upheld-ai-pdf-extract/.venv/bin:%(ENV_PATH)s"
```

Update Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status upheld-pdf-extract
```

---

## 4. Reverse Proxy Setup (NGINX Example)

When exposing the service behind NGINX, ensure `client_max_body_size` and timeouts accommodate PDF uploads:

```nginx
server {
    listen 80;
    server_name pdf-extract.yourdomain.internal;

    # Allow up to 50MB PDF uploads
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8020;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Keep timeouts long enough for 50-page PDF processing
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
    }
}
```

---

## 5. Production Health Monitoring

Configure your load balancer or uptime checker to poll:
- **Liveness Probe**: `GET http://localhost:8020/health/live` (returns 200 `{"status":"alive"}`)
- **Readiness Probe**: `GET http://localhost:8020/health/ready` (validates PyMuPDF C bindings)
- **Telemetry**: `GET http://localhost:8020/health/status` (CPU/Memory usage and limits)
