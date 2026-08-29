import json
import logging
from pathlib import Path
from typing import Union
import pandas as pd

logger = logging.getLogger("lpie.validator")


def validate_submission_file(
    submission_path: Union[str, Path] = "artifacts/submission/submission.csv",
    schema_path: Union[str, Path] = "specs/001-loan-performance-intelligence/contracts/submission_schema.json",
) -> int:
    """Validate submission.csv against schema contract."""
    sub_p = Path(submission_path)
    schema_p = Path(schema_path)

    if not sub_p.exists():
        logger.error(f"Submission file does not exist: {sub_p}")
        return 1
    if not schema_p.exists():
        logger.error(f"Submission schema does not exist: {schema_p}")
        return 1

    df = pd.read_csv(sub_p)
    logger.info(f"Loaded submission file with {len(df)} rows and {len(df.columns)} columns")

    with open(schema_p, "r", encoding="utf-8") as f:
        schema_json = json.load(f)

    # Validate column list
    req_cols = schema_json.get("required", [])
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Validation FAILED: Missing required columns: {missing_cols}")
        return 1

    # Check for nulls in required columns
    for col in req_cols:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            logger.error(f"Validation FAILED: Column '{col}' contains {null_count} nulls")
            return 1

    logger.info("Submission validation PASSED: all columns and non-null constraints satisfied.")
    return 0
