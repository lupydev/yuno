"""Tests unitarios para el DataLake Worker"""

from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.infraestructure.kafka.datalake.client import DataLakeQueryError
from app.workers.datalake_worker import DataLakeWorker


class TestDataLakeWorker:
    """Tests para DataLakeWorker"""

    @pytest.fixture
    def mock_datalake_client(self):
        """Mock del DataLake client"""
        return Mock()

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock del orchestrator"""
        mock = Mock()
        mock_event = Mock()
        mock_event.id = uuid4()
        mock_event.status_category = Mock(value="approved")
        mock.ingest.return_value = mock_event
        return mock

    @pytest.fixture
    def mock_orchestrator_factory(self, mock_orchestrator):
        """Factory que retorna el mock orchestrator"""
        return lambda: mock_orchestrator

    @pytest.fixture
    def worker(self, mock_datalake_client, mock_orchestrator_factory):
        """Worker para testing"""
        return DataLakeWorker(
            datalake_client=mock_datalake_client,
            orchestrator_factory=mock_orchestrator_factory,
            interval_seconds=60,
        )

    def test_init_success(self, mock_datalake_client, mock_orchestrator_factory):
        """Test: Inicialización exitosa del worker"""
        worker = DataLakeWorker(
            datalake_client=mock_datalake_client,
            orchestrator_factory=mock_orchestrator_factory,
            interval_seconds=120,
        )

        assert worker.datalake_client == mock_datalake_client
        assert worker.orchestrator_factory == mock_orchestrator_factory
        assert worker.interval_seconds == 120
        assert worker.scheduler is not None

    def test_process_batch_no_transactions(self, worker, mock_datalake_client):
        """Test: No hay transacciones para procesar"""
        mock_datalake_client.get_unprocessed_transactions.return_value = []

        worker._process_batch()

        # Debe obtener transacciones pero no procesar nada
        mock_datalake_client.get_unprocessed_transactions.assert_called_once_with(limit=100)
        mock_datalake_client.mark_as_processed.assert_not_called()

    def test_process_batch_success(self, worker, mock_datalake_client, mock_orchestrator_factory):
        """Test: Procesamiento exitoso de transacciones"""
        # Mock transactions
        transaction = {
            "id": str(uuid4()),
            "payload": {
                "data": {"amt": 100.50, "p_id": "Stripe"},
                "merchant": {"id": str(uuid4()), "name": "Test Store", "country": "CO"},
                "transactional_id": str(uuid4()),
            },
            "created_at": datetime.now(),
        }

        mock_datalake_client.get_unprocessed_transactions.return_value = [transaction]

        # Execute
        worker._process_batch()

        # Assertions
        mock_datalake_client.get_unprocessed_transactions.assert_called_once_with(limit=100)

        # Debe haber intentado procesar la transacción
        mock_orchestrator = mock_orchestrator_factory()
        mock_orchestrator.ingest.assert_called_once()

        # Debe marcar como procesada
        mock_datalake_client.mark_as_processed.assert_called_once_with([transaction["id"]])

    def test_process_batch_multiple_transactions(
        self, worker, mock_datalake_client, mock_orchestrator_factory
    ):
        """Test: Procesamiento de múltiples transacciones"""
        transactions = [
            {
                "id": str(uuid4()),
                "payload": {
                    "data": {"amt": 100.50},
                    "merchant": {"id": str(uuid4()), "name": "Store 1", "country": "CO"},
                    "transactional_id": str(uuid4()),
                },
                "created_at": datetime.now(),
            },
            {
                "id": str(uuid4()),
                "payload": {
                    "data": {"amt": 200.00},
                    "merchant": {"id": str(uuid4()), "name": "Store 2", "country": "US"},
                    "transactional_id": str(uuid4()),
                },
                "created_at": datetime.now(),
            },
        ]

        mock_datalake_client.get_unprocessed_transactions.return_value = transactions

        worker._process_batch()

        # Debe haber procesado ambas transacciones
        mock_orchestrator = mock_orchestrator_factory()
        assert mock_orchestrator.ingest.call_count == 2

        # Debe marcar ambas como procesadas
        processed_ids = [t["id"] for t in transactions]
        mock_datalake_client.mark_as_processed.assert_called_once_with(processed_ids)

    def test_process_batch_handles_normalization_error(
        self, worker, mock_datalake_client, mock_orchestrator_factory
    ):
        """Test: Manejo de error durante normalización"""
        transaction = {
            "id": str(uuid4()),
            "payload": {
                "data": {"invalid": "data"},
                "merchant": {"id": str(uuid4()), "name": "Test Store", "country": "CO"},
                "transactional_id": str(uuid4()),
            },
            "created_at": datetime.now(),
        }

        mock_datalake_client.get_unprocessed_transactions.return_value = [transaction]

        # Mock error en normalización
        mock_orchestrator = mock_orchestrator_factory()
        mock_orchestrator.ingest.side_effect = Exception("Normalization failed")

        # No debe lanzar excepción, solo logear
        worker._process_batch()

        # No debe marcar como procesada si falló
        mock_datalake_client.mark_as_processed.assert_not_called()

    def test_process_batch_partial_failure(
        self, worker, mock_datalake_client, mock_orchestrator_factory
    ):
        """Test: Algunas transacciones fallan, otras se procesan"""
        tx_success_1 = {
            "id": str(uuid4()),
            "payload": {
                "data": {"amt": 100.50},
                "merchant": {"id": str(uuid4()), "name": "Store 1", "country": "CO"},
                "transactional_id": str(uuid4()),
            },
            "created_at": datetime.now(),
        }

        tx_fail = {
            "id": str(uuid4()),
            "payload": {
                "data": {"invalid": "data"},
                "merchant": {"id": str(uuid4()), "name": "Store 2", "country": "US"},
                "transactional_id": str(uuid4()),
            },
            "created_at": datetime.now(),
        }

        tx_success_2 = {
            "id": str(uuid4()),
            "payload": {
                "data": {"amt": 300.00},
                "merchant": {"id": str(uuid4()), "name": "Store 3", "country": "PE"},
                "transactional_id": str(uuid4()),
            },
            "created_at": datetime.now(),
        }

        mock_datalake_client.get_unprocessed_transactions.return_value = [
            tx_success_1,
            tx_fail,
            tx_success_2,
        ]

        # Segunda transacción falla
        mock_orchestrator = mock_orchestrator_factory()
        mock_orchestrator.ingest.side_effect = [
            Mock(id=uuid4(), status_category=Mock(value="approved")),  # Success
            Exception("Failed"),  # Error
            Mock(id=uuid4(), status_category=Mock(value="pending")),  # Success
        ]

        worker._process_batch()

        # Solo debe marcar las 2 exitosas
        mock_datalake_client.mark_as_processed.assert_called_once_with(
            [tx_success_1["id"], tx_success_2["id"]]
        )

    def test_process_batch_handles_datalake_fetch_error(self, worker, mock_datalake_client):
        """Test: Error al obtener transacciones del Data Lake"""
        mock_datalake_client.get_unprocessed_transactions.side_effect = DataLakeQueryError(
            "Connection failed"
        )

        # No debe lanzar excepción, solo logear
        worker._process_batch()

        # No debe intentar marcar nada
        mock_datalake_client.mark_as_processed.assert_not_called()

    def test_process_batch_handles_mark_as_processed_error(
        self, worker, mock_datalake_client, mock_orchestrator_factory
    ):
        """Test: Error al marcar como procesadas"""
        transaction = {
            "id": str(uuid4()),
            "payload": {
                "data": {"amt": 100.50},
                "merchant": {"id": str(uuid4()), "name": "Test Store", "country": "CO"},
                "transactional_id": str(uuid4()),
            },
            "created_at": datetime.now(),
        }

        mock_datalake_client.get_unprocessed_transactions.return_value = [transaction]
        mock_datalake_client.mark_as_processed.side_effect = DataLakeQueryError("Update failed")

        # No debe lanzar excepción, solo logear
        worker._process_batch()

        # Debe haber intentado normalizar
        mock_orchestrator = mock_orchestrator_factory()
        mock_orchestrator.ingest.assert_called_once()

    def test_process_batch_enriches_raw_event(
        self, worker, mock_datalake_client, mock_orchestrator_factory
    ):
        """Test: El worker enriquece el raw_event con metadata del payload"""
        merchant_id = str(uuid4())
        transactional_id = str(uuid4())

        transaction = {
            "id": str(uuid4()),
            "payload": {
                "data": {"amt": 100.50, "p_id": "Stripe"},
                "merchant": {"id": merchant_id, "name": "Test Store", "country": "CO"},
                "transactional_id": transactional_id,
            },
            "created_at": datetime.now(),
        }

        mock_datalake_client.get_unprocessed_transactions.return_value = [transaction]

        worker._process_batch()

        # Verificar que el raw_event pasado al orchestrator tiene la metadata
        mock_orchestrator = mock_orchestrator_factory()
        call_args = mock_orchestrator.ingest.call_args

        raw_event = call_args.kwargs["raw_event"]
        assert raw_event["transactional_id"] == transactional_id
        assert raw_event["merchant_id"] == merchant_id
        assert raw_event["merchant_name"] == "Test Store"
        assert raw_event["merchant_country"] == "CO"
        assert raw_event["amt"] == 100.50  # Del data original

    def test_start_configures_scheduler(self, worker):
        """Test: start() configura y arranca el scheduler"""
        with patch.object(worker.scheduler, "add_job") as mock_add_job:
            with patch.object(worker.scheduler, "start") as mock_start:
                worker.start()

                # Debe agregar el job
                mock_add_job.assert_called_once()
                call_args = mock_add_job.call_args
                assert call_args.kwargs["func"] == worker._process_batch
                assert call_args.kwargs["id"] == "datalake_batch_processor"

                # Debe arrancar el scheduler
                mock_start.assert_called_once()

    def test_stop_shuts_down_scheduler(self, worker):
        """Test: stop() detiene el scheduler"""
        with patch.object(worker.scheduler, "shutdown") as mock_shutdown:
            worker.stop()

            mock_shutdown.assert_called_once_with(wait=True)
