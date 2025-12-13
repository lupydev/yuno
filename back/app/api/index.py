"""
API index - Central router aggregator

Aggregates all API routers with proper versioning and documentation.
Follows FastAPI best practices for API organization.
"""

from fastapi import APIRouter

from app.api.routers import auth_router, payments_router

# Main API router
api_router = APIRouter()

# Include all routers with appropriate prefixes and tags
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    payments_router,
    prefix="/payments",
    tags=["Payments"],
)

__all__ = ["api_router"]
