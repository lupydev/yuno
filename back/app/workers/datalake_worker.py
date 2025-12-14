"""
Data Lake Worker

Worker que consulta el Data Lake cada minuto para procesar
transacciones nuevas (no procesadas) y normalizarlas.

Usa APScheduler para ejecutar de forma periódica en background.
"""

import logging
from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.infraestructure.core.config import settings
from app.infraestructure.datalake.client import DataLakeClient, DataLakeQueryError
from app.services.ingestion_orchestrator import IngestionOrchestrator

logger = logging.getLogger(__name__)


# Type alias para la factory function
OrchestratorFactory = Callable[[], IngestionOrchestrator]


class DataLakeWorker:
    """
    Worker para procesar transacciones del Data Lake

    Responsabilidades:
    - Consultar Data Lake cada minuto
    - Obtener solo transacciones no procesadas
    - Normalizar usando IngestionOrchestrator
    - Marcar como procesadas en Data Lake
    - Manejo robusto de errores
    """

    def __init__(
        self,
        datalake_client: DataLakeClient,
        orchestrator_factory: OrchestratorFactory,
        interval_seconds: int = 60,
    ) -> None:
        """
        Inicializa el worker con inyección de dependencias

        Args:
            datalake_client: Cliente del Data Lake
            orchestrator_factory: Factory function que crea un IngestionOrchestrator
            interval_seconds: Intervalo de ejecución en segundos (default: 60)
        """
        self.datalake_client = datalake_client
        self.orchestrator_factory = orchestrator_factory
        self.interval_seconds = interval_seconds
        self.scheduler = BackgroundScheduler()

        logger.info(
            "DataLakeWorker initialized",
            extra={
                "interval_seconds": interval_seconds,
            },
        )

    def _process_batch(self) -> None:
        """
        Procesa un batch de transacciones del Data Lake

        Flujo:
        1. Obtener transacciones no procesadas
        2. Para cada transacción:
           - Normalizar usando orchestrator
           - Persistir en DB
           - Marcar como procesada en Data Lake
        3. Logging de métricas

        Este método se ejecuta cada minuto automáticamente.
        """
        logger.info("Starting Data Lake batch processing...")

        try:
            # 1. Obtener transacciones no procesadas
            transactions = self.datalake_client.get_unprocessed_transactions(limit=100)

            if not transactions:
                logger.debug("No unprocessed transactions found")
                return

            logger.info(
                f"Found {len(transactions)} unprocessed transactions",
                extra={"count": len(transactions)},
            )

            # Contadores para métricas
            processed_count = 0
            error_count = 0
            processed_ids: list[str] = []

            # 2. Procesar cada transacción
            for transaction in transactions:
                try:
                    # Crear orchestrator usando la factory (ya tiene session inyectada)
                    orchestrator = self.orchestrator_factory()

                    # Extraer información del payload
                    payload = transaction["payload"]

                    # El payload contiene: {data, merchant, transactional_id, id}
                    # La IA debe normalizar solo "data" (la parte heterogénea)
                    raw_event = payload.get("data", {})
                    merchant_info = payload.get("merchant", {})
                    transactional_id = payload.get("transactional_id")

                    # Enriquecer raw_event con metadata del payload
                    raw_event["transactional_id"] = transactional_id
                    raw_event["merchant_id"] = merchant_info.get("id")
                    raw_event["merchant_name"] = merchant_info.get("name")
                    raw_event["merchant_country"] = merchant_info.get("country")

                    # Normalizar y persistir
                    # La IA se enfocará en normalizar el campo "data" heterogéneo
                    normalized_event = orchestrator.ingest(
                        raw_event=raw_event,
                        provider_hint=raw_event.get("audit", {}).get("gw"),  # Hint: gateway name
                    )

                    # Guardar ID para marcar como procesado
                    processed_ids.append(transaction["id"])
                    processed_count += 1

                    logger.debug(
                        "Transaction processed successfully",
                        extra={
                            "transaction_id": transaction["id"],
                            "event_id": str(normalized_event.id),
                            "status": normalized_event.status_category.value,
                            "gateway": raw_event.get("audit", {}).get("gw"),
                        },
                    )

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "Failed to process transaction",
                        extra={
                            "transaction_id": transaction.get("id"),
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        exc_info=True,
                    )
                    # Continuar con la siguiente transacción

            # 3. Marcar como procesadas en Data Lake
            if processed_ids:
                try:
                    self.datalake_client.mark_as_processed(processed_ids)
                    logger.info(
                        f"Marked {len(processed_ids)} transactions as processed in Data Lake"
                    )
                except DataLakeQueryError as e:
                    logger.error(
                        "Failed to mark transactions as processed in Data Lake",
                        extra={"error": str(e), "count": len(processed_ids)},
                        exc_info=True,
                    )

            # 4. Log de métricas
            logger.info(
                "Batch processing completed",
                extra={
                    "total": len(transactions),
                    "processed": processed_count,
                    "errors": error_count,
                },
            )

        except DataLakeQueryError as e:
            logger.error(
                "Failed to fetch transactions from Data Lake",
                extra={"error": str(e)},
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                "Unexpected error during batch processing",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

    def start(self) -> None:
        """
        Inicia el worker

        Configura el scheduler para ejecutar cada minuto
        y arranca el scheduler en background.

        Ejemplo:
            ```python
            worker = DataLakeWorker(datalake_client)
            worker.start()
            # Worker corre en background cada minuto
            ```
        """
        # Configurar job para ejecutar cada minuto
        self.scheduler.add_job(
            func=self._process_batch,
            trigger=IntervalTrigger(seconds=self.interval_seconds),
            id="datalake_batch_processor",
            name="Data Lake Batch Processor",
            replace_existing=True,
            max_instances=1,  # Solo una instancia corriendo a la vez
        )

        # Arrancar scheduler
        self.scheduler.start()

        logger.info(
            "DataLakeWorker started",
            extra={
                "interval_seconds": self.interval_seconds,
                "job_id": "datalake_batch_processor",
            },
        )

    def stop(self) -> None:
        """
        Detiene el worker

        Ejemplo:
            ```python
            worker.stop()
            ```
        """
        self.scheduler.shutdown(wait=True)
        logger.info("DataLakeWorker stopped")

    def run_once(self) -> None:
        """
        Ejecuta una sola vez el procesamiento (útil para testing)

        Ejemplo:
            ```python
            worker = DataLakeWorker(datalake_client)
            worker.run_once()  # Procesa batch y termina
            ```
        """
        logger.info("Running Data Lake batch processing (one-time)")
        self._process_batch()


def create_datalake_worker() -> DataLakeWorker:
    """
    Factory para crear DataLakeWorker con configuración de settings

    Usa inyección de dependencias para crear todas las dependencias necesarias.

    Returns:
        DataLakeWorker configurado y listo para usar

    Ejemplo:
        ```python
        worker = create_datalake_worker()
        worker.start()
        ```
    """
    from app.domain.normalizers.ai_normalizer import AIBasedNormalizer
    from app.domain.normalizers.rule_normalizer import RuleBasedNormalizer
    from app.infraestructure.core.db import get_session_context
    from app.infraestructure.repositories.payment_repository import PaymentRepository

    # Factory function que crea un orchestrator con session fresca
    def create_orchestrator() -> IngestionOrchestrator:
        """Crea un orchestrator con todas sus dependencias"""
        session = get_session_context()
        repository = PaymentRepository(session)
        rule_normalizer = RuleBasedNormalizer()
        ai_normalizer = AIBasedNormalizer()

        return IngestionOrchestrator(
            repository=repository,
            rule_normalizer=rule_normalizer,
            ai_normalizer=ai_normalizer,
        )

    datalake_client = DataLakeClient(connection_url=settings.DATA_LAKE_URI)

    return DataLakeWorker(
        datalake_client=datalake_client,
        orchestrator_factory=create_orchestrator,
        interval_seconds=60,  # Cada minuto
    )
