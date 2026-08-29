from typing import Any, Dict, List
import pandas as pd
from lpie.labels.outcomes import compute_horizon_targets
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class LabelStage(BaseStage):
    name = "label"
    declared_inputs: List[str] = ["performance.parquet"]
    declared_outputs: List[str] = ["labeled_performance.parquet", "label_distribution.json"]

    def run(self, context: StageContext) -> Dict[str, Any]:
        df_perf = context.store.read_parquet("ingest", "performance.parquet")
        df_labeled = compute_horizon_targets(df_perf)

        context.store.write_parquet(
            df_labeled,
            self.name,
            "labeled_performance.parquet",
            sort_keys=["loan_id", "monthly_reporting_period"],
        )

        dist = {
            "total_rows": len(df_labeled),
            "target_deterioration_3m_rate": float(df_labeled["target_deterioration_3m"].mean()),
            "target_deterioration_6m_rate": float(df_labeled["target_deterioration_6m"].mean()),
            "target_default_12m_rate": float(df_labeled["target_default_12m"].mean()),
            "target_prepay_12m_rate": float(df_labeled["target_prepay_12m"].mean()),
            "target_next_state_counts": {k: int(v) for k, v in df_labeled["target_next_state"].value_counts().items()},
        }
        context.store.write_json(dist, self.name, "label_distribution.json")
        return dist


global_stage_registry.register(LabelStage())
