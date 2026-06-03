"""FastAPI application factory for AgentForge."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import metrics_response, prometheus_middleware
from app.services.audit_service import record_audit

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

    app.middleware("http")(prometheus_middleware)

    @app.middleware("http")
    async def audit_middleware(request, call_next):  # noqa: ANN001, ANN202
        response = await call_next(request)
        record_audit(request, response)
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics():  # noqa: ANN202
        return metrics_response()

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
