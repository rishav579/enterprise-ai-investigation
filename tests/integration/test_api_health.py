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
