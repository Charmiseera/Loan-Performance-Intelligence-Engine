from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from lpie.conf.models import PipelineConfig
from lpie.store.store import ArtifactStore


@dataclass
class StageContext:
    """Context container provided to every stage during execution."""
    config: PipelineConfig
    store: ArtifactStore
    stage_seed: int
    data_raw_dir: Path
    artifacts_dir: Path
    custom_options: Dict[str, Any] = field(default_factory=dict)


class BaseStage(ABC):
    """
    Abstract base class for all pipeline stages.
    Pure DAG nodes with explicitly declared input and output artifacts.
    """
    name: str = "base_stage"
    declared_inputs: List[str] = []
    declared_outputs: List[str] = []

    @abstractmethod
    def run(self, context: StageContext) -> Dict[str, Any]:
        """
        Execute stage operations.
        Reads declared input artifacts from context.store and writes declared output artifacts.
        Returns a metrics/summary dictionary to be recorded in run manifest and stage metrics.
        """
        pass
