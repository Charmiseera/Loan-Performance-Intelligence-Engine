import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import List, Optional

from lpie.conf.loader import load_pipeline_config
from lpie.conf.models import PipelineConfig
from lpie.conf.validator import validate_submission_file
from lpie.stages.base import StageContext
from lpie.stages.registry import StageRegistry, global_stage_registry
from lpie.store.manifest import RunManifest, StageExecutionRecord
from lpie.store.store import ArtifactStore
from lpie.util.logging import get_logger
from lpie.util.seed import derive_child_seed, set_global_seed

logger = get_logger("lpie.cli")


def execute_pipeline(
    config_path: str = "config/pipeline.yaml",
    selected_stages: Optional[List[str]] = None,
    registry: Optional[StageRegistry] = None,
) -> int:
    """
    Execute pipeline stages in topological dependency order.
    """
    if registry is None:
        registry = global_stage_registry

    cfg_p = Path(config_path)
    if not cfg_p.exists():
        logger.error(f"Config file not found: {cfg_p}")
        return 1

    with open(cfg_p, "rb") as f:
        config_bytes = f.read()

    config = load_pipeline_config(config_path)
    set_global_seed(config.seed)

    store = ArtifactStore(base_dir=config.paths.artifacts_dir)
    manifest = RunManifest.create(root_seed=config.seed, config_bytes=config_bytes)

    logger.info(f"=== Starting LPIE Pipeline Run ID: {manifest.run_id} (Seed: {config.seed}) ===")

    try:
        ordered_stages = registry.get_topological_order()
    except Exception as e:
        logger.error(f"Failed to resolve stage graph: {e}")
        return 1

    # Filter stages if requested
    if selected_stages:
        sel_set = set(selected_stages)
        ordered_stages = [s for s in ordered_stages if s.name in sel_set]

    for stage in ordered_stages:
        stage_cfg = config.stages.get(stage.name)
        if stage_cfg and not stage_cfg.enabled:
            logger.info(f"Skipping disabled stage: {stage.name}")
            continue

        stage_seed = derive_child_seed(config.seed, stage.name)
        ctx = StageContext(
            config=config,
            store=store,
            stage_seed=stage_seed,
            data_raw_dir=Path(config.paths.data_raw_dir),
            artifacts_dir=Path(config.paths.artifacts_dir),
            custom_options=stage_cfg.options if stage_cfg else {},
        )

        t_start = datetime.now(timezone.utc)
        logger.info(f"--- Running stage: {stage.name} (child seed: {stage_seed}) ---")

        try:
            metrics = stage.run(ctx)
            t_end = datetime.now(timezone.utc)
            duration = (t_end - t_start).total_seconds()

            # Record stage metrics
            store.write_json(metrics or {}, stage.name, "metrics.json")
            record = StageExecutionRecord(
                stage_name=stage.name,
                status="SUCCESS",
                start_time_utc=t_start.isoformat(),
                end_time_utc=t_end.isoformat(),
                duration_seconds=duration,
                input_artifacts=stage.declared_inputs,
                output_artifacts=stage.declared_outputs,
                metrics_summary=metrics or {},
            )
            manifest.record_stage(record)
            logger.info(f"Stage {stage.name} completed successfully in {duration:.2f}s")
        except Exception as e:
            t_end = datetime.now(timezone.utc)
            duration = (t_end - t_start).total_seconds()
            logger.exception(f"Stage {stage.name} FAILED: {e}")
            record = StageExecutionRecord(
                stage_name=stage.name,
                status="FAILED",
                start_time_utc=t_start.isoformat(),
                end_time_utc=t_end.isoformat(),
                duration_seconds=duration,
                input_artifacts=stage.declared_inputs,
                output_artifacts=stage.declared_outputs,
                error_message=str(e),
            )
            manifest.record_stage(record)
            manifest.finalize()
            store.write_json(manifest.to_dict(), "", "run_manifest.json")
            return 1

    manifest.finalize()
    store.write_json(manifest.to_dict(), "", "run_manifest.json")
    logger.info(f"=== Pipeline Run Completed in {manifest.total_duration_seconds:.2f}s ===")
    return 0


def validate_submission_file(
    submission_path: str = "artifacts/submission/submission.csv",
    schema_path: str = "specs/001-loan-performance-intelligence/contracts/submission_schema.json",
) -> int:
    """Validate submission.csv against schema contract."""
    sub_p = Path(submission_path)
    schema_p = Path(schema_path)

    if not sub_p.exists():
        logger.error(f"Submission file does not exist: {sub_p}")
        return 1
    if not schema_p.exists():
        logger.error(f"Submission schema does not exist: {schema_p}")
        return 1

    import pandas as pd
    df = pd.read_csv(sub_p)
    logger.info(f"Loaded submission file with {len(df)} rows and {len(df.columns)} columns")

    with open(schema_p, "r", encoding="utf-8") as f:
        schema_json = json.load(f)

    # Validate column list
    req_cols = schema_json.get("required", [])
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Validation FAILED: Missing required columns: {missing_cols}")
        return 1

    # Check for nulls in required columns
    for col in req_cols:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            logger.error(f"Validation FAILED: Column '{col}' contains {null_count} nulls")
            return 1

    logger.info("Submission validation PASSED: all columns and non-null constraints satisfied.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lpie",
        description="Loan Performance Intelligence Engine (LPIE) CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run the entire pipeline or a subset of stages")
    run_parser.add_argument("--config", default="config/pipeline.yaml", help="Path to pipeline YAML config")
    run_parser.add_argument("--stages", nargs="+", default=None, help="Specific stage names to run")

    # Command: stage
    stage_parser = subparsers.add_parser("stage", help="Run a single stage")
    stage_parser.add_argument("stage_name", help="Name of the stage to execute")
    stage_parser.add_argument("--config", default="config/pipeline.yaml", help="Path to pipeline YAML config")

    # Command: validate
    val_parser = subparsers.add_parser("validate", help="Validate submission.csv against contract")
    val_parser.add_argument("--submission", default="artifacts/submission/submission.csv", help="Path to submission.csv")
    val_parser.add_argument(
        "--schema",
        default="specs/001-loan-performance-intelligence/contracts/submission_schema.json",
        help="Path to submission schema JSON",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        return execute_pipeline(config_path=args.config, selected_stages=args.stages)
    elif args.command == "stage":
        return execute_pipeline(config_path=args.config, selected_stages=[args.stage_name])
    elif args.command == "validate":
        return validate_submission_file(submission_path=args.submission, schema_path=args.schema)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
