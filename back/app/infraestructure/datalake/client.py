"""Cliente para interactuar con la base de datos del Data Lake"""

import logging
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.domain.models.raw_payment import RawPaymentIngestion

logger = logging.getLogger(__name__)


class DataLakeConnectionError(Exception):
    """Error al conectarse al data lake"""

    pass


class DataLakeQueryError(Exception):
    """Error al ejecutar query en el data lake"""

    pass


class DataLakeClient:
    """Cliente para leer transacciones del data lake (PostgreSQL externo)"""

    def __init__(self, connection_url: str):
        """
        Inicializa el cliente del data lake

        Args:
            connection_url: URL de conexión PostgreSQL
                Formato: postgresql://user:pass@host:port/database
        """
        if not connection_url:
            raise ValueError("connection_url no puede estar vacío")

        try:
            # Usar postgresql+psycopg (mismo driver que el resto de la app)
            if connection_url.startswith("postgresql://"):
                connection_url = connection_url.replace("postgresql://", "postgresql+psycopg://")

            self.engine: Engine = create_engine(
                connection_url, pool_pre_ping=True, pool_size=5, max_overflow=10
            )
            logger.info("✅ DataLakeClient inicializado correctamente")
        except SQLAlchemyError as e:
            logger.error(f"❌ Error al crear engine del data lake: {e}")
            raise DataLakeConnectionError(f"No se pudo conectar al data lake: {e}") from e

    def get_unprocessed_transactions(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Obtiene transacciones no procesadas del data lake usando SQLModel

        Args:
            limit: Número máximo de transacciones a obtener

        Returns:
            Lista de transacciones como diccionarios con campos:
            - id (str): UUID del registro
            - payload (dict): Payload completo del JSONB que contiene:
                - data (dict): Datos heterogéneos de la transacción (ESTO es lo que la IA debe normalizar)
                - merchant (dict): Información del merchant {id, name, country}
                - transactional_id (str): UUID de la transacción
            - created_at (datetime): Timestamp de creación

        Raises:
            DataLakeQueryError: Si hay un error al ejecutar la query
        """
        try:
            with Session(self.engine) as session:
                # Query usando SQLModel
                statement = (
                    select(RawPaymentIngestion)
                    .where(RawPaymentIngestion.is_processed == False)
                    .order_by(RawPaymentIngestion.created_at)
                    .limit(limit)
                )

                rows = session.exec(statement).all()

                transactions = [
                    {
                        "id": str(row.id),
                        "payload": row.payload,  # JSONB completo
                        "created_at": row.created_at,
                    }
                    for row in rows
                ]

                logger.info(f"📊 Obtenidas {len(transactions)} transacciones no procesadas")
                return transactions

        except SQLAlchemyError as e:
            logger.error(f"❌ Error al obtener transacciones: {e}")
            raise DataLakeQueryError(f"Error al consultar transacciones no procesadas: {e}") from e

    def mark_as_processed(self, transaction_ids: list[str]) -> int:
        """
        Marca transacciones como procesadas en el data lake usando SQLModel

        Args:
            transaction_ids: Lista de UUIDs de transacciones a marcar

        Returns:
            Número de transacciones actualizadas

        Raises:
            DataLakeQueryError: Si hay un error al ejecutar la query
        """
        if not transaction_ids:
            logger.warning("⚠️  Lista de transaction_ids vacía, no se marcó nada")
            return 0

        try:
            with Session(self.engine) as session:
                # Obtener las transacciones a actualizar
                statement = select(RawPaymentIngestion).where(
                    RawPaymentIngestion.id.in_(transaction_ids)
                )
                transactions = session.exec(statement).all()

                # Marcar como procesadas
                for transaction in transactions:
                    transaction.is_processed = True

                session.commit()

                updated_count = len(transactions)
                logger.info(f"✅ Marcadas {updated_count} transacciones como procesadas")
                return updated_count

        except SQLAlchemyError as e:
            logger.error(f"❌ Error al marcar transacciones como procesadas: {e}")
            raise DataLakeQueryError(
                f"Error al actualizar transacciones como procesadas: {e}"
            ) from e

    def get_transaction_count(self, processed: bool | None = None) -> int:
        """
        Obtiene el conteo de transacciones en el data lake usando SQLModel

        Args:
            processed: Si es True, cuenta procesadas. Si es False, cuenta no procesadas.
                      Si es None, cuenta todas.

        Returns:
            Número total de transacciones

        Raises:
            DataLakeQueryError: Si hay un error al ejecutar la query
        """
        try:
            with Session(self.engine) as session:
                from sqlalchemy import func

                statement = select(func.count()).select_from(RawPaymentIngestion)

                if processed is not None:
                    statement = statement.where(RawPaymentIngestion.is_processed == processed)

                count = session.exec(statement).one()
                return count or 0

        except SQLAlchemyError as e:
            logger.error(f"❌ Error al contar transacciones: {e}")
            raise DataLakeQueryError(f"Error al contar transacciones: {e}") from e

    def health_check(self) -> bool:
        """
        Verifica la conexión con el data lake usando SQLModel

        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            with Session(self.engine) as session:
                from sqlalchemy import func

                # Simple query para verificar conexión
                session.exec(select(func.count()).select_from(RawPaymentIngestion)).one()
                logger.info("✅ Health check exitoso")
                return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Health check falló: {e}")
            return False
