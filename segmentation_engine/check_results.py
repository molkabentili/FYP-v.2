import pandas as pd
import json
import os

print("=" * 80)
print("ANALYSIS COMPLETION REPORT")
print("=" * 80)

# Check clustering results
print("\n✓ CLUSTERING RESULTS")
print("-" * 80)
df = pd.read_csv('clustered_data_with_segments.csv')
print(f"Data shape: {df.shape}")
print(f"Features: {df.columns.tolist()}")
print(f"Clusters: {sorted(df['cluster'].unique())}")
print(f"\nSegment Distribution:")
print(df['cluster'].value_counts().sort_index())

# Check features
print("\n✓ FEATURES USED FOR CLUSTERING")
print("-" * 80)
features = pd.read_csv('final_features_list.csv')
print(features.to_string(index=False))

# Check elbow analysis
print("\n✓ ELBOW & SILHOUETTE ANALYSIS")
print("-" * 80)
elbow = pd.read_csv('elbow_silhouette_analysis.csv')
print(elbow.to_string(index=False))

# Check for output files
print("\n✓ OUTPUT FILES GENERATED")
print("-" * 80)
output_files = [
    'clustered_data_with_segments.csv',
    'final_features_list.csv',
    'elbow_silhouette_analysis.csv',
    'clusters_pca.png',
    'clusters_umap.png'
]

for f in output_files:
    if os.path.exists(f):
        size = os.path.getsize(f)
        print(f"  ✓ {f} ({size:,} bytes)")
    else:
        print(f"  ✗ {f} (NOT FOUND)")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETED SUCCESSFULLY!")
print("=" * 80)
