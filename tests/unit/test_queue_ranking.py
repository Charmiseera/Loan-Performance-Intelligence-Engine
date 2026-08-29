import pandas as pd
import numpy as np
from lpie.anomaly.queue import prioritize_reviewer_queue
from lpie.anomaly.reconciliation import generate_reconciliation_fixture


def test_prioritize_reviewer_queue():
    df = pd.DataFrame({
        "loan_id": [f"L_{i:03d}" for i in range(50)],
        "monthly_reporting_period": [202401] * 50,
        "anomaly_score": np.linspace(0.1, 0.99, 50),
        "exception_required": [1 if i % 5 == 0 else 0 for i in range(50)],
        "rule_severity": ["HIGH" if i % 5 == 0 else "LOW" for i in range(50)],
        "current_actual_upb": [150000.0] * 50,
    })

    queue = prioritize_reviewer_queue(df, min_items=20)
    assert len(queue) == 20
    assert queue[0]["queue_rank"] == 1
    assert queue[0]["priority_score"] >= queue[-1]["priority_score"]
    assert "flag_source" in queue[0]


def test_generate_reconciliation_fixture():
    df = pd.DataFrame({
        "loan_id": ["L1", "L2", "L3"],
        "monthly_reporting_period": [202401, 202401, 202401],
        "current_actual_upb": [250000.0, 180000.0, 320000.0],
        "current_loan_delinquency_status": ["0", "1", "0"],
    })

    fixture = generate_reconciliation_fixture(df, sample_size=3)
    assert len(fixture) == 3
    assert "source_b_master_servicer_upb" in fixture.columns
    assert "fixture_provenance" in fixture.columns
    assert "CONSTRUCTED" in fixture["fixture_provenance"].iloc[0]
