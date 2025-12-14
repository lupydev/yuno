"""
API routers package

Exports all router instances for centralized registration.
"""

from app.api.routers import alert_reports, events, notifications, worker
from app.api.routers.alerts import router as alerts_router
from app.api.routers.analytics import router as analytics_router
from app.api.routers.auth import router as auth_router
from app.api.routers.health import router as health_router
from app.api.routers.teams import router as teams_router
from app.api.routers.users import router as users_router

__all__ = [
    "alert_reports",
    "alerts_router",
    "analytics_router",
    "auth_router",
    "events",
    "health_router",
    "notifications",
    "teams_router",
    "users_router",
    "worker",
]
