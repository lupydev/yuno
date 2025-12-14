from app.api.index import api_router
from app.infraestructure.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="validación y normalización de datos para una mejor toma de decisiones",
    version="0.0.1",
)

# Include API routes
app.include_router(api_router, prefix=settings.API)

# Configure CORS
_allow_origins = settings.all_cors_origins or ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
