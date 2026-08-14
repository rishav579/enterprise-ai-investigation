"""Integration tests for investigation synthesis service and API."""

import pytest
from httpx import ASGITransport, AsyncClient
from src.api.main import app
from src.config.settings import PROJECT_ROOT
from src.data.seed_database import seed_enterprise_database
from src.investigation.audit import AuditEventType
from src.investigation.models import InvestigationRequest
from src.investigation.orchestrator import InvestigationOrchestrator
from src.synthesis.models import SynthesisStatus
from src.synthesis.provider import MockLLMProvider
from src.synthesis.synthesizer import InvestigationSynthesizer
from src.tools.registry import create_default_tool_registry


@pytest.fixture(scope="module")
def seeded_registry(tmp_path_factory):
    temp = tmp_path_factory.mktemp("synth_integ_data")
    db_url = f"sqlite:///{temp}/synth_integ.db"
    seed_enterprise_database(db_url=db_url, seed=42)
    return create_default_tool_registry(
        db_url=db_url,
        doc_dir=PROJECT_ROOT / "data" / "raw",
    )


def test_synthesis_integration_full_pipeline(seeded_registry):
    """Test full pipeline: Orchestrator -> EvidenceStore -> Synthesizer -> Validated Report."""
    orchestrator = InvestigationOrchestrator(registry=seeded_registry)
    request = InvestigationRequest(
        question="Why did customer cancellations increase sharply in September 2025?",
        investigation_id="INV-SYNTH-INTEG-001",
    )
    run_result, store, audit = orchestrator.run_with_context(request)

    synthesizer = InvestigationSynthesizer(provider=MockLLMProvider())
    report = synthesizer.synthesize(
        question=request.question,
        investigation_run_id=request.investigation_id,
        store=store,
        plan=run_result.plan,
        run_result=run_result,
        audit=audit,
    )

    assert report.investigation_run_id == "INV-SYNTH-INTEG-001"
    assert report.citation_valid is True
    assert report.synthesis_status == SynthesisStatus.SUCCESS
    assert len(report.findings) > 0
    assert report.root_cause is not None
    assert "billing-gateway" in report.root_cause
    assert len(report.recommendations) > 0

    # Audit events check
    events = audit.all()
    event_types = [e.event_type for e in events]
    assert AuditEventType.SYNTHESIS_STARTED in event_types
    assert AuditEventType.SYNTHESIS_GENERATED in event_types
    assert AuditEventType.SYNTHESIS_VALIDATED in event_types


def test_synthesis_provider_exception_handling(seeded_registry):
    """Synthesizer handles provider exceptions gracefully and records audit failure."""
    orchestrator = InvestigationOrchestrator(registry=seeded_registry)
    request = InvestigationRequest(
        question="Why did customer cancellations increase sharply in September 2025?",
        investigation_id="INV-ERR-INTEG-001",
    )
    run_result, store, audit = orchestrator.run_with_context(request)

    class FailingProvider(MockLLMProvider):
        def generate(self, prompt: str) -> str:
            raise ConnectionError("Simulated LLM API network failure")

    synthesizer = InvestigationSynthesizer(provider=FailingProvider())
    report = synthesizer.synthesize(
        question=request.question,
        investigation_run_id=request.investigation_id,
        store=store,
        audit=audit,
    )

    assert report.synthesis_status == SynthesisStatus.ERROR
    assert report.citation_valid is False
    assert "Generation error" in report.validation_errors[0]

    event_types = [e.event_type for e in audit.all()]
    assert AuditEventType.SYNTHESIS_STARTED in event_types
    assert AuditEventType.SYNTHESIS_FAILED in event_types


def test_synthesis_malformed_json_handling(seeded_registry):
    """Synthesizer handles malformed provider output without crashing."""
    orchestrator = InvestigationOrchestrator(registry=seeded_registry)
    request = InvestigationRequest(
        question="Why did churn spike?",
        investigation_id="INV-MALFORMED-001",
    )
    run_result, store, audit = orchestrator.run_with_context(request)

    mock = MockLLMProvider(custom_response_json="NOT_VALID_JSON{{{")
    synthesizer = InvestigationSynthesizer(provider=mock)
    report = synthesizer.synthesize(
        question=request.question,
        investigation_run_id=request.investigation_id,
        store=store,
        audit=audit,
    )

    assert report.synthesis_status == SynthesisStatus.ERROR
    assert report.citation_valid is False
    assert any("Parsing error" in err for err in report.validation_errors)


@pytest.mark.anyio
async def test_api_investigate_endpoint():
    """Test the POST /investigations/investigate FastAPI endpoint."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        payload = {
            "question": "Why did customer cancellations increase sharply in September 2025?",
            "investigation_id": "INV-API-TEST-001",
        }
        response = await client.post("/investigations/investigate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "run_result" in data
        assert "report" in data
        assert data["report"]["citation_valid"] is True
        assert data["report"]["root_cause"] is not None
