from typing import Any, Dict, List, Optional
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder


class MultistateClassifier(BaseEstimator, ClassifierMixin):
    """
    Multinomial classifier predicting next loan state:
    ['CURRENT', '30_DAYS_DELINQUENT', '60_DAYS_DELINQUENT', '90_PLUS_DELINQUENT', 'PREPAID']
    """

    def __init__(self, n_estimators: int = 100, seed: int = 42):
        self.n_estimators = n_estimators
        self.seed = seed
        self.encoder = LabelEncoder()
        self.model = lgb.LGBMClassifier(
            objective="multiclass",
            n_estimators=self.n_estimators,
            random_state=self.seed,
            class_weight="balanced",
            verbosity=-1,
        )
        self.classes_: np.ndarray = np.array([])

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "MultistateClassifier":
        X_proc = X.copy()
        for col in X_proc.columns:
            if X_proc[col].dtype == "object" or X_proc[col].dtype == "string":
                X_proc[col] = X_proc[col].astype("category")

        y_encoded = self.encoder.fit_transform(y)
        self.classes_ = self.encoder.classes_
        self.model.fit(X_proc, y_encoded)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_proc = X.copy()
        for col in X_proc.columns:
            if X_proc[col].dtype == "object" or X_proc[col].dtype == "string":
                X_proc[col] = X_proc[col].astype("category")
        pred_encoded = self.model.predict(X_proc)
        return self.encoder.inverse_transform(pred_encoded)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_proc = X.copy()
        for col in X_proc.columns:
            if X_proc[col].dtype == "object" or X_proc[col].dtype == "string":
                X_proc[col] = X_proc[col].astype("category")
        return self.model.predict_proba(X_proc)
