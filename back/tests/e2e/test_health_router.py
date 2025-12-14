"""
E2E tests for Health Check Router

Tests para verificar los endpoints de health check.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture para TestClient"""
    return TestClient(app)


class TestHealthRouter:
    """Tests E2E para Health Router"""

    def test_health_check(self, client: TestClient):
        """Test: GET /health"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "version" in data

        # Verificar checks individuales
        checks = data["checks"]
        assert "database" in checks
        assert "openai" in checks
        assert "system" in checks

        # Status debería ser healthy si todo está bien
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        # DB check debería pasar (si la DB está corriendo)
        assert checks["database"] in ["ok", "error: unexpected result"]

        # System siempre debería estar ok
        assert checks["system"] == "ok"

    def test_readiness_check(self, client: TestClient):
        """Test: GET /health/readiness"""
        response = client.get("/api/health/readiness")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "status" in data
        assert "timestamp" in data

        # Status debería ser ready o not_ready
        assert data["status"] in ["ready", "not_ready"]

        # Si not_ready, debería tener reason
        if data["status"] == "not_ready":
            assert "reason" in data

    def test_liveness_check(self, client: TestClient):
        """Test: GET /health/liveness"""
        response = client.get("/api/health/liveness")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "status" in data
        assert "timestamp" in data

        # Liveness siempre debería estar alive (si el proceso responde)
        assert data["status"] == "alive"

    def test_health_check_format(self, client: TestClient):
        """Test: Verificar formato de respuesta del health check"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Verificar que timestamp es ISO 8601
        from datetime import datetime

        try:
            datetime.fromisoformat(data["timestamp"])
            timestamp_valid = True
        except ValueError:
            timestamp_valid = False

        assert timestamp_valid, "Timestamp should be in ISO 8601 format"

        # Verificar que version es string
        assert isinstance(data["version"], str)
