# SmartSeg - Ooredoo Customer Segmentation Platform

SmartSeg is a full-stack analytics project for telecom customer segmentation.
It combines a Python-based machine learning engine, a FastAPI backend, and a React + TypeScript frontend to transform raw CSV customer data into actionable market segments.

## What this project delivers

- Schema-aware CSV preprocessing for mixed telecom datasets.
- Feature engineering for churn-related and behavioral signals.
- Customer clustering with multiple algorithms:
  - K-Means
  - Hierarchical (Agglomerative)
  - DBSCAN
- Quality metrics and cluster profile outputs.
- Backend APIs for preprocessing, clustering, and algorithm comparison.
- Interactive frontend for running analyses and viewing results.
- SQLite persistence for analysis history and authentication.

## Tech stack

- Backend and ML: Python, pandas, scikit-learn, FastAPI, Pydantic
- Persistence: SQLite
- Frontend: React 18, TypeScript, Vite, Tailwind, Recharts, Radix UI
- Testing: pytest

## Repository structure

```text
PFE-Ooredoo/
|-- segmentation_engine/      # ML pipeline, API, tests, scripts
|   |-- api/                  # FastAPI application and persistence layer
|   |-- src/                  # preprocessing + clustering core logic
|   |-- run_preprocessing.py  # CLI preprocessing entrypoint
|   |-- run_feature_engineering.py
|   |-- run_clustering.py     # CLI clustering entrypoint
|   |-- requirements.txt
|
|-- frontend/                 # React + TypeScript web interface
|   |-- src/
|   |-- package.json
|
|-- api_data/                 # generated/preprocessed data and clustering outputs
|-- docs/                     # project documentation
|-- pytest.ini                # test configuration
```

## Quick start

### 1) Backend and segmentation engine

From the repository root:

```bash
cd segmentation_engine
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Run preprocessing:

```bash
python run_preprocessing.py --input data/real/telco_churn.csv --output-json preprocessing_result.json --output-cleaned-csv cleaned_telco.csv
```

Run feature engineering:

```bash
python run_feature_engineering.py --input data/real/telco_churn.csv --output data/real/telco_churn_engineered.csv
```

Run clustering (single algorithm):

```bash
python run_clustering.py --input cleaned_telco.csv --algorithm kmeans --clusters 3 --output clustering_result.json
```

Run clustering (all algorithms):

```bash
python run_clustering.py --input cleaned_telco.csv --algorithm all --output clustering_comparison.json
```

### 2) API server

From `segmentation_engine`:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Useful API URLs:

- Root: `http://localhost:8000/`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/api/health`

### 3) Frontend

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

Build production frontend:

```bash
npm run build
npm run preview
```

## Typical workflow

1. Prepare or upload a telecom CSV dataset.
2. Preprocess and validate numeric features.
3. Optionally engineer additional features.
4. Run clustering with one or more algorithms.
5. Compare metrics (silhouette, Davies-Bouldin, cluster statistics).
6. Visualize and export segments through the frontend/API.

## Recent Enhancements

- Added behavioral insights inside generated customer segments, allowing analysts to explore groups such as Dormant Users, Business Users, Premium Users, International Callers, and IoT Devices from within the main business segment profiles.
- Added targeted customer export for marketing campaigns, including all customers, complete business segments, or specific behavioral groups inside a segment.
- Improved segment analysis with deeper customer behavior understanding while keeping the original SmartSeg business-oriented segmentation workflow unchanged.

## Testing

From the repository root:

```bash
pytest
```

Current configuration runs tests under `segmentation_engine` and skips integration scripts that execute unsafe import-time HTTP calls.

## Data and outputs

- Input datasets are stored in project data folders (for example, `segmentation_engine/data/real/`).
- Processed files and API artifacts are typically written to `api_data/`.
- Clustering outputs are saved as JSON and segmented CSV files.

## Environment notes

- Recommended Python: 3.10+
- Recommended Node.js: 18+
- Default database path: `segmentation_engine/api_data/smartseg.db` (SQLite)

## Project status

This repository contains active experimentation assets (scripts, reports, generated data, and validations) used during the PFE implementation. The current structure supports both research iterations and product-oriented demo workflows.
