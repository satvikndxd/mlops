"""FastAPI application factory for AgentForge."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger("agentforge")


def create_app() -> FastAPI:
    configure_logging("DEBUG" if settings.debug else "INFO")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "AgentForge — open-source AgentOps platform for observability, cost "
            "tracking, evaluation, governance, and incident response of AI agents."
        ),
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health probes are also exposed at the root for load balancers.
    @app.get("/healthz", tags=["health"], summary="Liveness probe")
    def root_healthz() -> dict:
        return {"status": "ok", "app": settings.app_name}

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"name": settings.app_name, "docs": "/docs", "version": "0.1.0"}

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    logger.info("AgentForge API initialised (env=%s)", settings.environment)
    return app


app = create_app()
