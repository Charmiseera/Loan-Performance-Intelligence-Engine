from pathlib import Path
import pytest
from tests.fixtures.make_tiny_panel import generate_tiny_panel_dfs, write_tiny_pipe_delimited_files


@pytest.fixture
def synthetic_panel_dfs():
    """Returns in-memory synthetic origination and performance DataFrames."""
    return generate_tiny_panel_dfs()


@pytest.fixture
def synthetic_raw_dir(tmp_path):
    """Writes synthetic raw pipe-delimited sample files into a temporary directory."""
    raw_dir = tmp_path / "data" / "raw"
    write_tiny_pipe_delimited_files(raw_dir)
    return raw_dir


@pytest.fixture
def sample_config_path(tmp_path):
    """Provides path to test configuration."""
    return Path("config/pipeline.yaml")
