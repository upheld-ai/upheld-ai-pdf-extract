from __future__ import annotations

from fastapi import APIRouter
from app.api.v1.endpoints.extract import extract_router
from app.api.v1.endpoints.inspect import inspect_router
from app.api.v1.endpoints.render import render_router
from app.api.v1.endpoints.tables import tables_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(extract_router)
v1_router.include_router(tables_router)
v1_router.include_router(render_router)
v1_router.include_router(inspect_router)
