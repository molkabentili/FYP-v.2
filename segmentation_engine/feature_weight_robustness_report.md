# Feature Weight Robustness Check

Dataset: `data\real\telco_churn.csv` (7043 rows)

The baseline heuristic feature weights were compared with an alternative, more evenly distributed weighting scheme. Both variants were clustered with K-Means using k=3, StandardScaler normalization, random_state=42, and n_init=10. The observed churn flag was excluded from clustering to avoid target leakage.

| Scheme | Silhouette | Davies-Bouldin | Cluster sizes |
|---|---:|---:|---|
| Baseline | 0.3024 | 1.2242 | {'0': 2735, '1': 1941, '2': 2367} |
| Alternative | 0.2940 | 1.2582 | {'0': 2612, '1': 1958, '2': 2473} |

Adjusted Rand Index between the two assignments: **0.9368**.

Interpretation: the alternative coefficients changed some individual assignments, but the overall partition structure remained moderately similar and the quality metrics stayed in a close range. This supports using the current coefficients as interpretable heuristics, while acknowledging that they are not optimized or expert-calibrated weights.
