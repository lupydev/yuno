# Payment Observability System - Guía de Implementación Rápida

## 🎯 Para comenzar AHORA

Esta es tu guía ejecutiva para implementar el sistema. Lee primero, implementa después.

---

## 📚 Documentación Disponible

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** ⭐ **LEER PRIMERO**

   - Diseño completo del sistema
   - Flujos de datos
   - Principios SOLID aplicados
   - Modelos de dominio detallados

2. **[ROADMAP.md](./ROADMAP.md)** ⭐ **USAR COMO CHECKLIST**

   - Plan de implementación en 5 fases
   - Orden de ejecución recomendado
   - Estimaciones de tiempo
   - Testing por fase

3. **[BEST_PRACTICES.md](./BEST_PRACTICES.md)** ⭐ **CONSULTAR DURANTE DESARROLLO**

   - Ejemplos de código correcto vs incorrecto
   - Patrones de FastAPI, SQLModel, LangChain
   - Security y performance tips

4. **[PROJECT_README.md](./PROJECT_README.md)**
   - Guía de usuario final
   - Quick start
   - Casos de uso de demo

---

## 🚀 Plan de Acción (3 Días)

### DÍA 1: Foundation (4-5 horas)

**Objetivo**: Base sólida funcionando

#### Mañana (2-3h)

1. ✅ **Setup Inicial** (30 min)

   - Leer `ARCHITECTURE.md` secciones 1-4
   - Revisar estructura de carpetas
   - Configurar `.env` con credenciales

2. ✅ **Fase 1: Domain Models** (1.5h)

   - Crear `app/domain/models/enums.py`
   - Crear `app/domain/models/payment_event.py`
   - Crear `app/domain/models/schemas.py`
   - **Checkpoint**: Tests unitarios de modelos pasan

3. ✅ **Fase 1: Database** (1h)
   - Actualizar `db.py` con AsyncEngine
   - Generar migración Alembic
   - Aplicar migración
   - **Checkpoint**: `\d normalized_payment_events` muestra tabla

#### Tarde (2h)

4. ✅ **Fase 1: Interfaces** (30 min)

   - Crear `INormalizer` protocol
   - Crear `IPaymentRepository` protocol
   - **Checkpoint**: Interfaces importan sin errores

5. ✅ **Fase 2: AI Infrastructure** (1.5h)
   - Crear `app/infraestructure/ai/prompts.py`
   - Crear `app/infraestructure/ai/langchain_client.py`
   - Testear conexión con OpenAI
   - **Checkpoint**: `ChatOpenAI` se instancia correctamente

**Entregable Día 1**:

- ✅ Modelos de dominio completos
- ✅ Database schema creada
- ✅ Cliente de LangChain configurado

---

### DÍA 2: Services + API (5-6 horas)

**Objetivo**: API funcional que normaliza y guarda

#### Mañana (3h)

6. ✅ **Fase 2: AI Normalizer** (2h)

   - Implementar `AIBasedNormalizer` en `services/ai_normalizer.py`
   - Agregar retry logic con `tenacity`
   - Testear con eventos mock
   - **Checkpoint**: Normalización IA funciona con un ejemplo

7. ✅ **Fase 3: Repository** (1h)
   - Implementar `PaymentRepository` en `infraestructure/repositories/`
   - Métodos: `save()`, `get_by_id()`, `get_unprocessed()`
   - **Checkpoint**: Integration test guarda evento en DB

#### Tarde (2-3h)

8. ✅ **Fase 3: Orchestrator** (1.5h)

   - Implementar `IngestionOrchestrator` en `services/`
   - Coordinar normalización + validación + persistencia
   - Manejo de errores → UNPROCESSED
   - **Checkpoint**: Pipeline completo funciona end-to-end

9. ✅ **Fase 3: API Layer** (1.5h)
   - Crear schemas en `api/v1/schemas/`
   - Implementar router en `api/v1/routers/events.py`
   - Configurar dependency injection en `deps.py`
   - Integrar en `main.py`
   - **Checkpoint**: `POST /api/v1/events` responde 201

**Entregable Día 2**:

- ✅ API REST funcional
- ✅ Normalización con IA operativa
- ✅ Eventos se guardan en BD

---

### DÍA 3: Resilience + Analytics + Polish (4-5 horas)

**Objetivo**: Sistema robusto y demo-ready

#### Mañana (2-3h)

10. ✅ **Fase 4: Error Handling** (1.5h)

    - Crear jerarquía de excepciones en `domain/exceptions.py`
    - Implementar exception handlers en `main.py`
    - Agregar rate limiting con SlowAPI
    - **Checkpoint**: API retorna errores estructurados

11. ✅ **Fase 4: Retry Worker** (1h)
    - Implementar `workers/retry_unprocessed_worker.py`
    - Lógica de exponential backoff
    - **Checkpoint**: Worker procesa eventos UNPROCESSED

#### Tarde (2h)

12. ✅ **Fase 5: Analytics** (1.5h)

    - Implementar `AnalyticsService` en `services/`
    - Crear router `api/v1/routers/analytics.py`
    - Queries agregadas: métricas por provider, status, etc.
    - **Checkpoint**: `GET /api/v1/analytics/metrics` retorna datos

13. ✅ **Testing + Documentation** (30 min)
    - Ejecutar test suite completo
    - Actualizar README principal
    - Preparar casos de demo
    - **Checkpoint**: `pytest` pasa con >80% coverage

**Entregable Día 3**:

- ✅ Sistema resiliente (no pierde datos)
- ✅ Analytics funcionales
- ✅ Demo lista

---

## 📋 Checklist de Pre-Implementación

Antes de escribir código, asegurar:

- [ ] He leído `ARCHITECTURE.md` completamente
- [ ] Entiendo los principios SOLID aplicados
- [ ] Conozco el flujo de datos (diagrama en ARCHITECTURE.md)
- [ ] Tengo credenciales de OpenAI y PostgreSQL
- [ ] He configurado `.env` correctamente
- [ ] Sé qué es un Protocol vs ABC vs Interface
- [ ] Entiendo Dependency Injection en FastAPI

---

## 🎯 Decisiones de Arquitectura Clave

### 1. ¿Por qué SQLModel y no solo SQLAlchemy?

✅ **Respuesta**:

- Pydantic v2 integrado → validación automática
- Menos boilerplate (1 clase = modelo ORM + schema)
- Type hints nativos
- Compatible con FastAPI

### 2. ¿Por qué separar Normalizers en Rule-Based y AI?

✅ **Respuesta**:

- **Performance**: Rule-based < 1ms, AI ~500ms-2s
- **Costo**: Rules son gratis, AI cuesta por token
- **Determinismo**: Rules 100% predecibles
- **Estrategia**: Usar rules cuando sea posible, AI como fallback

### 3. ¿Por qué guardar eventos como UNPROCESSED en vez de rechazar?

✅ **Respuesta**:

- **No perder datos**: Mejor tener evento "sucio" que perderlo
- **Retry**: Worker puede reprocesar después
- **Auditoría**: Sabemos qué falló y por qué
- **Debugging**: raw_data preserva el original

### 4. ¿Por qué AsyncEngine en vez de sync?

✅ **Respuesta**:

- FastAPI es async nativo
- PostgreSQL + asyncpg es ~30% más rápido
- No bloquea event loop
- Escala mejor con muchas requests

---

## 🛠 Herramientas y Comandos Útiles

### Durante Desarrollo

```bash
# Auto-reload del servidor
uvicorn app.main:app --reload --port 8000

# Watch tests (cuando cambias código)
pytest-watch

# Linter + formatter
ruff check --fix . && ruff format .

# Generar migración
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic upgrade head

# Ver logs en tiempo real
tail -f logs/app.log | jq .  # Si usas JSON logging
```

### Testing

```bash
# Unit tests rápidos
pytest tests/unit/ -v

# Integration tests (más lentos)
pytest tests/integration/ -v --tb=short

# Coverage report
pytest --cov=app --cov-report=term --cov-report=html

# Test específico con debugging
pytest tests/unit/test_ai_normalizer.py::test_normalize_success -v -s
```

### Database

```bash
# Conectar a PostgreSQL
psql -U postgres -d payment_observability

# Ver estructura de tabla
\d normalized_payment_events

# Ver índices
\di

# Contar eventos
SELECT status_category, COUNT(*) FROM normalized_payment_events GROUP BY status_category;

# Ver eventos UNPROCESSED
SELECT id, validation_errors, raw_data FROM normalized_payment_events WHERE status_category = 'UNPROCESSED';
```

---

## 🚨 Errores Comunes y Soluciones

### Error 1: "database connection failed"

**Causa**: PostgreSQL no está corriendo o credenciales incorrectas

**Solución**:

```bash
# Verificar si PostgreSQL está corriendo
pg_isready

# O con Docker
docker ps | grep postgres

# Revisar .env
cat .env | grep POSTGRES
```

### Error 2: "openai.error.RateLimitError"

**Causa**: Demasiadas llamadas a OpenAI API

**Solución**:

```python
# Implementar exponential backoff (ya incluido en roadmap)
# O temporalmente deshabilitar IA
ENABLE_AI_NORMALIZATION=false
```

### Error 3: "AsyncSession not found"

**Causa**: No se configuró async engine correctamente

**Solución**:

```python
# Verificar que DATABASE_URI usa postgresql+psycopg_async
print(settings.DATABASE_URI)  # Debe incluir "_async"
```

### Error 4: Tests fallan con "event loop is closed"

**Causa**: Configuración incorrecta de pytest-asyncio

**Solución**:

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## 📊 Métricas de Éxito

Al final de los 3 días deberías tener:

### Funcionales

- ✅ Ingesta de eventos desde Postman/curl funciona
- ✅ Eventos se normalizan con IA
- ✅ Eventos se guardan en PostgreSQL
- ✅ Query de evento por ID retorna datos
- ✅ Analytics endpoint retorna métricas
- ✅ Eventos UNPROCESSED se guardan correctamente

### Técnicos

- ✅ Tests unitarios >80% coverage
- ✅ Tests de integración pasan
- ✅ No hay secrets hardcodeados
- ✅ Migrations aplicadas sin errores
- ✅ Linter (Ruff) pasa sin warnings
- ✅ Logs estructurados en JSON

### Performance

- ✅ Ingesta < 2s (incluyendo llamada IA)
- ✅ Query por ID < 100ms
- ✅ Analytics < 500ms

### Documentación

- ✅ README.md actualizado
- ✅ API docs (Swagger) accesibles
- ✅ Casos de demo preparados

---

## 🎬 Demo Script (Para Hackathon)

### Preparación

```bash
# 1. Limpiar DB
psql -U postgres -d payment_observability -c "TRUNCATE normalized_payment_events;"

# 2. Iniciar servidor
uvicorn app.main:app --reload --port 8000

# 3. Abrir Swagger UI
open http://localhost:8000/docs
```

### Demo Flow

**1. Health Check** (mostrar sistema funcionando)

```bash
curl http://localhost:8000/api/v1/health
```

**2. Caso 1: Evento Stripe (Rule-Based)** ⚡

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "raw_event": {
      "id": "ch_1234567890",
      "status": "succeeded",
      "amount": 5000,
      "currency": "usd",
      "merchant": "TechCorp Inc",
      "created": 1638360000
    },
    "provider": "stripe"
  }'
```

**Resultado esperado**:

- Normalizado en <100ms (rule-based)
- `normalization_method: "RULE_BASED"`
- `confidence_score: 1.0`

**3. Caso 2: Evento Desconocido (AI)** 🤖

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "raw_event": {
      "transaccion_id": "TXN-ABC-123",
      "comercio": "Tienda Online MX",
      "monto": "1,500.00 MXN",
      "estado": "aprobada",
      "pais": "México",
      "metodo": "tarjeta_credito",
      "fecha": "2025-12-13T15:30:00",
      "gateway": "custom_provider"
    }
  }'
```

**Resultado esperado**:

- Normalizado en ~1-2s (AI)
- `normalization_method: "AI"`
- `country: "MX"` (convertido de "México")
- `amount_usd: ~79` (convertido de MXN)
- `confidence_score: ~0.9`

**4. Caso 3: Analytics** 📊

```bash
curl http://localhost:8000/api/v1/analytics/metrics?start_date=2025-12-01&end_date=2025-12-31
```

**5. Mostrar en PostgreSQL**

```sql
SELECT
    merchant_name,
    provider,
    status_category,
    amount_usd,
    normalization_method
FROM normalized_payment_events
ORDER BY created_at DESC
LIMIT 10;
```

---

## 💡 Tips de Productividad

### 1. Usa snippets de código

Crea snippets en VS Code para modelos comunes:

- SQLModel table class
- FastAPI router
- Pydantic schema

### 2. Test-Driven Development

Escribe el test primero:

1. Define el test (lo que quieres lograr)
2. Implementa la funcionalidad mínima
3. Refactoriza

### 3. Commit frecuente

```bash
git commit -m "feat: add payment event model"
git commit -m "feat: implement AI normalizer"
git commit -m "test: add unit tests for normalizer"
```

### 4. Debug con breakpoints

```python
# En vez de print(), usa debugger
import pdb; pdb.set_trace()

# O con VS Code: F9 para breakpoint, F5 para debug
```

---

## 🎯 Siguiente Paso

**AHORA**:

1. ✅ Abre [ARCHITECTURE.md](./ARCHITECTURE.md) y lee secciones 1-5
2. ✅ Revisa la estructura de carpetas en ARCHITECTURE.md
3. ✅ Abre [ROADMAP.md](./ROADMAP.md) Fase 1
4. ✅ Configura tu `.env`
5. ✅ Comienza con `app/domain/models/enums.py`

**¡Éxito en la hackathon! 🚀**

---

**Documentación creada**: 2025-12-13
**Última actualización**: 2025-12-13
