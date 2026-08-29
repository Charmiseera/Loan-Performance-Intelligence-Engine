from typing import Any, Dict, List, Optional
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin


class GBDTModelWrapper(BaseEstimator, ClassifierMixin):
    """
    LightGBM gradient boosted tree classifier wrapper.
    Optimized for credit risk and prepayment modeling with class weighting and regularization.
    """

    def __init__(
        self,
        n_estimators: int = 150,
        learning_rate: float = 0.05,
        max_depth: int = 7,
        num_leaves: int = 45,
        min_child_samples: int = 30,
        subsample: float = 0.9,
        colsample_bytree: float = 0.85,
        seed: int = 42,
        class_weight: Optional[str] = "balanced",
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.num_leaves = num_leaves
        self.min_child_samples = min_child_samples
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.seed = seed
        self.class_weight = class_weight
        self.model = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            num_leaves=self.num_leaves,
            min_child_samples=self.min_child_samples,
            subsample=self.subsample,
            subsample_freq=1,
            colsample_bytree=self.colsample_bytree,
            random_state=self.seed,
            class_weight=self.class_weight,
            verbosity=-1,
            n_jobs=-1,
        )
        self.feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y: np.ndarray, sample_weight: Optional[np.ndarray] = None) -> "GBDTModelWrapper":
        # Convert object/string columns to category for LightGBM
        X_proc = X.copy()
        for col in X_proc.columns:
            if X_proc[col].dtype == "object" or X_proc[col].dtype == "string":
                X_proc[col] = X_proc[col].astype("category")

        self.feature_names_ = list(X_proc.columns)
        self.model.fit(X_proc, y, sample_weight=sample_weight)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_proc = X.copy()
        for col in X_proc.columns:
            if X_proc[col].dtype == "object" or X_proc[col].dtype == "string":
                X_proc[col] = X_proc[col].astype("category")
        return self.model.predict_proba(X_proc)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_proc = X.copy()
        for col in X_proc.columns:
            if X_proc[col].dtype == "object" or X_proc[col].dtype == "string":
                X_proc[col] = X_proc[col].astype("category")
        return self.model.predict(X_proc)

    @property
    def feature_importances_(self) -> np.ndarray:
        return self.model.feature_importances_
