# Cambios: Database Async → Sync para Hackathon

## 🎯 Decisión Arquitectónica

**Para simplificar el desarrollo durante la hackathon, usaremos sessions SYNC para la base de datos.**

### Razones:

1. **Simplicidad**: Menos complejidad en el código
2. **Velocidad de desarrollo**: No lidiar con async/await en DB
3. **Menos errores**: async/await puede ser confuso
4. **FastAPI sigue async**: Solo las operaciones de DB son sync
5. **Suficiente para demo**: Performance adecuada para hackathon

---

## 📝 Cambios en la Documentación

### ✅ Ya Actualizado

- [x] ROADMAP.md - Sección 1.3 (Database Setup)

### 🔄 Por Actualizar

Los siguientes archivos aún tienen referencias a async sessions que deben entenderse como sync:

#### ROADMAP.md

- Sección 3.1: Repository Implementation → métodos sin `await`
- Sección 3.4: API Router → sin `await` en llamadas a repo
- Sección 3.5: Dependency Injection → `SessionDep` en vez de `AsyncSessionDep`

#### BEST_PRACTICES.md

- Sección "SQLModel & Database" → ejemplos sync
- Sección "Testing" → tests sin @pytest.mark.asyncio

#### QUICK_REFERENCE.md

- Snippets de Repository → sin await
- Snippets de DI → SessionDep

---

## 💡 Guía Rápida de Conversión

### Antes (Async) ❌

```python
from sqlalchemy.ext.asyncio import AsyncSession

class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event):
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

# Uso
repo = PaymentRepository(session)
saved = await repo.save(event)  # Con await
```

### Ahora (Sync) ✅

```python
from sqlmodel import Session

class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, event):  # Sin async
        self.session.add(event)
        self.session.commit()  # Sin await
        self.session.refresh(event)  # Sin await
        return event

# Uso
repo = PaymentRepository(session)
saved = repo.save(event)  # Sin await
```

---

## 🔧 Configuración Actual (Correcta)

### db.py (Ya existente - NO TOCAR)

```python
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

### Repository Pattern

```python
from sqlmodel import select, Session

class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, event: NormalizedPaymentEvent) -> NormalizedPaymentEvent:
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_by_id(self, event_id: UUID) -> NormalizedPaymentEvent | None:
        result = self.session.execute(
            select(NormalizedPaymentEvent).where(NormalizedPaymentEvent.id == event_id)
        )
        return result.scalar_one_or_none()
```

### FastAPI Router (IMPORTANTE: Endpoints siguen siendo async)

```python
from fastapi import APIRouter
from app.infraestructure.core.db import SessionDep

router = APIRouter(prefix="/events")

@router.post("/")
async def ingest_event(  # ✅ async en endpoint
    request: EventIngestRequest,
    session: SessionDep,  # ✅ SessionDep (sync)
) -> EventIngestResponse:
    repo = PaymentRepository(session)
    event = repo.save(...)  # ✅ SIN await
    return EventIngestResponse.from_orm(event)
```

---

## ⚠️ Notas Importantes

1. **FastAPI endpoints siguen siendo `async def`**

   - FastAPI maneja async correctamente
   - Solo las operaciones de DB son sync

2. **No necesitas `await` en operaciones de DB**

   - `session.commit()` en vez de `await session.commit()`
   - `repo.save()` en vez de `await repo.save()`

3. **Testing es más simple**

   - No necesitas `@pytest.mark.asyncio`
   - Tests son funciones normales `def test_...()` no `async def`

4. **Database URI**
   - Usar: `postgresql+psycopg://...`
   - NO usar: `postgresql+psycopg_async://...`

---

## 📚 Referencias Actualizadas

Al leer la documentación, cuando veas:

- `AsyncSession` → entender como `Session`
- `await session.commit()` → entender como `session.commit()`
- `async def save(...)` → entender como `def save(...)`
- `AsyncSessionDep` → entender como `SessionDep`

---

## ✅ Checklist de Implementación

- [ ] Usar `Session` en vez de `AsyncSession`
- [ ] NO usar `await` en operaciones de DB
- [ ] Métodos de Repository son `def` no `async def`
- [ ] Tests son `def` no `async def` (sin @pytest.mark.asyncio)
- [ ] FastAPI endpoints siguen siendo `async def`
- [ ] DATABASE_URI: `postgresql+psycopg://...` (sin `_async`)

---

**Última actualización**: 2025-12-13
**Razón**: Simplificar desarrollo para Hackathon
