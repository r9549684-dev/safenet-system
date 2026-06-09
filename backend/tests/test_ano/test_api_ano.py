"""Интеграционные тесты для SafeNet ANO API."""
import importlib.util
import sys
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Прямой импорт модуля в обход app.api.__init__.py (чтобы избежать ошибки sqlalchemy)
spec = importlib.util.spec_from_file_location(
    "ano_api",
    "backend/app/api/ano.py"
)
ano_api = importlib.util.module_from_spec(spec)
sys.modules["ano_api"] = ano_api
spec.loader.exec_module(ano_api)

ano_router = ano_api.router

@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(ano_router)
    return app

@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestANOApi:
    def test_analyze_metrics(self, client: TestClient) -> None:
        """POST /ano/analyze должен вернуть IncidentResponse."""
        payload = {
            "server_id": "ae-1",
            "rtt_ms": 120.0,
            "jitter_ms": 35.0,
            "loss_pct": 12.0,
            "throughput_kbps": 500.0,
            "context": {"geo": "UAE", "protocol": "VLESS"}
        }
        response = client.post("/ano/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "incident_id" in data
        assert "scope" in data
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0
        assert "predictive_recommendation" in data
        assert "should_migrate" in data

    def test_get_recommendation_empty(self, client: TestClient) -> None:
        """GET /ano/recommendation/{server_id} для нового сервера."""
        response = client.get("/ano/recommendation/non-existent-server")
        assert response.status_code == 200
        
        data = response.json()
        assert data["server_id"] == "non-existent-server"
        assert data["recommended_action"] is None
        assert data["confidence"] == 0.0

    def test_get_shadow_report(self, client: TestClient) -> None:
        """GET /ano/shadow/report должен вернуть отчёт Meta-Agent."""
        # Сначала сгенерируем данные через analyze
        payload = {
            "server_id": "tr-1",
            "rtt_ms": 45.0,
            "jitter_ms": 8.0,
            "loss_pct": 2.0,
            "context": {"geo": "TR"}
        }
        client.post("/ano/analyze", json=payload)
        
        response = client.get("/ano/shadow/report")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_shadow_actions" in data
        assert data["total_shadow_actions"] >= 1  # Должно быть >= 1 после analyze
        assert "analysis_report" in data
        assert "ANALYSIS REPORT" in data["analysis_report"]
