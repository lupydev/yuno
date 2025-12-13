# Arquitectura del Sistema de Observabilidad de Pagos

## 📋 Índice

1. [Visión General](#visión-general)
2. [Stack Técnico](#stack-técnico)
3. [Arquitectura de Capas](#arquitectura-de-capas)
4. [Modelos de Dominio](#modelos-de-dominio)
5. [Flujo de Datos](#flujo-de-datos)
6. [Diseño de Servicios](#diseño-de-servicios)
7. [Principios de Diseño](#principios-de-diseño)

---

## 🎯 Visión General

Sistema backend de **Observabilidad de Pagos** diseñado para ingerir, normalizar y almacenar transacciones de pago provenientes de múltiples proveedores con formatos heterogéneos. Utiliza un enfoque híbrido (Reglas + IA) para garantizar consistencia y calidad de datos.

### Objetivos Principales

- ✅ **Ingesta Resiliente**: Aceptar datos en formatos variados sin perder información
- ✅ **Normalización Inteligente**: Usar IA para estandarizar datos complejos
- ✅ **Trazabilidad**: Mantener datos originales para auditoría
- ✅ **Analítica**: Estructura unificada para insights y métricas

---

## 🛠 Stack Técnico

```yaml
Framework: FastAPI 0.124.2+
ORM: SQLModel 0.0.27+ (Pydantic v2 + SQLAlchemy Core)
Database: PostgreSQL (con soporte JSONB)
AI/LLM:
  - LangChain 1.1.3+
  - LangChain-OpenAI 0.3.0+
  - OpenAI GPT-4o-mini (normalización rápida)
Migrations: Alembic 1.17.2+
Validation: Pydantic 2.12.5+
Async: asyncio + psycopg (async driver)
```

---

## 🏗 Arquitectura de Capas

Seguimos **Clean Architecture** y **Hexagonal Architecture** para separación de responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                  │
│  - Routers: /api/v1/events, /api/v1/analytics           │
│  - Validation: Request/Response schemas                 │
│  - Error Handling: Custom exception handlers            │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                  Application Services                   │
│  - IngestionOrchestrator: Coordina normalización        │
│  - AnalyticsService: Métricas y agregaciones            │
│  - EventProcessor: Validaciones de negocio              │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Domain Layer                          │
│  - Models: Entidades de negocio (SQLModel)              │
│  - Interfaces: Contratos (Protocols/ABC)                │
│  - Normalizers: Reglas de negocio para normalización    │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│               Infrastructure Layer                      │
│  - AI: LangChain clients (OpenAI/Anthropic)             │
│  - Database: AsyncSession, Repositories                 │
│  - Config: Settings, Environment vars                   │
│  - External APIs: Payment providers (futuro)            │
└─────────────────────────────────────────────────────────┘
```

### Estructura de Directorios

```
/app
├── main.py                          # Entry point - FastAPI app
├── __init__.py
│
├── /api                             # API Layer
│   ├── __init__.py
│   ├── main.py                      # Router aggregator
│   └── /v1
│       ├── __init__.py
│       ├── /routers
│       │   ├── events.py            # POST /events, GET /events/{id}
│       │   ├── analytics.py         # GET /analytics/metrics
│       │   └── health.py            # Health checks
│       └── /schemas
│           ├── event_request.py     # Request DTOs
│           └── event_response.py    # Response DTOs
│
├── /services                        # Application Services
│   ├── __init__.py
│   ├── ingestion_orchestrator.py   # Coordina normalización + persistencia
│   ├── ai_normalizer.py             # LangChain integration
│   ├── analytics_service.py         # Agregaciones y métricas
│   └── event_processor.py           # Validaciones de negocio
│
├── /domain                          # Domain Layer
│   ├── /models
│   │   ├── __init__.py
│   │   ├── payment_event.py         # NormalizedPaymentEvent (SQLModel)
│   │   └── failure_catalog.py       # Catálogo de errores
│   ├── /interfaces
│   │   ├── __init__.py
│   │   ├── normalizer.py            # Protocol para normalizadores
│   │   └── repository.py            # Repository interface
│   ├── /normalizers
│   │   ├── __init__.py
│   │   ├── rule_based.py            # Normalizador basado en reglas
│   │   └── hybrid.py                # Combina reglas + IA
│   └── /events                      # Domain Events (futuro)
│       └── __init__.py
│
├── /infraestructure                 # Infrastructure Layer
│   ├── /core
│   │   ├── config.py                # Pydantic Settings
│   │   ├── db.py                    # Async Engine + SessionDep
│   │   ├── deps.py                  # FastAPI dependencies
│   │   └── logging.py               # Structured logging
│   ├── /ai
│   │   ├── __init__.py
│   │   ├── langchain_client.py      # LangChain setup
│   │   └── prompts.py               # System prompts para normalización
│   ├── /repositories
│   │   ├── __init__.py
│   │   └── payment_repository.py    # Implementación de Repository
│   └── /kafka                       # (Opcional) Event streaming
│       ├── producer.py
│       └── consumer.py
│
└── /workers                         # Background Workers
    ├── __init__.py
    └── batch_normalizer.py          # Procesa eventos UNPROCESSED
```

---

## 📊 Modelos de Dominio

### 1. NormalizedPaymentEvent (Tabla Principal)

```python
from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Column, Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB


class NormalizedPaymentEvent(SQLModel, table=True):
    """
    Evento de pago normalizado.

    Principios:
    - Columnas tipadas para campos críticos (queries rápidas)
    - JSONB para metadatos flexibles
    - raw_data preserva el original (auditoría)
    - created_at para particionamiento futuro
    """
    __tablename__ = "normalized_payment_events"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Campos de Negocio (Indexados)
    merchant_name: str = Field(index=True, max_length=255)
    provider: str = Field(index=True, max_length=100)  # stripe, adyen, mercadopago
    country: str = Field(index=True, max_length=2)  # ISO 3166-1 alpha-2

    # Estado normalizado
    status_category: str = Field(index=True)  # APPROVED, FAILED, ERROR, PENDING
    failure_reason: str | None = Field(default=None, max_length=100)  # Código estandarizado

    # Métricas
    amount_usd: float = Field(index=True)  # Siempre en USD para consistencia
    latency_ms: int | None = Field(default=None)  # Tiempo de respuesta del provider

    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    normalized_at: datetime = Field(default_factory=datetime.utcnow)
    normalization_method: str = Field(default="AI")  # AI, RULE_BASED, HYBRID

    # Datos flexibles
    raw_data: dict = Field(default={}, sa_column=Column(JSONB))  # Evento original
    metadata: dict = Field(default={}, sa_column=Column(JSONB))  # Extra: fees, customer_id, etc

    # Campos de calidad
    confidence_score: float | None = Field(default=None)  # Confianza de la IA (0-1)
    validation_errors: list[str] | None = Field(default=None, sa_column=Column(JSONB))


class Config:
    """Configuración SQLModel"""
    arbitrary_types_allowed = True
```

### 2. Enums y Catálogos

```python
from enum import Enum

class PaymentStatus(str, Enum):
    """Estados normalizados de pagos"""
    APPROVED = "APPROVED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    PENDING = "PENDING"
    UNPROCESSED = "UNPROCESSED"  # Falló normalización

class FailureReason(str, Enum):
    """Catálogo de razones de falla estandarizadas"""
    # Bank-related
    BANK_DECLINE = "BANK_DECLINE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    CARD_EXPIRED = "CARD_EXPIRED"
    INVALID_CARD = "INVALID_CARD"

    # Fraud/Security
    FRAUD_SUSPECTED = "FRAUD_SUSPECTED"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"

    # Technical
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"

    # Business
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"

    # Unknown
    UNKNOWN = "UNKNOWN"

class NormalizationMethod(str, Enum):
    AI = "AI"
    RULE_BASED = "RULE_BASED"
    HYBRID = "HYBRID"
    MANUAL = "MANUAL"
```

---

## 🔄 Flujo de Datos

### Flujo de Ingesta (Happy Path)

```
┌─────────────┐
│   Client    │
│ POST /events│
└──────┬──────┘
       │ {"transaction": {...}, "provider": "stripe"}
       ▼
┌──────────────────────────────────────────┐
│   1. API Router (events.py)              │
│   - Validación básica (Pydantic)         │
│   - Rate limiting (SlowAPI)              │
└──────┬───────────────────────────────────┘
       │ EventIngestRequest
       ▼
┌──────────────────────────────────────────┐
│   2. IngestionOrchestrator               │
│   - Identifica proveedor                 │
│   - Selecciona estrategia normalización  │
└──────┬───────────────────────────────────┘
       │
       ├─── Rule-Based? ──> RuleBasedNormalizer
       │                    (Stripe, formato conocido)
       │
       └─── Unknown? ──────> AIBasedNormalizer
                             (LangChain + GPT-4o-mini)
       │
       ▼
┌──────────────────────────────────────────┐
│   3. AI Normalizer Service               │
│   - ChatOpenAI.with_structured_output    │
│   - System Prompt robusto                │
│   - Retry con exponential backoff        │
└──────┬───────────────────────────────────┘
       │ NormalizedPaymentEvent (Pydantic)
       ▼
┌──────────────────────────────────────────┐
│   4. EventProcessor (Validaciones)       │
│   - Validar country (ISO)                │
│   - Validar amount > 0                   │
│   - Mapear failure_reason a catálogo     │
└──────┬───────────────────────────────────┘
       │ Valid ✓
       ▼
┌──────────────────────────────────────────┐
│   5. PaymentRepository.save()            │
│   - AsyncSession.add()                   │
│   - Commit + Refresh                     │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│   6. Response                            │
│   {"id": "uuid", "status": "APPROVED"}   │
└──────────────────────────────────────────┘
```

### Flujo de Error (Resiliente)

```
┌─────────────────────────────────────┐
│  AI Normalizer FALLA                │
│  (Timeout, Rate Limit, Invalid JSON)│
└─────────┬───────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  Guardar como UNPROCESSED           │
│  - status_category = "UNPROCESSED"  │
│  - raw_data = input original        │
│  - validation_errors = [error_msg]  │
└─────────┬───────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  Worker Background (Cron)           │
│  - Retry UNPROCESSED events         │
│  - Exponential backoff              │
│  - Dead Letter Queue (3 intentos)   │
└─────────────────────────────────────┘
```

---

## 🧩 Diseño de Servicios

### 1. AI Normalizer Service

**Responsabilidad**: Transformar JSON heterogéneo → Pydantic estructurado usando LLM

**Decisiones de Diseño**:

- **Modelo**: GPT-4o-mini (velocidad + costo)
- **Temperatura**: 0.0 (determinismo)
- **Timeout**: 10s (SLA estricto)
- **Retry**: 2 intentos con backoff
- **Structured Output**: `with_structured_output(NormalizedPaymentSchema)`

**System Prompt** (Clave para calidad):

```
Eres un experto en normalización de datos de pagos.

INSTRUCCIONES CRÍTICAS:
1. NO inventes datos si no están presentes → usa None/null
2. Estandariza códigos de error según el catálogo:
   - "card declined", "tarjeta rechazada" → "BANK_DECLINE"
   - "insufficient funds", "fondos insuficientes" → "INSUFFICIENT_FUNDS"
   - etc.
3. Convierte SIEMPRE amounts a USD (usa rates si es necesario)
4. Formato de país: ISO 3166-1 alpha-2 (ej: "MX", "BR", "US")
5. Estados válidos: APPROVED, FAILED, ERROR, PENDING
6. Si latency_ms no está, calcula de timestamps si existen

PRIORIDAD: Precisión > Completitud
```

### 2. Ingestion Orchestrator

**Responsabilidad**: Coordinar todo el pipeline de ingesta

```python
class IngestionOrchestrator:
    """
    Orquesta el flujo completo de normalización y persistencia.

    Principios SOLID:
    - Single Responsibility: Solo coordina, no normaliza
    - Open/Closed: Extensible con nuevos normalizadores
    - Dependency Inversion: Depende de interfaces, no implementaciones
    """

    def __init__(
        self,
        ai_normalizer: INormalizer,
        rule_normalizer: INormalizer,
        repository: IPaymentRepository,
        processor: EventProcessor
    ):
        self.ai_normalizer = ai_normalizer
        self.rule_normalizer = rule_normalizer
        self.repository = repository
        self.processor = processor

    async def ingest(self, raw_event: dict) -> NormalizedPaymentEvent:
        """
        Pipeline:
        1. Seleccionar normalizador
        2. Normalizar
        3. Validar
        4. Persistir
        5. Manejar errores
        """
        ...
```

### 3. Rule-Based Normalizer (Performance)

Para proveedores conocidos (Stripe, Adyen), evitar llamadas a IA:

```python
class RuleBasedNormalizer(INormalizer):
    """
    Mapeos directos para formatos conocidos.

    Ventajas:
    - Latencia < 1ms
    - Sin costos de API
    - Determinístico 100%

    Usa factory pattern para cada proveedor.
    """

    def can_normalize(self, raw_event: dict) -> bool:
        """Verifica si el provider es soportado"""
        return raw_event.get("provider") in self.SUPPORTED_PROVIDERS

    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        """Mapeo directo basado en configuración"""
        ...
```

---

## 🎨 Principios de Diseño

### 1. SOLID Principles

#### Single Responsibility

- **AIService**: Solo interactúa con LangChain
- **Repository**: Solo operaciones de BD
- **Orchestrator**: Solo coordinación

#### Open/Closed

- Nuevos normalizadores se agregan sin modificar existentes
- Interface `INormalizer` permite extensión

#### Liskov Substitution

- Cualquier implementación de `INormalizer` es intercambiable

#### Interface Segregation

- Interfaces pequeñas: `INormalizer`, `IRepository`, `IEventProcessor`

#### Dependency Inversion

- Services dependen de abstracciones (Protocols), no clases concretas

### 2. Clean Code

```python
# ✅ BUENO: Nombres descriptivos
async def normalize_payment_event(raw_data: dict) -> NormalizedPaymentEvent:
    ...

# ❌ MALO: Nombres ambiguos
async def process(data: dict) -> dict:
    ...

# ✅ BUENO: Type hints completos
def calculate_latency(start: datetime, end: datetime) -> int:
    return (end - start).total_seconds() * 1000

# ❌ MALO: Sin tipos
def calc(s, e):
    return (e - s).total_seconds() * 1000
```

### 3. Error Handling Strategy

```python
# Jerarca de excepciones customizadas
class PaymentObservabilityException(Exception):
    """Base exception"""
    pass

class NormalizationException(PaymentObservabilityException):
    """Falló normalización"""
    pass

class AIServiceException(NormalizationException):
    """Específico de LLM"""
    pass

class ValidationException(PaymentObservabilityException):
    """Validación de negocio falló"""
    pass
```

### 4. Testing Strategy

```yaml
Unit Tests (70%):
  - Testar normalizers aisladamente
  - Mock de LangChain responses
  - Validaciones de negocio

Integration Tests (20%):
  - API endpoints con TestClient
  - Database con transactions rollback
  - AI service con VCR.py (grabar responses)

E2E Tests (10%):
  - Flujo completo con DB real
  - Simular eventos de proveedores reales
```

### 5. Performance Considerations

```python
# Índices de BD (definir en Alembic migration)
CREATE INDEX idx_payment_created_at ON normalized_payment_events(created_at DESC);
CREATE INDEX idx_payment_status ON normalized_payment_events(status_category);
CREATE INDEX idx_payment_provider ON normalized_payment_events(provider);
CREATE INDEX idx_payment_merchant ON normalized_payment_events(merchant_name);

# Composite index para analytics
CREATE INDEX idx_analytics ON normalized_payment_events(
    provider,
    status_category,
    created_at DESC
);
```

### 6. Observability

```python
# Structured Logging (JSON)
logger.info(
    "payment_normalized",
    extra={
        "event_id": str(event.id),
        "provider": event.provider,
        "status": event.status_category,
        "method": event.normalization_method,
        "latency_ms": processing_time,
        "confidence": event.confidence_score
    }
)

# Métricas (Prometheus - futuro)
- payment_events_total{provider, status}
- normalization_duration_seconds{method}
- ai_api_calls_total{model, status}
```

---

## 📝 Notas de Implementación

### Variables de Entorno Requeridas

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=payment_observability

# OpenAI
OPENAI_API_KEY=sk-...

# App
ENVIRONMENT=development
PROJECT_NAME="Payment Observability API"
SECRET_KEY=your-secret-key

# Optional
ANTHROPIC_API_KEY=sk-ant-...  # Fallback LLM
```

### Dependencias Adicionales

```toml
# Agregar a pyproject.toml
[project.dependencies]
# Ya existentes en tu proyecto ✓
# langchain>=1.1.3
# langchain-openai>=0.3.0
# sqlmodel>=0.0.27
# fastapi[standard]>=0.124.2

# Adicionales recomendadas
tenacity = ">=8.2.3"  # Retry logic robusto
httpx = ">=0.27.0"    # Async HTTP client
```

---

## 🚀 Próximos Pasos

Ver [ROADMAP.md](./ROADMAP.md) para el plan de implementación detallado.

---

**Última actualización**: 2025-12-13
**Autor**: Arquitectura para Hackathon Yuno
