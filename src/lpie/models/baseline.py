from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


class MajorityBaselineClassifier:
    """Baseline predicting empirical base rate observed in training split."""

    def __init__(self):
        self.base_rate: float = 0.0

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "MajorityBaselineClassifier":
        self.base_rate = float(np.mean(y)) if len(y) > 0 else 0.0
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        probs = np.full((len(X), 2), 1.0 - self.base_rate)
        probs[:, 1] = self.base_rate
        return probs


class LogisticBaselineClassifier:
    """Standard L2-regularized logistic regression reference model."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(random_state=seed, max_iter=500, class_weight="balanced")),
        ])

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "LogisticBaselineClassifier":
        # Keep numeric features
        X_num = X.select_dtypes(include=[np.number])
        self.pipeline.fit(X_num, y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_num = X.select_dtypes(include=[np.number])
        return self.pipeline.predict_proba(X_num)
