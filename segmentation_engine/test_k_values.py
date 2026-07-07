"""Validate clustering quality metrics across candidate K values."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler


PREPROCESSED_PATH = Path(__file__).resolve().parent / "test_preprocessed_for_api.csv"
K_RANGE = range(2, 11)


@pytest.fixture(scope="module")
def scaled_numeric_data():
    assert PREPROCESSED_PATH.exists(), f"Preprocessed fixture not found: {PREPROCESSED_PATH}"

    data = pd.read_csv(PREPROCESSED_PATH)
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

    assert not data.empty
    assert numeric_cols, "Expected at least one numeric feature for clustering"

    x = data[numeric_cols].copy()
    x_scaled = StandardScaler().fit_transform(x)

    assert x_scaled.shape == x.shape
    np.testing.assert_allclose(x_scaled.mean(axis=0), 0, atol=1e-7)

    return x_scaled


@pytest.fixture(scope="module")
def k_value_results(scaled_numeric_data):
    results = {}

    for k in K_RANGE:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(scaled_numeric_data)

        results[k] = {
            "silhouette": round(silhouette_score(scaled_numeric_data, labels), 4),
            "davies_bouldin": round(davies_bouldin_score(scaled_numeric_data, labels), 4),
            "calinski_harabasz": round(calinski_harabasz_score(scaled_numeric_data, labels), 2),
            "inertia": round(kmeans.inertia_, 2),
        }

    return results


def test_all_candidate_k_values_have_valid_metrics(k_value_results):
    assert set(k_value_results) == set(K_RANGE)

    for k, metrics in k_value_results.items():
        assert -1 <= metrics["silhouette"] <= 1, f"Invalid silhouette for K={k}"
        assert metrics["davies_bouldin"] > 0, f"Invalid Davies-Bouldin index for K={k}"
        assert metrics["calinski_harabasz"] > 0, f"Invalid Calinski-Harabasz score for K={k}"
        assert metrics["inertia"] > 0, f"Invalid inertia for K={k}"


def test_inertia_decreases_as_k_increases(k_value_results):
    inertias = [k_value_results[k]["inertia"] for k in K_RANGE]

    assert inertias == sorted(inertias, reverse=True)


def test_recommended_k_values_match_metric_analysis(k_value_results):
    best_silhouette_k = max(k_value_results, key=lambda k: k_value_results[k]["silhouette"])
    best_davies_bouldin_k = min(k_value_results, key=lambda k: k_value_results[k]["davies_bouldin"])
    best_calinski_harabasz_k = max(
        k_value_results,
        key=lambda k: k_value_results[k]["calinski_harabasz"],
    )

    assert best_silhouette_k in K_RANGE
    assert best_davies_bouldin_k in K_RANGE
    assert best_calinski_harabasz_k in K_RANGE

    assert all(
        k_value_results[best_silhouette_k]["silhouette"] >= metrics["silhouette"]
        for metrics in k_value_results.values()
    )
    assert all(
        k_value_results[best_davies_bouldin_k]["davies_bouldin"] <= metrics["davies_bouldin"]
        for metrics in k_value_results.values()
    )
    assert all(
        k_value_results[best_calinski_harabasz_k]["calinski_harabasz"]
        >= metrics["calinski_harabasz"]
        for metrics in k_value_results.values()
    )

    for production_candidate in [3, 4, 5]:
        assert production_candidate in k_value_results


def test_elbow_analysis_reductions_are_non_negative(k_value_results):
    reductions = []

    for k in range(2, 10):
        inertia = k_value_results[k]["inertia"]
        next_inertia = k_value_results[k + 1]["inertia"]
        reductions.append(100 * (inertia - next_inertia) / inertia)

    assert all(reduction >= 0 for reduction in reductions)
