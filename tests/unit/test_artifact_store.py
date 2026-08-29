import json
from pathlib import Path
import pandas as pd
import pytest
from lpie.store.store import ArtifactStore


def test_artifact_store_write_read_parquet(tmp_path):
    store = ArtifactStore(base_dir=tmp_path)
    df = pd.DataFrame({
        "loan_id": ["F06Q10000002", "F06Q10000001"],
        "reporting_month": [200603, 200604],
        "val": [10.5, 20.2],
    })
    
    # Store should deterministically sort by primary key
    path = store.write_parquet(df, "test_stage", "sample.parquet", sort_keys=["loan_id", "reporting_month"])
    assert path.exists()
    
    df_read = store.read_parquet("test_stage", "sample.parquet")
    assert len(df_read) == 2
    assert df_read["loan_id"].iloc[0] == "F06Q10000001"  # Sorted first


def test_artifact_store_json_and_markdown(tmp_path):
    store = ArtifactStore(base_dir=tmp_path)
    data = {"b_key": 2, "a_key": 1}
    
    json_path = store.write_json(data, "metrics", "summary.json")
    assert json_path.exists()
    
    read_data = store.read_json("metrics", "summary.json")
    assert read_data == data
    
    md_content = "# Test Report\nContent here."
    md_path = store.write_markdown(md_content, "reports", "report.md")
    assert md_path.exists()
    assert store.read_markdown("reports", "report.md") == md_content
