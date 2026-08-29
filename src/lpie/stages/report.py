from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import jinja2
import pandas as pd
from lpie.advanced.fairness import audit_subgroup_fairness_and_calibration
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class ReportStage(BaseStage):
    name = "report"
    declared_inputs: List[str] = [
        "models_manifest.json",
        "contract_validation.json",
        "global_importance.json",
        "scenario_projections.json",
    ]
    declared_outputs: List[str] = [
        "model_card.md",
        "fairness_audit_report.json",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        models_manifest = context.store.read_json("train", "models_manifest.json")
        metrics = models_manifest.get("metrics", {})

        template_dir = Path("templates")
        if template_dir.exists():
            jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(template_dir)),
                autoescape=jinja2.select_autoescape(),
            )
            template = jinja_env.get_template("model_card.md.j2")
            rendered = template.render(
                generation_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                metrics=metrics,
            )
        else:
            rendered = f"# Model Card\nGenerated {datetime.now(timezone.utc).isoformat()}"

        context.store.write_markdown(rendered, "reports", "model_card.md")

        # Subgroup Fairness & Calibration Audit (FR-103, FR-104)
        score_feats = context.store.read_parquet("features", "feature_matrix_scoring.parquet")
        score_preds = context.store.read_parquet("train", "predictions_scoring.parquet")
        merged = score_feats.merge(score_preds, on=["loan_id", "monthly_reporting_period"], how="inner")
        
        fairness_report = audit_subgroup_fairness_and_calibration(
            df=merged,
            prob_col="prob_default_12m",
            target_col="target_default_12m",
        )

        context.store.write_json(fairness_report, "reports", "fairness_audit_report.json")

        return {
            "reports_rendered": ["model_card.md", "fairness_audit_report.json"],
            "model_metrics_keys": list(metrics.keys()),
        }


global_stage_registry.register(ReportStage())
