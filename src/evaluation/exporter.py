"""Exports evaluation summaries to JSON and Markdown reports."""

import json
from pathlib import Path
from src.evaluation.models import EvaluationSummary


class EvaluationExporter:
    """Exports evaluation results to files."""

    @staticmethod
    def export_json(summary: EvaluationSummary, output_path: Path) -> None:
        """Export the summary as a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))

    @staticmethod
    def export_markdown(summary: EvaluationSummary, output_path: Path) -> None:
        """Export the summary as a readable Markdown report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "# Phase 6: Golden Dataset Evaluation Report",
            "",
            f"**Timestamp:** {summary.timestamp}",
            f"**Dataset Version:** {summary.dataset_version}",
            f"**Total Cases:** {summary.total_cases}",
            f"**Passed:** {summary.passed_cases}",
            f"**Failed:** {summary.failed_cases}",
            "",
            "## Aggregate Metrics",
            ""
        ]
        
        for name, value in summary.aggregate_metrics.items():
            lines.append(f"- **{name}**: {value:.2f}")
            
        lines.append("")
        lines.append("## Case Results")
        lines.append("")
        
        for case in summary.case_results:
            status = "✅ PASS" if case.passed else "❌ FAIL"
            lines.append(f"### {case.scenario_id} - {status}")
            lines.append(f"Run ID: `{case.run_id}`")
            lines.append("")
            
            if not case.passed and case.failure_reasons:
                lines.append("**Failure Reasons:**")
                for reason in case.failure_reasons:
                    lines.append(f"- {reason}")
                lines.append("")
                
            if case.metrics:
                lines.append("**Metrics:**")
                for metric in case.metrics:
                    lines.append(f"- {metric.name}: {metric.value:.2f}")
                lines.append("")
                
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
