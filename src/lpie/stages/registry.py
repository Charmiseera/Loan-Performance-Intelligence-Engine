from collections import defaultdict, deque
from typing import Dict, List, Optional, Set
from lpie.stages.base import BaseStage


class StageRegistry:
    """
    Registry for pipeline stages.
    Maintains the stage dependency graph based on declared input/output artifacts.
    Supports topological sorting and static input closure analysis.
    """

    def __init__(self):
        self._stages: Dict[str, BaseStage] = {}

    def register(self, stage: BaseStage) -> None:
        self._stages[stage.name] = stage

    def get_stage(self, name: str) -> Optional[BaseStage]:
        return self._stages.get(name)

    def list_stages(self) -> List[str]:
        return list(self._stages.keys())

    def get_artifact_producer_map(self) -> Dict[str, str]:
        """Maps each declared output artifact filename to the producing stage name."""
        producer_map: Dict[str, str] = {}
        for stage_name, stage in self._stages.items():
            for art in stage.declared_outputs:
                producer_map[art] = stage_name
        return producer_map

    def get_stage_dependencies(self) -> Dict[str, Set[str]]:
        """Compute the set of upstream stage dependencies for each registered stage."""
        producer_map = self.get_artifact_producer_map()
        deps: Dict[str, Set[str]] = defaultdict(set)

        for stage_name, stage in self._stages.items():
            for in_art in stage.declared_inputs:
                if in_art in producer_map:
                    producer = producer_map[in_art]
                    if producer != stage_name:
                        deps[stage_name].add(producer)

        return deps

    def get_topological_order(self) -> List[BaseStage]:
        """
        Return stages sorted in topological execution order (Kahn's algorithm).
        """
        deps = self.get_stage_dependencies()
        in_degree = {name: len(deps[name]) for name in self._stages}
        
        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        ordered_names: List[str] = []

        # Adjacency list (upstream -> downstream)
        adj: Dict[str, List[str]] = defaultdict(list)
        for downstream, upstreams in deps.items():
            for upstream in upstreams:
                adj[upstream].append(downstream)

        while queue:
            curr = queue.popleft()
            ordered_names.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered_names) != len(self._stages):
            missing = set(self._stages.keys()) - set(ordered_names)
            raise ValueError(f"Cyclic dependency detected among stages: {missing}")

        return [self._stages[name] for name in ordered_names]

    def get_transitive_input_artifacts(self, stage_name: str) -> Set[str]:
        """
        Find the full set of transitive input artifacts required by a stage.
        Used by static checks to prove that submission path has zero LLM dependencies.
        """
        if stage_name not in self._stages:
            raise KeyError(f"Stage {stage_name} not registered")

        producer_map = self.get_artifact_producer_map()
        visited_artifacts: Set[str] = set()
        to_process = list(self._stages[stage_name].declared_inputs)

        while to_process:
            art = to_process.pop(0)
            if art in visited_artifacts:
                continue
            visited_artifacts.add(art)
            
            # If artifact was produced by a registered stage, add its declared inputs too
            if art in producer_map:
                prod_stage_name = producer_map[art]
                prod_stage = self._stages[prod_stage_name]
                for upstream_art in prod_stage.declared_inputs:
                    if upstream_art not in visited_artifacts:
                        to_process.append(upstream_art)

        return visited_artifacts


global_stage_registry = StageRegistry()
