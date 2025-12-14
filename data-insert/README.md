# Data Insert Scripts

Scripts para generar e insertar datos de prueba en la base de datos PostgreSQL.

## Archivos

- `db_injector.py` - Genera datos RAW de pagos sin normalizar
- `normalized_db_injector.py` - Genera datos de pagos NORMALIZADOS
- `models.py` - Modelo SQLModel para eventos normalizados
- `enums.py` - Enumeraciones para estados y razones de fallo

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Generar datos RAW (formato original)

```bash
python db_injector.py
```

Genera 3000 registros en formato RAW con diferentes formatos (modern, legacy, nested, xml).

### Generar datos NORMALIZADOS

```bash
python normalized_db_injector.py
```

Genera 2000 registros normalizados siguiendo el esquema `NormalizedPaymentEvent`:

**Características:**
- ✅ Datos realistas de múltiples providers (Stripe, Adyen, PayU, etc.)
- ✅ Distribución realista de estados (60% aprobados, 20% fallidos, etc.)
- ✅ Razones de fallo específicas y consistentes
- ✅ Metadata completa (raw_data, event_metadata)
- ✅ Diferentes métodos de normalización (RULE_BASED, ML_MODEL, HYBRID)
- ✅ Confidence scores variables según el caso
- ✅ Latencias realistas (más altas para timeouts)

**Distribución de Estados:**
- APPROVED: 60%
- FAILED: 20%
- ERROR: 10%
- PENDING: 5%
- CANCELLED: 3%
- REFUNDED: 2%

## Configuración

Las URLs de base de datos están configuradas dentro de cada script:

- `db_injector.py`: Base de datos RAW
- `normalized_db_injector.py`: Base de datos normalizada (Railway PostgreSQL)

Para cambiar la cantidad de registros, modifica la variable `TOTAL_RECORDS` en cada script.

## Esquema de Datos Normalizados

El modelo `NormalizedPaymentEvent` incluye:

### Campos Principales
- `merchant_name`: Nombre del comercio
- `provider`: Proveedor de pago (stripe, adyen, etc.)
- `country`: Código ISO del país (MX, CO, PE, etc.)
- `status_category`: Estado normalizado (APPROVED, FAILED, ERROR, etc.)
- `failure_reason`: Razón específica de fallo (si aplica)

### Datos Financieros
- `amount`: Monto de la transacción
- `currency`: Moneda ISO (USD, MXN, EUR, etc.)

### Detalles del Provider
- `provider_transaction_id`: ID original del provider
- `provider_status`: Status original del provider
- `latency_ms`: Latencia en milisegundos

### Metadata de Normalización
- `raw_data`: Datos originales del evento (JSONB)
- `normalization_method`: Método usado (RULE_BASED, ML_MODEL, HYBRID)
- `confidence_score`: Score de confianza (0-1)
- `event_metadata`: Metadata adicional (JSONB)

### Timestamps
- `created_at`: Cuando se creó el evento
- `normalized_at`: Cuando se normalizó
- `updated_at`: Última actualización

## Índices de Base de Datos

El modelo incluye índices optimizados para queries comunes:
- `idx_created_at`: Búsquedas por fecha
- `idx_provider_status`: Filtrado por provider y status
- `idx_merchant_country`: Análisis por merchant y país
- `idx_analytics`: Queries analíticas complejas
