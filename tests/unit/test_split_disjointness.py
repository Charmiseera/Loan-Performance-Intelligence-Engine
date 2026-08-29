import pytest
from lpie.conf.loader import load_splits_config


def test_split_temporal_ordering_and_embargo_gaps():
    splits = load_splits_config("config/splits.yaml")
    
    # 1. Windows must be ordered in time
    assert splits.train.start_month <= splits.train.end_month
    assert splits.validation.start_month <= splits.validation.end_month
    assert splits.scoring.start_month <= splits.scoring.end_month

    # 2. Maximum label horizon is 12 months, embargo must be >= 12
    assert splits.embargo_months >= 12

    # 3. Gap between train.end_month and validation.start_month must be >= embargo
    # Note: 201712 to 201901 is 13 months (>= 12)
    def month_diff(m1: int, m2: int) -> int:
        y1, mo1 = divmod(m1, 100)
        y2, mo2 = divmod(m2, 100)
        return (y2 - y1) * 12 + (mo2 - mo1)

    gap_train_val = month_diff(splits.train.end_month, splits.validation.start_month) - 1
    assert gap_train_val >= splits.embargo_months, (
        f"Embargo gap between train ({splits.train.end_month}) and val ({splits.validation.start_month}) "
        f"is {gap_train_val} months, must be >= {splits.embargo_months}"
    )

    gap_val_score = month_diff(splits.validation.end_month, splits.scoring.start_month) - 1
    assert gap_val_score >= splits.embargo_months, (
        f"Embargo gap between val ({splits.validation.end_month}) and scoring ({splits.scoring.start_month}) "
        f"is {gap_val_score} months, must be >= {splits.embargo_months}"
    )
