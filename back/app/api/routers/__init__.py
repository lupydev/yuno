"""
API routers package

Exports all router instances for centralized registration.
"""

from app.api.routers import events, worker
from app.api.routers.auth import router as auth_router
from app.api.routers.teams import router as teams_router
from app.api.routers.users import router as users_router

__all__ = ["auth_router", "events", "teams_router", "users_router", "worker"]
