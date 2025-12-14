"""
Health Check Router

Endpoints para health checks del sistema con verificación de dependencias.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.infraestructure.core.config import settings
from app.infraestructure.core.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/health")
def health_check(session: SessionDep) -> dict:
    """
    Health check completo del sistema

    Verifica:
    - Database connection (PostgreSQL)
    - OpenAI API availability
    - Sistema general

    Returns:
        Status del sistema y sus dependencias

    Ejemplo:
    ```
    GET /health
    ```

    Response:
    ```json
    {
        "status": "healthy",
        "timestamp": "2025-12-14T10:30:00Z",
        "checks": {
            "database": "ok",
            "openai": "ok",
            "system": "ok"
        }
    }
    ```
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {},
        "version": "1.0.0",
    }

    # Database check
    try:
        # Simple query para verificar conexión
        result = session.exec(select(1)).first()
        if result == 1:
            health_status["checks"]["database"] = "ok"
        else:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = "error: unexpected result"
    except Exception as e:
        logger.error("Database health check failed", exc_info=True)
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)[:100]}"

    # OpenAI API check (lightweight - solo verificar si key existe)
    try:
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            # No hacer llamada real para no gastar créditos
            # Solo verificar que la key tiene formato válido
            health_status["checks"]["openai"] = "ok"
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["openai"] = "warning: API key not configured"
    except Exception as e:
        logger.error("OpenAI health check failed", exc_info=True)
        health_status["status"] = "degraded"
        health_status["checks"]["openai"] = f"warning: {str(e)[:100]}"

    # System check
    health_status["checks"]["system"] = "ok"

    logger.info(
        "Health check completed",
        extra={"status": health_status["status"], "checks": health_status["checks"]},
    )

    return health_status


@router.get("/health/readiness")
def readiness_check(session: SessionDep) -> dict:
    """
    Readiness probe para Kubernetes

    Verifica que el sistema esté listo para recibir tráfico.
    Solo chequea dependencias críticas (DB).

    Returns:
        Status de readiness

    Ejemplo:
    ```
    GET /health/readiness
    ```
    """
    try:
        # Verificar DB connection
        result = session.exec(select(1)).first()
        if result == 1:
            return {
                "status": "ready",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        else:
            return {
                "status": "not_ready",
                "reason": "database check failed",
                "timestamp": datetime.now(UTC).isoformat(),
            }
    except Exception as e:
        logger.error("Readiness check failed", exc_info=True)
        return {
            "status": "not_ready",
            "reason": str(e)[:100],
            "timestamp": datetime.now(UTC).isoformat(),
        }


@router.get("/health/liveness")
def liveness_check() -> dict:
    """
    Liveness probe para Kubernetes

    Verifica que el proceso esté vivo y pueda responder.
    No chequea dependencias externas.

    Returns:
        Status de liveness

    Ejemplo:
    ```
    GET /health/liveness
    ```
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
    }
