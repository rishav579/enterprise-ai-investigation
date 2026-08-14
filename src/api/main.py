"""FastAPI application entrypoint for Enterprise AI Investigation System."""

from fastapi import FastAPI
from src.config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise AI Investigation & Decision System (Simulation & Portfolio)",
)


@app.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}
