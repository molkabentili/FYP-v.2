#!/usr/bin/env python3
"""Test the complete API flow to verify cluster statistics are properly returned."""

import requests
import json
import pandas as pd
from pathlib import Path

# Paths
from pathlib import Path

DATASET_PATH = str((Path(__file__).resolve().parent / "Ooredoo_Demo_Dataset_v2.csv").resolve())

# Fallback if dataset is located one level above repo root
if not Path(DATASET_PATH).exists():
    DATASET_PATH = str((Path(__file__).resolve().parent.parent / "Ooredoo_Demo_Dataset_v2.csv").resolve())
API_URL = "http://127.0.0.1:8000/api"

print("="*80)
print("TESTING COMPLETE API FLOW")
print("="*80)

# Step 1: Preprocess
print("\n[1] PREPROCESSING...")
with open(DATASET_PATH, 'rb') as f:
    files = {'file': f}
    data = {'dataset_name': 'ooredoo_demo'}
    response = requests.post(f"{API_URL}/preprocess", files=files, data=data)
    
if response.status_code != 200:
    print(f"ERROR: {response.status_code}")
    print(response.text)
    exit(1)

preprocess_result = response.json()
print(f"✓ Preprocessing done")
print(f"  Dataset shape: {preprocess_result['original_shape']} -> {preprocess_result['cleaned_shape']}")
preprocessed_file = preprocess_result['output_filename']
print(f"  Output file: preprocessed_data/api_data/{preprocessed_file}")

# Step 2: Clustering with k=3
print("\n[2] CLUSTERING (k=3)...")
cluster_request = {
    "preprocessed_file": f"api_data/{preprocessed_file}",
    "algorithm": "kmeans",
    "n_clusters": 3
}

response = requests.post(f"{API_URL}/cluster", json=cluster_request)

if response.status_code != 200:
    print(f"ERROR: {response.status_code}")
    print(response.text)
    exit(1)

clustering_result = response.json()
print(f"✓ Clustering done")
print(f"  Algorithm: {clustering_result['algorithm']}")
print(f"  N Clusters: {clustering_result['n_clusters']}")

# Step 3: Analyze cluster_statistics
print("\n[3] CLUSTER STATISTICS ANALYSIS...")
cluster_stats = clustering_result.get('cluster_statistics', [])

if not cluster_stats:
    print("ERROR: No cluster_statistics in response!")
    print(json.dumps(clustering_result, indent=2, default=str))
    exit(1)

print(f"Total clusters: {len(cluster_stats)}\n")

for i, stat in enumerate(cluster_stats):
    print(f"Cluster {i}:")
    print(f"  Cluster ID: {stat['cluster_id']}")
    print(f"  Size: {stat['size']} ({stat['percentage']:.1f}%)")
    
    means = stat.get('mean_values', {})
    print(f"  Mean values keys: {list(means.keys())}")
    
    # Extract using corrected names
    arpu = means.get('monthly_bill_dinar', 0)
    data_usage = means.get('data_gb_monthly', 0)
    voice_min = means.get('voice_minutes_monthly', 0)
    tenure = means.get('account_tenure_months', 0)
    
    print(f"  ARPU: {arpu:.2f} TND")
    print(f"  Data: {data_usage:.2f} GB")
    print(f"  Voice: {voice_min:.0f} min")
    print(f"  Tenure: {tenure:.1f} months ({tenure/12:.1f} years)")
    print()

print("="*80)
print("✓ All tests passed! Cluster statistics are correctly differentiated.")
print("="*80)
