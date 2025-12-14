"""
Unit tests for PaymentRepository

Tests para validar CRUD operations del repositorio de pagos
"""

from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.domain.models.enums import NormalizationMethod, PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.infraestructure.repositories.payment_repository import PaymentRepository


@pytest.fixture
def mock_session():
    """Mock de SQLModel Session"""
    return Mock(spec=Session)


@pytest.fixture
def repository(mock_session):
    """Repository con session mock"""
    return PaymentRepository(session=mock_session)


@pytest.fixture
def sample_event():
    """Evento de ejemplo para tests"""
    return NormalizedPaymentEvent(
        merchant_name="Test Merchant",
        provider="TestProvider",
        country="US",
        status_category=PaymentStatus.APPROVED,
        amount=Decimal("100.00"),
        currency="USD",
        raw_data={"test": "data"},
        normalization_method=NormalizationMethod.RULE_BASED,
    )


class TestPaymentRepositoryInit:
    """Tests de inicialización"""

    def test_initialization(self, mock_session):
        """Debe inicializar correctamente con session"""
        repo = PaymentRepository(session=mock_session)

        assert repo.session == mock_session


class TestSave:
    """Tests para save()"""

    def test_save_adds_event_to_session(self, repository, sample_event, mock_session):
        """Debe agregar evento a la sesión"""
        repository.save(sample_event)

        mock_session.add.assert_called_once_with(sample_event)

    def test_save_commits_transaction(self, repository, sample_event, mock_session):
        """Debe hacer commit de la transacción"""
        repository.save(sample_event)

        mock_session.commit.assert_called_once()

    def test_save_refreshes_event(self, repository, sample_event, mock_session):
        """Debe refrescar el evento después del commit"""
        repository.save(sample_event)

        mock_session.refresh.assert_called_once_with(sample_event)

    def test_save_returns_event(self, repository, sample_event):
        """Debe retornar el evento guardado"""
        result = repository.save(sample_event)

        assert result == sample_event

    def test_save_sequence_is_correct(self, repository, sample_event, mock_session):
        """Debe ejecutar add → commit → refresh en orden"""
        manager = Mock()
        manager.attach_mock(mock_session.add, "add")
        manager.attach_mock(mock_session.commit, "commit")
        manager.attach_mock(mock_session.refresh, "refresh")

        repository.save(sample_event)

        # Verificar orden de llamadas
        assert manager.mock_calls[0][0] == "add"
        assert manager.mock_calls[1][0] == "commit"
        assert manager.mock_calls[2][0] == "refresh"


class TestGetById:
    """Tests para get_by_id()"""

    def test_get_by_id_executes_query(self, repository, mock_session):
        """Debe ejecutar query con el ID correcto"""
        event_id = uuid4()
        mock_result = Mock()
        mock_result.one_or_none.return_value = None
        mock_session.exec.return_value = mock_result

        repository.get_by_id(event_id)

        mock_session.exec.assert_called_once()

    def test_get_by_id_returns_event_when_found(self, repository, sample_event, mock_session):
        """Debe retornar evento cuando existe"""
        event_id = uuid4()
        sample_event.id = event_id

        mock_result = Mock()
        mock_result.one_or_none.return_value = sample_event
        mock_session.exec.return_value = mock_result

        result = repository.get_by_id(event_id)

        assert result == sample_event
        assert result.id == event_id

    def test_get_by_id_returns_none_when_not_found(self, repository, mock_session):
        """Debe retornar None cuando no existe"""
        event_id = uuid4()

        mock_result = Mock()
        mock_result.one_or_none.return_value = None
        mock_session.exec.return_value = mock_result

        result = repository.get_by_id(event_id)

        assert result is None


class TestGetByProviderTransactionId:
    """Tests para get_by_provider_transaction_id()"""

    def test_get_by_provider_transaction_id_executes_query(self, repository, mock_session):
        """Debe ejecutar query con el provider_transaction_id"""
        mock_result = Mock()
        mock_result.one_or_none.return_value = None
        mock_session.exec.return_value = mock_result

        repository.get_by_provider_transaction_id("tx_123")

        mock_session.exec.assert_called_once()

    def test_get_by_provider_transaction_id_returns_event(
        self, repository, sample_event, mock_session
    ):
        """Debe retornar evento cuando existe"""
        sample_event.provider_transaction_id = "tx_123"

        mock_result = Mock()
        mock_result.one_or_none.return_value = sample_event
        mock_session.exec.return_value = mock_result

        result = repository.get_by_provider_transaction_id("tx_123")

        assert result == sample_event
        assert result.provider_transaction_id == "tx_123"

    def test_get_by_provider_transaction_id_returns_none(self, repository, mock_session):
        """Debe retornar None cuando no existe"""
        mock_result = Mock()
        mock_result.one_or_none.return_value = None
        mock_session.exec.return_value = mock_result

        result = repository.get_by_provider_transaction_id("nonexistent")

        assert result is None


class TestGetUnprocessed:
    """Tests para get_unprocessed()"""

    def test_get_unprocessed_with_default_limit(self, repository, mock_session):
        """Debe usar limit default de 100"""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        repository.get_unprocessed()

        mock_session.exec.assert_called_once()

    def test_get_unprocessed_with_custom_limit(self, repository, mock_session):
        """Debe respetar limit custom"""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        repository.get_unprocessed(limit=50)

        mock_session.exec.assert_called_once()

    def test_get_unprocessed_returns_events(self, repository, sample_event, mock_session):
        """Debe retornar lista de eventos"""
        events = [sample_event, sample_event]

        mock_result = Mock()
        mock_result.all.return_value = events
        mock_session.exec.return_value = mock_result

        result = repository.get_unprocessed()

        assert result == events
        assert len(result) == 2


class TestGetByFilters:
    """Tests para get_by_filters()"""

    def test_get_by_filters_without_filters(self, repository, mock_session):
        """Debe funcionar sin filtros"""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        result = repository.get_by_filters()

        assert result == []
        mock_session.exec.assert_called_once()

    def test_get_by_filters_with_provider(self, repository, mock_session):
        """Debe filtrar por provider"""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        repository.get_by_filters(provider="TestProvider")

        mock_session.exec.assert_called_once()

    def test_get_by_filters_with_status(self, repository, mock_session):
        """Debe filtrar por status"""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        repository.get_by_filters(status=PaymentStatus.APPROVED)

        mock_session.exec.assert_called_once()

    def test_get_by_filters_with_multiple_filters(self, repository, mock_session):
        """Debe combinar múltiples filtros"""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        repository.get_by_filters(
            provider="Test",
            status=PaymentStatus.APPROVED,
            merchant_name="Merchant",
            country="US",
        )

        mock_session.exec.assert_called_once()

    def test_get_by_filters_respects_limit_and_offset(self, repository, mock_session):
        """Debe respetar limit y offset"""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        repository.get_by_filters(limit=10, offset=20)

        mock_session.exec.assert_called_once()


class TestCountByStatus:
    """Tests para count_by_status()"""

    def test_count_by_status_executes_query(self, repository, mock_session, sample_event):
        """Debe ejecutar query de count"""
        mock_result = Mock()
        mock_result.all.return_value = [sample_event] * 5  # 5 events
        mock_session.exec.return_value = mock_result

        result = repository.count_by_status(PaymentStatus.APPROVED)

        assert result == 5
        mock_session.exec.assert_called_once()

    def test_count_by_status_returns_zero_when_none(self, repository, mock_session):
        """Debe retornar 0 cuando no hay eventos"""
        mock_result = Mock()
        mock_result.all.return_value = []  # Empty list
        mock_session.exec.return_value = mock_result

        result = repository.count_by_status(PaymentStatus.FAILED)

        assert result == 0

    def test_count_by_status_with_different_statuses(self, repository, mock_session, sample_event):
        """Debe contar correctamente para diferentes status"""
        mock_result = Mock()
        mock_result.all.return_value = [sample_event] * 10  # 10 events
        mock_session.exec.return_value = mock_result

        result = repository.count_by_status(PaymentStatus.PENDING)

        assert result == 10
