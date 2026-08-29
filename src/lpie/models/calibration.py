from typing import Any, Optional
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression


class CalibratedModelWrapper:
    """
    Wraps an estimator with Isotonic / Platt probability calibration.
    Can be calibrated on a naturally-weighted holdout dataset (Principle V / Declared Tension 1).
    """

    def __init__(self, base_estimator: Any, method: str = "isotonic"):
        self.base_estimator = base_estimator
        self.method = method
        self.calibrator = None

    def fit_base(self, X: Any, y: np.ndarray, sample_weight: Optional[np.ndarray] = None) -> "CalibratedModelWrapper":
        if hasattr(self.base_estimator, "fit"):
            if sample_weight is not None:
                try:
                    self.base_estimator.fit(X, y, sample_weight=sample_weight)
                except TypeError:
                    self.base_estimator.fit(X, y)
            else:
                self.base_estimator.fit(X, y)
        return self

    def fit_calibration(self, X_val: Any, y_val: np.ndarray, sample_weight: Optional[np.ndarray] = None) -> "CalibratedModelWrapper":
        raw_probs = self.base_estimator.predict_proba(X_val)[:, 1]
        
        if self.method == "isotonic":
            self.calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            self.calibrator.fit(raw_probs, y_val, sample_weight=sample_weight)
        elif self.method == "sigmoid":
            from sklearn.linear_model import LogisticRegression
            self.calibrator = LogisticRegression()
            self.calibrator.fit(raw_probs.reshape(-1, 1), y_val, sample_weight=sample_weight)
        return self

    def predict_proba(self, X: Any) -> np.ndarray:
        raw_probs = self.base_estimator.predict_proba(X)
        if self.calibrator is None:
            return raw_probs

        pos_probs = raw_probs[:, 1]
        if self.method == "isotonic":
            cal_pos = self.calibrator.predict(pos_probs)
        elif self.method == "sigmoid":
            cal_pos = self.calibrator.predict_proba(pos_probs.reshape(-1, 1))[:, 1]
        else:
            cal_pos = pos_probs

        cal_pos = np.clip(cal_pos, 0.0, 1.0)
        return np.column_stack([1.0 - cal_pos, cal_pos])
