from app.core.config import settings
from fastapi import FastAPI

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="validación y normalización de datos para una mejor toma de decisiones",
    version="0.0.1",
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
