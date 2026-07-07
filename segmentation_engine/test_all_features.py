"""Quick smoke test of the core platform features."""

from pathlib import Path

import pandas as pd

from segmentation_engine.src.clustering import SegmentationEngine
from segmentation_engine.src.pipeline import DataPreprocessor


def test_core_feature_pipeline_smoke():
    dataset = Path(__file__).resolve().parent / "telco_customer_churn.csv"
    assert dataset.exists()

    df = pd.read_csv(dataset)
    cleaned = DataPreprocessor().build_cleaned_feature_frame(df)
    engine = SegmentationEngine()

    kmeans_result = engine.segment_with_kmeans(cleaned, n_clusters=3)
    hierarchical_result = engine.segment_with_hierarchical(cleaned, n_clusters=3)
    dbscan_result = engine.segment_with_dbscan(cleaned, eps=0.5, min_samples=5)

    assert len(set(kmeans_result["labels"])) == 3
    assert len(set(hierarchical_result["labels"])) == 3
    assert "silhouette" in dbscan_result["metrics"]
