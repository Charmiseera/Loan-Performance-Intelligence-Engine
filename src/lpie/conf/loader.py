import json
from pathlib import Path
from typing import Any, Dict, Union
import yaml

from lpie.conf.models import (
    FieldSpec,
    LLMConfig,
    PathsConfig,
    PipelineConfig,
    SamplingConfig,
    ScenariosConfig,
    ScenarioShift,
    SchemaConfig,
    SplitsConfig,
    SplitWindow,
    StageConfig,
)


def load_yaml_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_json_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON configuration file not found: {path.resolve()}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_pipeline_config(config_path: Union[str, Path]) -> PipelineConfig:
    """Load main pipeline configuration from YAML."""
    raw = load_yaml_config(config_path)
    
    paths_data = raw.get("paths", {})
    paths = PathsConfig(
        data_raw_dir=paths_data.get("data_raw_dir", "data/raw"),
        artifacts_dir=paths_data.get("artifacts_dir", "artifacts"),
        reports_dir=paths_data.get("reports_dir", "artifacts/reports"),
        contracts_dir=paths_data.get("contracts_dir", "specs/001-loan-performance-intelligence/contracts"),
    )

    sampling_data = raw.get("sampling", {})
    sampling = SamplingConfig(
        enabled=sampling_data.get("enabled", True),
        target_loans_total=sampling_data.get("target_loans_total", 60000),
        stratified_by_vintage=sampling_data.get("stratified_by_vintage", True),
        retain_all_credit_events=sampling_data.get("retain_all_credit_events", True),
        seed=sampling_data.get("seed", raw.get("seed", 42)),
    )

    stages_dict = {}
    for stage_name, stage_val in raw.get("stages", {}).items():
        if isinstance(stage_val, bool):
            stages_dict[stage_name] = StageConfig(enabled=stage_val)
        elif isinstance(stage_val, dict):
            stages_dict[stage_name] = StageConfig(
                enabled=stage_val.get("enabled", True),
                options=stage_val.get("options", {}),
            )

    return PipelineConfig(
        seed=raw.get("seed", 42),
        paths=paths,
        sampling=sampling,
        stages=stages_dict,
        schema_file=raw.get("schema_file", "config/schema_r47.yaml"),
        field_mapping_file=raw.get("field_mapping_file", "config/field_mapping.yaml"),
        splits_file=raw.get("splits_file", "config/splits.yaml"),
        features_file=raw.get("features_file", "config/features.yaml"),
        scenarios_file=raw.get("scenarios_file", "config/scenarios.yaml"),
        llm_file=raw.get("llm_file", "config/llm.yaml"),
        validation_rules_file=raw.get("validation_rules_file", "config/validation_rules.json"),
    )


def load_schema_config(schema_path: Union[str, Path]) -> SchemaConfig:
    """Load R47 schema configuration."""
    raw = load_yaml_config(schema_path)
    
    orig_fields = [
        FieldSpec(
            position=item["position"],
            name=item["name"],
            dtype=item["dtype"],
            description=item.get("description", ""),
            sentinels=item.get("sentinels", []),
            decodes=item.get("decodes", {}),
            is_key=item.get("is_key", False),
            is_temporal_key=item.get("is_temporal_key", False),
        )
        for item in raw.get("origination_fields", [])
    ]
    
    perf_fields = [
        FieldSpec(
            position=item["position"],
            name=item["name"],
            dtype=item["dtype"],
            description=item.get("description", ""),
            sentinels=item.get("sentinels", []),
            decodes=item.get("decodes", {}),
            is_key=item.get("is_key", False),
            is_temporal_key=item.get("is_temporal_key", False),
        )
        for item in raw.get("performance_fields", [])
    ]

    return SchemaConfig(origination_fields=orig_fields, performance_fields=perf_fields)


def load_splits_config(splits_path: Union[str, Path]) -> SplitsConfig:
    """Load temporal splits configuration."""
    raw = load_yaml_config(splits_path)
    return SplitsConfig(
        embargo_months=raw.get("embargo_months", 12),
        train=SplitWindow(**raw["train"]),
        validation=SplitWindow(**raw["validation"]),
        scoring=SplitWindow(**raw["scoring"]),
    )


def load_scenarios_config(scenarios_path: Union[str, Path]) -> ScenariosConfig:
    """Load macroeconomic scenario configurations."""
    raw = load_yaml_config(scenarios_path)
    return ScenariosConfig(
        baseline=ScenarioShift(**raw["baseline"]),
        adverse=ScenarioShift(**raw["adverse"]),
        high_prepayment=ScenarioShift(**raw["high_prepayment"]),
    )


def load_llm_config(llm_path: Union[str, Path]) -> LLMConfig:
    """Load LLM copilot configuration."""
    raw = load_yaml_config(llm_path)
    return LLMConfig(
        provider=raw.get("provider", "offline"),
        model_id=raw.get("model_id", "qwen-2.5-32b"),
        api_key_env_var=raw.get("api_key_env_var", "GROQ_API_KEY"),
        temperature=float(raw.get("temperature", 0.0)),
        max_tokens=int(raw.get("max_tokens", 1024)),
        grounding_min_citation_coverage=float(raw.get("grounding_min_citation_coverage", 0.95)),
        strict_numeric_validation=bool(raw.get("strict_numeric_validation", True)),
    )
