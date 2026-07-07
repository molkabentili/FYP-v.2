# SmartSeg K-Selection Regeneration

Dataset: `data\real\telco_churn_engineered.csv`
Rows: 7,043
Features used after preprocessing: 10

Features:
- `SeniorCitizen`
- `tenure`
- `MonthlyCharges`
- `TotalCharges`
- `estimated_usage_score`
- `customer_activity_score`
- `engagement_score`
- `contract_security_score`
- `digital_payment_score`
- `risk_signal_score`

## Best K By Metric

- Silhouette Score: k=2 (0.3149)
- Davies-Bouldin Index: k=8 (1.1620; lower is better)
- Calinski-Harabasz Index: k=2 (3846.23)
- Elbow Method estimate: k=5

## K=5 Check

- Silhouette Score at k=5: 0.3016
- Davies-Bouldin Index at k=5: 1.1828
- Calinski-Harabasz Index at k=5: 3208.11
- Inertia at k=5: 24945.93

K=5 is supported by the elbow-method estimate, but it is not the top value for Silhouette Score, Davies-Bouldin Index, or Calinski-Harabasz Index in this run. Therefore, K=5 should be presented as a balanced statistical-and-business choice rather than as the unique metric-optimal solution.

## Academically Defensible K=5 Justification

If K=5 is retained, present it as a business-driven modeling choice rather than a purely metric-optimal choice. The defensible argument is that K=5 can map naturally to five customer-management tiers, such as budget/light, standard, growth, high-value, and premium or at-risk customers. This choice is acceptable only if the resulting segment profiles are distinct, sufficiently sized, and actionable for marketing or retention decisions. The report should state that internal validation metrics are used as evidence, while final K selection balances statistical quality with business interpretability.

Generated files:
- `smartseg_k_selection_metrics.csv`
- `smartseg_k_selection_metrics.png`
- `smartseg_k_selection_metrics.svg`
