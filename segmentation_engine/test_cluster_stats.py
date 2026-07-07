"""Validate per-cluster statistics computed from K-Means labels."""

from pathlib import Path

import pandas as pd

from segmentation_engine.src.clustering import SegmentationEngine
from segmentation_engine.src.pipeline import DataPreprocessor


DATASET_PATH = Path(__file__).resolve().parent.parent / "Ooredoo_Demo_Dataset_v2.csv"
BUSINESS_METRIC_COLUMNS = [
    "monthly_bill_dinar",
    "data_gb_monthly",
    "voice_minutes_monthly",
    "account_tenure_months",
    "satisfaction_score",
]


def test_cluster_statistics_have_distinct_business_metric_means():
    """K-Means clusters should produce non-empty, distinguishable segments."""
    assert DATASET_PATH.exists(), f"Dataset fixture not found: {DATASET_PATH}"

    df = pd.read_csv(DATASET_PATH)
    cleaned_df = DataPreprocessor().build_cleaned_feature_frame(df)

    assert not cleaned_df.empty
    assert cleaned_df.shape[0] == df.shape[0]
    assert cleaned_df.select_dtypes(include="number").shape[1] == cleaned_df.shape[1]

    result = SegmentationEngine().segment_with_kmeans(cleaned_df, n_clusters=3)
    labels = pd.Series(result["labels"], name="cluster")

    assert result["n_clusters"] == 3
    assert len(labels) == len(cleaned_df)
    assert sorted(labels.unique().tolist()) == [0, 1, 2]

    cluster_sizes = labels.value_counts().sort_index()
    assert len(cluster_sizes) == 3
    assert cluster_sizes.sum() == len(cleaned_df)
    assert (cluster_sizes > 0).all()

    metric_columns = [column for column in BUSINESS_METRIC_COLUMNS if column in cleaned_df.columns]
    assert metric_columns, "No expected business metric columns were available for validation"

    cluster_means = cleaned_df.groupby(labels)[metric_columns].mean()

    for column in metric_columns:
        assert cluster_means[column].nunique() > 1, (
            f"Expected different cluster means for {column}, got "
            f"{cluster_means[column].to_dict()}"
        )
