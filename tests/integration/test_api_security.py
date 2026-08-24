"""Integration tests for environment-based API key protection on /investigations/* endpoints."""

import os
from unittest import mock

import pytest
from httpx import ASGITransport, AsyncClient
from src.api.main import app
from src.config.settings import Settings, settings


TEST_KEY = "test-investigation-key-123"


@pytest.mark.anyio
async def test_health_and_ready_remain_open_when_key_configured(monkeypatch):
    """Health/readiness probes must stay unauthenticated even when an API key is configured."""
    monkeypatch.setattr(settings, "investigation_api_key", TEST_KEY)
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            health = await client.get("/health")
            ready = await client.get("/ready")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


@pytest.mark.anyio
async def test_investigations_reject_missing_key_when_configured(monkeypatch):
    """With a key configured, requests without X-API-Key must be rejected with 401."""
    monkeypatch.setattr(settings, "investigation_api_key", TEST_KEY)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/investigations/scenarios")

    assert response.status_code == 401
    assert "Invalid or missing API key" in response.json()["detail"]


@pytest.mark.anyio
async def test_investigations_reject_incorrect_key_when_configured(monkeypatch):
    """With a key configured, an incorrect X-API-Key must be rejected with 401."""
    monkeypatch.setattr(settings, "investigation_api_key", TEST_KEY)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/investigations/scenarios",
            headers={"X-API-Key": "wrong-key"},
        )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_investigations_accept_correct_key_when_configured(monkeypatch):
    """With a key configured, the matching X-API-Key grants access."""
    monkeypatch.setattr(settings, "investigation_api_key", TEST_KEY)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/investigations/scenarios",
            headers={"X-API-Key": TEST_KEY},
        )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


@pytest.mark.anyio
async def test_investigations_open_when_key_not_configured(monkeypatch):
    """Default development/demo mode: no key configured means open access (backwards compatible)."""
    monkeypatch.setattr(settings, "investigation_api_key", None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        scenarios = await client.get("/investigations/scenarios")
        evaluate_latest = await client.get("/investigations/evaluation/latest")

    assert scenarios.status_code == 200
    # latest evaluation report is absent in clean environments -> 404 (not 401) proves the guard is off
    assert evaluate_latest.status_code in (200, 404)


def test_settings_reads_investigation_api_key_from_environment():
    """The documented INVESTIGATION_API_KEY variable maps onto the application settings."""
    with mock.patch.dict(os.environ, {"INVESTIGATION_API_KEY": TEST_KEY}):
        loaded = Settings(_env_file=None)
    assert loaded.investigation_api_key == TEST_KEY

    with mock.patch.dict(os.environ, {}, clear=True):
        unloaded = Settings(_env_file=None)
    assert unloaded.investigation_api_key is None
