from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from lpie.conf.loader import load_schema_config
from lpie.data.reader import stream_origination_files, stream_performance_files
from lpie.data.sample import compute_whole_loan_sample
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class IngestStage(BaseStage):
    name = "ingest"
    declared_inputs: List[str] = []
    declared_outputs: List[str] = [
        "origination.parquet",
        "performance.parquet",
        "sampling_manifest.json",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        schema = load_schema_config(context.config.schema_file)
        data_raw = context.data_raw_dir

        # Read origination files to build loan inventory
        orig_dfs = []
        for chunk in stream_origination_files(data_raw, schema, chunksize=50000):
            orig_dfs.append(chunk)

        if orig_dfs:
            orig_full = pd.concat(orig_dfs, ignore_index=True)
        else:
            orig_full = pd.DataFrame(columns=schema.origination_names)

        # Sampling step
        target_loans = context.config.sampling.target_loans_total
        if context.config.sampling.enabled and len(orig_full) > target_loans:
            # Derive vintage from first_payment_date
            loan_inv = pd.DataFrame({
                "loan_id": orig_full["loan_id"],
                "vintage": orig_full["first_payment_date"].apply(lambda x: int(str(x)[:4]) if pd.notna(x) and len(str(x)) >= 4 else 2006),
            })
            sampling_res = compute_whole_loan_sample(
                loan_inventory=loan_inv,
                target_total_loans=target_loans,
                retain_all_credit_events=context.config.sampling.retain_all_credit_events,
                seed=context.stage_seed,
            )
            admitted_ids = sampling_res.sampled_loan_ids
            orig_admitted = orig_full[orig_full["loan_id"].isin(admitted_ids)].copy()
        else:
            admitted_ids = set(orig_full["loan_id"].tolist())
            orig_admitted = orig_full.copy()
            sampling_res = None

        # Stream performance records for admitted loans
        perf_dfs = []
        for chunk in stream_performance_files(data_raw, schema, admitted_loan_ids=admitted_ids, chunksize=100000):
            perf_dfs.append(chunk)

        if perf_dfs:
            perf_full = pd.concat(perf_dfs, ignore_index=True)
        else:
            perf_full = pd.DataFrame(columns=schema.performance_names)

        # Write artifacts
        context.store.write_parquet(orig_admitted, self.name, "origination.parquet", sort_keys=["loan_id"])
        context.store.write_parquet(perf_full, self.name, "performance.parquet", sort_keys=["loan_id", "monthly_reporting_period"])

        sampling_info = {
            "total_origination_loans": len(orig_full),
            "admitted_loans": len(orig_admitted),
            "admitted_performance_rows": len(perf_full),
        }
        context.store.write_json(sampling_info, self.name, "sampling_manifest.json")

        return sampling_info


global_stage_registry.register(IngestStage())
