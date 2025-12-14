"""
API routers package

Exports all router instances for centralized registration.
"""

from app.api.routers import events, worker
from app.api.routers.analytics import router as analytics_router
from app.api.routers.auth import router as auth_router
from app.api.routers.health import router as health_router
from app.api.routers.teams import router as teams_router
from app.api.routers.users import router as users_router

__all__ = [
    "analytics_router",
    "auth_router",
    "events",
    "health_router",
    "teams_router",
    "users_router",
    "worker",
]
