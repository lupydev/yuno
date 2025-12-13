# Guía de Mejores Prácticas - Payment Observability System

## 📚 Tabla de Contenidos

1. [Principios de Diseño](#principios-de-diseño)
2. [FastAPI Best Practices](#fastapi-best-practices)
3. [SQLModel & Database](#sqlmodel--database)
4. [LangChain & AI Integration](#langchain--ai-integration)
5. [Error Handling](#error-handling)
6. [Testing](#testing)
7. [Security](#security)
8. [Performance](#performance)

---

## 🎯 Principios de Diseño

### SOLID Principles

#### 1. Single Responsibility Principle (SRP)

**✅ CORRECTO:**

```python
# Cada clase tiene UNA responsabilidad clara

class AIBasedNormalizer:
    """Solo se encarga de normalizar usando IA"""
    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        ...

class PaymentRepository:
    """Solo se encarga de operaciones de BD"""
    async def save(self, event: NormalizedPaymentEvent) -> NormalizedPaymentEvent:
        ...

class IngestionOrchestrator:
    """Solo coordina el flujo de ingesta"""
    async def ingest(self, raw_event: dict) -> NormalizedPaymentEvent:
        ...
```

**❌ INCORRECTO:**

```python
class PaymentService:
    """Hace DEMASIADAS cosas - viola SRP"""
    async def normalize_and_save_and_send_email(self, raw_event: dict):
        # Normaliza con IA
        normalized = await self._call_openai(raw_event)

        # Guarda en BD
        await self._save_to_db(normalized)

        # Envía email (responsabilidad extra)
        await self._send_notification_email(normalized)

        # Hace analytics (otra responsabilidad)
        await self._update_metrics(normalized)
```

#### 2. Open/Closed Principle (OCP)

**✅ CORRECTO:**

```python
from abc import ABC, abstractmethod

# Abierto a extensión, cerrado a modificación
class INormalizer(Protocol):
    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        ...

# Extensión: Agregar nuevo normalizador SIN modificar existentes
class StripeNormalizer:
    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        # Lógica específica de Stripe
        ...

class AdyenNormalizer:
    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        # Lógica específica de Adyen
        ...

class AIBasedNormalizer:
    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        # Lógica genérica con LLM
        ...
```

**❌ INCORRECTO:**

```python
class Normalizer:
    async def normalize(self, raw_event: dict, provider: str):
        # Cada vez que agregamos un provider, modificamos esta clase
        if provider == "stripe":
            return self._normalize_stripe(raw_event)
        elif provider == "adyen":
            return self._normalize_adyen(raw_event)
        elif provider == "mercadopago":  # Nueva modificación
            return self._normalize_mercadopago(raw_event)
        # ... más if/elif
```

#### 3. Dependency Inversion Principle (DIP)

**✅ CORRECTO:**

```python
# Depende de abstracciones, no de implementaciones concretas

class IngestionOrchestrator:
    def __init__(
        self,
        normalizer: INormalizer,  # Interface, no clase concreta
        repository: IPaymentRepository,  # Interface
    ):
        self.normalizer = normalizer
        self.repository = repository

# Dependency Injection en FastAPI
def get_ingestion_orchestrator(
    normalizer: Annotated[INormalizer, Depends(get_normalizer)],
    repo: Annotated[IPaymentRepository, Depends(get_repository)]
) -> IngestionOrchestrator:
    return IngestionOrchestrator(normalizer, repo)
```

**❌ INCORRECTO:**

```python
# Depende de implementaciones concretas
class IngestionOrchestrator:
    def __init__(self):
        # Crea sus propias dependencias (acoplamiento fuerte)
        self.normalizer = AIBasedNormalizer()
        self.repository = PaymentRepository(Session())
        self.openai_client = OpenAI(api_key="hardcoded")  # ¡Horror!
```

---

## 🚀 FastAPI Best Practices

### 1. Request/Response Models Separados

**✅ CORRECTO:**

```python
# Schemas de API separados de modelos de dominio

# Request DTO
class EventIngestRequest(BaseModel):
    raw_event: dict = Field(..., description="Evento de pago en cualquier formato")
    provider: str | None = Field(None, description="Hint del proveedor")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "raw_event": {"status": "succeeded", "amount": 5000},
                "provider": "stripe"
            }
        }
    )

# Response DTO
class EventIngestResponse(BaseModel):
    id: UUID
    status: PaymentStatus
    message: str = "Event ingested successfully"

    # NO incluir campos sensibles o internos
    model_config = ConfigDict(from_attributes=True)

# Modelo de dominio (separado)
class NormalizedPaymentEvent(SQLModel, table=True):
    # Campos completos para BD
    ...
```

**❌ INCORRECTO:**

```python
# Usar el mismo modelo para todo
@router.post("/events")
async def ingest_event(event: NormalizedPaymentEvent):  # ❌ Modelo de BD en request
    # Esto expone campos internos y permite ataques de mass assignment
    ...
```

### 2. Dependency Injection Correcta

**✅ CORRECTO:**

```python
from typing import Annotated

# Definir dependencias reusables
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

@router.post("/events")
async def ingest_event(
    request: EventIngestRequest,
    session: AsyncSessionDep,  # Inyectado automáticamente
    orchestrator: Annotated[IngestionOrchestrator, Depends(get_orchestrator)]
) -> EventIngestResponse:
    result = await orchestrator.ingest(request.raw_event)
    return EventIngestResponse.from_orm(result)
```

**❌ INCORRECTO:**

```python
@router.post("/events")
async def ingest_event(request: EventIngestRequest):
    # Crear dependencias manualmente (anti-pattern)
    session = AsyncSession(engine)
    repo = PaymentRepository(session)
    orchestrator = IngestionOrchestrator(repo)

    # Olvidamos cerrar session → memory leak
    result = await orchestrator.ingest(request.raw_event)
    return result
```

### 3. Error Handling con Exception Handlers

**✅ CORRECTO:**

```python
# main.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

@app.exception_handler(ValidationException)
async def validation_exception_handler(
    request: Request,
    exc: ValidationException
) -> JSONResponse:
    logger.warning(
        "validation_error",
        extra={
            "path": request.url.path,
            "error": str(exc),
            "error_code": exc.error_code
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "error_code": exc.error_code
        }
    )
```

**❌ INCORRECTO:**

```python
@router.post("/events")
async def ingest_event(request: EventIngestRequest):
    try:
        result = await orchestrator.ingest(request.raw_event)
        return result
    except Exception as e:  # ❌ Catch genérico en cada endpoint
        return {"error": str(e)}  # ❌ No usa status codes correctos
```

### 4. Validaciones con Pydantic

**✅ CORRECTO:**

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict

class EventIngestRequest(BaseModel):
    raw_event: dict = Field(..., min_length=1)
    provider: str | None = Field(None, max_length=50)

    @field_validator("raw_event")
    @classmethod
    def validate_not_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("raw_event cannot be empty")
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider_format(cls, v: str | None) -> str | None:
        if v is not None:
            allowed_providers = ["stripe", "adyen", "mercadopago"]
            if v.lower() not in allowed_providers:
                logger.warning(f"Unknown provider: {v}")
        return v.lower() if v else None

    model_config = ConfigDict(str_strip_whitespace=True)
```

**❌ INCORRECTO:**

```python
class EventIngestRequest(BaseModel):
    raw_event: dict  # Sin validaciones
    provider: str  # Sin límites

    # Validar en el endpoint (anti-pattern)
```

---

## 🗄 SQLModel & Database

### 1. Async Sessions Correctamente

**✅ CORRECTO:**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# engine.py
async_engine = create_async_engine(
    str(settings.DATABASE_URI),
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,  # Validar conexiones antes de usar
    pool_size=20,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Evitar queries extra después de commit
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**❌ INCORRECTO:**

```python
# Usar sync sessions en código async
def get_session():  # ❌ Función sync
    with Session(engine) as session:  # ❌ Bloquea el event loop
        yield session

# Crear engine sin pool configuration
engine = create_async_engine(str(settings.DATABASE_URI))  # ❌ Sin tuning
```

### 2. Modelos SQLModel con Índices

**✅ CORRECTO:**

```python
from sqlmodel import Field, SQLModel, Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from uuid import UUID, uuid4

class NormalizedPaymentEvent(SQLModel, table=True):
    __tablename__ = "normalized_payment_events"

    # Índices definidos en el modelo
    __table_args__ = (
        Index("idx_created_at", "created_at"),
        Index("idx_provider_status", "provider", "status_category"),
        Index("idx_merchant_country", "merchant_name", "country"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_name: str = Field(index=True, max_length=255)
    status_category: str = Field(index=True, max_length=50)

    # JSONB para datos flexibles
    raw_data: dict = Field(default={}, sa_column=Column(JSONB))
    metadata: dict = Field(default={}, sa_column=Column(JSONB))

    # Validaciones de negocio
    @field_validator("amount_usd")
    @classmethod
    def validate_positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
```

**❌ INCORRECTO:**

```python
class NormalizedPaymentEvent(SQLModel, table=True):
    # Sin índices → queries lentas
    merchant_name: str  # Sin index en campo que se filtra frecuentemente
    status_category: str

    # JSONB sin type hints
    raw_data = Column(JSONB)  # ❌ Sin Field(), sin default

    # Sin validaciones
```

### 3. Repository Pattern

**✅ CORRECTO:**

```python
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event: NormalizedPaymentEvent) -> NormalizedPaymentEvent:
        """Guarda un evento, manejando duplicados"""
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_by_id(self, event_id: UUID) -> NormalizedPaymentEvent | None:
        """Obtiene evento por ID"""
        result = await self.session.execute(
            select(NormalizedPaymentEvent).where(NormalizedPaymentEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_filters(
        self,
        provider: str | None = None,
        status: PaymentStatus | None = None,
        limit: int = 100,
    ) -> list[NormalizedPaymentEvent]:
        """Query con filtros opcionales"""
        query = select(NormalizedPaymentEvent)

        if provider:
            query = query.where(NormalizedPaymentEvent.provider == provider)
        if status:
            query = query.where(NormalizedPaymentEvent.status_category == status)

        query = query.limit(limit).order_by(NormalizedPaymentEvent.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())
```

**❌ INCORRECTO:**

```python
# Queries directas en endpoints (anti-pattern)
@router.get("/events")
async def get_events(session: AsyncSessionDep):
    # ❌ Lógica de BD en API layer
    result = await session.execute(select(NormalizedPaymentEvent))
    return result.scalars().all()
```

---

## 🤖 LangChain & AI Integration

### 1. Structured Output con Retry

**✅ CORRECTO:**

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

class NormalizedPaymentSchema(BaseModel):
    """Schema para structured output de LangChain"""
    merchant_name: str
    provider: str
    country: str
    status_category: PaymentStatus
    amount_usd: float
    # ... otros campos

class AIBasedNormalizer:
    def __init__(self, settings: Settings):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.0,  # Determinismo
            timeout=settings.AI_TIMEOUT_SECONDS,
            max_retries=0,  # Manejamos retries manualmente
        )

        self.structured_llm = self.llm.with_structured_output(
            NormalizedPaymentSchema
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PAYMENT_NORMALIZATION_SYSTEM_PROMPT),
            ("user", "{raw_event}")
        ])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        """Normaliza con retry automático"""
        try:
            chain = self.prompt | self.structured_llm

            result = await chain.ainvoke({
                "raw_event": json.dumps(raw_event, indent=2)
            })

            logger.info(
                "ai_normalization_success",
                extra={
                    "provider": result.provider,
                    "status": result.status_category
                }
            )

            return result

        except Exception as e:
            logger.error(
                "ai_normalization_failed",
                exc_info=True,
                extra={"raw_event": raw_event}
            )
            raise AIServiceException(f"Normalization failed: {e}")
```

**❌ INCORRECTO:**

```python
class AIBasedNormalizer:
    async def normalize(self, raw_event: dict):
        # ❌ Sin structured output → parsing manual frágil
        response = await self.llm.ainvoke(f"Normaliza esto: {raw_event}")

        # ❌ Parsing manual de JSON
        result = json.loads(response.content)

        # ❌ Sin validación
        return result

        # ❌ Sin retry
        # ❌ Sin logging
        # ❌ Sin manejo de errores específicos
```

### 2. System Prompts Robustos

**✅ CORRECTO:**

```python
PAYMENT_NORMALIZATION_SYSTEM_PROMPT = """
Eres un experto en normalización de datos de pagos de múltiples proveedores.

INSTRUCCIONES CRÍTICAS:
1. NO inventes datos si no están presentes en el input → usa null
2. SIEMPRE valida que los valores sean coherentes (ej: amount > 0)
3. Estandariza códigos de error según este catálogo:
   - "card declined", "tarjeta rechazada", "declined" → "BANK_DECLINE"
   - "insufficient funds", "fondos insuficientes" → "INSUFFICIENT_FUNDS"
   - "expired", "vencida" → "CARD_EXPIRED"
   - "timeout" → "TIMEOUT"

4. Convierte amounts SIEMPRE a USD:
   - Si currency != USD, usa exchange rates aproximados
   - Si no está la currency, asume USD

5. Formato de país: ISO 3166-1 alpha-2 (ej: "MX", "BR", "US")
   - Si viene "Mexico" → "MX"
   - Si viene "Brasil" → "BR"

6. Estados válidos: APPROVED, FAILED, ERROR, PENDING
   - "succeeded", "approved", "completado" → APPROVED
   - "failed", "declined", "rechazado" → FAILED
   - "error", "exception" → ERROR
   - "pending", "processing" → PENDING

PRIORIDAD: Precisión > Completitud
Si tienes dudas, usa null en vez de adivinar.

IMPORTANTE: Retorna SOLO el JSON estructurado, sin explicaciones.
"""
```

**❌ INCORRECTO:**

```python
SYSTEM_PROMPT = "Normaliza este pago"  # ❌ Muy vago

# O peor aún:
prompt = f"Convierte este JSON {raw_event} a formato standard"  # ❌ Sin estructura
```

### 3. Manejo de Rate Limits y Timeouts

**✅ CORRECTO:**

```python
from openai import RateLimitError, APITimeoutError, APIError

class AIBasedNormalizer:
    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        try:
            return await self._do_normalize(raw_event)

        except RateLimitError as e:
            # Rate limit → esperar y reintentar
            logger.warning(
                "openai_rate_limit",
                extra={"retry_after": e.response.headers.get("Retry-After")}
            )
            raise AIServiceException("AI service rate limited") from e

        except APITimeoutError as e:
            # Timeout → puede ser temporal
            logger.error("openai_timeout", exc_info=True)
            raise AIServiceException("AI service timeout") from e

        except APIError as e:
            # Error de OpenAI
            logger.error(
                "openai_api_error",
                exc_info=True,
                extra={"status_code": e.status_code}
            )
            raise AIServiceException(f"AI API error: {e}") from e
```

**❌ INCORRECTO:**

```python
async def normalize(self, raw_event: dict):
    try:
        return await self.llm.ainvoke(...)
    except Exception as e:  # ❌ Catch genérico
        print(f"Error: {e}")  # ❌ Sin logging estructurado
        return None  # ❌ Devuelve None en vez de raise
```

---

## 🛡 Error Handling

### 1. Jerarquía de Excepciones Custom

**✅ CORRECTO:**

```python
class PaymentObservabilityException(Exception):
    """Base exception para el dominio"""
    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class NormalizationException(PaymentObservabilityException):
    """Errores de normalización"""
    pass

class AIServiceException(NormalizationException):
    """Específico de servicios de IA"""
    pass

class ValidationException(PaymentObservabilityException):
    """Errores de validación de negocio"""
    pass

class RepositoryException(PaymentObservabilityException):
    """Errores de persistencia"""
    pass

# Uso
raise AIServiceException(
    "Failed to normalize event",
    error_code="AI_TIMEOUT"
)
```

### 2. Guardar Eventos Fallidos (No Perder Datos)

**✅ CORRECTO:**

```python
class IngestionOrchestrator:
    async def ingest(self, raw_event: dict) -> NormalizedPaymentEvent:
        try:
            # Pipeline normal
            normalized = await self.normalizer.normalize(raw_event)
            event = self._to_model(normalized, raw_event)
            return await self.repository.save(event)

        except AIServiceException as e:
            # IA falló → guardar como UNPROCESSED
            logger.warning(
                "normalization_failed_saving_as_unprocessed",
                extra={"error": str(e)}
            )
            return await self._save_as_unprocessed(raw_event, str(e))

        except ValidationException as e:
            # Validación falló → también guardar
            return await self._save_as_unprocessed(raw_event, str(e))

    async def _save_as_unprocessed(
        self,
        raw_event: dict,
        error_message: str
    ) -> NormalizedPaymentEvent:
        """Guarda evento que no se pudo procesar"""
        unprocessed_event = NormalizedPaymentEvent(
            status_category=PaymentStatus.UNPROCESSED,
            merchant_name="UNKNOWN",
            provider="UNKNOWN",
            country="XX",
            amount_usd=0.0,
            raw_data=raw_event,
            validation_errors=[error_message],
            normalization_method=NormalizationMethod.MANUAL,
        )
        return await self.repository.save(unprocessed_event)
```

---

## 🧪 Testing

### 1. Unit Tests con Mocks

**✅ CORRECTO:**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_ai_normalizer_success():
    # Arrange
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = NormalizedPaymentSchema(
        merchant_name="Test Merchant",
        provider="stripe",
        country="US",
        status_category=PaymentStatus.APPROVED,
        amount_usd=100.0,
    )

    normalizer = AIBasedNormalizer(mock_llm)
    raw_event = {"status": "succeeded", "amount": 100}

    # Act
    result = await normalizer.normalize(raw_event)

    # Assert
    assert result.merchant_name == "Test Merchant"
    assert result.status_category == PaymentStatus.APPROVED
    mock_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_ai_normalizer_timeout():
    # Arrange
    mock_llm = AsyncMock()
    mock_llm.ainvoke.side_effect = APITimeoutError("Timeout")

    normalizer = AIBasedNormalizer(mock_llm)

    # Act & Assert
    with pytest.raises(AIServiceException) as exc_info:
        await normalizer.normalize({})

    assert "timeout" in str(exc_info.value).lower()
```

### 2. Integration Tests con Test Database

**✅ CORRECTO:**

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def test_db():
    """Fixture de DB de test con transacciones rollback"""
    engine = create_async_engine(
        "postgresql+psycopg_async://user:pass@localhost/test_db"
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()  # Rollback después de cada test

@pytest.mark.asyncio
async def test_payment_repository_save(test_db):
    # Arrange
    repo = PaymentRepository(test_db)
    event = NormalizedPaymentEvent(
        merchant_name="Test",
        provider="stripe",
        country="US",
        status_category=PaymentStatus.APPROVED,
        amount_usd=100.0,
    )

    # Act
    saved = await repo.save(event)

    # Assert
    assert saved.id is not None

    # Verificar que se guardó
    retrieved = await repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.merchant_name == "Test"
```

---

## 🔒 Security

### 1. Nunca Hardcodear Secrets

**✅ CORRECTO:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    POSTGRES_PASSWORD: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Usar desde settings
llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY)
```

**❌ INCORRECTO:**

```python
# ❌ Hardcoded secrets
OPENAI_API_KEY = "sk-1234567890abcdef"  # ❌ Nunca hacer esto

llm = ChatOpenAI(api_key="sk-hardcoded")  # ❌ Horror
```

### 2. Sanitizar Datos Sensibles en Logs

**✅ CORRECTO:**

```python
def sanitize_event_for_logging(event: dict) -> dict:
    """Remueve datos sensibles antes de loggear"""
    sensitive_fields = ["card_number", "cvv", "ssn", "password"]

    sanitized = event.copy()
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "***REDACTED***"

    return sanitized

logger.info(
    "event_received",
    extra={"event": sanitize_event_for_logging(raw_event)}
)
```

---

## ⚡ Performance

### 1. Usar Bulk Inserts

**✅ CORRECTO:**

```python
async def save_batch(self, events: list[NormalizedPaymentEvent]) -> None:
    """Guarda múltiples eventos en una transacción"""
    self.session.add_all(events)
    await self.session.commit()
```

### 2. Índices Compuestos para Queries Comunes

**✅ CORRECTO:**

```python
class NormalizedPaymentEvent(SQLModel, table=True):
    __table_args__ = (
        # Índice compuesto para analytics
        Index(
            "idx_analytics",
            "provider",
            "status_category",
            "created_at",
        ),
    )
```

---

**Fin de Best Practices Guide** 🎉
