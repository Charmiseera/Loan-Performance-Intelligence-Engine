from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class FeatureSpec:
    name: str
    dtype: str = "float64"
    window: Tuple[int, int] = (0, 0)  # (relative_start_month, relative_end_month), e.g. (-6, 0)
    source: Optional[str] = None
    agg: Optional[str] = None
    description: str = ""
    is_categorical: bool = False

    def __post_init__(self):
        # Strict Principle II assertion: No feature can look into the future
        lo, hi = self.window
        if hi > 0:
            raise ValueError(
                f"Principle II VIOLATION: Forward-looking feature window ({lo}, {hi}) for feature '{self.name}' is forbidden."
            )


class FeatureRegistry:
    """Registry maintaining active feature specifications with leakage enforcement."""

    def __init__(self):
        self._specs: Dict[str, FeatureSpec] = {}

    def register(self, spec: FeatureSpec) -> None:
        self._specs[spec.name] = spec

    def get_feature(self, name: str) -> Optional[FeatureSpec]:
        return self._specs.get(name)

    def list_features(self) -> List[FeatureSpec]:
        return list(self._specs.values())

    @property
    def feature_names(self) -> List[str]:
        return list(self._specs.keys())
