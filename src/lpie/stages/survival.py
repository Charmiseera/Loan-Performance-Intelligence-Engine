from typing import Any, Dict, List
import pandas as pd
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry
from lpie.survival.cause_specific import compute_cause_specific_hazards
from lpie.survival.dataset import build_survival_dataset
from lpie.survival.incidence import compute_cumulative_incidence_functions


class SurvivalStage(BaseStage):
    name = "survival"
    declared_inputs: List[str] = ["labeled_performance.parquet"]
    declared_outputs: List[str] = [
        "survival_curves.json",
        "competing_risk_summary.json",
        "cause_specific_hazards.json",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        df = context.store.read_parquet("label", "labeled_performance.parquet")

        # 1. Build right-censored panel survival dataset (FR-037)
        # Sample for speed if large
        SURVIVAL_SAMPLE = 50_000
        unique_loans = df["loan_id"].drop_duplicates()
        if len(unique_loans) > SURVIVAL_SAMPLE:
            sampled_loans = unique_loans.sample(n=SURVIVAL_SAMPLE, random_state=context.stage_seed)
            df_sub = df[df["loan_id"].isin(sampled_loans)]
        else:
            df_sub = df

        survival_df = build_survival_dataset(df_sub, max_duration_months=120)

        # 2. Compute cause-specific hazards and risk set counts (FR-038, FR-040)
        hazards = compute_cause_specific_hazards(survival_df, max_time=60)
        context.store.write_json(hazards, self.name, "cause_specific_hazards.json")

        # 3. Compute Aalen-Johansen Cumulative Incidence Functions (FR-039, SC-012)
        cif_results = compute_cumulative_incidence_functions(hazards)

        curves = {
            "loan_ages": cif_results["time_points"],
            "risk_set_sizes": cif_results["at_risk"],
            "default_cumulative_incidence": cif_results["cif_default"],
            "prepayment_cumulative_incidence": cif_results["cif_prepay"],
            "overall_survival": cif_results["overall_survival"],
        }
        context.store.write_json(curves, self.name, "survival_curves.json")

        summary = {
            "model_type": "Cause-Specific Competing Risks (Aalen-Johansen CIF)",
            "censoring_handled": "Right-censoring at last observation month (FR-037)",
            "cohort_loans_analyzed": len(survival_df),
            "max_default_cif": max(cif_results["cif_default"]) if cif_results["cif_default"] else 0.0,
            "max_prepay_cif": max(cif_results["cif_prepay"]) if cif_results["cif_prepay"] else 0.0,
            "cif_sum_valid": cif_results["bounds_validated"],
        }
        context.store.write_json(summary, self.name, "competing_risk_summary.json")
        return summary


global_stage_registry.register(SurvivalStage())
