# Sistema de Observabilidad de Pagos

## 🎯 Descripción

Sistema backend de observabilidad para transacciones de pago diseñado para la Hackathon Yuno. Ingesta, normaliza y almacena eventos de pago de múltiples proveedores usando un enfoque híbrido de **Reglas + IA**.

### Características Principales

- ✅ **Normalización Inteligente**: LangChain + GPT-4o-mini para datos heterogéneos
- ✅ **Ingesta Resiliente**: No pierde eventos, maneja errores elegantemente
- ✅ **API REST**: FastAPI con documentación automática
- ✅ **Analítica**: Métricas y agregaciones en tiempo real
- ✅ **Async First**: PostgreSQL async + SQLModel para performance

---

## 🛠 Stack Técnico

```yaml
Framework: FastAPI 0.124.2+
ORM: SQLModel (Pydantic v2 + SQLAlchemy)
Database: PostgreSQL con JSONB
AI: LangChain + OpenAI (GPT-4o-mini)
Migrations: Alembic
Testing: Pytest + Pytest-Asyncio
Code Quality: Ruff
```

---

## 📋 Prerequisitos

- Python 3.13+
- PostgreSQL 15+
- OpenAI API Key
- uv (package manager) o pip

---

## 🚀 Quick Start

### 1. Clonar y Setup

```bash
# Clonar repositorio
cd back/

# Crear virtual environment (si usas pip)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# o
.venv\Scripts\activate  # Windows

# Instalar dependencias
uv sync
# o
pip install -e .
```

### 2. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Variables requeridas**:

```env
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
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Configurar Base de Datos

```bash
# Opción A: Docker (recomendado)
docker-compose up -d postgres

# Opción B: PostgreSQL local
createdb payment_observability

# Aplicar migraciones
alembic upgrade head
```

### 4. Ejecutar Servidor

```bash
# Modo desarrollo
uvicorn app.main:app --reload --port 8000

# Servidor corriendo en: http://localhost:8000
# Docs interactivas: http://localhost:8000/docs
```

### 5. Probar API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Ingestar evento de prueba
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "raw_event": {
      "status": "succeeded",
      "amount": 5000,
      "currency": "usd",
      "merchant": "Acme Corp",
      "provider": "stripe"
    }
  }'
```

---

## 📚 Documentación

### Documentos Arquitectónicos

- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) - Diseño detallado del sistema, principios SOLID, patrones
- [**ROADMAP.md**](docs/ROADMAP.md) - Plan de implementación en 5 fases
- [**API.md**](docs/API.md) - Especificación completa de endpoints (por crear)

### Documentación Interactiva

Una vez que el servidor esté corriendo:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 🏗 Arquitectura

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │
│   POST /events  |  GET /analytics   │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│     Application Services            │
│  - IngestionOrchestrator            │
│  - AIBasedNormalizer                │
│  - AnalyticsService                 │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         Domain Layer                │
│  - NormalizedPaymentEvent (Model)   │
│  - Normalizers (Business Logic)     │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│      Infrastructure Layer           │
│  - PostgreSQL (AsyncSession)        │
│  - LangChain Client                 │
│  - Repositories                     │
└─────────────────────────────────────┘
```

Ver [ARCHITECTURE.md](docs/ARCHITECTURE.md) para detalles completos.

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Solo unit tests
pytest tests/unit/ -v

# Solo integration tests
pytest tests/integration/ -v

# Con logs detallados
pytest -v -s
```

### Estructura de Tests

```
tests/
├── unit/          # Tests aislados (mocks)
├── integration/   # Tests con DB/API
└── e2e/          # Tests end-to-end
```

---

## 📊 Estructura del Proyecto

```
back/
├── app/
│   ├── main.py                    # Entry point
│   ├── api/                       # Routers y schemas
│   │   └── v1/
│   │       └── routers/
│   │           ├── events.py      # POST /events
│   │           ├── analytics.py   # Métricas
│   │           └── health.py
│   ├── services/                  # Lógica de aplicación
│   │   ├── ingestion_orchestrator.py
│   │   ├── ai_normalizer.py
│   │   └── analytics_service.py
│   ├── domain/                    # Modelos y reglas de negocio
│   │   ├── models/
│   │   │   ├── payment_event.py
│   │   │   └── enums.py
│   │   ├── interfaces/
│   │   └── normalizers/
│   └── infraestructure/           # Capa de infraestructura
│       ├── core/
│       │   ├── config.py
│       │   ├── db.py
│       │   └── deps.py
│       ├── ai/
│       │   ├── langchain_client.py
│       │   └── prompts.py
│       └── repositories/
├── alembic/                       # Migraciones de DB
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

---

## 🔧 Desarrollo

### Linting y Formateo

```bash
# Ejecutar Ruff (linter + formatter)
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .
```

### Crear Nueva Migración

```bash
# Auto-generar desde cambios en modelos
alembic revision --autogenerate -m "descripcion_del_cambio"

# Revisar archivo generado en alembic/versions/

# Aplicar migración
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Variables de Entorno para Dev

```env
# Habilitar logs de queries SQL
ENVIRONMENT=development

# Deshabilitar IA para testing local
ENABLE_AI_NORMALIZATION=false

# Usar mock de OpenAI
OPENAI_API_KEY=sk-test-mock
```

---

## 📈 Roadmap de Implementación

### ✅ Fase 1: Foundation (Completada)

- [x] Modelos de dominio
- [x] Setup de DB
- [x] Configuración base

### 🚧 Fase 2: AI Integration (En Progreso)

- [ ] LangChain client
- [ ] AI normalizer service
- [ ] Rule-based normalizer

### 📋 Fase 3: API Layer (Pendiente)

- [ ] Routers de eventos
- [ ] Analytics endpoints
- [ ] Dependency injection

### 🛡 Fase 4: Resilience (Pendiente)

- [ ] Error handling
- [ ] Retry worker
- [ ] Rate limiting

### 📊 Fase 5: Analytics (Pendiente)

- [ ] Métricas dashboard
- [ ] Structured logging
- [ ] Health checks

Ver [ROADMAP.md](docs/ROADMAP.md) para detalles completos.

---

## 🤝 Contribución (Post-Hackathon)

1. Fork el repositorio
2. Crear branch feature: `git checkout -b feature/nueva-feature`
3. Commit cambios: `git commit -am 'Add nueva feature'`
4. Push al branch: `git push origin feature/nueva-feature`
5. Crear Pull Request

### Convenciones de Código

- **Type hints** obligatorios
- **Docstrings** para funciones públicas
- **Tests** para nuevas features
- **Commits** descriptivos (Conventional Commits)

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles

---

## 👥 Equipo

Desarrollado para la Hackathon Yuno 2025

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Docs**: [docs/](docs/)
- **Email**: your-email@example.com

---

## 🎉 Demo

### Caso de Uso: Normalización Stripe

```bash
# Evento de Stripe (formato conocido)
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "raw_event": {
      "id": "ch_1234567890",
      "object": "charge",
      "amount": 2000,
      "currency": "usd",
      "status": "succeeded",
      "merchant": "Test Merchant",
      "created": 1638360000
    },
    "provider": "stripe"
  }'

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "APPROVED",
  "normalization_method": "RULE_BASED",
  "confidence_score": 1.0,
  "message": "Event ingested successfully"
}
```

### Caso de Uso: Normalización con IA

```bash
# Evento desconocido (formato custom)
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "raw_event": {
      "transaccion_id": "ABC123",
      "comercio": "Tienda XYZ",
      "monto": "50.00 USD",
      "estado": "aprobada",
      "pais": "México",
      "proveedor": "gateway_custom",
      "fecha": "2025-12-13T10:30:00Z"
    }
  }'

# Response (normalizado por IA):
{
  "id": "660f9511-f30c-52e5-b827-557766551111",
  "status": "APPROVED",
  "normalization_method": "AI",
  "confidence_score": 0.95,
  "message": "Event ingested successfully"
}
```

---

**¡Listo para la Hackathon! 🚀**
