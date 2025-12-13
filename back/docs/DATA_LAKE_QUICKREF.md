# 🌊 Data Lake Integration - Quick Reference

## 🎯 Comandos Rápidos

### Setup Inicial

**✅ Data Lake ya está desplegado y con datos**

```bash
# 1. NO requiere dependencias adicionales (usa SQLAlchemy existente)

# 2. Configurar .env con las credenciales del data lake
cat >> .env << EOF
DATALAKE_DATABASE_URL=postgresql://readonly:pass@datalake.yuno.com:5432/payments_lake
POLL_INTERVAL_SECONDS=43200  # 12 horas (2x al día)
EOF

# 3. ¡Listo! Ya puedes ejecutar el worker
```

### Ejecutar Worker

```bash
# Opción 1: Ejecutar una vez (--once flag)
python -m app.workers.data_lake_poller --once

# Opción 2: Cron (2 veces al día) ⭐ RECOMENDADO HACKATHON
crontab -e
# Agregar: 0 0,12 * * * cd /path/to/yuno/back && .venv/bin/python -m app.workers.data_lake_poller --once >> /var/log/yuno-poller.log 2>&1
```

### Testing

```bash
# Unit tests
pytest tests/unit/test_s3_client.py -v

# Integration tests (mock S3)
pytest tests/integration/test_data_lake_poller.py -v

# Test manual con archivo local
# 1. Subir archivo a S3
aws s3 cp sample_transactions.json \
  s3://yuno-payments-lake/raw-payments/2024-12-13/

# 2. Ver logs del worker
tail -f logs/data_lake_poller.log
```

---

## 📝 Código de Ejemplo

### Tabla SQL del Data Lake

```sql
-- Ejecutar en DB del data lake
CREATE TABLE raw_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data JSONB NOT NULL,              -- Datos heterogéneos (JSON, XML, CSV)
    merchant JSONB NOT NULL,          -- {id, name, country}
    transactional_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP
);

CREATE INDEX idx_raw_transactions_processed ON raw_transactions(processed) WHERE processed = false;
```

### Insertar Datos de Prueba

```sql
-- Ejemplo 1: JSON tipo Stripe
INSERT INTO raw_transactions (data, merchant, transactional_id) VALUES (
  '{"amt": 25.84, "p_id": "Stripe", "exec_ms": 402, "st_code": 1, "server_txt": "00_SUCCESS", "card_country": "ES"}',
  '{"id": "06cbe458-8bfd-408b-81d4-215a5b1b4594", "name": "Falabella", "country": "CO"}',
  'fbd7fbbf-6332-4ce8-97bc-22df148e5b8b'
);

-- Ejemplo 2: XML como string
INSERT INTO raw_transactions (data, merchant, transactional_id) VALUES (
  '{"type": "XML_BLOB", "content": "<Tx><MerchID>2040ca76-48fa-4daa-b29d-2ebb956fd1ee</MerchID><Org>CL</Org><Val>129.97</Val><Stat>APPROVED</Stat></Tx>"}',
  '{"id": "2040ca76-48fa-4daa-b29d-2ebb956fd1ee", "name": "Shopito", "country": "PE"}',
  '73f578b6-02f1-4eaf-aabb-297b15c9a64a'
);

-- Ejemplo 3: JSON tipo PayU
INSERT INTO raw_transactions (data, merchant, transactional_id) VALUES (
  '{"status": "APPROVED", "provider": "PayU", "origin_iso": "AR", "amount_details": {"value": 422.45, "currency": "USD"}}',
  '{"id": "38b80531-5702-43b7-84e0-e7fb86bd73b5", "name": "Netflix", "country": "PE"}',
  'cdb391e2-cab7-4cf8-b043-c997f17d8bb4'
);
```

### Cliente PostgreSQL

```python
# app/infraestructure/datalake/client.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import List, Dict, Any

class DataLakeClient:
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
            rows = result.fetchall()

            return [
                {
                    'id': str(row.id),
                    'data': row.data,                    # JSONB parseado
                    'merchant': row.merchant,             # JSONB parseado
                    'transactional_id': str(row.transactional_id),
                    'created_at': row.created_at
                }
                for row in rows
            ]

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

### Worker Simplificado

```python
# app/workers/data_lake_poller.py
import time
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.infraestructure.core.db import engine
from app.infraestructure.datalake.client import DataLakeClient
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

class DataLakePoller:
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
            return

        logger.info(f"⏰ Polling continuo cada {self.poll_interval/3600:.1f} horas")
        while True:
            try:
                self.poll_and_process()
            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
            time.sleep(self.poll_interval)

    def poll_and_process(self):
        """Polling de transacciones"""
        transactions = self.datalake_client.get_unprocessed_transactions(
            limit=self.batch_size
        )

        if not transactions:
            logger.info("✨ No hay transacciones nuevas")
            return

        logger.info(f"📊 Procesando {len(transactions)} transacciones")

        processed_ids = []
        for tx in transactions:
            try:
                self._process_transaction(tx)
                processed_ids.append(tx['id'])
            except Exception as e:
                logger.error(f"Error procesando {tx['id']}: {e}")

        if processed_ids:
            self.datalake_client.mark_as_processed(processed_ids)
            logger.info(f"✅ Procesadas {len(processed_ids)}")

    def _process_transaction(self, transaction: Dict[str, Any]):
        """Procesa una transacción"""
        tx_data = transaction['data']           # JSONB heterogéneo
        merchant = transaction['merchant']      # {id, name, country}
        transactional_id = transaction['transactional_id']

        # Detectar provider desde el campo data
        provider = self._detect_provider(tx_data)

        # Enriquecer con metadata
        enriched_data = {
            'id': transaction['id'],
            'transactional_id': transactional_id,
            'merchant': merchant,
            'raw_data': tx_data
        }

        # Normalizar y guardar en DB principal
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
        if 'type' in data and data['type'] == 'XML_BLOB':
            return 'unknown_xml'
        return 'unknown'


# Main entry point
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit (for cron)")
    args = parser.parse_args()

    datalake_url = os.getenv("DATALAKE_DATABASE_URL")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "43200"))

    poller = DataLakePoller(
        datalake_connection=datalake_url,
        poll_interval=poll_interval,
        run_once=args.once
    )
    poller.run()
```

                session.add(pf)
                session.commit()

                logger.info(f"✅ Processed {len(records)} records from {file_info['key']}")

            except Exception as e:
                pf.processing_status = "failed"
                pf.error_message = str(e)
                session.add(pf)
                session.commit()
                logger.error(f"❌ Failed to process {file_info['key']}: {e}")

if **name** == "**main**":
import os
from dotenv import load_dotenv

    load_dotenv()

    poller = DataLakePoller(
        datalake_url=os.getenv("DATALAKE_BASE_URL"),
        api_key=os.getenv("DATALAKE_API_KEY"),
        poll_interval=int(os.getenv("POLL_INTERVAL_SECONDS", "43200")),  # 12h default
        run_once="--once" in sys.argv
    )
    poller.run()

````

---

## 🧪 Testing con Moto (Mock S3)

```python
# tests/integration/test_data_lake_poller.py
import pytest
from moto import mock_s3
import boto3
import json

@mock_s3
def test_s3_file_detection():
    # Setup mock S3
    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_client.create_bucket(Bucket='test-bucket')

    # Upload test file
    test_data = [
        {"transaction_id": "tx1", "amount": 100.50},
        {"transaction_id": "tx2", "amount": 250.00}
    ]
    s3_client.put_object(
        Bucket='test-bucket',
        Key='raw/test_file.json',
        Body=json.dumps(test_data)
    )

    # Test poller
    from app.workers.data_lake_poller import DataLakePoller
    poller = DataLakePoller(bucket_name='test-bucket', poll_interval=1)

    # List files
    files = poller.s3_client.list_new_files()
    assert len(files) == 1
    assert files[0]['key'] == 'raw/test_file.json'

    # Download and parse
    content = poller.s3_client.download_file_content('raw/test_file.json')
    records = poller.s3_client.parse_json_file(content)
    assert len(records) == 2
    assert records[0]['transaction_id'] == 'tx1'
````

---

## 🔧 Configuración AWS

### IAM Policy Mínima

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetBucketLocation"],
      "Resource": "arn:aws:s3:::yuno-payments-lake"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::yuno-payments-lake/raw-payments/*"
    }
  ]
}
```

### S3 Bucket Structure

```
s3://yuno-payments-lake/
├── raw-payments/           # Input: archivos crudos
│   ├── 2024-12-13/
│   │   ├── transactions_001.json
│   │   ├── transactions_002.jsonl
│   │   └── transactions_003.csv
│   └── 2024-12-14/
│       └── transactions_004.parquet
│
├── processed/              # Output: archivos procesados (opcional)
│   └── 2024-12-13/
│       └── normalized_001.parquet
│
└── failed/                 # Errores (opcional)
    └── 2024-12-13/
        └── error_001.json
```

---

## 📊 Monitoreo

### Queries SQL Útiles

```sql
-- Archivos procesados hoy
SELECT COUNT(*), processing_status
FROM processed_files
WHERE started_at >= CURRENT_DATE
GROUP BY processing_status;

-- Archivos fallidos recientes
SELECT file_path, error_message, started_at
FROM processed_files
WHERE processing_status = 'failed'
ORDER BY started_at DESC
LIMIT 10;

-- Throughput por hora
SELECT
    DATE_TRUNC('hour', completed_at) as hour,
    COUNT(*) as files,
    SUM(records_count) as total_records,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM processed_files
WHERE processing_status = 'completed'
  AND completed_at >= CURRENT_DATE - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;

-- Archivos grandes (> 10 MB)
SELECT file_path, file_size / 1024 / 1024 as size_mb, records_count
FROM processed_files
WHERE file_size > 10485760
ORDER BY file_size DESC
LIMIT 20;
```

### Logs Importantes

```bash
# Filtrar por nivel
grep "ERROR" logs/data_lake_poller.log

# Archivos procesados exitosamente
grep "✅ Processed" logs/data_lake_poller.log

# Archivos fallidos
grep "❌ Failed" logs/data_lake_poller.log

# Latencia de procesamiento
grep "processing_time_ms" logs/data_lake_poller.log | \
  awk '{print $NF}' | \
  sort -n | \
  tail -10
```

---

## 🚀 Deployment

### Systemd Service

```bash
# Crear servicio
sudo nano /etc/systemd/system/data-lake-poller.service

# Contenido:
[Unit]
Description=Yuno Data Lake Poller Worker
After=network.target postgresql.service

[Service]
Type=simple
User=yuno
WorkingDirectory=/opt/yuno-backend
Environment="PATH=/opt/yuno-backend/.venv/bin"
EnvironmentFile=/opt/yuno-backend/.env
ExecStart=/opt/yuno-backend/.venv/bin/python -m app.workers.data_lake_poller
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Habilitar y arrancar
sudo systemctl daemon-reload
sudo systemctl enable data-lake-poller
sudo systemctl start data-lake-poller
sudo systemctl status data-lake-poller
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.8"

services:
  data-lake-poller:
    build: .
    command: python -m app.workers.data_lake_poller
    env_file: .env
    depends_on:
      - postgres
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
```

---

## 🎯 Troubleshooting

### Problema: Worker no detecta archivos nuevos

```bash
# Verificar conexión a S3
aws s3 ls s3://yuno-payments-lake/raw-payments/

# Verificar credenciales
aws sts get-caller-identity

# Verificar logs
tail -f logs/data_lake_poller.log | grep "Found.*files"
```

### Problema: Archivos marcados como fallidos

```sql
-- Ver detalles del error
SELECT object_key, error_message, started_at
FROM processed_files
WHERE processing_status = 'failed'
ORDER BY started_at DESC
LIMIT 5;

-- Reintentar archivo
UPDATE processed_files
SET processing_status = 'pending', error_message = NULL
WHERE object_key = 'raw-payments/2024-12-13/file.json';
```

### Problema: Procesamiento muy lento

```python
# Optimización: procesar en paralelo
from concurrent.futures import ThreadPoolExecutor

def _process_files_parallel(self, files, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(self._process_file, files)
```

---

## 📚 Referencias

- [Documentación completa](./DATA_LAKE_INTEGRATION.md)
- [ROADMAP Fase 4](./ROADMAP.md#fase-4-data-lake-integration)
- [Diagramas](./DIAGRAMS.md#8-data-lake-integration-architecture)
