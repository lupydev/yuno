"""
Unit tests for IngestionOrchestrator

Tests para validar el orquestador de ingestión con Strategy Pattern
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.domain.exceptions import NormalizationException
from app.domain.models.enums import NormalizationMethod, PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.services.ingestion_orchestrator import IngestionOrchestrator


@pytest.fixture
def mock_repository():
    """Mock del repositorio"""
    repo = Mock()
    # save() retorna el evento con ID generado
    repo.save.return_value = NormalizedPaymentEvent(
        id=uuid4(),
        merchant_name="Test Merchant",
        provider="TestProvider",
        country="US",
        status_category=PaymentStatus.APPROVED,
        amount=100,
        currency="USD",
        raw_data={},
        normalization_method=NormalizationMethod.RULE_BASED,
    )
    return repo


@pytest.fixture
def mock_rule_normalizer():
    """Mock del rule-based normalizer"""
    normalizer = Mock()
    normalizer.can_normalize.return_value = True
    normalizer.normalize.return_value = NormalizedPaymentEvent(
        merchant_name="Test Merchant",
        provider="RuleProvider",
        country="US",
        status_category=PaymentStatus.APPROVED,
        amount=100,
        currency="USD",
        raw_data={},
        normalization_method=NormalizationMethod.RULE_BASED,
    )
    return normalizer


@pytest.fixture
def mock_ai_normalizer():
    """Mock del AI-based normalizer"""
    normalizer = Mock()
    normalizer.can_normalize.return_value = True
    normalizer.normalize.return_value = NormalizedPaymentEvent(
        merchant_name="AI Merchant",
        provider="AIProvider",
        country="MX",
        status_category=PaymentStatus.APPROVED,
        amount=200,
        currency="MXN",
        raw_data={},
        normalization_method=NormalizationMethod.AI_BASED,
    )
    return normalizer


@pytest.fixture
def orchestrator(mock_repository, mock_rule_normalizer, mock_ai_normalizer):
    """Orchestrator con todos los mocks"""
    return IngestionOrchestrator(
        repository=mock_repository,
        rule_normalizer=mock_rule_normalizer,
        ai_normalizer=mock_ai_normalizer,
    )


class TestIngestionOrchestratorInit:
    """Tests de inicialización"""

    def test_initialization_success(
        self, mock_repository, mock_rule_normalizer, mock_ai_normalizer
    ):
        """Debe inicializar correctamente"""
        orchestrator = IngestionOrchestrator(
            repository=mock_repository,
            rule_normalizer=mock_rule_normalizer,
            ai_normalizer=mock_ai_normalizer,
        )

        assert orchestrator.repository == mock_repository
        assert orchestrator.rule_normalizer == mock_rule_normalizer
        assert orchestrator.ai_normalizer == mock_ai_normalizer


class TestSelectNormalizer:
    """Tests para _select_normalizer()"""

    def test_selects_rule_based_when_can_normalize(self, orchestrator):
        """Debe seleccionar rule-based si puede normalizar"""
        raw_event = {"provider": "adyen", "amount": 100}
        orchestrator.rule_normalizer.can_normalize.return_value = True

        normalizer = orchestrator._select_normalizer(raw_event)

        assert normalizer == orchestrator.rule_normalizer
        orchestrator.rule_normalizer.can_normalize.assert_called_once_with(raw_event)

    def test_selects_ai_based_when_rule_cannot_normalize(self, orchestrator):
        """Debe seleccionar AI si rule-based no puede normalizar"""
        raw_event = {"unknown": "provider"}
        orchestrator.rule_normalizer.can_normalize.return_value = False

        normalizer = orchestrator._select_normalizer(raw_event)

        assert normalizer == orchestrator.ai_normalizer
        orchestrator.rule_normalizer.can_normalize.assert_called_once_with(raw_event)


class TestIngestSuccess:
    """Tests de ingestión exitosa"""

    def test_ingest_with_rule_based_normalizer(self, orchestrator):
        """Debe ingestar usando rule-based normalizer"""
        raw_event = {"provider": "adyen", "amount": 100}
        orchestrator.rule_normalizer.can_normalize.return_value = True

        result = orchestrator.ingest(raw_event)

        # Verifica que usó rule-based
        orchestrator.rule_normalizer.can_normalize.assert_called_once()
        orchestrator.rule_normalizer.normalize.assert_called_once_with(raw_event)

        # Verifica que persistió
        orchestrator.repository.save.assert_called_once()

        # Verifica resultado
        assert result.id is not None
        assert isinstance(result, NormalizedPaymentEvent)

    def test_ingest_with_ai_normalizer(self, orchestrator):
        """Debe ingestar usando AI normalizer cuando rule-based no puede"""
        raw_event = {"unknown": "provider"}
        orchestrator.rule_normalizer.can_normalize.return_value = False

        result = orchestrator.ingest(raw_event)

        # Verifica que intentó rule-based primero
        orchestrator.rule_normalizer.can_normalize.assert_called_once()

        # Verifica que usó AI
        orchestrator.ai_normalizer.normalize.assert_called_once_with(raw_event)

        # Verifica que persistió
        orchestrator.repository.save.assert_called_once()

        # Verifica resultado
        assert result.id is not None

    def test_ingest_with_provider_hint(self, orchestrator):
        """Debe aceptar provider_hint (aunque no lo use actualmente)"""
        raw_event = {"amount": 100}
        orchestrator.rule_normalizer.can_normalize.return_value = True

        result = orchestrator.ingest(raw_event, provider_hint="stripe")

        assert result.id is not None
        orchestrator.repository.save.assert_called_once()

    def test_ingest_returns_saved_event(self, orchestrator):
        """Debe retornar el evento guardado del repositorio"""
        raw_event = {"amount": 100}
        orchestrator.rule_normalizer.can_normalize.return_value = True

        saved_event = NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Saved",
            provider="Test",
            country="US",
            status_category=PaymentStatus.APPROVED,
            amount=100,
            currency="USD",
            raw_data={},
            normalization_method=NormalizationMethod.RULE_BASED,
        )
        orchestrator.repository.save.return_value = saved_event

        result = orchestrator.ingest(raw_event)

        assert result == saved_event
        assert result.merchant_name == "Saved"


class TestIngestErrors:
    """Tests de manejo de errores"""

    def test_ingest_raises_normalization_exception(self, orchestrator):
        """Debe propagar NormalizationException"""
        raw_event = {"amount": 100}
        orchestrator.rule_normalizer.can_normalize.return_value = True
        orchestrator.rule_normalizer.normalize.side_effect = NormalizationException(
            "Failed to normalize"
        )

        with pytest.raises(NormalizationException) as exc_info:
            orchestrator.ingest(raw_event)

        assert "Failed to normalize" in str(exc_info.value)

    def test_ingest_handles_repository_error(self, orchestrator):
        """Debe manejar errores del repositorio"""
        raw_event = {"amount": 100}
        orchestrator.rule_normalizer.can_normalize.return_value = True
        orchestrator.repository.save.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            orchestrator.ingest(raw_event)

        assert "Database error" in str(exc_info.value)

    def test_ingest_logs_normalization_error(self, orchestrator):
        """Debe loggear errores de normalización"""
        raw_event = {"amount": 100}
        orchestrator.rule_normalizer.can_normalize.return_value = True
        orchestrator.rule_normalizer.normalize.side_effect = NormalizationException("Test error")

        with pytest.raises(NormalizationException):
            with patch("app.services.ingestion_orchestrator.logger") as mock_logger:
                orchestrator.ingest(raw_event)
                # Verifica que se loggeó el error
                assert mock_logger.error.called


class TestIngestIntegration:
    """Tests de integración del flujo completo"""

    def test_complete_ingestion_flow(self, orchestrator):
        """Debe completar flujo: select → normalize → save"""
        raw_event = {
            "provider": "test",
            "amount": 500,
            "currency": "USD",
            "status": "approved",
        }
        orchestrator.rule_normalizer.can_normalize.return_value = True

        result = orchestrator.ingest(raw_event)

        # 1. Seleccionó normalizer
        orchestrator.rule_normalizer.can_normalize.assert_called_once()

        # 2. Normalizó
        orchestrator.rule_normalizer.normalize.assert_called_once()

        # 3. Guardó
        orchestrator.repository.save.assert_called_once()

        # 4. Retornó evento guardado
        assert result is not None
        assert result.id is not None

    def test_strategy_pattern_switches_to_ai(self, orchestrator):
        """Debe cambiar de rule-based a AI automáticamente"""
        raw_event = {"unknown_provider": "data"}

        # Rule-based no puede normalizar
        orchestrator.rule_normalizer.can_normalize.return_value = False

        result = orchestrator.ingest(raw_event)

        # Verificar Strategy Pattern
        orchestrator.rule_normalizer.can_normalize.assert_called_once()
        orchestrator.ai_normalizer.normalize.assert_called_once()
        assert result is not None
