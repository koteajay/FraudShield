"""Main FastAPI application entrypoint for FraudShield."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.database import init_db
from app.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.logging_config import logger, setup_logging
from app.routers import (
    health,
    behaviour,
    devices,
    security,
    transactions,
    users,
    dashboard,
    analytics,
    rules,
)
from app.journey import router as journey_router
from app.schemas.health import ApiInfoResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager managing startup and shutdown tasks."""
    # 1. Configure structured logging
    setup_logging()
    logger.info(f"{settings.APP_NAME} backend starting (env: {settings.APP_ENV})")

    # 2. Safely initialize database connection and metadata
    try:
        init_db()
    except Exception as exc:
        logger.error(f"Fatal error during database initialization: {exc}")

    # 3. Log application startup completion
    logger.info("Application startup complete")

    yield

    # 4. Clean shutdown handling
    logger.info(f"{settings.APP_NAME} backend shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="Explainable fraud detection and reviewer platform API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)  # Provides GET /health
app.include_router(health.router, prefix=settings.API_PREFIX)  # Also provides GET /api/health
app.include_router(behaviour.router, prefix=settings.API_PREFIX)  # Provides GET /api/users/{id}/behaviour-profile
app.include_router(devices.router, prefix=settings.API_PREFIX)  # Provides GET /api/users/{id}/devices
app.include_router(security.router, prefix=settings.API_PREFIX)  # Provides GET /api/users/{id}/account-takeover-risk
app.include_router(journey_router, prefix=settings.API_PREFIX)  # Provides GET /api/transactions/{id}/journey
app.include_router(transactions.router, prefix=settings.API_PREFIX)  # Provides /api/transactions
app.include_router(users.router, prefix=settings.API_PREFIX)  # Provides /api/users/{id}/profile & /journey
app.include_router(dashboard.router, prefix=settings.API_PREFIX)  # Provides /api/dashboard/stats
app.include_router(analytics.router, prefix=settings.API_PREFIX)  # Provides /api/analytics/fraud
app.include_router(rules.router, prefix=settings.API_PREFIX)  # Provides /api/rules & /api/rules/performance


@app.get(
    "/api",
    response_model=ApiInfoResponse,
    tags=["System"],
    summary="API Metadata",
    description="Provides basic service status and version information.",
)
def api_info():
    """Returns general API metadata and running environment."""
    return ApiInfoResponse(
        name=settings.APP_NAME,
        version="0.1.0",
        environment=settings.APP_ENV,
        status="running",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
