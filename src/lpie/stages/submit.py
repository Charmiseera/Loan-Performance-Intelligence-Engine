from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from lpie.conf.validator import validate_submission_file
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class SubmitStage(BaseStage):
    name = "submit"
    declared_inputs: List[str] = [
        "predictions_scoring.parquet",
        "anomaly_scoring.parquet",
        "attributions_scoring.parquet",
    ]
    declared_outputs: List[str] = [
        "submission.csv",
        "submission_manifest.json",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        preds = context.store.read_parquet("train", "predictions_scoring.parquet")
        anomalies = context.store.read_parquet("anomaly", "anomaly_scoring.parquet")
        attrs = context.store.read_parquet("explain", "attributions_scoring.parquet")

        # Merge on primary composite key: [loan_id, monthly_reporting_period]
        merged = preds.merge(
            anomalies[["loan_id", "monthly_reporting_period", "anomaly_score", "exception_required", "exception_type", "recommended_action"]],
            on=["loan_id", "monthly_reporting_period"],
            how="inner",
        ).merge(
            attrs[["loan_id", "monthly_reporting_period", "top_drivers"]],
            on=["loan_id", "monthly_reporting_period"],
            how="inner",
        )

        # Standard column order per contracts/submission_schema.json
        df_sub = pd.DataFrame({
            "loan_id": merged["loan_id"],
            "reporting_month": merged["monthly_reporting_period"],
            "next_3m_delinquency_prob": merged["prob_deterioration_3m"],
            "next_6m_delinquency_prob": merged["prob_deterioration_6m"],
            "next_12m_default_prob": merged["prob_default_12m"],
            "next_12m_prepayment_prob": merged["prob_prepay_12m"],
            "next_state": merged["next_state"],
            "exception_required": merged["exception_required"],
            "exception_type": merged["exception_type"],
            "anomaly_score": merged["anomaly_score"],
            "top_drivers": merged["top_drivers"],
            "recommended_action": merged["recommended_action"],
            "confidence": merged["confidence"],
        })

        # Write submission.csv to artifacts/submission/submission.csv
        csv_path = context.store.write_csv(
            df_sub,
            "submission",
            "submission.csv",
            sort_keys=["loan_id", "reporting_month"],
        )

        # Run schema validation contract
        schema_path = context.config.paths.contracts_dir + "/submission_schema.json"
        val_code = validate_submission_file(str(csv_path), schema_path)
        if val_code != 0:
            raise ValueError(f"Submission validation FAILED against schema contract: {schema_path}")

        manifest = {
            "submission_file": str(csv_path),
            "record_count": len(df_sub),
            "column_count": len(df_sub.columns),
            "contract_validation": "PASSED",
        }
        context.store.write_json(manifest, "submission", "submission_manifest.json")
        return manifest


global_stage_registry.register(SubmitStage())
