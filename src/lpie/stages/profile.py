from typing import Any, Dict, List
import pandas as pd
from lpie.advanced.drift_monitor import compute_high_resolution_drift
from lpie.data.drift import compute_population_drift
from lpie.data.profile_stats import compute_column_statistics, detect_missingness_patterns
from lpie.data.quality_score import compute_record_quality_scores
from lpie.data.rule_evaluator import evaluate_cross_column_rules
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class ProfileStage(BaseStage):
    name = "profile"
    declared_inputs: List[str] = ["origination.parquet", "performance.parquet"]
    declared_outputs: List[str] = [
        "profile_metrics.json",
        "quality_scores.parquet",
        "population_drift.json",
        "advanced_drift_metrics.json",
        "validation_rules_summary.json",
        "data_intelligence_report.md",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        df_orig = context.store.read_parquet("ingest", "origination.parquet")
        df_perf = context.store.read_parquet("ingest", "performance.parquet")

        total_loans = len(df_orig)
        total_perf_rows = len(df_perf)

        # 1. Column distribution statistics & missingness patterns (FR-010, FR-011)
        orig_stats = compute_column_statistics(df_orig)
        missing_patterns = detect_missingness_patterns(df_orig, top_k=5)

        # 2. Cross-column business validation rules (FR-013, FR-015)
        rule_eval_results = evaluate_cross_column_rules(df_orig)
        context.store.write_json(rule_eval_results, self.name, "validation_rules_summary.json")

        # 3. Record-level & batch-level data quality scores (FR-017, FR-018, SC-016)
        quality_df, batch_quality = compute_record_quality_scores(df_orig)
        quality_df["loan_id"] = df_orig["loan_id"] if "loan_id" in df_orig.columns else df_orig.index
        context.store.write_parquet(quality_df, self.name, "quality_scores.parquet", sort_keys=["loan_id"])

        # 4. High-Resolution Population drift (FR-016, FR-106, SC-015)
        drift_results = []
        adv_drift = []
        if not df_perf.empty and "monthly_reporting_period" in df_perf.columns:
            sorted_months = sorted(df_perf["monthly_reporting_period"].dropna().unique())
            if len(sorted_months) >= 4:
                split_idx = len(sorted_months) * 2 // 3
                early_months = sorted_months[:split_idx]
                late_months = sorted_months[split_idx:]
                early_df = df_perf[df_perf["monthly_reporting_period"].isin(early_months)]
                late_df = df_perf[df_perf["monthly_reporting_period"].isin(late_months)]
                drift_results = compute_population_drift(early_df, late_df)
                adv_drift = compute_high_resolution_drift(early_df, late_df)

        context.store.write_json(drift_results, self.name, "population_drift.json")
        context.store.write_json(adv_drift, self.name, "advanced_drift_metrics.json")

        profile_summary = {
            "total_loans": total_loans,
            "total_monthly_records": total_perf_rows,
            "origination_column_statistics": orig_stats,
            "missingness_patterns": missing_patterns,
            "batch_quality_score": batch_quality,
            "rule_violations": {k: v.get("violation_count", 0) for k, v in rule_eval_results.items()},
            "top_drift_features": [d["feature"] for d in drift_results[:5]],
        }
        context.store.write_json(profile_summary, self.name, "profile_metrics.json")

        # Render complete markdown report
        lines = [
            "# Data Intelligence and Profiling Report\n",
            f"- **Total Loans Ingested**: {total_loans:,}",
            f"- **Total Monthly Performance Records**: {total_perf_rows:,}",
            f"- **Batch Quality Score**: {batch_quality['batch_mean_quality_score']:.1f} / 100.0 (High Quality Share: {batch_quality['high_quality_record_share']:.1%})",
            f"- **Completeness / Validity / Consistency**: {batch_quality['mean_completeness']:.1f} / {batch_quality['mean_validity']:.1f} / {batch_quality['mean_consistency']:.1f}\n",
            "## Deterministic Cross-Column Rule Evaluations",
        ]
        for r_code, r_data in rule_eval_results.items():
            lines.append(f"- **{r_data['rule_name']}**: {r_data['violation_count']} violations ({r_data['violation_rate']:.2%}) — Severity: {r_data['severity']}")

        if drift_results:
            lines.append("\n## Population Drift Analysis (Top Shifted Features)")
            lines.append("| Feature | PSI | KS Statistic | Drift Status | Alert |")
            lines.append("|---|---|---|---|---|")
            for d in adv_drift[:10]:
                lines.append(f"| {d['feature']} | {d['psi']:.4f} | {d['ks_statistic']:.4f} | {d['drift_status']} | {d['alert_level']} |")

        context.store.write_markdown("\n".join(lines), self.name, "data_intelligence_report.md")
        return profile_summary


global_stage_registry.register(ProfileStage())
