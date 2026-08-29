from typing import Any, Dict, List
import pandas as pd
from lpie.conf.loader import load_json_config, load_schema_config
from lpie.anomaly.rules import evaluate_deterministic_rules
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class ContractStage(BaseStage):
    name = "contract"
    declared_inputs: List[str] = ["origination.parquet", "performance.parquet"]
    declared_outputs: List[str] = ["contract_validation.json", "rule_violations.parquet"]

    def run(self, context: StageContext) -> Dict[str, Any]:
        df_orig = context.store.read_parquet("ingest", "origination.parquet")
        df_perf = context.store.read_parquet("ingest", "performance.parquet")
        rules_config = load_json_config(context.config.validation_rules_file)

        # Merge origination attributes to performance for cross-table rule validation
        combined = df_perf.merge(
            df_orig[["loan_id", "first_payment_date", "maturity_date", "original_upb", "credit_score", "original_ltv", "original_dti"]],
            on="loan_id",
            how="left",
        )

        violation_counts, violation_flags = evaluate_deterministic_rules(combined, rules_config)
        violation_flags["loan_id"] = combined["loan_id"]
        violation_flags["monthly_reporting_period"] = combined["monthly_reporting_period"]
        violation_flags["total_violations"] = violation_counts

        context.store.write_parquet(
            violation_flags,
            self.name,
            "rule_violations.parquet",
            sort_keys=["loan_id", "monthly_reporting_period"],
        )

        summary = {
            "total_records_evaluated": len(combined),
            "records_with_violations": int((violation_counts > 0).sum()),
            "violation_rate": float((violation_counts > 0).mean()),
            "violation_counts_by_rule": {col: int(violation_flags[col].sum()) for col in violation_flags.columns if col not in ("loan_id", "monthly_reporting_period", "total_violations")},
        }
        context.store.write_json(summary, self.name, "contract_validation.json")
        return summary


global_stage_registry.register(ContractStage())
