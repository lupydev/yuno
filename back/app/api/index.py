"""
API index - Central router aggregator

Aggregates all API routers with proper versioning and documentation.
Follows FastAPI best practices for API organization.
"""

from fastapi import APIRouter

from app.api.routers import (
    analytics_router,
    auth_router,
    events,
    health_router,
    notifications,
    teams_router,
    users_router,
    worker,
)

# Main API router
api_router = APIRouter()

# Health checks (sin prefix para que sea /health directamente)
api_router.include_router(
    health_router,
    tags=["Health"],
)

# Include all routers with appropriate prefixes and tags
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

api_router.include_router(
    notifications.router,
)

api_router.include_router(
    events.router,
    prefix="/events",
    tags=["Payment Events"],
)

api_router.include_router(
    worker.router,
    prefix="/worker",
    tags=["Worker Control"],
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics & Monitoring"],
)

__all__ = ["api_router"]
