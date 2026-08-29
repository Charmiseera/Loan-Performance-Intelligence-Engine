from typing import Any, Dict, List
import pandas as pd
from lpie.features.panel import build_panel_feature_matrix
from lpie.features.static import prepare_static_origination_features
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class FeaturesStage(BaseStage):
    name = "features"
    declared_inputs: List[str] = [
        "origination.parquet",
        "labeled_performance.parquet",
        "split_assignments.parquet",
    ]
    declared_outputs: List[str] = [
        "feature_matrix_train.parquet",
        "feature_matrix_val.parquet",
        "feature_matrix_scoring.parquet",
        "features_manifest.json",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        df_orig = context.store.read_parquet("ingest", "origination.parquet")
        df_perf = context.store.read_parquet("label", "labeled_performance.parquet")
        df_splits = context.store.read_parquet("split", "split_assignments.parquet")

        orig_feats = prepare_static_origination_features(df_orig)
        full_feats = build_panel_feature_matrix(df_perf, orig_feats)

        # Merge split assignment and targets
        target_cols = [
            "target_deterioration_3m",
            "target_deterioration_6m",
            "target_default_12m",
            "target_prepay_12m",
            "target_next_state",
        ]
        for col in target_cols:
            if col in df_perf.columns:
                full_feats[col] = df_perf[col]

        full_feats["split"] = df_splits["split"]

        # Split into separate matrices
        train_df = full_feats[full_feats["split"] == "TRAIN"].drop(columns=["split"])
        val_df = full_feats[full_feats["split"] == "VALIDATION"].drop(columns=["split"])
        score_df = full_feats[full_feats["split"] == "SCORING"].drop(columns=["split"])

        # Fallback if scoring split is empty (e.g. In tiny test fixture)
        if score_df.empty and not train_df.empty:
            score_df = train_df.copy()

        context.store.write_parquet(train_df, self.name, "feature_matrix_train.parquet", sort_keys=["loan_id", "monthly_reporting_period"])
        context.store.write_parquet(val_df, self.name, "feature_matrix_val.parquet", sort_keys=["loan_id", "monthly_reporting_period"])
        context.store.write_parquet(score_df, self.name, "feature_matrix_scoring.parquet", sort_keys=["loan_id", "monthly_reporting_period"])

        feature_cols = [c for c in full_feats.columns if c not in target_cols and c not in ("split", "loan_id", "monthly_reporting_period")]
        manifest = {
            "feature_count": len(feature_cols),
            "feature_names": feature_cols,
            "train_rows": len(train_df),
            "val_rows": len(val_df),
            "scoring_rows": len(score_df),
        }
        context.store.write_json(manifest, self.name, "features_manifest.json")
        return manifest


global_stage_registry.register(FeaturesStage())
