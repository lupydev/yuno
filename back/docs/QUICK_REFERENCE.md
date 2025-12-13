# Quick Reference - Payment Observability System

## ⚡ Comandos Más Usados

```bash
# Desarrollo
uvicorn app.main:app --reload              # Iniciar servidor
pytest                                     # Ejecutar tests
ruff check --fix .                        # Lint + fix
alembic upgrade head                      # Aplicar migraciones

# Database
psql -U postgres -d payment_observability # Conectar a DB
alembic revision --autogenerate -m "msg" # Nueva migración

# Testing
pytest tests/unit/ -v                     # Solo unit tests
pytest --cov=app --cov-report=html       # Con coverage
```

---

## 📂 Estructura Rápida

```
app/
├── main.py                    # Entry point
├── api/v1/routers/
│   ├── events.py             # POST /events
│   └── analytics.py          # GET /metrics
├── services/
│   ├── ai_normalizer.py      # LangChain + OpenAI
│   ├── ingestion_orchestrator.py
│   └── analytics_service.py
├── domain/
│   ├── models/
│   │   ├── payment_event.py  # SQLModel table
│   │   └── enums.py          # PaymentStatus, etc
│   └── interfaces/
│       ├── normalizer.py     # INormalizer protocol
│       └── repository.py     # IRepository protocol
└── infraestructure/
    ├── core/
    │   ├── config.py         # Settings
    │   ├── db.py            # AsyncEngine
    │   └── deps.py          # DI
    ├── ai/
    │   ├── langchain_client.py
    │   └── prompts.py
    └── repositories/
        └── payment_repository.py
```

---

## 🎯 Checklist de Implementación

### Fase 1: Foundation (3h)

- [ ] Crear `domain/models/enums.py` (PaymentStatus, FailureReason)
- [ ] Crear `domain/models/payment_event.py` (NormalizedPaymentEvent)
- [ ] Actualizar `infraestructure/core/db.py` (AsyncEngine)
- [ ] Generar migración: `alembic revision --autogenerate`
- [ ] Aplicar migración: `alembic upgrade head`
- [ ] Crear interfaces: `INormalizer`, `IPaymentRepository`

### Fase 2: AI Integration (3h)

- [ ] Crear `infraestructure/ai/prompts.py` (system prompt)
- [ ] Crear `infraestructure/ai/langchain_client.py`
- [ ] Implementar `services/ai_normalizer.py`
- [ ] Agregar retry logic con `tenacity`
- [ ] Test con evento mock

### Fase 3: API Layer (2h)

- [ ] Implementar `infraestructure/repositories/payment_repository.py`
- [ ] Implementar `services/ingestion_orchestrator.py`
- [ ] Crear schemas en `api/v1/schemas/`
- [ ] Implementar `api/v1/routers/events.py`
- [ ] Configurar DI en `infraestructure/core/deps.py`
- [ ] Integrar routers en `main.py`

### Fase 4: Resilience (2h)

- [ ] Crear `domain/exceptions.py` (jerarquía de excepciones)
- [ ] Implementar exception handlers en `main.py`
- [ ] Agregar rate limiting (SlowAPI)
- [ ] Implementar `workers/retry_unprocessed_worker.py`

### Fase 5: Analytics (2h)

- [ ] Implementar `services/analytics_service.py`
- [ ] Crear `api/v1/routers/analytics.py`
- [ ] Mejorar health checks en `api/v1/routers/health.py`
- [ ] Configurar structured logging

---

## 🔧 Snippets de Código

### SQLModel Table

```python
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4
from datetime import datetime

class NormalizedPaymentEvent(SQLModel, table=True):
    __tablename__ = "normalized_payment_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_name: str = Field(index=True, max_length=255)
    status_category: str = Field(index=True)
    amount_usd: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### FastAPI Router con DI

```python
from fastapi import APIRouter, Depends
from typing import Annotated

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/")
async def ingest_event(
    request: EventIngestRequest,
    orchestrator: Annotated[IngestionOrchestrator, Depends(get_orchestrator)]
) -> EventIngestResponse:
    result = await orchestrator.ingest(request.raw_event)
    return EventIngestResponse.from_orm(result)
```

### LangChain Structured Output

```python
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class NormalizedPaymentSchema(BaseModel):
    merchant_name: str
    status_category: str
    amount_usd: float

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
structured_llm = llm.with_structured_output(NormalizedPaymentSchema)

result = await structured_llm.ainvoke(prompt)
```

### Dependency Injection

```python
from typing import Annotated
from fastapi import Depends

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

def get_repository(session: AsyncSessionDep) -> PaymentRepository:
    return PaymentRepository(session)

def get_orchestrator(
    repo: Annotated[PaymentRepository, Depends(get_repository)],
    normalizer: Annotated[AIBasedNormalizer, Depends(get_normalizer)]
) -> IngestionOrchestrator:
    return IngestionOrchestrator(repo, normalizer)
```

---

## 🧪 Testing Patterns

### Unit Test con Mock

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_ai_normalizer():
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = NormalizedPaymentSchema(...)

    normalizer = AIBasedNormalizer(mock_llm)
    result = await normalizer.normalize({"status": "succeeded"})

    assert result.status_category == "APPROVED"
```

### Integration Test

```python
@pytest.mark.asyncio
async def test_repository_save(test_db: AsyncSession):
    repo = PaymentRepository(test_db)
    event = NormalizedPaymentEvent(...)

    saved = await repo.save(event)
    assert saved.id is not None
```

---

## 🐛 Debugging

### Ver logs SQL

```python
# config.py
echo = True  # En development
```

### Debugger en código

```python
import pdb; pdb.set_trace()
# O en VS Code: F9 breakpoint, F5 debug
```

### Query PostgreSQL

```sql
-- Ver eventos recientes
SELECT id, merchant_name, status_category, created_at
FROM normalized_payment_events
ORDER BY created_at DESC
LIMIT 10;

-- Eventos UNPROCESSED
SELECT * FROM normalized_payment_events
WHERE status_category = 'UNPROCESSED';
```

---

## 🚨 Errores Comunes

| Error                         | Causa                          | Solución                                  |
| ----------------------------- | ------------------------------ | ----------------------------------------- |
| "database connection failed"  | PostgreSQL no está corriendo   | `docker-compose up -d postgres`           |
| "openai.error.RateLimitError" | Muchas llamadas a OpenAI       | Implementar exponential backoff           |
| "AsyncSession not found"      | No configuraste async engine   | Verificar `DATABASE_URI` tiene `_async`   |
| "event loop is closed"        | pytest-asyncio mal configurado | `asyncio_mode = "auto"` en pyproject.toml |

---

## 📊 Queries Útiles

### Analytics

```sql
-- Total por status
SELECT status_category, COUNT(*)
FROM normalized_payment_events
GROUP BY status_category;

-- Top providers
SELECT provider, COUNT(*), SUM(amount_usd)
FROM normalized_payment_events
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY provider
ORDER BY COUNT(*) DESC;

-- Success rate
SELECT
    provider,
    ROUND(
        COUNT(*) FILTER (WHERE status_category = 'APPROVED')::numeric /
        COUNT(*) * 100, 2
    ) as success_rate
FROM normalized_payment_events
GROUP BY provider;
```

---

## 🔐 Variables de Entorno Críticas

```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_DB=payment_observability
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# AI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# App
ENVIRONMENT=development
```

---

## 📝 Convenciones

### Commits

```bash
git commit -m "feat: add payment event model"
git commit -m "fix: handle OpenAI timeout"
git commit -m "test: add unit tests for normalizer"
git commit -m "docs: update architecture"
```

### Branches

```bash
git checkout -b feature/ai-normalizer
git checkout -b fix/database-connection
git checkout -b refactor/repository-pattern
```

---

## 🎯 Demo Script

```bash
# 1. Health check
curl http://localhost:8000/api/v1/health

# 2. Ingestar evento
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "raw_event": {
      "status": "succeeded",
      "amount": 5000,
      "currency": "usd",
      "merchant": "Acme Corp"
    },
    "provider": "stripe"
  }'

# 3. Ver en DB
psql -U postgres -d payment_observability -c \
  "SELECT * FROM normalized_payment_events ORDER BY created_at DESC LIMIT 1;"
```

---

## 🔗 Links Rápidos

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 📚 Documentos Relacionados

- [INDEX.md](./INDEX.md) - Índice completo
- [START_HERE.md](./START_HERE.md) - Guía de inicio
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Diseño técnico
- [ROADMAP.md](./ROADMAP.md) - Plan de implementación
- [BEST_PRACTICES.md](./BEST_PRACTICES.md) - Guía de código

---

**Quick Reference v1.0** - Última actualización: 2025-12-13
