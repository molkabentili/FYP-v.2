"""Regenerate K-selection analysis for the SmartSeg clustering workflow.

This script uses the real IBM Telco dataset variant currently used for the
feature-engineering analysis, applies the same numeric preprocessing path used
before K-Means, excludes target/leakage fields, evaluates k=2..10, and writes
report-ready artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from src.pipeline import DataPreprocessor


ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "data" / "real" / "telco_churn_engineered.csv"
OUTPUT_DIR = ROOT / "k_selection_outputs"
CSV_PATH = OUTPUT_DIR / "smartseg_k_selection_metrics.csv"
PNG_PATH = OUTPUT_DIR / "smartseg_k_selection_metrics.png"
SVG_PATH = OUTPUT_DIR / "smartseg_k_selection_metrics.svg"
SUMMARY_MD_PATH = OUTPUT_DIR / "smartseg_k_selection_summary.md"
SUMMARY_JSON_PATH = OUTPUT_DIR / "smartseg_k_selection_summary.json"

K_RANGE = range(2, 11)
RANDOM_STATE = 42
N_INIT = 10
MAX_ITER = 300

# These fields encode known churn/target information and must not drive
# unsupervised customer segmentation.
LEAKAGE_COLUMNS = {"observed_churn_flag", "churn", "churn_flag", "target", "label"}


def load_preprocessed_features(dataset_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load data and apply the SmartSeg numeric preprocessing pipeline."""
    raw_df = pd.read_csv(dataset_path)

    preprocessor = DataPreprocessor()
    feature_frame = preprocessor.build_cleaned_feature_frame(raw_df)

    leakage_to_drop = [
        col for col in feature_frame.columns if col.strip().lower() in LEAKAGE_COLUMNS
    ]
    feature_frame = feature_frame.drop(columns=leakage_to_drop, errors="ignore")

    return raw_df, feature_frame


def evaluate_k_values(features: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Scale features and compute K-Means quality metrics for k=2..10."""
    scaled = StandardScaler().fit_transform(features)

    rows = []
    for k in K_RANGE:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=N_INIT,
            max_iter=MAX_ITER,
        )
        labels = model.fit_predict(scaled)

        rows.append(
            {
                "k": k,
                "silhouette_score": silhouette_score(scaled, labels),
                "davies_bouldin_index": davies_bouldin_score(scaled, labels),
                "calinski_harabasz_index": calinski_harabasz_score(scaled, labels),
                "inertia": model.inertia_,
            }
        )

    return pd.DataFrame(rows), scaled


def estimate_elbow_k(results: pd.DataFrame) -> int:
    """Estimate elbow as the point farthest from the line joining endpoints."""
    points = results[["k", "inertia"]].to_numpy(dtype=float)
    start = points[0]
    end = points[-1]
    line = end - start
    line_norm = np.linalg.norm(line)
    if line_norm == 0:
        return int(results.iloc[0]["k"])

    vectors = start - points
    distances = np.abs(line[0] * vectors[:, 1] - line[1] * vectors[:, 0]) / line_norm
    return int(results.iloc[int(np.argmax(distances))]["k"])


def best_k_summary(results: pd.DataFrame) -> dict[str, int | float | bool]:
    """Identify best k according to each metric."""
    best_silhouette = results.loc[results["silhouette_score"].idxmax()]
    best_davies = results.loc[results["davies_bouldin_index"].idxmin()]
    best_calinski = results.loc[results["calinski_harabasz_index"].idxmax()]
    elbow_k = estimate_elbow_k(results)

    return {
        "best_silhouette_k": int(best_silhouette["k"]),
        "best_silhouette_score": float(best_silhouette["silhouette_score"]),
        "best_davies_bouldin_k": int(best_davies["k"]),
        "best_davies_bouldin_index": float(best_davies["davies_bouldin_index"]),
        "best_calinski_harabasz_k": int(best_calinski["k"]),
        "best_calinski_harabasz_index": float(best_calinski["calinski_harabasz_index"]),
        "estimated_elbow_k": elbow_k,
        "k5_metric_optimum": 5
        in {
            int(best_silhouette["k"]),
            int(best_davies["k"]),
            int(best_calinski["k"]),
            elbow_k,
        },
    }


def style_axes(ax: plt.Axes, title: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel(ylabel)
    ax.set_xticks(list(K_RANGE))
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def annotate_best(ax: plt.Axes, k: int, y: float, label: str, color: str) -> None:
    ax.scatter([k], [y], s=80, color=color, edgecolor="white", zorder=5)
    ax.annotate(
        label,
        xy=(k, y),
        xytext=(8, 10),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        color=color,
        arrowprops={"arrowstyle": "->", "color": color, "lw": 1.0},
    )


def create_metric_figure(results: pd.DataFrame, summary: dict[str, int | float | bool]) -> None:
    """Create a high-resolution 2x2 figure with all K-selection metrics."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "figure.dpi": 150,
        }
    )

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2))
    fig.suptitle(
        "SmartSeg K-Means K-Selection Metrics (IBM Telco Engineered Dataset)",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    x = results["k"]
    red = "#C91F37"
    blue = "#1F77B4"
    green = "#2CA02C"
    purple = "#6F42C1"
    gray = "#6C757D"

    ax = axes[0, 0]
    ax.plot(x, results["inertia"], marker="o", color=blue, linewidth=2.2)
    style_axes(ax, "Elbow Method", "Inertia (lower is better)")
    elbow_k = int(summary["estimated_elbow_k"])
    elbow_y = float(results.loc[results["k"] == elbow_k, "inertia"].iloc[0])
    annotate_best(ax, elbow_k, elbow_y, f"Elbow k={elbow_k}", blue)
    ax.axvline(5, color=gray, linestyle=":", linewidth=1.4, label="k=5")
    ax.legend(frameon=False, loc="upper right")

    ax = axes[0, 1]
    ax.plot(x, results["silhouette_score"], marker="o", color=green, linewidth=2.2)
    style_axes(ax, "Silhouette Score", "Score (higher is better)")
    best_k = int(summary["best_silhouette_k"])
    best_y = float(results.loc[results["k"] == best_k, "silhouette_score"].iloc[0])
    annotate_best(ax, best_k, best_y, f"Best k={best_k}", green)
    ax.axvline(5, color=gray, linestyle=":", linewidth=1.4)

    ax = axes[1, 0]
    ax.plot(x, results["davies_bouldin_index"], marker="o", color=red, linewidth=2.2)
    style_axes(ax, "Davies-Bouldin Index", "Index (lower is better)")
    best_k = int(summary["best_davies_bouldin_k"])
    best_y = float(results.loc[results["k"] == best_k, "davies_bouldin_index"].iloc[0])
    annotate_best(ax, best_k, best_y, f"Best k={best_k}", red)
    ax.axvline(5, color=gray, linestyle=":", linewidth=1.4)

    ax = axes[1, 1]
    ax.plot(x, results["calinski_harabasz_index"], marker="o", color=purple, linewidth=2.2)
    style_axes(ax, "Calinski-Harabasz Index", "Index (higher is better)")
    best_k = int(summary["best_calinski_harabasz_k"])
    best_y = float(results.loc[results["k"] == best_k, "calinski_harabasz_index"].iloc[0])
    annotate_best(ax, best_k, best_y, f"Best k={best_k}", purple)
    ax.axvline(5, color=gray, linestyle=":", linewidth=1.4)

    fig.text(
        0.5,
        0.015,
        "Preprocessing: SmartSeg DataPreprocessor numeric cleaning, target/leakage exclusion, StandardScaler; K-Means random_state=42, n_init=10.",
        ha="center",
        fontsize=9,
        color="#444444",
    )

    fig.tight_layout(rect=[0.02, 0.04, 0.98, 0.95])
    fig.savefig(PNG_PATH, dpi=350, bbox_inches="tight")
    fig.savefig(SVG_PATH, bbox_inches="tight")
    plt.close(fig)


def write_summary(
    raw_df: pd.DataFrame,
    features: pd.DataFrame,
    results: pd.DataFrame,
    summary: dict[str, int | float | bool],
) -> None:
    k5_row = results.loc[results["k"] == 5].iloc[0]
    metric_winners = {
        "Silhouette Score": summary["best_silhouette_k"],
        "Davies-Bouldin Index": summary["best_davies_bouldin_k"],
        "Calinski-Harabasz Index": summary["best_calinski_harabasz_k"],
        "Elbow Method": summary["estimated_elbow_k"],
    }

    payload = {
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "rows": int(raw_df.shape[0]),
        "raw_columns": int(raw_df.shape[1]),
        "features_used": features.columns.tolist(),
        "n_features_used": int(features.shape[1]),
        "metric_winners": metric_winners,
        "k5_metrics": {
            "silhouette_score": float(k5_row["silhouette_score"]),
            "davies_bouldin_index": float(k5_row["davies_bouldin_index"]),
            "calinski_harabasz_index": float(k5_row["calinski_harabasz_index"]),
            "inertia": float(k5_row["inertia"]),
        },
        "k5_metric_optimum": bool(summary["k5_metric_optimum"]),
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if int(summary["estimated_elbow_k"]) == 5:
        k5_interpretation = (
            "K=5 is supported by the elbow-method estimate, but it is not the "
            "top value for Silhouette Score, Davies-Bouldin Index, or "
            "Calinski-Harabasz Index in this run. Therefore, K=5 should be "
            "presented as a balanced statistical-and-business choice rather "
            "than as the unique metric-optimal solution."
        )
    elif payload["k5_metric_optimum"]:
        k5_interpretation = (
            "K=5 is directly supported by at least one internal validation criterion."
        )
    else:
        k5_interpretation = (
            "K=5 is not the optimum according to any single metric in this run. "
            "It can still be justified only as a business segmentation choice when "
            "the additional granularity produces interpretable and actionable "
            "customer groups without creating very small or redundant segments."
        )

    SUMMARY_MD_PATH.write_text(
        "\n".join(
            [
                "# SmartSeg K-Selection Regeneration",
                "",
                f"Dataset: `{payload['dataset']}`",
                f"Rows: {payload['rows']:,}",
                f"Features used after preprocessing: {payload['n_features_used']}",
                "",
                "Features:",
                *[f"- `{col}`" for col in payload["features_used"]],
                "",
                "## Best K By Metric",
                "",
                f"- Silhouette Score: k={summary['best_silhouette_k']} "
                f"({summary['best_silhouette_score']:.4f})",
                f"- Davies-Bouldin Index: k={summary['best_davies_bouldin_k']} "
                f"({summary['best_davies_bouldin_index']:.4f}; lower is better)",
                f"- Calinski-Harabasz Index: k={summary['best_calinski_harabasz_k']} "
                f"({summary['best_calinski_harabasz_index']:.2f})",
                f"- Elbow Method estimate: k={summary['estimated_elbow_k']}",
                "",
                "## K=5 Check",
                "",
                f"- Silhouette Score at k=5: {k5_row['silhouette_score']:.4f}",
                f"- Davies-Bouldin Index at k=5: {k5_row['davies_bouldin_index']:.4f}",
                f"- Calinski-Harabasz Index at k=5: {k5_row['calinski_harabasz_index']:.2f}",
                f"- Inertia at k=5: {k5_row['inertia']:.2f}",
                "",
                k5_interpretation,
                "",
                "## Academically Defensible K=5 Justification",
                "",
                "If K=5 is retained, present it as a business-driven modeling choice rather than a purely metric-optimal choice. The defensible argument is that K=5 can map naturally to five customer-management tiers, such as budget/light, standard, growth, high-value, and premium or at-risk customers. This choice is acceptable only if the resulting segment profiles are distinct, sufficiently sized, and actionable for marketing or retention decisions. The report should state that internal validation metrics are used as evidence, while final K selection balances statistical quality with business interpretability.",
                "",
                "Generated files:",
                f"- `{CSV_PATH.name}`",
                f"- `{PNG_PATH.name}`",
                f"- `{SVG_PATH.name}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_df, features = load_preprocessed_features(DATASET_PATH)
    results, _ = evaluate_k_values(features)
    summary = best_k_summary(results)

    results_rounded = results.copy()
    for col in results_rounded.columns:
        if col != "k":
            results_rounded[col] = results_rounded[col].round(6)
    results_rounded.to_csv(CSV_PATH, index=False)

    create_metric_figure(results, summary)
    write_summary(raw_df, features, results, summary)

    print("SmartSeg K-selection analysis regenerated.")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Rows: {raw_df.shape[0]:,}; features used: {features.shape[1]}")
    print(f"CSV: {CSV_PATH}")
    print(f"PNG: {PNG_PATH}")
    print(f"SVG: {SVG_PATH}")
    print(f"Summary: {SUMMARY_MD_PATH}")
    print(results_rounded.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
