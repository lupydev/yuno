# 🚀 Data Lake Integration - Próximos Pasos

## ✅ Estado Actual

- **Data lake desplegado** ✓
- **Datos cargados** ✓
- **Documentación completa** ✓

---

## 📋 Pasos para Implementar

### 1️⃣ Configurar Conexión (5 min)

```bash
# Agregar credenciales a .env
cat >> .env << EOF
DATALAKE_DATABASE_URL=postgresql://USER:PASS@HOST:PORT/DATABASE
POLL_INTERVAL_SECONDS=43200
EOF
```

**Reemplaza**:

- `USER:PASS`: Credenciales del data lake
- `HOST:PORT`: Host y puerto de la DB
- `DATABASE`: Nombre de la base de datos

### 2️⃣ Verificar Conexión (2 min)

```bash
# Probar conexión
psql $DATALAKE_DATABASE_URL -c "\dt"

# Ver datos disponibles
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*) FROM raw_transactions WHERE processed = false;"

# Ver muestra de datos
psql $DATALAKE_DATABASE_URL -c "SELECT id, merchant->>'name' as merchant, transactional_id FROM raw_transactions LIMIT 3;"
```

### 3️⃣ Implementar Cliente (30 min)

Crear: `app/infraestructure/datalake/client.py`

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

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
            rows = result.fetchall()

            return [
                {
                    'id': str(row.id),
                    'data': row.data,
                    'merchant': row.merchant,
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
            logger.info(f"✅ Marcadas {len(transaction_ids)} transacciones como procesadas")
```

### 4️⃣ Implementar Worker (1 hora)

Crear: `app/workers/data_lake_poller.py`

```python
import time
import logging
import argparse
import os
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
        poll_interval: int = 43200,
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

        # 3. Marcar como procesadas en el data lake
        if processed_ids:
            self.datalake_client.mark_as_processed(processed_ids)
            logger.info(f"✅ Procesadas {len(processed_ids)} transacciones")

    def _process_transaction(self, transaction: Dict[str, Any]):
        """Procesa una transacción individual"""
        tx_data = transaction['data']
        merchant = transaction['merchant']
        transactional_id = transaction['transactional_id']

        # Detectar provider del campo data
        provider = self._detect_provider(tx_data)

        logger.info(f"🔄 Procesando transaction {transactional_id} from {provider}")
        logger.info(f"   Merchant: {merchant.get('name')} ({merchant.get('country')})")

        # Enriquecer con metadata
        enriched_data = {
            'id': transaction['id'],
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
        if 'provider' in data:
            return data['provider'].lower()
        if 'p_id' in data:
            return data['p_id'].lower()
        if 'type' in data and data['type'] == 'XML_BLOB':
            return 'unknown_xml'

        return 'unknown'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit (for cron)")
    args = parser.parse_args()

    datalake_url = os.getenv("DATALAKE_DATABASE_URL")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "43200"))

    if not datalake_url:
        raise ValueError("DATALAKE_DATABASE_URL no configurado en .env")

    poller = DataLakePoller(
        datalake_connection=datalake_url,
        poll_interval=poll_interval,
        run_once=args.once
    )

    poller.run()
```

### 5️⃣ Testing (15 min)

```bash
# 1. Ejecutar worker una vez
python -m app.workers.data_lake_poller --once

# 2. Ver logs
tail -f logs/data_lake_poller.log

# 3. Verificar procesamiento en data lake
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*) FROM raw_transactions WHERE processed = true;"

# 4. Verificar datos normalizados en DB principal
psql $DATABASE_URL -c "SELECT COUNT(*) FROM normalized_payment_events;"
```

### 6️⃣ Desplegar en Producción (10 min)

**Opción A: Cron (Recomendado para hackathon)**

```bash
# Agregar a crontab (ejecutar 2 veces al día: 00:00 y 12:00)
crontab -e

# Agregar línea:
0 0,12 * * * cd /path/to/yuno/back && .venv/bin/python -m app.workers.data_lake_poller --once >> /var/log/yuno-poller.log 2>&1
```

**Opción B: Systemd (Para servidor)**

```bash
# Crear servicio
sudo nano /etc/systemd/system/data-lake-poller.service

# Contenido:
[Unit]
Description=Yuno Data Lake Poller
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/yuno/back
Environment="PATH=/path/to/yuno/back/.venv/bin"
ExecStart=/path/to/yuno/back/.venv/bin/python -m app.workers.data_lake_poller
Restart=always

[Install]
WantedBy=multi-user.target

# Habilitar
sudo systemctl enable data-lake-poller
sudo systemctl start data-lake-poller
```

---

## 📊 Monitoreo

### Ver Estado

```bash
# Transacciones pendientes
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*) FROM raw_transactions WHERE processed = false;"

# Transacciones procesadas hoy
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*) FROM raw_transactions WHERE processed = true AND processed_at::date = CURRENT_DATE;"

# Últimas 10 procesadas
psql $DATALAKE_DATABASE_URL -c "SELECT id, merchant->>'name' as merchant, processed_at FROM raw_transactions WHERE processed = true ORDER BY processed_at DESC LIMIT 10;"
```

### Ver Logs

```bash
# Logs en tiempo real
tail -f logs/data_lake_poller.log

# Logs de cron
tail -f /var/log/yuno-poller.log

# Logs de systemd
sudo journalctl -u data-lake-poller -f
```

---

## 🔧 Troubleshooting

### Error de Conexión

```bash
# Verificar conectividad
psql $DATALAKE_DATABASE_URL -c "SELECT version();"

# Verificar que la tabla existe
psql $DATALAKE_DATABASE_URL -c "\d raw_transactions"
```

### No Hay Datos

```bash
# Verificar que hay datos no procesados
psql $DATALAKE_DATABASE_URL -c "SELECT COUNT(*), processed FROM raw_transactions GROUP BY processed;"
```

### Provider No Detectado

Revisar el método `_detect_provider()` y agregar más lógica según los campos disponibles en tus datos.

---

## 📚 Documentación Completa

- **Guía completa**: [DATA_LAKE_INTEGRATION.md](./DATA_LAKE_INTEGRATION.md)
- **Quick reference**: [DATA_LAKE_QUICKREF.md](./DATA_LAKE_QUICKREF.md)
- **Roadmap**: [ROADMAP.md](./ROADMAP.md#fase-4-data-lake-integration)

---

## ⏱ Tiempo Total Estimado

- Configuración: **5 min**
- Verificación: **2 min**
- Cliente: **30 min**
- Worker: **1 hora**
- Testing: **15 min**
- Deploy: **10 min**

**Total: ~2 horas** 🚀
