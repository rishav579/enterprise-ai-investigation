"""FastAPI application entrypoint for Enterprise AI Investigation System."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.config.settings import PROJECT_ROOT, settings
from src.investigation.models import InvestigationRequest, InvestigationRunResult
from src.investigation.orchestrator import InvestigationOrchestrator
from src.synthesis.models import InvestigationReport
from src.synthesis.synthesizer import InvestigationSynthesizer
from src.tools.registry import create_default_tool_registry

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise AI Investigation & Decision System (Simulation & Portfolio)",
)


class SynthesizeRequestPayload(BaseModel):
    """Payload for requesting synthesis on an investigation."""
    question: str = Field(..., min_length=5, max_length=1000)
    investigation_id: Optional[str] = Field(None)
    scenario_hint: Optional[str] = Field(None)


class FullInvestigationResponse(BaseModel):
    """Combined response payload containing run results and synthesized report."""
    run_result: InvestigationRunResult
    report: InvestigationReport


@app.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}


@app.post("/investigations/investigate", response_model=FullInvestigationResponse)
async def run_full_investigation(payload: SynthesizeRequestPayload) -> FullInvestigationResponse:
    """Execute end-to-end investigation: plan -> tools -> evidence -> synthesis."""
    try:
        registry = create_default_tool_registry(
            doc_dir=PROJECT_ROOT / "data" / "raw"
        )
        orchestrator = InvestigationOrchestrator(registry=registry)
        request = InvestigationRequest(
            question=payload.question,
            investigation_id=payload.investigation_id or f"INV-API",
            scenario_hint=payload.scenario_hint,
        )
        run_result, store, audit = orchestrator.run_with_context(request)

        synthesizer = InvestigationSynthesizer()
        report = synthesizer.synthesize(
            question=request.question,
            investigation_run_id=request.investigation_id,
            store=store,
            plan=run_result.plan,
            run_result=run_result,
            audit=audit,
        )
        return FullInvestigationResponse(run_result=run_result, report=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")
