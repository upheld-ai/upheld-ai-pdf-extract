.PHONY: help install dev run run-prod test clean

help:
	@echo "Available commands for upheld-ai-pdf-extract:"
	@echo "  make install       Install all production and test dependencies"
	@echo "  make dev           Run local FastAPI development server with hot-reload"
	@echo "  make run-prod      Run production server using Gunicorn and Uvicorn workers"
	@echo "  make test          Run the full automated test suite (pytest)"
	@echo "  make clean         Remove cached bytecode and temporary files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest httpx

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8020 --reload

run: dev

run-prod:
	gunicorn -c gunicorn_conf.py app.main:app

test:
	pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
