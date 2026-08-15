"""Integration test for FastAPI health check endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app


@pytest.mark.anyio
async def test_health_check_endpoint():
    """Verify GET /health returns HTTP 200 and status ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}


@pytest.mark.anyio
async def test_readiness_check_endpoint():
    """Verify GET /ready returns HTTP 200 and readiness payload with database status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert "app" in data
        assert "version" in data


@pytest.mark.anyio
async def test_cors_headers_allowed():
    """Verify CORS middleware responds with correct headers for allowed origins."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"



