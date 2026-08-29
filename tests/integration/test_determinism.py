import filecmp
from pathlib import Path
import pytest
import yaml
from lpie.cli import execute_pipeline
from tests.fixtures.make_tiny_panel import write_tiny_pipe_delimited_files


def test_seeded_pipeline_determinism_byte_identical(tmp_path):
    """
    FR-071 / SC-002:
    Execute two full seeded pipeline runs with the same configuration and seed
    and assert that the generated submission.csv files are byte-identical.
    """
    raw_dir = tmp_path / "data" / "raw"
    write_tiny_pipe_delimited_files(raw_dir)

    def run_with_output_dir(art_dir_name: str) -> Path:
        art_dir = tmp_path / art_dir_name
        cfg_path = tmp_path / f"config_{art_dir_name}.yaml"
        cfg_data = {
            "seed": 42,
            "paths": {
                "data_raw_dir": str(raw_dir),
                "artifacts_dir": str(art_dir),
                "reports_dir": str(art_dir / "reports"),
                "contracts_dir": "specs/001-loan-performance-intelligence/contracts",
            },
            "sampling": {"enabled": False, "target_loans_total": 1000, "seed": 42},
            "stages": {s: {"enabled": True} for s in [
                "ingest", "contract", "profile", "label", "split", "features",
                "train", "survival", "anomaly", "explain", "scenario", "narrate", "report", "submit"
            ]},
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

        res = execute_pipeline(config_path=str(cfg_path))
        assert res == 0
        return art_dir / "submission" / "submission.csv"

    sub1 = run_with_output_dir("run1")
    sub2 = run_with_output_dir("run2")

    assert sub1.exists()
    assert sub2.exists()
    assert filecmp.cmp(sub1, sub2, shallow=False), "Repeated seeded pipeline runs must produce byte-identical submission.csv"
