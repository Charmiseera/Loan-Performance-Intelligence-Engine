from typing import Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer


class LearnedAnomalyDetector:
    """
    Unsupervised statistical anomaly detector using IsolationForest.
    Generates normalized anomaly scores in [0.0, 1.0].
    """

    def __init__(self, contamination: float = 0.05, seed: int = 42):
        self.contamination = contamination
        self.seed = seed
        self.imputer = SimpleImputer(strategy="median")
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.seed,
            n_estimators=100,
            n_jobs=-1,
        )

    def fit(self, X: pd.DataFrame) -> "LearnedAnomalyDetector":
        X_num = X.select_dtypes(include=[np.number])
        if X_num.empty:
            return self
        X_imp = self.imputer.fit_transform(X_num)
        self.model.fit(X_imp)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        X_num = X.select_dtypes(include=[np.number])
        if X_num.empty or not hasattr(self.model, "estimators_"):
            return np.zeros(len(X))
        X_imp = self.imputer.transform(X_num)
        # IsolationForest decision_function: lower means more anomalous
        raw_scores = self.model.decision_function(X_imp)
        # Invert and normalize to [0, 1] range
        scores_norm = 0.5 - (raw_scores * 1.5)
        return np.clip(scores_norm, 0.0, 1.0)
