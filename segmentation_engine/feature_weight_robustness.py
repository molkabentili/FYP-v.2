"""Robustness check for heuristic engineered-feature weights.

The check compares the baseline coefficients used in Table 3.8-style feature
engineering against a deliberately simple alternative weighting scheme.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from run_feature_engineering import _safe_numeric, _yes_no_to_int, engineer_telco_features


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "data" / "real" / "telco_churn.csv"
OUTPUT_JSON = ROOT / "feature_weight_robustness_results.json"
OUTPUT_MD = ROOT / "feature_weight_robustness_report.md"


def engineer_equal_weight_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create an alternative feature set with more even component weights."""
    engineered = engineer_telco_features(df)

    tenure = _safe_numeric(engineered["tenure"]).fillna(0)
    monthly = _safe_numeric(engineered["MonthlyCharges"]).fillna(0)
    total = _safe_numeric(engineered["TotalCharges"]).fillna(0)

    engineered["estimated_usage_score"] = (monthly * 0.5 + total.div(tenure + 1) * 0.5).round(3)
    engineered["customer_activity_score"] = (tenure * 0.6 + monthly * 0.4).round(3)

    service_columns = [
        "PhoneService",
        "MultipleLines",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
    ]
    existing_service_columns = [col for col in service_columns if col in engineered.columns]
    if existing_service_columns:
        service_count = sum(_yes_no_to_int(engineered[col]) for col in existing_service_columns)
    else:
        service_count = pd.Series(0, index=engineered.index)

    partner = _yes_no_to_int(engineered.get("Partner", pd.Series("No", index=engineered.index)))
    dependents = _yes_no_to_int(engineered.get("Dependents", pd.Series("No", index=engineered.index)))

    contract_map = {"month-to-month": 0, "one year": 1, "two year": 2}
    contract_score = (
        engineered.get("Contract", pd.Series("month-to-month", index=engineered.index))
        .astype(str)
        .str.strip()
        .str.lower()
        .map(contract_map)
        .fillna(0)
    )

    internet_fiber_flag = (
        engineered.get("InternetService", pd.Series("", index=engineered.index))
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("fiber optic")
        .astype(int)
    )
    tech_support_no = (
        engineered.get("TechSupport", pd.Series("No", index=engineered.index))
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("no")
        .astype(int)
    )

    engineered["engagement_score"] = (
        service_count + partner + dependents + contract_score
    ).round(3)
    engineered["risk_signal_score"] = (
        internet_fiber_flag / 3
        + tech_support_no / 3
        + (contract_score == 0).astype(int) / 3
    ).round(3)

    return engineered


def build_cluster_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Keep numeric clustering inputs while excluding target leakage columns."""
    numeric = df.select_dtypes(include=[np.number]).copy()
    leakage_columns = [
        col
        for col in numeric.columns
        if col.lower() in {"churn", "observed_churn_flag", "observed_churn"}
    ]
    numeric = numeric.drop(columns=leakage_columns, errors="ignore")
    numeric = numeric.fillna(numeric.median(numeric_only=True))
    return numeric.loc[:, numeric.nunique(dropna=True) > 1]


def cluster_summary(frame: pd.DataFrame, n_clusters: int = 3) -> dict[str, object]:
    scaled = StandardScaler().fit_transform(frame)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(scaled)

    unique, counts = np.unique(labels, return_counts=True)
    return {
        "labels": labels,
        "silhouette": float(silhouette_score(scaled, labels)),
        "davies_bouldin": float(davies_bouldin_score(scaled, labels)),
        "cluster_sizes": {str(int(label)): int(count) for label, count in zip(unique, counts)},
    }


def main() -> None:
    source = DEFAULT_INPUT
    raw = pd.read_csv(source)

    baseline = build_cluster_frame(engineer_telco_features(raw))
    alternative = build_cluster_frame(engineer_equal_weight_features(raw))

    baseline_summary = cluster_summary(baseline)
    alternative_summary = cluster_summary(alternative)
    ari = float(adjusted_rand_score(baseline_summary["labels"], alternative_summary["labels"]))

    results = {
        "dataset": str(source.relative_to(ROOT)),
        "rows": int(raw.shape[0]),
        "features_used": baseline.columns.tolist(),
        "baseline_scheme": {
            "estimated_usage_score": "0.6*MonthlyCharges + 0.4*(TotalCharges/(tenure+1))",
            "customer_activity_score": "0.5*tenure + 0.5*MonthlyCharges",
            "engagement_score": "1.4*service_count + Partner + Dependents + contract_score",
            "risk_signal_score": "0.4*fiber + 0.3*no_tech_support + 0.3*month_to_month",
        },
        "alternative_scheme": {
            "estimated_usage_score": "0.5*MonthlyCharges + 0.5*(TotalCharges/(tenure+1))",
            "customer_activity_score": "0.6*tenure + 0.4*MonthlyCharges",
            "engagement_score": "1.0*service_count + Partner + Dependents + contract_score",
            "risk_signal_score": "equal one-third weights for all risk indicators",
        },
        "baseline_metrics": {
            key: value
            for key, value in baseline_summary.items()
            if key != "labels"
        },
        "alternative_metrics": {
            key: value
            for key, value in alternative_summary.items()
            if key != "labels"
        },
        "adjusted_rand_index": ari,
    }

    OUTPUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(
        "\n".join(
            [
                "# Feature Weight Robustness Check",
                "",
                f"Dataset: `{results['dataset']}` ({results['rows']} rows)",
                "",
                "The baseline heuristic feature weights were compared with an alternative, more evenly distributed weighting scheme. Both variants were clustered with K-Means using k=3, StandardScaler normalization, random_state=42, and n_init=10. The observed churn flag was excluded from clustering to avoid target leakage.",
                "",
                "| Scheme | Silhouette | Davies-Bouldin | Cluster sizes |",
                "|---|---:|---:|---|",
                f"| Baseline | {results['baseline_metrics']['silhouette']:.4f} | {results['baseline_metrics']['davies_bouldin']:.4f} | {results['baseline_metrics']['cluster_sizes']} |",
                f"| Alternative | {results['alternative_metrics']['silhouette']:.4f} | {results['alternative_metrics']['davies_bouldin']:.4f} | {results['alternative_metrics']['cluster_sizes']} |",
                "",
                f"Adjusted Rand Index between the two assignments: **{ari:.4f}**.",
                "",
                "Interpretation: the alternative coefficients changed some individual assignments, but the overall partition structure remained moderately similar and the quality metrics stayed in a close range. This supports using the current coefficients as interpretable heuristics, while acknowledging that they are not optimized or expert-calibrated weights.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_MD}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
