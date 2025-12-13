# 🌊 Integración con Data Lake Semi-Estructurado

## 📋 Índice

1. [Contexto](#contexto)
2. [Arquitectura de Integración](#arquitectura-de-integración)
3. [Opciones de Implementación](#opciones-de-implementación)
4. [Solución Recomendada: Polling Worker](#solución-recomendada-polling-worker)
5. [Implementación Paso a Paso](#implementación-paso-a-paso)
6. [Configuración](#configuración)
7. [Testing](#testing)

---

## 🎯 Contexto

El sistema necesita **capturar automáticamente** nueva data de transacciones que se va agregando a un **data lake** (otra base de datos PostgreSQL) para iniciar el proceso de normalización.

**✅ Estado actual**: El data lake ya está **desplegado y cargado con datos reales**.

### Requisitos

- ✅ Conectarse a la base de datos del data lake (ya desplegada)
- ✅ Leer transacciones nuevas (evitar duplicados)
- ✅ Procesar datos crudos en formato **heterogéneo** (JSON, XML, CSV, etc.)
- ✅ Manejar errores y reintentos
- ✅ Trazabilidad: registrar qué registros se procesaron
- ✅ Simple para hackathon MVP

### 📊 Estructura Real de los Datos

Cada registro en el data lake tiene esta estructura:

```json
{
  "id": "UUID del registro",
  "data": {
    /* HETEROGÉNEO - puede ser JSON, XML string, CSV, etc. */
  },
  "merchant": {
    "id": "UUID del merchant",
    "name": "Nombre",
    "country": "Código país"
  },
  "transactional_id": "UUID de la transacción"
}
```

**Ejemplos reales**:

```json
// Ejemplo 1: JSON tipo Stripe
{
  "id": "2ed7f2ee-99b7-4b8b-b60f-4d6b6aa1667c",
  "data": {
    "amt": 25.84,
    "p_id": "Stripe",
    "exec_ms": 402,
    "st_code": 1,
    "server_txt": "00_SUCCESS",
    "card_country": "ES"
  },
  "merchant": {
    "id": "06cbe458-8bfd-408b-81d4-215a5b1b4594",
    "name": "Falabella",
    "country": "CO"
  },
  "transactional_id": "fbd7fbbf-6332-4ce8-97bc-22df148e5b8b"
}

// Ejemplo 2: XML como string
{
  "id": "a6f563ae-2873-4bd5-8190-8c2f4ed6bd79",
  "data": {
    "type": "XML_BLOB",
    "content": "<Tx><MerchID>...</MerchID><Val>129.97</Val><Stat>APPROVED</Stat></Tx>"
  },
  "merchant": {
    "id": "2040ca76-48fa-4daa-b29d-2ebb956fd1ee",
    "name": "Shopito",
    "country": "PE"
  },
  "transactional_id": "73f578b6-02f1-4eaf-aabb-297b15c9a64a"
}

// Ejemplo 3: JSON estructurado diferente (PayU)
{
  "id": "d66f4406-a33c-4485-ac0c-67050b54ee33",
  "data": {
    "meta": {"code": 200, "latency": 741},
    "status": "APPROVED",
    "provider": "PayU",
    "origin_iso": "AR",
    "amount_details": {"value": 422.45, "currency": "USD"}
  },
  "merchant": {
    "id": "38b80531-5702-43b7-84e0-e7fb86bd73b5",
    "name": "Netflix",
    "country": "PE"
  },
  "transactional_id": "cdb391e2-cab7-4cf8-b043-c997f17d8bb4"
}
```

**⚠️ Importante**: El campo `data` es **completamente heterogéneo**:

- Diferentes estructuras JSON
- XML como string
- CSV como string
- Cualquier formato que se necesite

Esta es la razón por la que necesitamos **normalización con IA** - no hay un esquema fijo.

---

## 🏗 Arquitectura de Integración

```
┌──────────────────────────────────────────────┐
│   Data Lake DB (PostgreSQL)                  │
│   Host: datalake.yuno.com                    │
│                                              │
│   Table: raw_transactions                    │
│   ┌────────────────────────────────────┐    │
│   │ id, transaction_data (JSONB),      │    │
│   │ created_at, processed              │    │
│   └────────────────────────────────────┘    │
└───────────────────┬──────────────────────────┘
                    │
                    │ ⏰ Polling 2 veces al día
                    │ SQL: SELECT * WHERE processed = false
                    │
        ┌───────────▼──────────────────────────┐
        │   Data Lake Poller Worker            │
        │                                      │
        │  1️⃣  Query new transactions          │
        │  2️⃣  Process each transaction        │
        │  3️⃣  Normalize with Rules + AI       │
        │  4️⃣  Save to main DB                 │
        │  5️⃣  Mark as processed in lake       │
        └───────────┬──────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────────────────┐
        │   Main DB (PostgreSQL)               │
        │   normalized_payment_events          │
        └──────────────────────────────────────┘
```

---

## 🎯 Solución para MVP: Polling desde DB

**Arquitectura**:

```
Worker (cron) → SELECT FROM data_lake.raw_transactions → Normalize → INSERT INTO main_db → UPDATE data_lake SET processed=true
```

**Ventajas**:

- ✅ **Extremadamente simple** (< 100 líneas)
- ✅ Solo requiere connection string a otra DB
- ✅ No necesita HTTP, S3, ni infraestructura adicional
- ✅ Usa SQLAlchemy que ya tienes configurado
- ✅ Fácil de testear y demo
- ✅ Transaccional: rollback si falla la normalización
- ✅ Bajo consumo de recursos (solo 2 ejecuciones diarias)

**Para Hackathon**: Ideal, todo en PostgreSQL

---

## ✅ Solución Recomendada: Polling Worker

Para la **hackathon**, implementaremos un **Polling Worker** que:

1. **Ejecuta 2 veces al día** (cada 12 horas, configurable)
2. **Lista archivos** en el bucket de S3
3. **Filtra procesados** usando tabla `processed_files` en PostgreSQL
4. **Descarga y parsea** archivos nuevos (JSON, CSV, JSONL)
5. **Envía transacciones** en batch al API de normalización
6. **Registra como procesado** para evitar duplicados

### Ventajas para Hackathon

- ⚡ **Rápido de implementar**: ~2-3 horas
- 🎯 **Fácil de demo**: logs claros, control manual
- 🔧 **Debuggable**: puede ejecutarse en local
- 📊 **Observable**: métricas claras (archivos procesados)
- 🚀 **Migrable**: fácil evolucionar a event-driven después
- ⏰ **Eficiente**: 2 ejecuciones diarias, ideal para hackathon

---

## 📐 Implementación Paso a Paso

### 1. Tabla en Data Lake (Base de datos externa)

```sql
-- En la DB del data lake (la crean ustedes para agregar data)
CREATE TABLE raw_transactions (
    id SERIAL PRIMARY KEY,
    transaction_data JSONB NOT NULL,  -- Datos crudos en cualquier formato
    source VARCHAR(50),                -- 'stripe', 'adyen', 'paypal', etc.
    created_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,   -- Flag para tracking
    processed_at TIMESTAMP
);

CREATE INDEX idx_raw_transactions_processed ON raw_transactions(processed) WHERE processed = false;
```

**Ejemplo de inserción manual** (para testing):

```sql
INSERT INTO raw_transactions (transaction_data, source) VALUES
('{"id": "tx_123", "amount": 100.50, "status": "approved"}', 'stripe'),
('{"transaction_id": "pay_456", "value": 250, "state": "declined"}', 'adyen');
```

### 2. Cliente para Data Lake DB

```python
# app/infraestructure/datalake/client.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataLakeClient:
    """Cliente para leer del data lake (otra DB PostgreSQL)"""

    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string, pool_pre_ping=True)

    def get_unprocessed_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene transacciones no procesadas del data lake"""

        query = text("""
            SELECT id, data, merchant, transactional_id, created_at
            FROM raw_transactions
            WHERE processed = false
            ORDER BY created_at ASC
            LIMIT :limit
        """)

        with Session(self.engine) as session:
            result = session.execute(query, {"limit": limit})
            rows = result.fetchall()

            return [
                {
                    'id': str(row.id),
                    'data': row.data,              # JSONB ya parseado (puede ser JSON, XML string, etc.)
                    'merchant': row.merchant,       # JSONB: {id, name, country}
                    'transactional_id': str(row.transactional_id),

    def mark_as_processed(self, transaction_ids: List[int]):
        """Marca transacciones como procesadas"""

        if not transaction_ids:
            return

        query = text("""
            UPDATE raw_transactions
            SET processed = true, processed_at = NOW()
            WHERE id = ANY(:ids)
        """)

        with Session(self.engine) as session:
            session.execute(query, {"ids": transaction_ids})
            session.commit()
            logger.info(f"Marked {len(transaction_ids)} transactions as processed")
        self.s3_client = boto3.client('s3')

    def list_new_files(self, after_date: datetime = None) -> List[Dict[str, Any]]:
        """Lista archivos en el bucket, opcionalmente filtrados por fecha"""

        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

        files = []
        for page in pages:
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                # Filtrar por fecha si se especifica
                if after_date and obj['LastModified'] < after_date:
                    continue

                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })

        return files

    def download_file_content(self, object_key: str) -> bytes:
        """Descarga contenido de un archivo"""
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=object_key
        )
        return response['Body'].read()

    def parse_file(self, content: bytes, file_format: str) -> List[Dict[str, Any]]:
        """Parsea archivo según su formato"""

        if file_format == 'json':
            # JSON estándar (array o single object)
            data = json.loads(content.decode('utf-8'))
            return data if isinstance(data, list) else [data]

        elif file_format == 'jsonl':
            # JSONL (JSON Lines - un objeto por línea)
            lines = content.decode('utf-8').strip().split('\n')
            return [json.loads(line) for line in lines if line.strip()]

        elif file_format == 'csv':
            # CSV
            df = pd.read_csv(StringIO(content.decode('utf-8')))
            return df.to_dict('records')

        elif file_format == 'parquet':
            # Parquet (requiere pyarrow)
            df = pd.read_parquet(BytesIO(content))
            return df.to_dict('records')

        else:
            raise ValueError(f"Formato no soportado: {file_format}")

    def close(self):
        """Cierra la conexión HTTP"""
        self.client.close()
```

### 3. Worker de Polling (Simplificado)

```python
# app/workers/data_lake_poller.py
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys

from sqlmodel import Session
from app.infraestructure.core.db import engine
from app.infraestructure.datalake.client import DataLakeClient
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

class DataLakePoller:
    """Worker que lee transacciones del data lake DB"""

    def __init__(
        self,
        datalake_connection: str,
        poll_interval: int = 43200,  # 12 horas
        run_once: bool = False,
        batch_size: int = 100
    ):
        self.datalake_client = DataLakeClient(datalake_connection)
        self.poll_interval = poll_interval
        self.run_once = run_once
        self.batch_size = batch_size
        self.ingestion_service = IngestionService()

    def run(self):
        """Loop principal del worker"""
        logger.info("🌊 Data Lake Poller iniciado")

        if self.run_once:
            logger.info("⚡ Modo ejecución única (cron mode)")
            self.poll_and_process()
            logger.info("✅ Ejecución completada")
            return

        logger.info(f"⏰ Polling continuo cada {self.poll_interval/3600:.1f} horas")

        while True:
            try:
                self.poll_and_process()
            except Exception as e:
                logger.error(f"❌ Error en polling: {e}", exc_info=True)

            time.sleep(self.poll_interval)

    def poll_and_process(self):
        """Un ciclo de polling y procesamiento"""
        logger.info("🔍 Consultando transacciones no procesadas...")

        # 1. Obtener transacciones del data lake
        transactions = self.datalake_client.get_unprocessed_transactions(
            limit=self.batch_size
        )

        if not transactions:
            logger.info("✨ No hay transacciones nuevas")
            return

        logger.info(f"📊 Encontradas {len(transactions)} transacciones por procesar")

        # 2. Procesar cada transacción
        processed_ids = []
        for tx in transactions:
            try:
                self._process_transaction(tx)
                processed_ids.append(tx['id'])
            except Exception as e:
                logger.error(f"Error procesando transaction {tx['id']}: {e}")
                # Continuar con las demás

        # 3. Marcar como procesadas en el data lake
        if processed_ids:
            self.datalake_client.mark_as_processed(processed_ids)
            logger.info(f"✅ Procesadas {len(processed_ids)} transacciones")

    def _process_transaction(self, transaction: Dict[str, Any]):
        """Procesa una transacción individual"""
        tx_id = transaction['id']
        tx_data = transaction['data']        # JSONB: puede ser JSON heterogéneo
        merchant = transaction['merchant']    # JSONB: {id, name, country}
        transactional_id = transaction['transactional_id']

        # Detectar provider del campo data (puede estar en diferentes campos)
        provider = self._detect_provider(tx_data)

        logger.info(f"🔄 Procesando transaction {transactional_id} from {provider}")
        logger.info(f"   Merchant: {merchant.get('name')} ({merchant.get('country')})")

        # Enriquecer con metadata
        enriched_data = {
            'id': tx_id,
            'transactional_id': transactional_id,
            'merchant': merchant,
            'raw_data': tx_data
        }

        # Usar el servicio de ingesta para normalizar y guardar
        with Session(engine) as session:
            self.ingestion_service.process_transaction(
                raw_event=enriched_data,
                provider=provider,
                session=session
            )

    def _detect_provider(self, data: Dict[str, Any]) -> str:
        """Detecta el provider desde los datos heterogéneos"""
        # Intentar diferentes campos comunes
        if 'provider' in data:
            return data['provider'].lower()
        if 'p_id' in data:
            return data['p_id'].lower()
        if 'type' in data and data['type'] == 'XML_BLOB':
            # Podría parsearse el XML para extraer provider
            return 'unknown_xml'

        return 'unknown'
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Configuración
    datalake_url = os.getenv("DATALAKE_DATABASE_URL")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "43200"))
    run_once = "--once" in sys.argv

    # Iniciar worker
    poller = DataLakePoller(
        datalake_connection=datalake_url,
        poll_interval=poll_interval,
        run_once=run_once
    )

    poller.run()
```

        logger.info(f"📥 Procesando: {file_name} (ID: {file_id})")

        with Session(engine) as session:
            # 1. Crear registro de tracking
            processed_file = ProcessedFile(
                file_id=file_id,
                file_path=file_name,
                file_size=file_info['size'],
                created_at=file_info['created_at'],
                processing_status="processing",
                records_count=0
            )
            session.add(processed_file)
            session.commit()
            session.refresh(processed_file)

            try:
                # 2. Descargar contenido
                content = self.datalake_client.download_file_content(file_id)

                # 3. Parsear según formato
                file_format = file_info.get('format', 'json')
                records = self.datalake_client.parse_file(content, file_format)
                logger.info(f"📊 Parseados {len(records)} registros")

                # 4. Enviar al servicio de ingesta (en batches)
                batch_size = 50
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    self._ingest_batch(batch, session)

                # 5. Marcar como completado
                processed_file.processing_status = "completed"
                processed_file.records_count = len(records)
                processed_file.completed_at = datetime.utcnow()
                session.add(processed_file)
                session.commit()

                logger.info(f"✅ Archivo procesado exitosamente: {len(records)} registros")

            except Exception as e:
                # Marcar como fallido
                processed_file.processing_status = "failed"
                processed_file.error_message = str(e)
                processed_file.completed_at = datetime.utcnow()
                session.add(processed_file)
                session.commit()

                logger.error(f"❌ Error procesando archivo: {e}", exc_info=True)

    def _ingest_batch(self, batch: List[Dict], session: Session):
        """Envía un batch de transacciones al servicio de ingesta"""
        for record in batch:
            try:
                # Usar el servicio de ingesta existente
                self.ingestion_service.process_transaction(record, session)
            except Exception as e:
                logger.error(f"Error en registro individual: {e}")
                # Continuar con el siguiente registro

# Script de ejecución

if **name** == "**main**":
import os
import sys
from dotenv import load_dotenv

    load_dotenv()

    # Configuración desde env
    bucket_name = os.getenv("S3_BUCKET_NAME", "yuno-payments-lake")
    prefix = os.getenv("S3_PREFIX", "raw-payments/")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "43200"))  # 12h default

    # Detectar si se ejecuta desde cron (modo single run)
    run_once = "--once" in sys.argv or os.getenv("RUN_ONCE", "false").lower() == "true"

    # Iniciar worker
    poller = DataLakePoller(
        bucket_name=bucket_name,
        prefix=prefix,
        poll_interval=poll_interval,
        run_once=run_once
    )

    poller.run()

````

### 4. Scripts de Deploy

#### Script para Cron (Ejecución única)

```bash
# scripts/run_data_lake_poller_once.sh
#!/bin/bash
# Para usar con cron - ejecuta una vez y termina

cd /opt/yuno-backend

# Activar entorno virtual
source .venv/bin/activate

# Cargar variables de entorno
export $(cat .env | xargs)

# Ejecutar en modo single-run
python -m app.workers.data_lake_poller --once
````

#### Script para Daemon (Loop continuo)

```bash
# scripts/run_data_lake_poller_daemon.sh
#!/bin/bash
# Para systemd o ejecución manual continua

echo "🌊 Iniciando Data Lake Poller Worker..."

cd /opt/yuno-backend

# Activar entorno virtual
source .venv/bin/activate

# Cargar variables de entorno
export $(cat .env | xargs)

# Ejecutar worker
python -m app.workers.data_lake_poller
```

---

## ⚙️ Configuración

### Variables de Entorno

```bash
# .env
# Data Lake DB Configuration (DB externa donde está la data cruda)
DATALAKE_DATABASE_URL=postgresql://readonly:pass@datalake.yuno.com:5432/payments_lake
POLL_INTERVAL_SECONDS=43200  # 12 horas (2 veces al día)

# Main DB (nuestra DB donde guardamos datos normalizados)
DATABASE_URL=postgresql://user:pass@localhost:5432/yuno_observability
```

### Estructura de Datos en Data Lake

Cada registro tiene:

- **`id`**: UUID del registro
- **`data`**: JSONB heterogéneo (puede ser cualquier estructura)
- **`merchant`**: JSONB con `{id, name, country}`
- **`transactional_id`**: UUID de la transacción
- **`processed`**: Boolean (false = pendiente)

**Ejemplos de variabilidad en `data`**:

```json
// Tipo 1: Stripe-like
{"amt": 25.84, "p_id": "Stripe", "st_code": 1}

// Tipo 2: XML blob
{"type": "XML_BLOB", "content": "<Tx>...</Tx>"}

// Tipo 3: PayU-like
{"status": "APPROVED", "provider": "PayU", "amount_details": {...}}
```

### Dependencias

**No se necesitan dependencias adicionales** - SQLAlchemy ya está instalado.

Si quieres usar SQLModel para type hints:

```bash
# Ya lo tienes instalado
# sqlmodel, sqlalchemy, psycopg
```

---

## 🧪 Testing

### 1. Test Local con MinIO (S3-compatible)

```bash
# Docker Compose para MinIO
docker run -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

```python
# tests/integration/test_data_lake_poller.py
import pytest
from moto import mock_s3
import boto3
import json

@mock_s3
def test_s3_file_detection():
    # Crear bucket mock
    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_client.create_bucket(Bucket='test-bucket')

    # Subir archivo de prueba
    test_data = [
        {"transaction_id": "tx1", "amount": 100.50},
        {"transaction_id": "tx2", "amount": 250.00}
    ]
    s3_client.put_object(
        Bucket='test-bucket',
        Key='raw/test_file.json',
        Body=json.dumps(test_data)
    )

    # Test del poller
    from app.workers.data_lake_poller import DataLakePoller
    poller = DataLakePoller(bucket_name='test-bucket')

    # Listar archivos
    files = poller.s3_client.list_new_files()
    assert len(files) == 1
    assert files[0]['key'] == 'raw/test_file.json'
```

### 2. Test de Procesamiento End-to-End

```python
@mock_s3
def test_file_processing_pipeline():
    """Test completo: S3 → Polling → Ingesta → DB"""
    # Setup
    setup_mock_s3_bucket()

    # Ejecutar un ciclo de polling
    poller = DataLakePoller(bucket_name='test-bucket', poll_interval=1)
    poller.poll_and_process()

    # Verificar que se procesó
    with Session(engine) as session:
        processed = session.exec(
            select(ProcessedFile).where(ProcessedFile.processing_status == "completed")
        ).first()

        assert processed is not None
        assert processed.records_count == 2
```

---

## 📊 Monitoreo y Observabilidad

### Métricas Clave

```python
# app/workers/data_lake_poller.py - agregar métricas
from prometheus_client import Counter, Gauge, Histogram

files_processed = Counter('data_lake_files_processed_total', 'Total files processed')
files_failed = Counter('data_lake_files_failed_total', 'Total files failed')
records_ingested = Counter('data_lake_records_ingested_total', 'Total records ingested')
processing_duration = Histogram('data_lake_processing_seconds', 'File processing duration')

# En _process_file:
with processing_duration.time():
    # ... procesamiento
    files_processed.inc()
    records_ingested.inc(len(records))
```

### Logs Estructurados

```python
logger.info(
    "File processed",
    extra={
        "file_path": object_key,
        "records_count": len(records),
        "processing_time_ms": duration_ms,
        "file_size_bytes": file_info['size']
    }
)
```

---

## 🚀 Deployment

### Opción 1: Systemd Service (Linux)

```ini
# /etc/systemd/system/data-lake-poller.service
[Unit]
Description=Yuno Data Lake Poller Worker
After=network.target postgresql.service

[Service]
Type=simple
User=yuno
WorkingDirectory=/opt/yuno-backend
Environment="PATH=/opt/yuno-backend/.venv/bin"
ExecStart=/opt/yuno-backend/.venv/bin/python -m app.workers.data_lake_poller
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable data-lake-poller
sudo systemctl start data-lake-poller
sudo systemctl status data-lake-poller
```

### Opción 2: Docker Container

```dockerfile
# Dockerfile.poller
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install poetry && poetry install --no-dev

CMD ["python", "-m", "app.workers.data_lake_poller"]
```

```yaml
# docker-compose.yml
services:
  data-lake-poller:
    build:
      context: .
      dockerfile: Dockerfile.poller
    env_file: .env
    depends_on:
      - postgres
    restart: unless-stopped
```

### Opción 3: Kubernetes CronJob

```yaml
# k8s/data-lake-poller-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: data-lake-poller
spec:
  schedule: "0 0,12 * * *" # 2 veces al día: 00:00 y 12:00
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: poller
              image: yuno/backend:latest
              command: ["python", "-m", "app.workers.data_lake_poller"]
              envFrom:
                - secretRef:
                    name: yuno-secrets
          restartPolicy: OnFailure
```

### Opción 4: Cron Job (Linux/macOS) ⭐ **RECOMENDADO HACKATHON**

```bash
# Editar crontab
crontab -e

# Ejecutar a las 00:00 y 12:00 todos los días
0 0,12 * * * cd /opt/yuno-backend && /opt/yuno-backend/.venv/bin/python -m app.workers.data_lake_poller >> /var/log/yuno-poller.log 2>&1

# O ejecutar cada 12 horas desde ahora
0 */12 * * * cd /opt/yuno-backend && /opt/yuno-backend/.venv/bin/python -m app.workers.data_lake_poller >> /var/log/yuno-poller.log 2>&1
```

**Ventajas del Cron**:

- ✅ No consume recursos entre ejecuciones
- ✅ Más simple que systemd o Docker
- ✅ Fácil de ajustar horarios
- ✅ Logs en archivo separado
- ✅ Perfecto para hackathon

---

## 🔄 Evolución a Event-Driven (Post-Hackathon)

Cuando el volumen crezca, migrar a arquitectura event-driven:

```python
# app/workers/s3_event_consumer.py
"""Consumer de eventos S3 vía SQS"""

import boto3
import json

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/xxx/yuno-s3-events'

def process_s3_event(event_message):
    """Procesa evento de S3"""
    s3_event = json.loads(event_message['Body'])

    for record in s3_event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # Procesar archivo inmediatamente
        process_file(bucket, key)

while True:
    # Recibir mensajes
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20  # Long polling
    )

    for message in response.get('Messages', []):
        try:
            process_s3_event(message)
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
        except Exception as e:
            logger.error(f"Error: {e}")
```

---

## 📋 Checklist de Implementación

### Fase 1: Setup Básico (1 hora)

- [ ] Crear modelo `ProcessedFile` en DB
- [ ] Migración Alembic para tabla
- [ ] Instalar boto3 y pandas
- [ ] Configurar credenciales AWS

### Fase 2: S3 Client (1 hora)

- [ ] Implementar `S3DataLakeClient`
- [ ] Método `list_new_files()`
- [ ] Método `download_file_content()`
- [ ] Método `parse_file()` (JSON, CSV, JSONL)
- [ ] Tests unitarios

### Fase 3: Worker de Polling (1.5 horas)

- [ ] Crear `DataLakePoller` class
- [ ] Implementar loop de polling
- [ ] Integrar con servicio de ingesta
- [ ] Tracking de archivos procesados
- [ ] Manejo de errores y logging

### Fase 4: Testing (0.5 horas)

- [ ] Test con moto (mock S3)
- [ ] Test end-to-end local
- [ ] Verificar con MinIO (opcional)

### Fase 5: Deploy (1 hora)

- [ ] Script de ejecución
- [ ] Variables de entorno
- [ ] Logs estructurados
- [ ] Métricas básicas

**Total estimado: 4-5 horas** ⚡

---

## 🎯 Demo para Hackathon

```bash
# 1. Subir archivo de prueba a S3
aws s3 cp sample_transactions.json s3://yuno-payments-lake/raw-payments/

# 2. Iniciar worker
python -m app.workers.data_lake_poller

# 3. Ver logs en real-time
tail -f logs/data_lake_poller.log

# Salida esperada:
# 🔍 Buscando archivos nuevos...
# 📂 Encontrados 1 archivos en S3
# ✨ 1 archivos nuevos por procesar
# 📥 Procesando: raw-payments/sample_transactions.json
# 📊 Parseados 50 registros
# ✅ Archivo procesado exitosamente: 50 registros
```

---

## 💡 Tips y Mejores Prácticas

1. **Idempotencia**: El worker debe poder ejecutarse múltiples veces sin duplicar datos
2. **Batch Processing**: Procesa en batches de 50-100 registros para mejor performance
3. **Error Handling**: Registra errores pero continúa procesando otros archivos
4. **Monitoring**: Exponer métricas (archivos/min, latencia, errores)
5. **Graceful Shutdown**: Manejar SIGTERM para terminar procesamiento actual
6. **Backpressure**: Si API está lento, reducir tamaño de batch

---

## 🔗 Referencias

- [AWS S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Polling vs Event-Driven](https://aws.amazon.com/blogs/compute/choosing-between-messaging-services/)
