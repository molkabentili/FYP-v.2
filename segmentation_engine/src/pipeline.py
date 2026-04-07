from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import ID_LIKE_KEYWORDS, PipelineConfig


class DataPreprocessor:
    """Schema-agnostic data preprocessing pipeline.

    The preprocessor adapts to different CSV schemas by detecting numeric features,
    dropping weak columns, imputing missing values, and preparing cleaned datasets
    for downstream clustering or segmentation tasks.
    """

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()

    def inspect_from_csv(self, csv_path: str) -> dict[str, Any]:
        df = pd.read_csv(csv_path)
        self._validate_dataframe(df)
        schema = self._analyze_schema(df)
        return {
            "dataset": csv_path,
            "summary": self._build_dataset_summary(df),
            "schema": schema,
        }

    def preprocess_from_csv(self, csv_path: str) -> dict[str, Any]:
        df = pd.read_csv(csv_path)
        return self.preprocess_dataframe(df, dataset_name=csv_path)

    def build_cleaned_feature_frame_from_csv(self, csv_path: str) -> pd.DataFrame:
        df = pd.read_csv(csv_path)
        return self.build_cleaned_feature_frame(df)

    def build_cleaned_feature_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate_dataframe(df)
        schema = self._analyze_schema(df)
        prep = self._prepare_features(df, schema)
        return prep["feature_frame"].copy()

    def preprocess_dataframe(self, df: pd.DataFrame, dataset_name: str = "dataset") -> dict[str, Any]:
        self._validate_dataframe(df)
        schema = self._analyze_schema(df)
        prep = self._prepare_features(df, schema)

        cleaned_df = prep["feature_frame"].copy()
        return {
            "dataset": dataset_name,
            "summary": self._build_dataset_summary(df),
            "schema": schema,
            "features_used": prep["used_features"],
            "cleaning": {
                "dropped_missing_columns": prep["dropped_missing_columns"],
                "dropped_zero_variance_columns": prep["dropped_zero_variance_columns"],
                "filled_numeric_columns": prep["filled_numeric_columns"],
            },
            "cleaned_shape": {
                "rows": int(cleaned_df.shape[0]),
                "columns": int(cleaned_df.shape[1]),
            },
            "cleaned_preview": cleaned_df.head(20).to_dict(orient="records"),
        }

    def _analyze_schema(self, df: pd.DataFrame) -> dict[str, Any]:
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        all_columns = df.columns.tolist()
        categorical_columns = [col for col in all_columns if col not in numeric_columns]
        id_like_columns = self._detect_id_like_columns(all_columns)
        missing_ratio = df.isna().mean().sort_values(ascending=False)
        high_missing_columns = missing_ratio[
            missing_ratio > self.config.missing_ratio_threshold
        ].index.tolist()

        return {
            "all_columns": all_columns,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "id_like_columns": id_like_columns,
            "high_missing_columns": high_missing_columns,
            "column_missing_ratio": {
                col: float(ratio)
                for col, ratio in missing_ratio.to_dict().items()
            },
        }

    def _build_dataset_summary(self, df: pd.DataFrame) -> dict[str, Any]:
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "dtypes": dtypes,
        }

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise ValueError("Input dataset is empty.")
        if df.shape[1] == 0:
            raise ValueError("Input dataset has no columns.")

    def _detect_id_like_columns(self, columns: list[str]) -> list[str]:
        id_like = []
        for col in columns:
            normalized = col.strip().lower().replace(" ", "_")
            if normalized in ID_LIKE_KEYWORDS:
                id_like.append(col)
                continue
            if normalized.endswith("_id") or normalized.startswith("id_"):
                id_like.append(col)
        return id_like

    def _prepare_features(self, df: pd.DataFrame, schema: dict[str, Any]) -> dict[str, Any]:
        numeric = [col for col in schema["numeric_columns"] if col not in schema["id_like_columns"]]
        if not numeric:
            return {
                "feature_frame": pd.DataFrame(index=df.index),
                "used_features": [],
                "dropped_missing_columns": [],
                "dropped_zero_variance_columns": [],
                "filled_numeric_columns": [],
            }

        frame = df[numeric].copy()

        missing_ratio = frame.isna().mean()
        dropped_missing = missing_ratio[missing_ratio > self.config.missing_ratio_threshold].index.tolist()
        frame = frame.drop(columns=dropped_missing, errors="ignore")

        filled_numeric = []
        for col in frame.columns.tolist():
            if frame[col].isna().any():
                frame[col] = frame[col].fillna(frame[col].median())
                filled_numeric.append(col)

        zero_variance_cols = []
        for col in frame.columns.tolist():
            if frame[col].nunique(dropna=True) <= 1:
                zero_variance_cols.append(col)
        frame = frame.drop(columns=zero_variance_cols, errors="ignore")

        return {
            "feature_frame": frame,
            "used_features": frame.columns.tolist(),
            "dropped_missing_columns": dropped_missing,
            "dropped_zero_variance_columns": zero_variance_cols,
            "filled_numeric_columns": filled_numeric,
        }
