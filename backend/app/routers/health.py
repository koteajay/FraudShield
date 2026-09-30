"""Health check endpoint router."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.database import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application & Database Health Check",
    description="Verifies the FastAPI service is active and verifies SQLite database connectivity.",
)
def get_health():
    """Checks the health of the application and its database connection."""
    db_connected = check_db_health()

    if not db_connected:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "database": "disconnected",
            },
        )

    return HealthResponse(
        status="ok",
        database="connected",
    )
