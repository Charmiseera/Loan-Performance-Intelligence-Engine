from pathlib import Path
import pytest
from lpie.conf.loader import (
    load_pipeline_config,
    load_schema_config,
    load_splits_config,
    load_scenarios_config,
    load_llm_config,
    load_json_config,
)


def test_load_pipeline_config():
    config = load_pipeline_config("config/pipeline.yaml")
    assert config.seed == 42
    assert config.paths.data_raw_dir == "data/raw"
    assert config.paths.artifacts_dir == "artifacts"
    assert "ingest" in config.stages
    assert config.stages["ingest"].enabled is True


def test_load_schema_config():
    schema = load_schema_config("config/schema_r47.yaml")
    assert len(schema.origination_fields) == 31, "R47 origination file must have 31 fields"
    assert len(schema.performance_fields) == 35, "R47 performance file must have 35 fields"
    
    assert "credit_score" in schema.origination_names
    assert "loan_id" in schema.origination_names
    assert "loan_id" in schema.performance_names
    assert "monthly_reporting_period" in schema.performance_names
    
    assert "credit_score" in schema.origination_sentinels
    assert 9999 in schema.origination_sentinels["credit_score"]


def test_load_splits_config():
    splits = load_splits_config("config/splits.yaml")
    assert splits.embargo_months == 12
    assert splits.train.start_month < splits.train.end_month
    assert splits.validation.start_month > splits.train.end_month
    assert splits.scoring.start_month > splits.validation.end_month


def test_load_scenarios_config():
    scenarios = load_scenarios_config("config/scenarios.yaml")
    assert scenarios.baseline.name == "baseline"
    assert scenarios.adverse.default_multiplier > 1.0
    assert scenarios.high_prepayment.prepayment_multiplier > 1.0


def test_load_validation_rules():
    rules = load_json_config("config/validation_rules.json")
    assert "rules" in rules
    assert len(rules["rules"]) >= 5
