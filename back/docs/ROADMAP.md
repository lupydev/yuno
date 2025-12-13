# Roadmap de Implementación - Payment Observability System

## 🎯 Objetivo

Implementar un sistema de observabilidad de pagos funcional en 5 fases, priorizando MVP para la hackathon.

---

## 📊 Visión de Fases

```
FASE 1 (Core Foundation) → FASE 2 (AI Integration) → FASE 3 (API) → FASE 4 (Data Lake) → FASE 5 (Analytics)
     ⏱ 2-3h                    ⏱ 2-3h                 ⏱ 1-2h         ⏱ 3-4h              ⏱ 1-2h
```

**Total estimado**: 9-14 horas de desarrollo

> **🌊 NUEVO**: Fase 4 incluye integración con Data Lake para captura automática de transacciones

---

## 🏗 FASE 1: Foundation & Domain Layer (CRÍTICO)

**Objetivo**: Establecer base sólida - modelos, configuración, DB setup

### ✅ Checklist

#### 1.1 Configuración y Dependencias

- [ ] **Revisar pyproject.toml**

  ```bash
  # Verificar que están instaladas:
  - sqlmodel>=0.0.27
  - langchain>=1.1.3
  - langchain-openai>=0.3.0
  - fastapi[standard]>=0.124.2
  - alembic>=1.17.2

  # Instalar adicionales si faltan:
  uv add tenacity httpx
  ```

- [ ] **Actualizar .env**

  ```bash
  # Agregar variables faltantes
  OPENAI_API_KEY=sk-...
  POSTGRES_DB=payment_observability  # O el nombre que prefieras
  ```

- [ ] **Verificar Settings en config.py**

  ```python
  # Agregar en app/infraestructure/core/config.py
  class Settings(BaseSettings):
      # ... existing fields ...

      # AI Configuration
      OPENAI_API_KEY: str
      OPENAI_MODEL: str = "gpt-4o-mini"
      AI_TIMEOUT_SECONDS: int = 10
      AI_MAX_RETRIES: int = 2

      # Feature Flags
      ENABLE_AI_NORMALIZATION: bool = True
      ENABLE_RULE_BASED_NORMALIZATION: bool = True
  ```

#### 1.2 Domain Models

- [ ] **Crear enums y catálogos**

  - Archivo: `app/domain/models/enums.py`
  - Contenido: `PaymentStatus`, `FailureReason`, `NormalizationMethod`
  - Testing: Unit tests para validación de valores

- [ ] **Crear modelo principal NormalizedPaymentEvent**

  - Archivo: `app/domain/models/payment_event.py`
  - SQLModel con todos los campos especificados
  - Incluir `Config` para JSONB
  - Validaciones con Pydantic validators

- [ ] **Crear schemas de Pydantic para normalización**
  - Archivo: `app/domain/models/schemas.py`
  - `NormalizedPaymentSchema` (sin campos de auditoría)
  - `RawEventInput` (validación de entrada)

#### 1.3 Database Setup

- [ ] **Mantener db.py con Engine sync (ya está configurado)**

  ```python
  # app/infraestructure/core/db.py (YA EXISTE - no modificar)
  from sqlmodel import Session, create_engine
  from typing import Annotated
  from fastapi import Depends

  engine = create_engine(
      str(settings.DATABASE_URI),
      echo=settings.ENVIRONMENT == "development",
      future=True,
  )

  def get_session():
      with Session(engine) as session:
          yield session

  SessionDep = Annotated[Session, Depends(get_session)]
  ```

  **⚡ HACKATHON**: Usamos sessions **sync** para simplificar desarrollo. FastAPI sigue siendo async en endpoints.

- [ ] **Crear migración Alembic inicial**

  ```bash
  # Generar migración
  alembic revision --autogenerate -m "create_normalized_payment_events_table"

  # Revisar migration file manualmente
  # Asegurar índices correctos

  # Aplicar
  alembic upgrade head
  ```

- [ ] **Verificar tabla en PostgreSQL**
  ```bash
  psql -U postgres -d payment_observability
  \d normalized_payment_events
  \di  # Ver índices
  ```

#### 1.4 Domain Interfaces (Protocols)

- [ ] **Crear interface para Normalizer**

  - Archivo: `app/domain/interfaces/normalizer.py`

  ```python
  from typing import Protocol
  from app.domain.models.schemas import NormalizedPaymentSchema

  class INormalizer(Protocol):
      async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
          """Normaliza evento crudo a schema estructurado"""
          ...

      def can_normalize(self, raw_event: dict) -> bool:
          """Verifica si puede normalizar este tipo de evento"""
          ...
  ```

- [ ] **Crear interface para Repository**

  - Archivo: `app/domain/interfaces/repository.py`

  ```python
  from typing import Protocol
  from uuid import UUID
  from app.domain.models.payment_event import NormalizedPaymentEvent

  class IPaymentRepository(Protocol):
      async def save(self, event: NormalizedPaymentEvent) -> NormalizedPaymentEvent:
          ...

      async def get_by_id(self, event_id: UUID) -> NormalizedPaymentEvent | None:
          ...

      async def get_unprocessed(self, limit: int = 100) -> list[NormalizedPaymentEvent]:
          """Para worker de retry"""
          ...
  ```

### 🧪 Testing Fase 1

```bash
# Unit tests
pytest tests/unit/models/test_payment_event.py -v
pytest tests/unit/models/test_enums.py -v

# Integration test de DB
pytest tests/integration/test_database.py -v
```

### 📝 Deliverables Fase 1

- ✅ Modelos de dominio completos con validaciones
- ✅ Database schema creada y migrada
- ✅ Interfaces definidas (contratos claros)
- ✅ Configuración centralizada
- ✅ Tests unitarios pasando

---

## 🤖 FASE 2: AI Integration Layer

**Objetivo**: Implementar normalización con LangChain + OpenAI

### ✅ Checklist

#### 2.1 Infrastructure - LangChain Client

- [ ] **Crear módulo de prompts**

  - Archivo: `app/infraestructure/ai/prompts.py`

  ```python
  PAYMENT_NORMALIZATION_SYSTEM_PROMPT = """
  Eres un experto en normalización de datos de pagos...
  [Incluir prompt completo de ARCHITECTURE.md]
  """

  PAYMENT_NORMALIZATION_USER_PROMPT = """
  Normaliza el siguiente evento de pago:
  {raw_event}
  """
  ```

- [ ] **Crear cliente de LangChain**

  - Archivo: `app/infraestructure/ai/langchain_client.py`

  ```python
  from langchain_openai import ChatOpenAI
  from langchain_core.prompts import ChatPromptTemplate

  class LangChainClient:
      def __init__(self, settings: Settings):
          self.llm = ChatOpenAI(
              model=settings.OPENAI_MODEL,
              temperature=0.0,
              timeout=settings.AI_TIMEOUT_SECONDS,
              max_retries=settings.AI_MAX_RETRIES,
              api_key=settings.OPENAI_API_KEY
          )

      def get_structured_llm(self, schema: Type[BaseModel]):
          return self.llm.with_structured_output(schema)
  ```

#### 2.2 Service - AI Normalizer

- [ ] **Implementar AIBasedNormalizer**

  - Archivo: `app/services/ai_normalizer.py`
  - Usar `with_structured_output(NormalizedPaymentSchema)`
  - Implementar retry logic con `tenacity`
  - Logging estructurado de cada llamada
  - Calcular `confidence_score` basado en response

- [ ] **Manejo de errores específicos**

  ```python
  from openai import RateLimitError, APITimeoutError

  try:
      result = await self.llm.ainvoke(...)
  except RateLimitError:
      # Guardar como UNPROCESSED con reason
      ...
  except APITimeoutError:
      # Retry con backoff
      ...
  except Exception as e:
      # Log y raise custom exception
      logger.error("ai_normalization_failed", exc_info=True)
      raise AIServiceException(f"Normalization failed: {e}")
  ```

#### 2.3 Service - Rule-Based Normalizer (Opcional pero recomendado)

- [ ] **Implementar RuleBasedNormalizer**

  - Archivo: `app/domain/normalizers/rule_based.py`
  - Factory pattern para cada provider
  - Mapeos directos (sin IA)
  - Ejemplo: Stripe, Adyen

- [ ] **Crear catálogo de reglas**
  ```python
  STRIPE_MAPPINGS = {
      "status": {
          "succeeded": PaymentStatus.APPROVED,
          "failed": PaymentStatus.FAILED,
          "pending": PaymentStatus.PENDING,
      },
      "failure_codes": {
          "card_declined": FailureReason.BANK_DECLINE,
          "insufficient_funds": FailureReason.INSUFFICIENT_FUNDS,
          # ...
      }
  }
  ```

#### 2.4 Service - Hybrid Normalizer (Orchestrator)

- [ ] **Combinar Rule + AI**
  - Archivo: `app/domain/normalizers/hybrid.py`
  - Strategy pattern:
    1. Intentar rule-based primero
    2. Si falla o no es confiable → AI
  - Logging de decisión tomada

### 🧪 Testing Fase 2

```bash
# Tests con mocks de OpenAI
pytest tests/unit/services/test_ai_normalizer.py -v

# Integration test con VCR.py (grabar responses)
pytest tests/integration/test_ai_normalization.py --record-mode=once

# Validar prompts con diferentes inputs
pytest tests/unit/ai/test_prompts.py -v
```

### 📝 Deliverables Fase 2

- ✅ AI normalizer funcional con LangChain
- ✅ Rule-based normalizer para providers conocidos
- ✅ Hybrid normalizer con estrategia inteligente
- ✅ Error handling robusto
- ✅ Tests con mocks y VCR

---

## 🌐 FASE 3: API Layer (FastAPI)

**Objetivo**: Exponer endpoints REST para ingesta y consulta

### ✅ Checklist

#### 3.1 Repository Implementation

- [ ] **Implementar PaymentRepository**

  - Archivo: `app/infraestructure/repositories/payment_repository.py`

  ```python
  from sqlmodel import select
  from sqlalchemy.ext.asyncio import AsyncSession

  class PaymentRepository:
      def __init__(self, session: AsyncSession):
          self.session = session

      async def save(self, event: NormalizedPaymentEvent) -> NormalizedPaymentEvent:
          self.session.add(event)
          await self.session.commit()
          await self.session.refresh(event)
          return event

      async def get_by_id(self, event_id: UUID) -> NormalizedPaymentEvent | None:
          result = await self.session.execute(
              select(NormalizedPaymentEvent).where(NormalizedPaymentEvent.id == event_id)
          )
          return result.scalar_one_or_none()
  ```

#### 3.2 Application Service - Ingestion Orchestrator

- [ ] **Crear IngestionOrchestrator**

  - Archivo: `app/services/ingestion_orchestrator.py`
  - Coordinar normalización + validación + persistencia
  - Manejo de errores → UNPROCESSED

  ```python
  class IngestionOrchestrator:
      async def ingest(self, raw_event: dict) -> NormalizedPaymentEvent:
          try:
              # 1. Seleccionar normalizador
              normalizer = self._select_normalizer(raw_event)

              # 2. Normalizar
              normalized_schema = await normalizer.normalize(raw_event)

              # 3. Convertir a modelo SQLModel
              event = NormalizedPaymentEvent(
                  **normalized_schema.model_dump(),
                  raw_data=raw_event,
                  normalized_at=datetime.utcnow(),
                  normalization_method=normalizer.method_name
              )

              # 4. Validar negocio
              self._validate_business_rules(event)

              # 5. Persistir
              saved_event = await self.repository.save(event)

              logger.info("event_ingested", extra={"event_id": str(saved_event.id)})
              return saved_event

          except Exception as e:
              # Guardar como UNPROCESSED
              return await self._save_as_unprocessed(raw_event, str(e))
  ```

#### 3.3 API Schemas (Request/Response DTOs)

- [ ] **Crear schemas de API**

  - Archivo: `app/api/v1/schemas/event_schemas.py`

  ```python
  from pydantic import BaseModel, Field

  class EventIngestRequest(BaseModel):
      """Request body para POST /events"""
      raw_event: dict = Field(..., description="Evento de pago en cualquier formato")
      provider: str | None = Field(None, description="Hint del proveedor (opcional)")

  class EventIngestResponse(BaseModel):
      """Response de ingesta exitosa"""
      id: UUID
      status: PaymentStatus
      normalization_method: str
      confidence_score: float | None
      message: str = "Event ingested successfully"

  class EventDetailResponse(BaseModel):
      """Response detallada de un evento"""
      id: UUID
      merchant_name: str
      provider: str
      country: str
      status_category: PaymentStatus
      failure_reason: str | None
      amount_usd: float
      created_at: datetime
      metadata: dict
      # Omitir raw_data en response por seguridad
  ```

#### 3.4 API Router - Events

- [ ] **Implementar router de eventos**

  - Archivo: `app/api/v1/routers/events.py`

  ```python
  from fastapi import APIRouter, HTTPException, status
  from app.infraestructure.core.db import AsyncSessionDep

  router = APIRouter(prefix="/events", tags=["events"])

  @router.post("/", response_model=EventIngestResponse, status_code=status.HTTP_201_CREATED)
  async def ingest_event(
      request: EventIngestRequest,
      session: AsyncSessionDep,
      # Orchestrator inyectado via dependency
  ) -> EventIngestResponse:
      """
      Ingesta un evento de pago y lo normaliza.

      - Acepta JSON en cualquier formato
      - Normaliza usando AI o reglas
      - Retorna evento guardado
      """
      orchestrator = IngestionOrchestrator(...)
      event = await orchestrator.ingest(request.raw_event)
      return EventIngestResponse.from_orm(event)

  @router.get("/{event_id}", response_model=EventDetailResponse)
  async def get_event(
      event_id: UUID,
      session: AsyncSessionDep,
  ) -> EventDetailResponse:
      """Obtiene detalles de un evento por ID"""
      repo = PaymentRepository(session)
      event = await repo.get_by_id(event_id)

      if not event:
          raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail=f"Event {event_id} not found"
          )

      return EventDetailResponse.from_orm(event)
  ```

#### 3.5 Dependency Injection

- [ ] **Crear factories en deps.py**

  - Archivo: `app/infraestructure/core/deps.py`

  ```python
  from typing import Annotated
  from fastapi import Depends

  def get_langchain_client() -> LangChainClient:
      return LangChainClient(settings)

  def get_ai_normalizer(
      client: Annotated[LangChainClient, Depends(get_langchain_client)]
  ) -> AIBasedNormalizer:
      return AIBasedNormalizer(client)

  def get_payment_repository(
      session: AsyncSessionDep
  ) -> PaymentRepository:
      return PaymentRepository(session)

  def get_ingestion_orchestrator(
      ai_norm: Annotated[AIBasedNormalizer, Depends(get_ai_normalizer)],
      repo: Annotated[PaymentRepository, Depends(get_payment_repository)],
  ) -> IngestionOrchestrator:
      return IngestionOrchestrator(
          ai_normalizer=ai_norm,
          repository=repo
      )
  ```

#### 3.6 Integrar routers en main.py

- [ ] **Actualizar main.py**

  ```python
  from app.api.v1.routers import events, health
  from fastapi.middleware.cors import CORSMiddleware

  app = FastAPI(...)

  # CORS
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.all_cors_origins,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # Routers
  app.include_router(events.router, prefix="/api/v1")
  app.include_router(health.router, prefix="/api/v1")
  ```

### 🧪 Testing Fase 3

```bash
# Integration tests de API
pytest tests/integration/test_events_api.py -v

# E2E test con DB real
pytest tests/e2e/test_ingestion_flow.py -v

# Manual testing
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"raw_event": {...}, "provider": "stripe"}'
```

### 📝 Deliverables Fase 3

- ✅ API REST funcional con endpoints documentados
- ✅ Dependency Injection configurada
- ✅ Error handling y validación
- ✅ Testing básico de endpoints

---

## 🌊 FASE 4: Data Lake Integration (NUEVO)

**Objetivo**: Capturar automáticamente transacciones desde una DB de data lake con datos heterogéneos

**✅ Estado**: El data lake ya está **desplegado y cargado con datos reales**

> **📚 Documentación completa**: Ver [DATA_LAKE_INTEGRATION.md](./DATA_LAKE_INTEGRATION.md)

### 📊 Estructura de Datos

El data lake contiene registros con esta estructura:

```json
{
  "id": "UUID",
  "data": {
    /* HETEROGÉNEO - JSON, XML string, CSV, etc. */
  },
  "merchant": { "id": "UUID", "name": "...", "country": "..." },
  "transactional_id": "UUID"
}
```

**El campo `data` puede contener cualquier cosa**:

- JSON con diferentes estructuras (`amt`, `p_id` vs `status`, `provider`)
- XML como string en campo `content`
- CSV como string
- Cualquier formato semi-estructurado

### ✅ Checklist

#### 4.1 Configurar Conexión al Data Lake

- [ ] **Obtener credenciales del data lake** (ya desplegado)

  ```bash
  # Agregar a .env
  DATALAKE_DATABASE_URL=postgresql://readonly:pass@datalake.yuno.com:5432/payments_lake
  POLL_INTERVAL_SECONDS=43200  # 12 horas
  ```

- [ ] **Verificar estructura de la tabla existente**

  La tabla `raw_transactions` tiene:

  - `id` (UUID): ID del registro
  - `data` (JSONB): Datos heterogéneos
  - `merchant` (JSONB): Info del merchant
  - `transactional_id` (UUID): ID de transacción
  - `processed` (boolean): Flag para evitar duplicados

#### 4.2 Cliente PostgreSQL para Data Lake

- [ ] **Implementar DataLakeClient**

  - Archivo: `app/infraestructure/datalake/client.py`

  ```python
  from sqlalchemy import create_engine, text
  from sqlalchemy.orm import Session
  from typing import List, Dict, Any

  class DataLakeClient:
      """Cliente para leer del data lake (otra DB PostgreSQL)"""

      def __init__(self, connection_url: str):
          self.engine = create_engine(connection_url, pool_pre_ping=True)

      def get_unprocessed_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
          """Obtiene transacciones no procesadas"""
          query = text("""
              SELECT id, data, merchant, transactional_id, created_at
              FROM raw_transactions
              WHERE processed = false
              ORDER BY created_at ASC
              LIMIT :limit
          """)

          with Session(self.engine) as session:
              result = session.execute(query, {"limit": limit})
              return [dict(row) for row in result]

      def mark_as_processed(self, transaction_ids: List[str]):
          """Marca transacciones como procesadas"""
          query = text("""
              UPDATE raw_transactions
              SET processed = true, processed_at = NOW()
              WHERE id = ANY(:ids)
          """)

          with Session(self.engine) as session:
              session.execute(query, {"ids": transaction_ids})
              session.commit()
  ```

- [ ] **NO requiere dependencias adicionales** (usa SQLAlchemy existente)

#### 4.3 Worker de Polling

- [ ] **Crear DataLakePoller worker**

  - Archivo: `app/workers/data_lake_poller.py`

  ```python
  class DataLakePoller:
      """Worker que revisa el data lake periódicamente"""

      def __init__(
          self,
          datalake_connection: str,
          poll_interval: int = 43200,  # 12 horas
          run_once: bool = False
      ):
          self.datalake_client = DataLakeClient(datalake_connection)
          self.ingestion_service = IngestionService()

      def run(self):
          """Loop principal"""
          if self.run_once:
              self.poll_and_process()
              return

          while True:
              self.poll_and_process()
              time.sleep(self.poll_interval)

      def poll_and_process(self):
          """Polling de transacciones"""
          # 1. Obtener no procesadas
          transactions = self.datalake_client.get_unprocessed_transactions(limit=100)

          # 2. Procesar cada una
          processed_ids = []
          for tx in transactions:
              try:
                  self._process_transaction(tx)
                  processed_ids.append(tx['id'])
              except Exception as e:
                  logger.error(f"Error: {e}")

          # 3. Marcar como procesadas
          if processed_ids:
              self.datalake_client.mark_as_processed(processed_ids)

      def _process_transaction(self, transaction: Dict[str, Any]):
          """Procesa una transacción"""
          # Detectar provider desde el campo data heterogéneo
          provider = self._detect_provider(transaction['data'])

          # Enriquecer con metadata
          enriched_data = {
              'id': transaction['id'],
              'transactional_id': transaction['transactional_id'],
              'merchant': transaction['merchant'],
              'raw_data': transaction['data']
          }

          # Normalizar con IngestionService
          with Session(engine) as session:
              self.ingestion_service.process_transaction(
                  raw_event=enriched_data,
                  provider=provider,
                  session=session
              )

      def _detect_provider(self, data: Dict[str, Any]) -> str:
          """Detecta provider desde datos heterogéneos"""
          if 'provider' in data:
              return data['provider'].lower()
          if 'p_id' in data:
              return data['p_id'].lower()
          return 'unknown'
  ```

- [ ] **Script de ejecución con argparse**

  ```bash
  # Ejecución única (para cron)
  python -m app.workers.data_lake_poller --once

  # Loop continuo (para testing)
  python -m app.workers.data_lake_poller
  ```

#### 4.4 Configuración

- [ ] **Variables de entorno**

  ```bash
  # .env
  DATALAKE_DATABASE_URL=postgresql://readonly:pass@datalake.yuno.com:5432/payments_lake
  POLL_INTERVAL_SECONDS=43200  # 12 horas (2 veces al día)
  ```

- [ ] **Cron para ejecución 2x al día**

  ```bash
  # crontab -e
  0 0,12 * * * cd /path/to/yuno/back && .venv/bin/python -m app.workers.data_lake_poller --once >> /var/log/yuno-poller.log 2>&1
  ```

#### 4.5 Testing

- [ ] **Insertar datos de prueba en data lake**

  ```bash
  # En DB del data lake
  psql $DATALAKE_DATABASE_URL -f scripts/create_raw_transactions.sql
  ```

- [ ] **Ejecutar worker manualmente**

  ```bash
  # Testing local
  python -m app.workers.data_lake_poller --once

  # Ver logs
  tail -f logs/data_lake_poller.log
  ```

### 🧪 Testing Fase 4

**✅ Data lake ya desplegado y con datos**

```bash
# 1. Verificar datos en data lake
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*) FROM raw_transactions WHERE processed = false;"

# 2. Ver muestra de los datos
psql $DATALAKE_DATABASE_URL -c "SELECT id, merchant->>'name' as merchant, processed FROM raw_transactions LIMIT 5;"

# 3. Ejecutar worker una vez (testing)
python -m app.workers.data_lake_poller --once

# 4. Verificar que se procesaron
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*) FROM raw_transactions WHERE processed = true;"

# 5. Ver logs
tail -f logs/data_lake_poller.log
```

### 📝 Deliverables Fase 4

- ✅ Tabla `raw_transactions` en data lake DB (ya desplegada)
- ✅ Cliente PostgreSQL `DataLakeClient`
- ✅ Worker `DataLakePoller` con detección de provider
- ✅ Integración con servicio de ingesta existente
- ✅ Soporte para datos heterogéneos (JSON, XML, CSV)
- ✅ Documentación completa en DATA_LAKE_INTEGRATION.md
- ✅ Tests con mock S3
- ✅ Documentación completa en DATA_LAKE_INTEGRATION.md

### ⚡ Quick Start - Data Lake Integration

**✅ Data lake ya desplegado y con datos**

```bash
# 1. Configurar .env con credenciales del data lake
echo "DATALAKE_DATABASE_URL=postgresql://readonly:pass@datalake.yuno.com:5432/payments_lake" >> .env
echo "POLL_INTERVAL_SECONDS=43200" >> .env

# 2. Verificar conexión y datos disponibles
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*) FROM raw_transactions WHERE processed = false;"

# 3. Ejecutar worker una vez (testing)
python -m app.workers.data_lake_poller --once

# 4. Setup cron para 2x al día (producción)
(crontab -l 2>/dev/null; echo "0 0,12 * * * cd $(pwd) && .venv/bin/python -m app.workers.data_lake_poller --once >> /var/log/yuno-poller.log 2>&1") | crontab -

# 5. Monitorear
tail -f logs/data_lake_poller.log
```

### 🔄 Opciones de Arquitectura

El documento [DATA_LAKE_INTEGRATION.md](./DATA_LAKE_INTEGRATION.md) incluye 3 opciones:

1. **Polling Worker** ⭐ (Recomendada para hackathon) - Simple, funcional
2. **S3 Events + SQS** - Event-driven, producción-ready
3. **S3 + Kafka** - Para integración con pipeline existente

---

## 📊 FASE 5: Analytics & Monitoring

- ✅ Repository implementado
- ✅ Orchestrator coordinando todo el flujo
- ✅ Tests de integración pasando

---

## 🛡 FASE 4: Resilience & Error Handling

**Objetivo**: Sistema robusto que no pierde datos

### ✅ Checklist

#### 4.1 Custom Exceptions

- [ ] **Crear jerarquía de excepciones**
  - Archivo: `app/domain/exceptions.py`
  - Ver ARCHITECTURE.md para jerarquía completa
  - Incluir `error_code` para tracking

#### 4.2 Global Exception Handlers

- [ ] **Implementar handlers en main.py**

  ```python
  from fastapi import Request
  from fastapi.responses import JSONResponse

  @app.exception_handler(AIServiceException)
  async def ai_service_exception_handler(request: Request, exc: AIServiceException):
      logger.error("ai_service_error", exc_info=True)
      return JSONResponse(
          status_code=503,
          content={
              "error": "AI service unavailable",
              "detail": str(exc),
              "retry_after": 60
          }
      )
  ```

#### 4.3 Background Worker - Retry Unprocessed

- [ ] **Crear worker de retry**

  - Archivo: `app/workers/retry_unprocessed_worker.py`

  ```python
  import asyncio
  from datetime import datetime, timedelta

  async def retry_unprocessed_events():
      """
      Cron job que reintenta eventos UNPROCESSED.

      Lógica:
      1. Query eventos UNPROCESSED de últimas 24h
      2. Retry con exponential backoff
      3. Después de 3 intentos → Dead Letter Queue
      """
      while True:
          try:
              async with AsyncSessionLocal() as session:
                  repo = PaymentRepository(session)
                  events = await repo.get_unprocessed(limit=100)

                  for event in events:
                      await retry_single_event(event, repo)

              await asyncio.sleep(300)  # Cada 5 min

          except Exception as e:
              logger.error("worker_error", exc_info=True)
              await asyncio.sleep(60)
  ```

#### 4.4 Rate Limiting

- [ ] **Agregar SlowAPI (ya está en deps)**

  - Configurar en main.py

  ```python
  from slowapi import Limiter, _rate_limit_exceeded_handler
  from slowapi.util import get_remote_address
  from slowapi.errors import RateLimitExceeded

  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

  @router.post("/events")
  @limiter.limit("10/minute")  # 10 requests por minuto
  async def ingest_event(...):
      ...
  ```

#### 4.5 Request Validation

- [ ] **Validaciones exhaustivas en schemas**

  ```python
  from pydantic import validator, Field

  class EventIngestRequest(BaseModel):
      raw_event: dict = Field(..., min_length=1)

      @validator("raw_event")
      def validate_not_empty(cls, v):
          if not v:
              raise ValueError("raw_event cannot be empty")
          return v
  ```

### 🧪 Testing Fase 4

```bash
# Test de error handling
pytest tests/unit/test_exceptions.py -v

# Test de worker
pytest tests/integration/test_retry_worker.py -v

# Load testing (opcional)
locust -f tests/load/locustfile.py
```

### 📝 Deliverables Fase 4

- ✅ Sistema que nunca pierde eventos
- ✅ Retry automático de fallos
- ✅ Rate limiting configurado
- ✅ Exception handling robusto
- ✅ Worker background funcionando

---

## 📊 FASE 5: Analytics & Monitoring

**Objetivo**: Endpoints para insights y observabilidad

### ✅ Checklist

#### 5.1 Analytics Service

- [ ] **Crear servicio de analítica**

  - Archivo: `app/services/analytics_service.py`

  ```python
  from sqlalchemy import func, select

  class AnalyticsService:
      async def get_metrics_summary(
          self,
          start_date: datetime,
          end_date: datetime
      ) -> dict:
          """
          Retorna métricas agregadas:
          - Total events por status
          - Success rate por provider
          - Avg latency
          - Top failure reasons
          """
          ...

      async def get_provider_stats(self, provider: str) -> dict:
          """Stats específicos de un provider"""
          ...
  ```

#### 5.2 Analytics Router

- [ ] **Implementar endpoints de analytics**

  - Archivo: `app/api/v1/routers/analytics.py`

  ```python
  @router.get("/metrics/summary")
  async def get_metrics_summary(
      start_date: datetime = Query(...),
      end_date: datetime = Query(...),
      service: AnalyticsService = Depends(get_analytics_service)
  ) -> dict:
      """Dashboard de métricas generales"""
      return await service.get_metrics_summary(start_date, end_date)

  @router.get("/metrics/providers/{provider}")
  async def get_provider_metrics(
      provider: str,
      service: AnalyticsService = Depends(...)
  ) -> dict:
      """Métricas por provider"""
      return await service.get_provider_stats(provider)
  ```

#### 5.3 Structured Logging Enhancements

- [ ] **Mejorar logging en logging.py**

  ```python
  import structlog

  structlog.configure(
      processors=[
          structlog.stdlib.filter_by_level,
          structlog.stdlib.add_logger_name,
          structlog.stdlib.add_log_level,
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.JSONRenderer()
      ],
      wrapper_class=structlog.stdlib.BoundLogger,
      logger_factory=structlog.stdlib.LoggerFactory(),
  )
  ```

#### 5.4 Health Checks Detallados

- [ ] **Expandir health endpoint**

  - Archivo: `app/api/v1/routers/health.py`

  ```python
  @router.get("/health")
  async def health_check(session: AsyncSessionDep) -> dict:
      """
      Health check con dependencias:
      - DB connection
      - OpenAI API
      - Disk space (opcional)
      """
      health_status = {
          "status": "healthy",
          "timestamp": datetime.utcnow(),
          "checks": {}
      }

      # DB check
      try:
          await session.execute(select(1))
          health_status["checks"]["database"] = "ok"
      except Exception as e:
          health_status["status"] = "unhealthy"
          health_status["checks"]["database"] = f"error: {e}"

      # OpenAI check (lightweight)
      try:
          # Ping endpoint simple
          health_status["checks"]["openai"] = "ok"
      except:
          health_status["checks"]["openai"] = "degraded"

      return health_status
  ```

### 🧪 Testing Fase 5

```bash
# Analytics tests
pytest tests/integration/test_analytics.py -v

# Health check tests
pytest tests/e2e/test_health.py -v
```

### 📝 Deliverables Fase 5

- ✅ Dashboard de métricas funcional
- ✅ Logging estructurado en JSON
- ✅ Health checks completos
- ✅ Analytics queries optimizadas

---

## 🎬 Post-Hackathon Enhancements (Opcional)

### Nice-to-Have Features

1. **Authentication & Authorization**

   - JWT tokens
   - API keys para proveedores

2. **Kafka Integration**

   - Stream eventos para procesamiento async
   - Event-driven architecture

3. **Caching Layer**

   - Redis para queries frecuentes
   - Cache de reglas de normalización

4. **Frontend Dashboard**

   - Next.js + TailwindCSS
   - Gráficas con Recharts
   - Real-time updates con WebSockets

5. **Advanced AI Features**

   - Detección de anomalías
   - Predicción de fallos
   - Clustering de merchants

6. **Compliance**
   - Anonimización de datos sensibles
   - Auditoría completa
   - GDPR compliance

---

## 📋 Orden de Implementación Recomendado

### Día 1 (Setup + Core)

1. ✅ Fase 1.1 - Configuración (30 min)
2. ✅ Fase 1.2 - Models & Enums (1h)
3. ✅ Fase 1.3 - Database Setup (1h)
4. ✅ Fase 1.4 - Interfaces (30 min)
5. ✅ Fase 2.1 - AI Infrastructure (1h)
6. ✅ Fase 2.2 - AI Normalizer (1.5h)

### Día 2 (API + Resilience)

7. ✅ Fase 3.1 - Repository (45 min)
8. ✅ Fase 3.2 - Orchestrator (1h)
9. ✅ Fase 3.3-3.6 - API Layer (2h)
10. ✅ Fase 4 - Error Handling (1.5h)

### Día 3 (Polish + Analytics)

11. ✅ Fase 5 - Analytics (1.5h)
12. ✅ Testing E2E (1h)
13. ✅ Documentation (30 min)
14. ✅ Demo Preparation (1h)

---

## 🔍 Validation Checklist (Pre-Demo)

### Funcional

- [ ] Ingesta evento con formato Stripe → APPROVED
- [ ] Ingesta evento desconocido → Normalizado por IA
- [ ] Evento inválido → UNPROCESSED (no crash)
- [ ] Query evento por ID → Retorna detalles
- [ ] Analytics → Retorna métricas correctas

### Técnico

- [ ] Tests unitarios pasando (>80% coverage)
- [ ] Tests integración pasando
- [ ] Migraciones aplicadas sin errores
- [ ] Logs estructurados en JSON
- [ ] No hay secrets hardcodeados

### Performance

- [ ] Ingesta < 2s (con AI)
- [ ] Query por ID < 100ms
- [ ] Analytics < 500ms
- [ ] Rate limiting funcionando

### Documentación

- [ ] README.md actualizado
- [ ] API docs (OpenAPI) generadas
- [ ] ARCHITECTURE.md completo
- [ ] .env.example actualizado

---

## 🚀 Quick Start Guide

```bash
# 1. Setup environment
uv sync
cp .env.example .env
# Editar .env con credenciales

# 2. Database
docker-compose up -d postgres  # Si usas Docker
alembic upgrade head

# 3. Run server
uvicorn app.main:app --reload --port 8000

# 4. Test
curl http://localhost:8000/api/v1/health

# 5. Ingest test event
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
```

---

## 📚 Referencias Útiles

- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [SQLModel Docs](https://sqlmodel.tiangolo.com/)
- [LangChain Structured Output](https://python.langchain.com/docs/how_to/structured_output/)
- [Clean Architecture in Python](https://github.com/cosmic-python/book)

---

**Última actualización**: 2025-12-13
**Próxima revisión**: Después de cada fase completada
