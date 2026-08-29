from pathlib import Path
import pytest
from lpie.conf.loader import load_schema_config


def test_schema_config_matches_r47_field_counts():
    schema = load_schema_config("config/schema_r47.yaml")
    
    # R47 Origination must have exactly 31 fields (pos 1 to 31)
    assert len(schema.origination_fields) == 31
    orig_positions = [f.position for f in schema.origination_fields]
    assert orig_positions == list(range(1, 32))
    
    # R47 Performance must have exactly 35 fields (pos 1 to 35)
    assert len(schema.performance_fields) == 35
    perf_positions = [f.position for f in schema.performance_fields]
    assert perf_positions == list(range(1, 36))


def test_schema_config_key_definitions():
    schema = load_schema_config("config/schema_r47.yaml")
    
    # Origination join key
    orig_keys = [f.name for f in schema.origination_fields if f.is_key]
    assert orig_keys == ["loan_id"]
    
    # Performance join key and temporal key
    perf_keys = [f.name for f in schema.performance_fields if f.is_key]
    assert perf_keys == ["loan_id"]
    
    perf_temporal = [f.name for f in schema.performance_fields if f.is_temporal_key]
    assert perf_temporal == ["monthly_reporting_period"]


def test_schema_config_r47_critical_fields():
    schema = load_schema_config("config/schema_r47.yaml")
    
    # Servicer is in performance (pos 34) in R47, NOT in origination
    assert "servicer_name" in schema.performance_names
    assert "servicer_name" not in schema.origination_names
    
    # MI cancellation indicator is in performance (pos 33) in R47
    assert "mi_cancellation_indicator" in schema.performance_names
    assert "mi_cancellation_indicator" not in schema.origination_names
    
    # Actual loss is performance pos 22
    perf_pos_map = {f.position: f.name for f in schema.performance_fields}
    assert perf_pos_map[22] == "actual_loss"
    assert perf_pos_map[9] == "zero_balance_code"
    assert perf_pos_map[4] == "current_delinquency_status"
