from typing import Dict, Any, List
import pytest
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import StageRegistry


class MockIngestStage(BaseStage):
    name = "ingest"
    declared_inputs: List[str] = []
    declared_outputs: List[str] = ["origination.parquet", "performance.parquet"]

    def run(self, ctx: StageContext) -> Dict[str, Any]:
        return {"records_read": 100}


class MockSplitStage(BaseStage):
    name = "split"
    declared_inputs: List[str] = ["origination.parquet", "performance.parquet"]
    declared_outputs: List[str] = ["split_definition.json"]

    def run(self, ctx: StageContext) -> Dict[str, Any]:
        return {"splits_created": 3}


class MockNarrateStage(BaseStage):
    name = "narrate"
    declared_inputs: List[str] = ["split_definition.json"]
    declared_outputs: List[str] = ["reviewer_notes.md"]

    def run(self, ctx: StageContext) -> Dict[str, Any]:
        return {"notes_generated": 5}


class MockSubmitStage(BaseStage):
    name = "submit"
    declared_inputs: List[str] = ["split_definition.json"]
    declared_outputs: List[str] = ["submission.csv"]

    def run(self, ctx: StageContext) -> Dict[str, Any]:
        return {"rows": 10}


def test_stage_registry_topological_sort():
    registry = StageRegistry()
    registry.register(MockSubmitStage())
    registry.register(MockSplitStage())
    registry.register(MockIngestStage())
    registry.register(MockNarrateStage())

    ordered = registry.get_topological_order()
    names = [s.name for s in ordered]
    assert names.index("ingest") < names.index("split")
    assert names.index("split") < names.index("submit")
    assert names.index("split") < names.index("narrate")


def test_stage_registry_transitive_inputs_closure():
    registry = StageRegistry()
    registry.register(MockIngestStage())
    registry.register(MockSplitStage())
    registry.register(MockNarrateStage())
    registry.register(MockSubmitStage())

    # Check transitive closure of submit inputs
    submit_transitive_inputs = registry.get_transitive_input_artifacts("submit")
    assert "origination.parquet" in submit_transitive_inputs
    assert "split_definition.json" in submit_transitive_inputs
    # LLM stage output 'reviewer_notes.md' must NOT be in submit's transitive inputs!
    assert "reviewer_notes.md" not in submit_transitive_inputs
