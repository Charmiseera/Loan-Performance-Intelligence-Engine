"""Pipeline stages package."""

from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import StageRegistry, global_stage_registry

# Import all stages to trigger automatic registration in global_stage_registry
import lpie.stages.ingest
import lpie.stages.contract
import lpie.stages.label
import lpie.stages.split
import lpie.stages.features
import lpie.stages.train
import lpie.stages.survival
import lpie.stages.anomaly
import lpie.stages.explain
import lpie.stages.scenario
import lpie.stages.narrate
import lpie.stages.profile
import lpie.stages.report
import lpie.stages.submit

__all__ = ["BaseStage", "StageContext", "StageRegistry", "global_stage_registry"]
