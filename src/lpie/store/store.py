import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd


class ArtifactStore:
    """
    Deterministic filesystem storage manager for pipeline stage artifacts.
    Handles Parquet, JSON, JSONL, CSV, and Markdown.
    Guarantees deterministic sorting of rows and keys for reproducible outputs (Principle IV).
    """

    def __init__(self, base_dir: Union[str, Path] = "artifacts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_stage_dir(self, stage_name: str) -> Path:
        stage_dir = self.base_dir / stage_name
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir

    def get_artifact_path(self, stage_name: str, filename: str) -> Path:
        return self.get_stage_dir(stage_name) / filename

    def write_parquet(
        self,
        df: pd.DataFrame,
        stage_name: str,
        filename: str,
        sort_keys: Optional[List[str]] = None,
    ) -> Path:
        path = self.get_artifact_path(stage_name, filename)
        df_out = df.copy()
        if sort_keys:
            valid_keys = [k for k in sort_keys if k in df_out.columns]
            if valid_keys:
                df_out = df_out.sort_values(by=valid_keys).reset_index(drop=True)
        df_out.to_parquet(path, index=False, engine="pyarrow")
        return path

    def read_parquet(self, stage_name: str, filename: str) -> pd.DataFrame:
        path = self.get_artifact_path(stage_name, filename)
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {path}")
        return pd.read_parquet(path, engine="pyarrow")

    def write_json(self, data: Any, stage_name: str, filename: str) -> Path:
        path = self.get_artifact_path(stage_name, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, default=str)
        return path

    def read_json(self, stage_name: str, filename: str) -> Any:
        path = self.get_artifact_path(stage_name, filename)
        if not path.exists():
            raise FileNotFoundError(f"JSON artifact not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def append_jsonl(self, record: Dict[str, Any], stage_name: str, filename: str) -> Path:
        path = self.get_artifact_path(stage_name, filename)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True, default=str) + "\n")
        return path

    def read_jsonl(self, stage_name: str, filename: str) -> List[Dict[str, Any]]:
        path = self.get_artifact_path(stage_name, filename)
        if not path.exists():
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def write_markdown(self, content: str, stage_name: str, filename: str) -> Path:
        path = self.get_artifact_path(stage_name, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def read_markdown(self, stage_name: str, filename: str) -> str:
        path = self.get_artifact_path(stage_name, filename)
        if not path.exists():
            raise FileNotFoundError(f"Markdown artifact not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_csv(
        self,
        df: pd.DataFrame,
        stage_name: str,
        filename: str,
        sort_keys: Optional[List[str]] = None,
    ) -> Path:
        path = self.get_artifact_path(stage_name, filename)
        df_out = df.copy()
        if sort_keys:
            valid_keys = [k for k in sort_keys if k in df_out.columns]
            if valid_keys:
                df_out = df_out.sort_values(by=valid_keys).reset_index(drop=True)
        df_out.to_csv(path, index=False, encoding="utf-8")
        return path

    def write_joblib(self, obj: Any, stage_name: str, filename: str) -> Path:
        import joblib
        path = self.get_artifact_path(stage_name, filename)
        joblib.dump(obj, path)
        return path

    def read_joblib(self, stage_name: str, filename: str) -> Any:
        import joblib
        path = self.get_artifact_path(stage_name, filename)
        if not path.exists():
            raise FileNotFoundError(f"Joblib artifact not found: {path}")
        return joblib.load(path)
