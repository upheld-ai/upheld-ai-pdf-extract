import os
from fastapi import APIRouter, Response, status

try:
    import psutil
except ImportError:
    psutil = None
from app.config import settings
from app.services.pdf_engine import PDFEngine

try:
    import pymupdf as fitz
    fitz_version = getattr(fitz, "__version__", "unknown")
except Exception:
    try:
        import fitz
        fitz_version = getattr(fitz, "__version__", "unknown")
    except Exception:
        fitz_version = "not installed"

health_router = APIRouter(prefix="/health", tags=["Health & Observability"])


@health_router.get("/live")
async def liveness():
    """Kubernetes liveness probe: indicates whether the process is alive."""
    return {"status": "alive"}


@health_router.get("/ready")
async def readiness(response: Response):
    """
    Kubernetes readiness probe: indicates whether the service is ready to accept traffic.
    Validates underlying C-engine availability.
    """
    if not PDFEngine.is_available():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "reason": "PyMuPDF engine is unavailable."}

    return {"status": "ready", "engine": "pymupdf", "engine_version": fitz_version}


@health_router.get("/status")
async def system_status():
    """Detailed runtime telemetry for production diagnostics."""
    mem_info = None
    try:
        process = psutil.Process(os.getpid())
        mem_info = {
            "rss_mb": round(process.memory_info().rss / (1024 * 1024), 2),
            "cpu_percent": process.cpu_percent(),
        }
    except Exception:
        pass

    return {
        "status": "healthy" if PDFEngine.is_available() else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "engine": {
            "name": "PyMuPDF",
            "version": fitz_version,
            "available": PDFEngine.is_available(),
        },
        "limits": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "max_pages": settings.MAX_PAGES,
            "default_render_dpi": settings.DEFAULT_RENDER_DPI,
        },
        "process": mem_info,
    }
