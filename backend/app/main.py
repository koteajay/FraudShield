"""Main FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import verify_database_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connection on startup
    db_connected = verify_database_connection()
    if not db_connected:
        print("[WARNING] Failed to establish initial database connection.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Explainable fraud detection and reviewer platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Health Check")
def health_check():
    """Health check endpoint required by Phase 0 specification."""
    return {"status": "ok"}


@app.get("/api", summary="API Information")
def api_info():
    """API metadata and service status."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
