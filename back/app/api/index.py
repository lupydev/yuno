"""
API index - Central router aggregator

Aggregates all API routers with proper versioning and documentation.
"""

from fastapi import APIRouter

from app.api.routers import auth_router, events, teams_router, users_router, worker

# Main API router
api_router = APIRouter()

# Authentication & User Management
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    teams_router,
    prefix="/teams",
    tags=["Teams"],
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)

# Payment Events
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(worker.router, prefix="/worker", tags=["worker"])

__all__ = ["api_router"]
