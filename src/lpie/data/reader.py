from pathlib import Path
from typing import Generator, List, Optional, Set, Union
import pandas as pd
from lpie.conf.models import SchemaConfig
from lpie.data.sentinels import apply_sentinel_policy


def find_raw_files(data_raw_dir: Union[str, Path], prefix: str) -> List[Path]:
    """Find and return all raw files starting with prefix (e.g. 'sample_orig_' or 'sample_perf_')."""
    p = Path(data_raw_dir)
    if not p.exists():
        return []
    # Match both .txt and .csv or uncompressed files
    files = sorted([f for f in p.glob(f"{prefix}*.txt")] + [f for f in p.glob(f"{prefix}*.csv")])
    return files


def stream_origination_files(
    data_raw_dir: Union[str, Path],
    schema: SchemaConfig,
    admitted_loan_ids: Optional[Set[str]] = None,
    chunksize: int = 50000,
) -> Generator[pd.DataFrame, None, None]:
    """
    Stream and parse raw origination files in bounded chunks with schema narrowing.
    """
    files = find_raw_files(data_raw_dir, "sample_orig_")
    names = schema.origination_names
    dtypes = schema.origination_dtypes
    sentinels = schema.origination_sentinels

    for fpath in files:
        for chunk in pd.read_csv(
            fpath,
            sep="|",
            header=None,
            names=names,
            dtype=dtypes,
            chunksize=chunksize,
            low_memory=False,
            na_values=["", " "],
            keep_default_na=True,
        ):
            if admitted_loan_ids is not None:
                chunk = chunk[chunk["loan_id"].isin(admitted_loan_ids)]
            if chunk.empty:
                continue
            chunk_clean, _ = apply_sentinel_policy(chunk, sentinels)
            yield chunk_clean


def stream_performance_files(
    data_raw_dir: Union[str, Path],
    schema: SchemaConfig,
    admitted_loan_ids: Optional[Set[str]] = None,
    chunksize: int = 100000,
) -> Generator[pd.DataFrame, None, None]:
    """
    Stream and parse raw monthly performance files in bounded chunks with schema narrowing.
    """
    files = find_raw_files(data_raw_dir, "sample_perf_")
    names = schema.performance_names
    dtypes = schema.performance_dtypes
    sentinels = schema.performance_sentinels

    for fpath in files:
        for chunk in pd.read_csv(
            fpath,
            sep="|",
            header=None,
            names=names,
            dtype=dtypes,
            chunksize=chunksize,
            low_memory=False,
            na_values=["", " "],
            keep_default_na=True,
        ):
            if admitted_loan_ids is not None:
                chunk = chunk[chunk["loan_id"].isin(admitted_loan_ids)]
            if chunk.empty:
                continue
            chunk_clean, _ = apply_sentinel_policy(chunk, sentinels)
            yield chunk_clean
