from pathlib import Path
import pytest
import yaml
from lpie.cli import execute_pipeline
from lpie.stages.registry import global_stage_registry
from tests.fixtures.make_tiny_panel import write_tiny_pipe_delimited_files


def test_pipeline_end_to_end_on_synthetic_fixture(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    artifacts_dir = tmp_path / "artifacts"
    write_tiny_pipe_delimited_files(raw_dir)

    # Write a test pipeline config pointing to tmp_path
    test_cfg_path = tmp_path / "pipeline.yaml"
    cfg_data = {
        "seed": 42,
        "paths": {
            "data_raw_dir": str(raw_dir),
            "artifacts_dir": str(artifacts_dir),
            "reports_dir": str(artifacts_dir / "reports"),
            "contracts_dir": "specs/001-loan-performance-intelligence/contracts",
        },
        "sampling": {
            "enabled": False,
            "target_loans_total": 1000,
            "seed": 42,
        },
        "stages": {
            "ingest": {"enabled": True},
            "contract": {"enabled": True},
            "profile": {"enabled": True},
            "label": {"enabled": True},
            "split": {"enabled": True},
            "features": {"enabled": True},
            "train": {"enabled": True},
            "survival": {"enabled": True},
            "anomaly": {"enabled": True},
            "explain": {"enabled": True},
            "scenario": {"enabled": True},
            "narrate": {"enabled": True},
            "report": {"enabled": True},
            "submit": {"enabled": True},
        },
        "schema_file": "config/schema_r47.yaml",
        "field_mapping_file": "config/field_mapping.yaml",
        "splits_file": "config/splits.yaml",
        "features_file": "config/features.yaml",
        "scenarios_file": "config/scenarios.yaml",
        "llm_file": "config/llm.yaml",
        "validation_rules_file": "config/validation_rules.json",
    }
    with open(test_cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg_data, f)

    # Execute pipeline
    exit_code = execute_pipeline(config_path=str(test_cfg_path))
    assert exit_code == 0, "Full pipeline execution must succeed"

    # Verify declared output artifacts exist
    assert (artifacts_dir / "submission" / "submission.csv").exists()
    assert (artifacts_dir / "reports" / "model_card.md").exists()
    assert (artifacts_dir / "run_manifest.json").exists()
