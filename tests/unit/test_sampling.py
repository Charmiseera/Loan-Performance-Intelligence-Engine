import pandas as pd
import pytest
from lpie.data.sample import compute_whole_loan_sample, StratifiedSamplingResult


def test_stratified_whole_loan_sampling():
    # Synthetic loan inventory: 10 loans across 2 vintages (2006, 2020)
    # 2 have credit events (ZB in 02, 03, 09, 15)
    loan_df = pd.DataFrame({
        "loan_id": [f"L{i:03d}" for i in range(10)],
        "vintage": [2006]*5 + [2020]*5,
        "is_credit_event": [False, True, False, False, False, False, False, True, False, False],
    })
    
    result = compute_whole_loan_sample(
        loan_inventory=loan_df,
        target_total_loans=6,
        retain_all_credit_events=True,
        seed=42,
    )
    
    assert len(result.sampled_loan_ids) <= 6
    # Both credit events must be retained
    assert "L001" in result.sampled_loan_ids
    assert "L007" in result.sampled_loan_ids
    
    # Check weight map
    assert len(result.sampling_weights) == len(result.sampled_loan_ids)
    assert result.sampling_weights["L001"] == 1.0  # Retained with prob 1.0
