from pathlib import Path
import pytest
import yaml
from lpie.cli import execute_pipeline
from tests.fixtures.make_tiny_panel import write_tiny_pipe_delimited_files


def test_pipeline_execution_with_llm_disabled(tmp_path):
    """
    FR-073 / SC-006:
    Execute pipeline with LLM / narrate stage disabled and verify that a valid
    submission.csv is still produced without errors.
    """
    raw_dir = tmp_path / "data" / "raw"
    art_dir = tmp_path / "artifacts"
    write_tiny_pipe_delimited_files(raw_dir)

    cfg_path = tmp_path / "config_no_llm.yaml"
    cfg_data = {
        "seed": 42,
        "paths": {
            "data_raw_dir": str(raw_dir),
            "artifacts_dir": str(art_dir),
            "reports_dir": str(art_dir / "reports"),
            "contracts_dir": "specs/001-loan-performance-intelligence/contracts",
        },
        "sampling": {"enabled": False, "target_loans_total": 1000, "seed": 42},
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
            "narrate": {"enabled": False},  # LLM disabled!
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
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg_data, f)

    exit_code = execute_pipeline(config_path=str(cfg_path))
    assert exit_code == 0, "Pipeline must run successfully without LLM"
    assert (art_dir / "submission" / "submission.csv").exists()
