from __future__ import annotations

import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.legacy import legacy_router
from app.api.v1.endpoints.health import health_router
from app.api.v1.router import v1_router
from app.config import settings
from app.core.exceptions import PDFExtractException, pdf_exception_handler
from app.core.logging import logger
from app.core.middleware import RequestCorrelationMiddleware
from app.services.pdf_engine import PDFEngine


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management: startup validation and graceful shutdown."""
    # Validate critical configuration
    try:
        settings.validate()
        logger.info(f"Loaded configuration for environment: {settings.ENVIRONMENT}")
    except RuntimeError as exc:
        logger.error(f"Configuration error: {exc}")

    # Check extraction engine
    if PDFEngine.is_available():
        logger.info("PyMuPDF engine initialized successfully.")
    else:
        logger.warning(
            "PyMuPDF (fitz) is not installed in the active environment. "
            "Please install pymupdf to enable document extraction."
        )

    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} on port {settings.PORT}"
    )

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}.")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production_hidden" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production_hidden" else None,
    )

    # 1. Register Core Middlewares
    application.add_middleware(RequestCorrelationMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # 2. Register Global Exception Handlers
    application.add_exception_handler(PDFExtractException, pdf_exception_handler)

    # 3. Mount Routers
    # Health checks (unauthenticated, for Kubernetes/monitoring probes)
    application.include_router(health_router)

    # Legacy router (100% backward-compatible with upheld-ai-statements)
    application.include_router(legacy_router)

    # V1 modern modular endpoints
    application.include_router(v1_router)

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
    )
