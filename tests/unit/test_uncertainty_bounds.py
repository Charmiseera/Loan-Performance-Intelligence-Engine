import numpy as np
import pytest
from lpie.models.uncertainty import compute_prediction_confidence, compute_prediction_intervals


def test_prediction_confidence_and_intervals():
    probs = np.array([0.02, 0.05, 0.50, 0.85, 0.98])
    conf = compute_prediction_confidence(probs)

    assert len(conf) == len(probs)
    assert np.all(conf >= 0.05)
    assert np.all(conf <= 0.99)
    # Confidence is lowest near 0.50
    assert conf[2] < conf[0]
    assert conf[2] < conf[4]

    # Test intervals
    lower, upper = compute_prediction_intervals(probs, confidence_level=0.90)
    assert len(lower) == len(probs)
    assert len(upper) == len(probs)
    assert np.all(lower <= probs)
    assert np.all(upper >= probs)
    assert np.all(lower >= 0.0)
    assert np.all(upper <= 1.0)
