# SmartSeg Adaptive Segmentation Engine

This module implements a schema-agnostic customer segmentation pipeline following a hybrid academic strategy:

- Real dataset baseline (IBM Telco).
- Engineered real dataset variant (feature engineering).
- Optional synthetic stress-test dataset.

## What it does

- Loads CSV data with pandas.
- Detects schema (numeric, categorical, ID-like columns).
- Selects numeric clustering features automatically.
- Drops high-missing and zero-variance columns.
- Fills missing numeric values using median.
- Standardizes features with `StandardScaler`.
- Tests `k` from 2 to 10 using K-Means.
- Computes silhouette and Davies-Bouldin scores.
- Picks best `k` and builds segmentation outputs.

## Sprint 2: Data Management and Preprocessing

Use this mode when you want to validate and clean a dataset before clustering.

- Load and inspect CSV shape/types.
- Detect numeric, categorical, and ID-like columns.
- Flag high-missing columns.
- Keep numeric features only.
- Drop high-missing and zero-variance numeric columns.
- Fill numeric missing values with median.

Run preprocessing only:

```bash
python run_preprocessing.py --input data/real/telco_churn.csv --output-json preprocessing_result.json --output-cleaned-csv cleaned_telco.csv
```

## Sprint 3 preparation: Feature engineering on real data

Generate engineered features from the IBM Telco dataset:

```bash
python run_feature_engineering.py --input data/real/telco_churn.csv --output data/real/telco_churn_engineered.csv
```

## Output object

Each run returns a structured result containing:

- `clusters`
- `cluster_sizes`
- `cluster_profiles`
- `metrics`
- `used_features`
- `processing_summary`

## Project layout

- `src/pipeline.py`: adaptive segmentation logic.
- `src/config.py`: thresholds and defaults.
- `run_experiments.py`: executes real + synthetic experiment suite.
- `experiment_config.yaml`: dataset and scenario configuration.
- `data/real/`: place downloaded real datasets here.
- `data/synthetic/`: generated synthetic datasets are written here.

## Setup

```bash
pip install -r requirements.txt
```

## Run experiments

```bash
python run_experiments.py
```

Optional:

```bash
python run_experiments.py --config experiment_config.yaml --output experiment_results.json
```

## Dataset strategy used in this repository

Expected real dataset files:

- `data/real/telco_churn.csv`
- `data/real/telco_churn_engineered.csv`
- `data/real/online_retail.csv`

Optional synthetic scenario is generated automatically by `run_experiments.py`.

## Notes for academic reporting

- Treat real datasets as primary validation.
- Use synthetic datasets for robustness tests only.
- Report best `k`, silhouette, Davies-Bouldin, and selected features per dataset.
