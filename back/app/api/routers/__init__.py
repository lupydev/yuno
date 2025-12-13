"""
API routers package

Exports all router instances for centralized registration.
"""

from app.api.routers.auth import router as auth_router
from app.api.routers.payments import router as payments_router

__all__ = ["auth_router", "payments_router"]
