from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.coding import router as coding_router
from app.api.v1.endpoints.evaluations import router as evaluations_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.interviews import router as interviews_router
from app.api.v1.endpoints.resumes import router as resumes_router
from app.api.v1.endpoints.skills import router as skills_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount subrouters
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(skills_router)
api_v1_router.include_router(resumes_router)
api_v1_router.include_router(interviews_router)
api_v1_router.include_router(coding_router)
api_v1_router.include_router(evaluations_router)
