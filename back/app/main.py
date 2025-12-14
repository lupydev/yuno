import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.index import api_router
from app.infraestructure.core.config import settings
from app.workers.datalake_worker import create_datalake_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación (startup/shutdown)

    Inicializa y detiene el worker del Data Lake que procesa
    transacciones cada minuto automáticamente.
    """
    # Startup
    try:
        logger.info("Starting Data Lake worker...")
        app.state.datalake_worker = create_datalake_worker()
        app.state.datalake_worker.start()
        logger.info("✅ Data Lake worker started successfully")
    except Exception as e:
        logger.error(
            "Failed to start Data Lake worker",
            extra={"error": str(e)},
            exc_info=True,
        )
        app.state.datalake_worker = None

    yield

    # Shutdown
    if hasattr(app.state, "datalake_worker") and app.state.datalake_worker:
        try:
            logger.info("Stopping Data Lake worker...")
            app.state.datalake_worker.stop()
            logger.info("✅ Data Lake worker stopped successfully")
        except Exception as e:
            logger.error(
                "Error stopping Data Lake worker",
                extra={"error": str(e)},
                exc_info=True,
            )


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="validación y normalización de datos para una mejor toma de decisiones",
    version="0.0.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check(request: Request):
    """Health check endpoint"""
    worker = getattr(request.app.state, "datalake_worker", None)
    return {
        "status": "healthy",
        "worker": "running" if worker and worker.scheduler.running else "stopped",
    }
