from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import platform
import sys
from typing import Any, Dict, List, Optional
import lightgbm
import numpy as np
import pandas as pd
import pyarrow
import sklearn
import xgboost


@dataclass
class StageExecutionRecord:
    stage_name: str
    status: str  # "SUCCESS", "FAILED", "SKIPPED"
    start_time_utc: str
    end_time_utc: str
    duration_seconds: float
    input_artifacts: List[str] = field(default_factory=list)
    output_artifacts: List[str] = field(default_factory=list)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class RunManifest:
    """
    Provenance manifest recording full execution environment, seeds, config hashes, and stage timings.
    Satisfies Principle IV (Reproducibility) and SC-002.
    """
    run_id: str
    root_seed: int
    config_hash: str
    start_time_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time_utc: Optional[str] = None
    total_duration_seconds: float = 0.0
    python_version: str = field(default_factory=lambda: sys.version.split()[0])
    os_info: str = field(default_factory=lambda: f"{platform.system()} {platform.release()}")
    package_versions: Dict[str, str] = field(default_factory=lambda: {
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "pyarrow": pyarrow.__version__,
        "scikit-learn": sklearn.__version__,
        "lightgbm": lightgbm.__version__,
        "xgboost": xgboost.__version__,
    })
    stages: Dict[str, StageExecutionRecord] = field(default_factory=dict)

    @classmethod
    def create(cls, root_seed: int, config_bytes: bytes) -> "RunManifest":
        config_hash = hashlib.sha256(config_bytes).hexdigest()
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{config_hash[:8]}"
        return cls(run_id=run_id, root_seed=root_seed, config_hash=config_hash)

    def record_stage(self, stage_record: StageExecutionRecord) -> None:
        self.stages[stage_record.stage_name] = stage_record

    def finalize(self) -> None:
        self.end_time_utc = datetime.now(timezone.utc).isoformat()
        if self.start_time_utc and self.end_time_utc:
            t0 = datetime.fromisoformat(self.start_time_utc)
            t1 = datetime.fromisoformat(self.end_time_utc)
            self.total_duration_seconds = (t1 - t0).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
