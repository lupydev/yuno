# Payment Observability System - Yuno Hackathon 🚀

Sistema backend de observabilidad para transacciones de pago que normaliza datos heterogéneos usando **IA + Reglas**.

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Raw Event  │ ───> │ AI + Rules   │ ───> │ Normalized  │
│  (Dirty)    │      │ Normalizer   │      │ Data (Clean)│
└─────────────┘      └──────────────┘      └─────────────┘
```

---

## 📚 **DOCUMENTACIÓN COMPLETA**

> **⚠️ IMPORTANTE**: Toda la documentación técnica y arquitectónica está en la carpeta [`/docs`](./docs/)

### 🎯 Comienza Aquí

**📋 [INDEX.md](docs/INDEX.md)** - Resumen ejecutivo de toda la documentación

**Para implementar el sistema, lee la documentación en este orden:**

| #     | Documento                                          | Propósito                         | Tiempo     |
| ----- | -------------------------------------------------- | --------------------------------- | ---------- |
| **1** | **[📖 START_HERE.md](docs/START_HERE.md)**         | Guía rápida de 3 días             | 15 min     |
| **2** | **[🏗 ARCHITECTURE.md](docs/ARCHITECTURE.md)**      | Diseño técnico completo           | 1h         |
| **3** | **[🗺 ROADMAP.md](docs/ROADMAP.md)**                | Plan de implementación en 5 fases | 30 min     |
| **4** | **[✨ BEST_PRACTICES.md](docs/BEST_PRACTICES.md)** | Guía de código (✅ vs ❌)         | Referencia |
| **5** | **[📊 DIAGRAMS.md](docs/DIAGRAMS.md)**             | Diagramas visuales                | Referencia |
| **6** | **[📝 PROJECT_README.md](docs/PROJECT_README.md)** | Guía de usuario final             | 20 min     |

---

## 📦 Documentación Creada

```
docs/
├── INDEX.md                    # 📋 Índice maestro (leer primero)
├── CAMBIOS_SYNC_DB.md         # ⚡ IMPORTANTE: DB Sync para Hackathon
├── DATA_LAKE_INTEGRATION.md   # 🌊 NUEVO: Integración con Data Lake
├── START_HERE.md               # 🚀 Guía rápida de 3 días
├── ARCHITECTURE.md             # 🏗  Diseño técnico completo
├── ROADMAP.md                  # 🗺  Plan de implementación (5 fases)
├── BEST_PRACTICES.md           # ✨  Guía de código (✅ vs ❌)
├── DIAGRAMS.md                 # 📊  Diagramas visuales
├── PROJECT_README.md           # 📝  Guía de usuario final
├── QUICK_REFERENCE.md          # ⚡  Comandos y snippets
└── SUMMARY.md                  # 🎉  Resumen del trabajo completo

Total: 11 documentos | ~190 KB | ~6,500 líneas
```

### 🎯 Comienza Ahora

1. **⚡ IMPORTANTE**: [docs/CAMBIOS_SYNC_DB.md](docs/CAMBIOS_SYNC_DB.md) - **Cambio clave para Hackathon**
2. **🌊 NUEVO**: [docs/DATA_LAKE_INTEGRATION.md](docs/DATA_LAKE_INTEGRATION.md) - **Captura automática desde S3**
3. **Lee**: [docs/INDEX.md](docs/INDEX.md) (5 min)
4. **Planifica**: [docs/START_HERE.md](docs/START_HERE.md) (15 min)
5. **Implementa**: [docs/ROADMAP.md](docs/ROADMAP.md) (sigue las fases)

---

## ⚡ Quick Start (Cuando estés listo para implementar)

```bash
# 1. Instalar dependencias
uv sync

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 3. Aplicar migraciones
alembic upgrade head

# 4. Ejecutar servidor
uvicorn app.main:app --reload --port 8000

# 5. Abrir documentación interactiva
open http://localhost:8000/docs
```

> **⚠️ Nota**: Este Quick Start es para DESPUÉS de implementar el código.
> **Primero** lee la documentación en `/docs` para entender QUÉ implementar.

---

## 🛠 Stack Técnico

```yaml
Framework: FastAPI 0.124.2+
ORM: SQLModel (Pydantic v2 + SQLAlchemy)
Database: PostgreSQL con JSONB
AI: LangChain + OpenAI (GPT-4o-mini)
Migrations: Alembic
Testing: Pytest + Pytest-Asyncio
```

---

## 📂 Estructura del Proyecto

```
back/
├── docs/                      # 📚 TODA LA DOCUMENTACIÓN AQUÍ
│   ├── START_HERE.md         # ⭐ Comienza aquí
│   ├── ARCHITECTURE.md       # Diseño del sistema
│   ├── ROADMAP.md           # Plan de implementación
│   ├── BEST_PRACTICES.md    # Guía de código
│   └── PROJECT_README.md    # Guía de usuario
│
├── app/
│   ├── main.py              # Entry point
│   ├── api/                 # Routers FastAPI
│   ├── services/            # Lógica de aplicación
│   ├── domain/              # Modelos y reglas de negocio
│   └── infraestructure/     # DB, AI, config
│
├── tests/
├── alembic/
├── pyproject.toml
└── README.md               # Este archivo
```

---

## 🎯 Características Principales

- ✅ **Normalización Inteligente**: LangChain + GPT-4o-mini (híbrido Reglas + IA)
- ✅ **Ingesta desde Data Lake**: Captura automática desde S3/Azure/GCS 🌊 **NUEVO**
- ✅ **Múltiples Formatos**: JSON, JSONL, CSV, Parquet
- ✅ **API REST**: Documentación automática (Swagger)
- ✅ **Analítica**: Métricas en tiempo real
- ✅ **Clean Architecture**: SOLID, testeable, mantenible
- ✅ **Tracking de Archivos**: Idempotencia garantizada

### 🌊 Data Lake Integration

El sistema ahora soporta **captura automática** de transacciones desde data lakes semi-estructurados:

```bash
# Worker de polling 2 veces al día (cada 12 horas)
# Conexión simple via URI - no requiere AWS/S3
python -m app.workers.data_lake_poller --once

# Solo necesitas configurar la URI del data lake
export DATALAKE_BASE_URL=https://datalake.yuno.com/api

# Soporta: JSON, JSONL, CSV, Parquet
# Normaliza y almacena automáticamente
```

**📚 Ver documentación completa**: [DATA_LAKE_INTEGRATION.md](docs/DATA_LAKE_INTEGRATION.md)

---

## 🚀 Próximos Pasos

1. ✅ Lee [docs/START_HERE.md](docs/START_HERE.md)
2. ✅ Revisa [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. ✅ Sigue el plan en [docs/ROADMAP.md](docs/ROADMAP.md)
4. ✅ Comienza a implementar

---

## 📞 Recursos

- **API Docs**: http://localhost:8000/docs (cuando el servidor esté corriendo)
- **Documentación**: [docs/](./docs/)
- **Tests**: `pytest`

---

**Desarrollado para Hackathon Yuno 2025** 🎉
