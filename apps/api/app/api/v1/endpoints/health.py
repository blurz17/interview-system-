from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.session import check_db_health
from app.schemas.health import LiveHealthResponse, ReadyHealthResponse

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("/live", response_model=LiveHealthResponse, status_code=status.HTTP_200_OK)
async def health_live() -> LiveHealthResponse:
    return LiveHealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )


@router.get("/ready", response_model=ReadyHealthResponse)
async def health_ready():
    db_healthy = await check_db_health()
    status_str = "ok" if db_healthy else "degraded"
    dependencies = {
        "database": "connected" if db_healthy else "unavailable",
    }
    http_status = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "status": status_str,
            "dependencies": dependencies,
        },
    )
