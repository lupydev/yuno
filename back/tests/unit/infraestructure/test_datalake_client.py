"""Tests unitarios para el cliente del Data Lake"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from app.infraestructure.datalake.client import (
    DataLakeClient,
    DataLakeConnectionError,
    DataLakeQueryError,
)


class TestDataLakeClient:
    """Tests para DataLakeClient"""

    @pytest.fixture
    def mock_connection_url(self):
        """URL de conexión de prueba"""
        return "postgresql://test:test@localhost:5432/test_datalake"

    @pytest.fixture
    def client(self, mock_connection_url):
        """Cliente del data lake para testing"""
        with patch("app.infraestructure.datalake.client.create_engine"):
            return DataLakeClient(mock_connection_url)

    def test_init_success(self, mock_connection_url):
        """Test: Inicialización exitosa del cliente"""
        with patch("app.infraestructure.datalake.client.create_engine") as mock_engine:
            client = DataLakeClient(mock_connection_url)

            assert client is not None
            mock_engine.assert_called_once()
            assert "postgresql://" in mock_connection_url

    def test_init_empty_url_raises_error(self):
        """Test: URL vacía debe lanzar ValueError"""
        with pytest.raises(ValueError, match="connection_url no puede estar vacío"):
            DataLakeClient("")

    def test_init_invalid_url_raises_error(self):
        """Test: URL inválida debe lanzar DataLakeConnectionError"""
        with patch(
            "app.infraestructure.datalake.client.create_engine",
            side_effect=OperationalError("Mock error", None, None),
        ):
            with pytest.raises(DataLakeConnectionError, match="No se pudo conectar al data lake"):
                DataLakeClient("invalid://url")

    def test_get_unprocessed_transactions_success(self, client):
        """Test: Obtener transacciones no procesadas exitosamente"""
        # Mock data
        mock_tx_id = uuid4()
        mock_created_at = datetime.now()

        mock_row = MagicMock()
        mock_row.id = mock_tx_id
        mock_row.payload = {
            "data": {"amt": 100.50, "p_id": "Stripe"},
            "merchant": {"id": str(uuid4()), "name": "Test Store", "country": "CO"},
            "transactional_id": str(uuid4()),
        }
        mock_row.created_at = mock_created_at

        # Mock session con SQLModel
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_result = MagicMock()
            mock_result.all.return_value = [mock_row]
            mock_session_instance.exec.return_value = mock_result

            # Execute
            transactions = client.get_unprocessed_transactions(limit=10)

            # Assertions
            assert len(transactions) == 1
            assert transactions[0]["id"] == str(mock_tx_id)
            assert transactions[0]["payload"]["data"]["amt"] == 100.50
            assert transactions[0]["payload"]["merchant"]["name"] == "Test Store"
            assert transactions[0]["created_at"] == mock_created_at

    def test_get_unprocessed_transactions_empty(self, client):
        """Test: No hay transacciones pendientes"""
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session_instance.exec.return_value = mock_result

            transactions = client.get_unprocessed_transactions()

            assert transactions == []

    def test_get_unprocessed_transactions_query_error(self, client):
        """Test: Error al consultar transacciones"""
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_session_instance.exec.side_effect = OperationalError("DB Error", None, None)

            with pytest.raises(DataLakeQueryError, match="Error al consultar transacciones"):
                client.get_unprocessed_transactions()

    def test_mark_as_processed_success(self, client):
        """Test: Marcar transacciones como procesadas exitosamente"""
        tx_ids = [str(uuid4()), str(uuid4())]

        # Mock transactions
        mock_tx1 = MagicMock()
        mock_tx1.is_processed = False
        mock_tx2 = MagicMock()
        mock_tx2.is_processed = False

        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_result = MagicMock()
            mock_result.all.return_value = [mock_tx1, mock_tx2]
            mock_session_instance.exec.return_value = mock_result

            updated = client.mark_as_processed(tx_ids)

            assert updated == 2
            assert mock_tx1.is_processed is True
            assert mock_tx2.is_processed is True
            mock_session_instance.commit.assert_called_once()

    def test_mark_as_processed_empty_list(self, client):
        """Test: Lista vacía no debe hacer nada"""
        updated = client.mark_as_processed([])

        assert updated == 0

    def test_mark_as_processed_query_error(self, client):
        """Test: Error al marcar como procesadas"""
        tx_ids = [str(uuid4())]

        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            # El error debe ocurrir en session.commit() después de exec()
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session_instance.exec.return_value = mock_result
            mock_session_instance.commit.side_effect = OperationalError("DB Error", None, None)

            with pytest.raises(DataLakeQueryError, match="Error al actualizar transacciones"):
                client.mark_as_processed(tx_ids)

    def test_get_transaction_count_all(self, client):
        """Test: Contar todas las transacciones"""
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_result = MagicMock()
            mock_result.one.return_value = 42
            mock_session_instance.exec.return_value = mock_result

            count = client.get_transaction_count()

            assert count == 42

    def test_get_transaction_count_processed(self, client):
        """Test: Contar transacciones procesadas"""
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_result = MagicMock()
            mock_result.one.return_value = 10
            mock_session_instance.exec.return_value = mock_result

            count = client.get_transaction_count(processed=True)

            assert count == 10

    def test_get_transaction_count_unprocessed(self, client):
        """Test: Contar transacciones no procesadas"""
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_result = MagicMock()
            mock_result.one.return_value = 32
            mock_session_instance.exec.return_value = mock_result

            count = client.get_transaction_count(processed=False)

            assert count == 32

    def test_health_check_success(self, client):
        """Test: Health check exitoso"""
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_result = MagicMock()
            mock_result.one.return_value = 0
            mock_session_instance.exec.return_value = mock_result

            result = client.health_check()

            assert result is True

    def test_health_check_failure(self, client):
        """Test: Health check falla"""
        with patch("app.infraestructure.datalake.client.Session") as mock_session:
            mock_session_instance = mock_session.return_value.__enter__.return_value
            mock_session_instance.exec.side_effect = OperationalError(
                "Connection failed", None, None
            )

            result = client.health_check()

            assert result is False
