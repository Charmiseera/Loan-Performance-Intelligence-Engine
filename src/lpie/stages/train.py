from typing import Any, Dict, List
import numpy as np
import pandas as pd
from lpie.models.baseline import LogisticBaselineClassifier, MajorityBaselineClassifier
from lpie.models.calibration import CalibratedModelWrapper
from lpie.models.gbdt import GBDTModelWrapper
from lpie.models.metrics import compute_classification_metrics
from lpie.models.multistate import MultistateClassifier
from lpie.models.uncertainty import compute_prediction_confidence
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class TrainStage(BaseStage):
    name = "train"
    declared_inputs: List[str] = [
        "feature_matrix_train.parquet",
        "feature_matrix_val.parquet",
        "feature_matrix_scoring.parquet",
    ]
    declared_outputs: List[str] = [
        "predictions_scoring.parquet",
        "models_manifest.json",
        "model_comparison.json",
        "models_bundle.joblib",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        train_df = context.store.read_parquet("features", "feature_matrix_train.parquet")
        val_df = context.store.read_parquet("features", "feature_matrix_val.parquet")
        score_df = context.store.read_parquet("features", "feature_matrix_scoring.parquet")

        target_cols = [
            "target_deterioration_3m",
            "target_deterioration_6m",
            "target_default_12m",
            "target_prepay_12m",
            "target_next_state",
        ]
        feature_cols = [
            c for c in train_df.columns
            if c not in target_cols and c not in ("loan_id", "monthly_reporting_period")
        ]

        X_train = train_df[feature_cols]
        X_val = val_df[feature_cols] if not val_df.empty else X_train
        X_score = score_df[feature_cols] if not score_df.empty else X_train

        predictions_df = pd.DataFrame({
            "loan_id": score_df["loan_id"] if not score_df.empty else train_df["loan_id"],
            "monthly_reporting_period": score_df["monthly_reporting_period"] if not score_df.empty else train_df["monthly_reporting_period"],
        })

        targets_binary = [
            ("target_deterioration_3m", "prob_deterioration_3m"),
            ("target_deterioration_6m", "prob_deterioration_6m"),
            ("target_default_12m", "prob_default_12m"),
            ("target_prepay_12m", "prob_prepay_12m"),
        ]

        metrics_summary: Dict[str, Any] = {}
        baseline_metrics_summary: Dict[str, Any] = {}
        model_comparison: List[Dict[str, Any]] = []
        baseline_models_fitted: Dict[str, Any] = {}
        fitted_models: Dict[str, Any] = {}

        for target_name, prob_col in targets_binary:
            y_train = train_df[target_name].values if target_name in train_df.columns else np.zeros(len(train_df))
            y_val = val_df[target_name].values if target_name in val_df.columns else y_train

            base_rate = float(np.mean(y_val)) if len(y_val) > 0 else 0.0

            # --- Baseline: Logistic Regression on subsample (FR-032) ---
            # Cap at 50k rows for speed — sufficient for a representative named comparison.
            BASELINE_SAMPLE = 50_000
            rng = np.random.default_rng(context.stage_seed)
            if len(X_train) > BASELINE_SAMPLE:
                bl_idx = rng.choice(len(X_train), size=BASELINE_SAMPLE, replace=False)
                X_bl = X_train.iloc[bl_idx]
                y_bl = y_train[bl_idx]
            else:
                X_bl, y_bl = X_train, y_train

            baseline = LogisticBaselineClassifier(seed=context.stage_seed)
            if len(np.unique(y_bl)) > 1 and len(X_bl.select_dtypes(include=[np.number]).columns) > 0:
                baseline.fit(X_bl, y_bl)
                if len(np.unique(y_val)) > 1:
                    bl_preds = baseline.predict_proba(X_val)[:, 1]
                    bl_metrics = compute_classification_metrics(y_val, bl_preds)
                else:
                    bl_metrics = {"roc_auc": 0.5, "pr_auc": base_rate, "brier_score": base_rate * (1 - base_rate)}
            else:
                bl_metrics = {"roc_auc": 0.5, "pr_auc": base_rate, "brier_score": base_rate * (1 - base_rate)}
            baseline_metrics_summary[prob_col] = bl_metrics
            baseline_models_fitted[prob_col] = baseline

            # --- Improved: LightGBM + Isotonic Calibration ---
            gbdt = GBDTModelWrapper(seed=context.stage_seed)
            if len(np.unique(y_train)) > 1:
                gbdt.fit(X_train, y_train)
                cal_model = CalibratedModelWrapper(gbdt, method="isotonic")
                if len(np.unique(y_val)) > 1 and len(X_val) > 5:
                    cal_model.fit_calibration(X_val, y_val)
            else:
                cal_model = CalibratedModelWrapper(MajorityBaselineClassifier().fit(X_train, y_train))

            fitted_models[prob_col] = cal_model
            preds = cal_model.predict_proba(X_score)[:, 1]
            predictions_df[prob_col] = np.clip(preds, 0.0, 1.0)

            # --- Evaluate improved model on validation split ---
            if len(np.unique(y_val)) > 1:
                val_preds = cal_model.predict_proba(X_val)[:, 1]
                imp_metrics = compute_classification_metrics(y_val, val_preds)
                metrics_summary[prob_col] = imp_metrics
            else:
                imp_metrics = {
                    "total_samples": len(y_val),
                    "positive_count": int(np.sum(y_val)),
                    "positive_base_rate": base_rate,
                    "pr_auc": 0.0,
                    "roc_auc": 0.5,
                    "brier_score": 0.0,
                }
                metrics_summary[prob_col] = imp_metrics

            # --- Build comparison row (FR-032: state improvements and regressions) ---
            roc_delta = imp_metrics.get("roc_auc", 0.5) - bl_metrics.get("roc_auc", 0.5)
            pr_delta = imp_metrics.get("pr_auc", 0.0) - bl_metrics.get("pr_auc", 0.0)
            model_comparison.append({
                "target": prob_col,
                "positive_base_rate": round(base_rate, 5),
                "baseline_model": "LogisticRegression (L2, balanced)",
                "baseline_roc_auc": round(bl_metrics.get("roc_auc", 0.5), 4),
                "baseline_pr_auc": round(bl_metrics.get("pr_auc", base_rate), 4),
                "baseline_brier": round(bl_metrics.get("brier_score", 0.0), 5),
                "improved_model": "LightGBM + Isotonic Calibration",
                "improved_roc_auc": round(imp_metrics.get("roc_auc", 0.5), 4),
                "improved_pr_auc": round(imp_metrics.get("pr_auc", 0.0), 4),
                "improved_brier": round(imp_metrics.get("brier_score", 0.0), 5),
                "roc_auc_delta": round(roc_delta, 4),
                "pr_auc_delta": round(pr_delta, 4),
                "improvement_direction": "IMPROVED" if roc_delta > 0.01 else ("REGRESSION" if roc_delta < -0.01 else "NEUTRAL"),
            })

        # Next state classifier
        y_train_st = train_df["target_next_state"].values if "target_next_state" in train_df.columns else np.array(["CURRENT"] * len(train_df))
        multistate = MultistateClassifier(seed=context.stage_seed)
        if len(np.unique(y_train_st)) > 1:
            multistate.fit(X_train, y_train_st)
            predictions_df["next_state"] = multistate.predict(X_score)
        else:
            predictions_df["next_state"] = "CURRENT"

        # Compute confidence score based on default margin
        confidence_vals = compute_prediction_confidence(
            predictions_df["prob_default_12m"].values,
            feature_matrix=X_score,
        )
        predictions_df["confidence"] = confidence_vals

        context.store.write_parquet(
            predictions_df,
            self.name,
            "predictions_scoring.parquet",
            sort_keys=["loan_id", "monthly_reporting_period"],
        )

        manifest = {
            "model_type": "LightGBM + Isotonic Calibration",
            "baseline_model_type": "LogisticRegression (L2, balanced)",
            "targets_trained": [t[1] for t in targets_binary] + ["next_state"],
            "scoring_record_count": len(predictions_df),
            "metrics": metrics_summary,
            "baseline_metrics": baseline_metrics_summary,
            "model_comparison": model_comparison,
        }
        context.store.write_json(manifest, self.name, "models_manifest.json")
        # Also write standalone comparison artifact for report template
        context.store.write_json(model_comparison, self.name, "model_comparison.json")

        # Serialize complete trained model bundle so models are persisted to disk
        model_bundle = {
            "fitted_models": fitted_models,
            "multistate_model": multistate,
            "baseline_models": baseline_models_fitted,
            "feature_cols": feature_cols,
            "stage_seed": context.stage_seed,
        }
        context.store.write_joblib(model_bundle, self.name, "models_bundle.joblib")
        return manifest


global_stage_registry.register(TrainStage())
