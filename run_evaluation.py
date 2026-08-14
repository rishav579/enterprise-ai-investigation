import sys
from pathlib import Path

from src.config.settings import PROJECT_ROOT
from src.data.seed_database import seed_enterprise_database
from src.tools.registry import create_default_tool_registry
from src.evaluation.scenarios import get_golden_dataset
from src.evaluation.runner import EvaluationRunner
from src.evaluation.exporter import EvaluationExporter


def main():
    print("Initializing Phase 6 Evaluation...")
    
    # 1. Setup Data Environment
    db_url = "sqlite:///eval_phase6.db"
    print("Seeding deterministic enterprise database...")
    seed_enterprise_database(db_url=db_url, seed=42)
    
    doc_dir = PROJECT_ROOT / "data" / "raw"
    registry = create_default_tool_registry(db_url=db_url, doc_dir=doc_dir)
    
    # 2. Get Golden Dataset
    dataset = get_golden_dataset()
    print(f"Loaded {len(dataset)} evaluation scenarios.")
    
    # 3. Run Evaluation
    runner = EvaluationRunner(registry=registry)
    print("Running scenarios...")
    summary = runner.run_all(dataset)
    
    # 4. Export Results
    reports_dir = PROJECT_ROOT / "evaluation_reports"
    json_path = reports_dir / "latest_evaluation.json"
    md_path = reports_dir / "latest_evaluation.md"
    
    EvaluationExporter.export_json(summary, json_path)
    EvaluationExporter.export_markdown(summary, md_path)
    
    print("\nEvaluation Complete.")
    print(f"Passed: {summary.passed_cases}/{summary.total_cases}")
    
    if summary.failed_cases > 0:
        print("\nFailed Scenarios:")
        for case in summary.case_results:
            if not case.passed:
                print(f"  - {case.scenario_id}: {case.failure_reasons}")
        sys.exit(1)
        
    print(f"\nReports saved to {reports_dir}")
    sys.exit(0)

if __name__ == "__main__":
    main()
