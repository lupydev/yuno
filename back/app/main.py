from app.api.index import api_router
from app.infraestructure.core.config import settings
from fastapi import FastAPI

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="validación y normalización de datos para una mejor toma de decisiones",
    version="0.0.1",
)

# Include API routes
app.include_router(api_router, prefix=settings.API)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
