"""
Worker Management Router

Endpoints para monitorear y controlar el Data Lake worker.
"""

import logging
from typing import Any

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
def get_worker_status(request: Request) -> dict[str, Any]:
    """
    Obtiene el estado del Data Lake worker

    Returns:
        Estado del worker (running/stopped) y configuración

    Example:
        ```bash
        curl http://localhost:8000/api/worker/status
        ```
    """
    datalake_worker = getattr(request.app.state, "datalake_worker", None)

    if not datalake_worker:
        return {
            "status": "not_initialized",
            "running": False,
        }

    is_running = datalake_worker.scheduler.running

    response = {
        "status": "running" if is_running else "stopped",
        "running": is_running,
        "interval_seconds": datalake_worker.interval_seconds,
    }

    # Agregar info de jobs si está corriendo
    if is_running:
        jobs = datalake_worker.scheduler.get_jobs()
        response["jobs"] = [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in jobs
        ]

    logger.debug("Worker status requested", extra=response)

    return response


@router.post("/trigger")
def trigger_worker(request: Request) -> dict[str, Any]:
    """
    Ejecuta el worker manualmente (una sola vez)

    Útil para testing o procesamiento inmediato de datos nuevos.

    Returns:
        Mensaje de confirmación

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/worker/trigger
        ```
    """
    datalake_worker = getattr(request.app.state, "datalake_worker", None)

    if not datalake_worker:
        return {
            "status": "error",
            "message": "Worker not initialized",
        }

    try:
        logger.info("Manual worker trigger requested")
        datalake_worker.run_once()

        return {
            "status": "success",
            "message": "Worker executed successfully",
        }
    except Exception as e:
        logger.error(
            "Failed to trigger worker manually",
            extra={"error": str(e)},
            exc_info=True,
        )
        return {
            "status": "error",
            "message": f"Failed to execute worker: {str(e)}",
        }
