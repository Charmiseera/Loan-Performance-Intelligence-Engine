from pathlib import Path
import pytest
from lpie.conf.loader import load_schema_config
from lpie.data.reader import stream_origination_files, stream_performance_files
from tests.fixtures.make_tiny_panel import write_tiny_pipe_delimited_files


def test_streaming_origination_and_performance(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    write_tiny_pipe_delimited_files(raw_dir)
    
    schema = load_schema_config("config/schema_r47.yaml")
    
    # Stream origination
    orig_chunks = list(stream_origination_files(raw_dir, schema, chunksize=10))
    assert len(orig_chunks) >= 1
    df_orig = orig_chunks[0]
    assert len(df_orig) == 5
    assert "loan_id" in df_orig.columns
    assert "credit_score" in df_orig.columns
    
    # Stream performance
    perf_chunks = list(stream_performance_files(raw_dir, schema, chunksize=20))
    assert len(perf_chunks) >= 1
    df_perf = perf_chunks[0]
    assert "loan_id" in df_perf.columns
    assert "monthly_reporting_period" in df_perf.columns
    assert "current_delinquency_status" in df_perf.columns
