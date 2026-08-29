from typing import Any, Dict, List
import pandas as pd
from lpie.anomaly.actions import determine_recommended_action
from lpie.anomaly.combine import compute_composite_anomaly_score
from lpie.anomaly.learned import LearnedAnomalyDetector
from lpie.anomaly.queue import prioritize_reviewer_queue
from lpie.anomaly.reconciliation import generate_reconciliation_fixture
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class AnomalyStage(BaseStage):
    name = "anomaly"
    declared_inputs: List[str] = [
        "feature_matrix_scoring.parquet",
        "predictions_scoring.parquet",
        "rule_violations.parquet",
    ]
    declared_outputs: List[str] = [
        "anomaly_scoring.parquet",
        "reviewer_queue.json",
        "reconciliation_fixture.parquet",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        feats_score = context.store.read_parquet("features", "feature_matrix_scoring.parquet")
        preds_score = context.store.read_parquet("train", "predictions_scoring.parquet")
        violations = context.store.read_parquet("contract", "rule_violations.parquet")

        # Merge rule violations with scoring records
        merged = feats_score[["loan_id", "monthly_reporting_period"]].merge(
            violations, on=["loan_id", "monthly_reporting_period"], how="left"
        )
        rule_counts = merged["total_violations"].fillna(0)

        # Fit and score IsolationForest
        detector = LearnedAnomalyDetector(seed=context.stage_seed)
        detector.fit(feats_score)
        stat_scores = detector.score(feats_score)

        # Composite anomaly score and exception classification
        comp_scores, exc_req, exc_types = compute_composite_anomaly_score(stat_scores, rule_counts)

        # Merge with predictions for action determination
        preds_merged = feats_score[["loan_id", "monthly_reporting_period"]].merge(
            preds_score, on=["loan_id", "monthly_reporting_period"], how="left"
        )
        p_def = preds_merged["prob_default_12m"].fillna(0.0)
        p_prep = preds_merged["prob_prepay_12m"].fillna(0.0)
        confidence = preds_merged.get("confidence", pd.Series(0.85, index=feats_score.index))

        rec_actions = determine_recommended_action(
            pd.Series(exc_req, index=feats_score.index),
            exc_types,
            p_def,
            p_prep,
        )

        anomaly_df = pd.DataFrame({
            "loan_id": feats_score["loan_id"],
            "monthly_reporting_period": feats_score["monthly_reporting_period"],
            "statistical_anomaly_score": stat_scores,
            "anomaly_score": comp_scores,
            "exception_required": exc_req,
            "exception_type": exc_types.values,
            "recommended_action": rec_actions.values,
            "confidence": confidence.values if hasattr(confidence, "values") else confidence,
        })

        context.store.write_parquet(
            anomaly_df,
            self.name,
            "anomaly_scoring.parquet",
            sort_keys=["loan_id", "monthly_reporting_period"],
        )

        # 1. Build prioritized 25-item reviewer queue (FR-046, SC-017)
        reviewer_queue = prioritize_reviewer_queue(anomaly_df, min_items=25)
        context.store.write_json(reviewer_queue, self.name, "reviewer_queue.json")

        # 2. Build synthetic reconciliation fixture (FR-043, SC-026)
        reconcil_df = generate_reconciliation_fixture(feats_score, sample_size=100, seed=context.stage_seed)
        context.store.write_parquet(reconcil_df, self.name, "reconciliation_fixture.parquet")

        summary = {
            "total_records_scored": len(anomaly_df),
            "exceptions_required_count": int(exc_req.sum()),
            "exception_rate": float(exc_req.mean()),
            "action_distribution": {k: int(v) for k, v in rec_actions.value_counts().items()},
            "queue_size": len(reviewer_queue),
            "reconciliation_records": len(reconcil_df),
        }
        return summary


global_stage_registry.register(AnomalyStage())
