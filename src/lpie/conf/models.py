from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SamplingConfig:
    enabled: bool = True
    target_loans_total: int = 60000
    stratified_by_vintage: bool = True
    retain_all_credit_events: bool = True
    seed: int = 42


@dataclass
class PathsConfig:
    data_raw_dir: str = "data/raw"
    artifacts_dir: str = "artifacts"
    reports_dir: str = "artifacts/reports"
    contracts_dir: str = "specs/001-loan-performance-intelligence/contracts"


@dataclass
class StageConfig:
    enabled: bool = True
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    seed: int = 42
    paths: PathsConfig = field(default_factory=PathsConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    stages: Dict[str, StageConfig] = field(default_factory=dict)
    schema_file: str = "config/schema_r47.yaml"
    field_mapping_file: str = "config/field_mapping.yaml"
    splits_file: str = "config/splits.yaml"
    features_file: str = "config/features.yaml"
    scenarios_file: str = "config/scenarios.yaml"
    llm_file: str = "config/llm.yaml"
    validation_rules_file: str = "config/validation_rules.json"


@dataclass
class FieldSpec:
    position: int
    name: str
    dtype: str
    description: str = ""
    sentinels: List[Any] = field(default_factory=list)
    decodes: Dict[str, str] = field(default_factory=dict)
    is_key: bool = False
    is_temporal_key: bool = False


@dataclass
class SchemaConfig:
    origination_fields: List[FieldSpec] = field(default_factory=list)
    performance_fields: List[FieldSpec] = field(default_factory=list)

    @property
    def origination_names(self) -> List[str]:
        return [f.name for f in self.origination_fields]

    @property
    def performance_names(self) -> List[str]:
        return [f.name for f in self.performance_fields]

    @property
    def origination_dtypes(self) -> Dict[str, str]:
        return {f.name: f.dtype for f in self.origination_fields}

    @property
    def performance_dtypes(self) -> Dict[str, str]:
        return {f.name: f.dtype for f in self.performance_fields}

    @property
    def origination_sentinels(self) -> Dict[str, List[Any]]:
        return {f.name: f.sentinels for f in self.origination_fields if f.sentinels}

    @property
    def performance_sentinels(self) -> Dict[str, List[Any]]:
        return {f.name: f.sentinels for f in self.performance_fields if f.sentinels}


@dataclass
class SplitWindow:
    start_month: int
    end_month: int
    description: str = ""


@dataclass
class SplitsConfig:
    embargo_months: int = 12
    train: SplitWindow = field(default_factory=lambda: SplitWindow(200601, 201712, "Train window"))
    validation: SplitWindow = field(default_factory=lambda: SplitWindow(201901, 202112, "Validation window"))
    scoring: SplitWindow = field(default_factory=lambda: SplitWindow(202301, 202512, "Out-of-time scoring window"))


@dataclass
class ScenarioShift:
    name: str
    description: str
    interest_rate_shift_bps: float = 0.0
    hpi_growth_pct: float = 0.0
    unemployment_rate_delta_pct: float = 0.0
    prepayment_multiplier: float = 1.0
    default_multiplier: float = 1.0


@dataclass
class ScenariosConfig:
    baseline: ScenarioShift = field(default_factory=lambda: ScenarioShift("baseline", "Baseline macroeconomic conditions"))
    adverse: ScenarioShift = field(default_factory=lambda: ScenarioShift("adverse", "Adverse credit stress scenario"))
    high_prepayment: ScenarioShift = field(default_factory=lambda: ScenarioShift("high_prepayment", "High prepayment refi boom"))


@dataclass
class LLMConfig:
    provider: str = "offline"  # "groq" or "offline"
    model_id: str = "qwen-2.5-32b"
    api_key_env_var: str = "GROQ_API_KEY"
    temperature: float = 0.0
    max_tokens: int = 1024
    grounding_min_citation_coverage: float = 0.95
    strict_numeric_validation: bool = True
