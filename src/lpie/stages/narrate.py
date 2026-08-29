from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from lpie.conf.loader import load_llm_config
from lpie.llm.grounding import GroundingValidator
from lpie.llm.offline_provider import OfflineTemplateProvider
from lpie.llm.promptlog import PromptLogger
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


class NarrateStage(BaseStage):
    name = "narrate"
    declared_inputs: List[str] = [
        "reviewer_queue.json",
        "feature_matrix_scoring.parquet",
        "predictions_scoring.parquet",
    ]
    declared_outputs: List[str] = [
        "reviewer_notes.md",
        "prompt_log.jsonl",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        llm_cfg = load_llm_config(context.config.llm_file)
        queue = context.store.read_json("anomaly", "reviewer_queue.json")
        score_feats = context.store.read_parquet("features", "feature_matrix_scoring.parquet")
        score_preds = context.store.read_parquet("train", "predictions_scoring.parquet")

        prompt_logger = PromptLogger(context.store.get_artifact_path(self.name, "prompt_log.jsonl"))
        grounding_validator = GroundingValidator()
        provider = OfflineTemplateProvider()  # Deterministic offline provider default

        notes: List[str] = ["# Reviewer Case Summary Notes\n"]
        accepted_count = 0
        total_cases = min(5, len(queue))

        for item in queue[:total_cases]:
            lid = item["loan_id"]
            row_feat = score_feats[score_feats["loan_id"] == lid]
            row_pred = score_preds[score_preds["loan_id"] == lid]

            ctx_data = {
                "loan_id": lid,
                "credit_score": float(row_feat["credit_score"].iloc[0]) if not row_feat.empty and "credit_score" in row_feat.columns and pd.notna(row_feat["credit_score"].iloc[0]) else 700.0,
                "original_upb": float(row_feat["original_upb"].iloc[0]) if not row_feat.empty and "original_upb" in row_feat.columns else 200000.0,
                "prob_default_12m": float(row_pred["prob_default_12m"].iloc[0]) if not row_pred.empty else 0.05,
                "prob_prepay_12m": float(row_pred["prob_prepay_12m"].iloc[0]) if not row_pred.empty else 0.10,
                "exception_type": item.get("exception_type", "NONE"),
                "top_drivers": "credit_score; current_actual_upb",
                "recommended_action": item.get("recommended_action", "MONITOR"),
            }

            prompt = f"Generate reviewer note for loan {lid} with context {ctx_data}"
            raw_note = provider.generate(prompt, ctx_data)

            # Grounding check
            val_res = grounding_validator.validate(raw_note, ctx_data)
            prompt_logger.log_call(
                provider="offline",
                model_id=llm_cfg.model_id,
                prompt=prompt,
                response=raw_note,
                grounding_context=ctx_data,
                is_accepted=val_res.is_valid,
                rejection_reasons=val_res.unresolved_claims,
            )

            if val_res.is_valid:
                notes.append(raw_note + "\n\n---\n")
                accepted_count += 1

        full_md = "\n".join(notes)
        context.store.write_markdown(full_md, self.name, "reviewer_notes.md")

        return {
            "cases_processed": total_cases,
            "accepted_notes": accepted_count,
            "rejection_count": total_cases - accepted_count,
        }


global_stage_registry.register(NarrateStage())
