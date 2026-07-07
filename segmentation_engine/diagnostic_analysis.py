import pandas as pd
import numpy as np
from scipy import stats
import json
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("DIAGNOSTIC: SEGMENTATION ISSUES ANALYSIS")
print("="*80)

# ==================== PART 1: INPUT DATA ANALYSIS ====================
print("\n" + "="*80)
print("PART 1: UPLOADED DATA EXAMINATION")
print("="*80)

df_original = pd.read_csv('api_data/test_data.csv')
print(f"\nShape: {df_original.shape}")
print(f"Columns ({len(df_original.columns)}): {df_original.columns.tolist()}")

print("\n" + "-"*80)
print("DATA TYPES & MISSING VALUES")
print("-"*80)
for col in df_original.columns:
    missing = df_original[col].isnull().sum()
    pct = (missing / len(df_original)) * 100
    print(f"{col:20s} | Type: {str(df_original[col].dtype):10s} | Missing: {missing:4d} ({pct:5.2f}%)")

print("\n" + "-"*80)
print("NUMERIC COLUMNS STATISTICS & DISTRIBUTIONS")
print("-"*80)

numeric_cols = df_original.select_dtypes(include=[np.number]).columns
for col in numeric_cols:
    data = df_original[col].dropna()
    skewness = stats.skew(data)
    kurtosis = stats.kurtosis(data)
    cv = (data.std() / data.mean()) if data.mean() != 0 else 0  # Coefficient of variation
    print(f"\n{col}:")
    print(f"  Min/Max:     {data.min():12.2f} / {data.max():12.2f}")
    print(f"  Mean/Std:    {data.mean():12.2f} / {data.std():12.2f}")
    print(f"  Median/Q1/Q3: {data.median():12.2f} / {data.quantile(0.25):12.2f} / {data.quantile(0.75):12.2f}")
    print(f"  Skewness:    {skewness:12.4f} (>1 or <-1 = highly skewed)")
    print(f"  Kurtosis:    {kurtosis:12.4f}")
    print(f"  CV (Coef of Var): {cv:12.4f} (variation relative to mean)")

print("\n" + "-"*80)
print("FIRST 5 ROWS")
print("-"*80)
print(df_original.head())

# ==================== PART 2: PREPROCESSING ANALYSIS ====================
print("\n" + "="*80)
print("PART 2: PREPROCESSED DATA EXAMINATION")
print("="*80)

df_preprocessed = pd.read_csv('api_data/preprocessed_test_customer_data.csv')
print(f"\nShape after preprocessing: {df_preprocessed.shape}")
print(f"Columns: {df_preprocessed.columns.tolist()}")

print("\n" + "-"*80)
print("PREPROCESSED DATA STATISTICS")
print("-"*80)
for col in df_preprocessed.columns:
    data = df_preprocessed[col].dropna()
    print(f"\n{col}:")
    print(f"  Min/Max:     {data.min():12.2f} / {data.max():12.2f}")
    print(f"  Mean/Std:    {data.mean():12.2f} / {data.std():12.2f}")
    print(f"  Median:      {data.median():12.2f}")

print("\n" + "-"*80)
print("CORRELATION MATRIX (Preprocessed)")
print("-"*80)
corr_matrix = df_preprocessed.corr()
print(corr_matrix)

# ==================== PART 3: SEGMENTATION RESULTS ANALYSIS ====================
print("\n" + "="*80)
print("PART 3: K-MEANS SEGMENTATION RESULTS")
print("="*80)

df_segmented = pd.read_csv('api_data/segmented_kmeans_500.csv')
print(f"\nSegmentation shape: {df_segmented.shape}")

# Extract cluster column
if 'cluster' in df_segmented.columns:
    cluster_col = 'cluster'
elif 'segment' in df_segmented.columns:
    cluster_col = 'segment'
else:
    cluster_col = df_segmented.columns[-1]

print(f"Cluster column: {cluster_col}")
print(f"\nCluster distribution:")
cluster_dist = df_segmented[cluster_col].value_counts().sort_index()
print(cluster_dist)
print(f"\nCluster percentages:")
print(cluster_dist / len(df_segmented) * 100)

# ==================== PART 4: FEATURE DOMINANCE ANALYSIS ====================
print("\n" + "="*80)
print("PART 4: FEATURE DOMINANCE CHECK")
print("="*80)

print("\nFeature scales BEFORE preprocessing (in original data):")
for col in numeric_cols:
    data = df_original[col].dropna()
    feature_range = data.max() - data.min()
    print(f"{col:20s} | Range: {feature_range:15.2f} | Mean: {data.mean():12.2f}")

print("\nPotential issues:")
print("- If one feature has MUCH larger range, it will dominate clustering")
print("- Example: Voice usage [0-100] vs Data usage [0-1000000] → Data usage will dominate")

# ==================== PART 5: CLUSTER CHARACTERISTICS ====================
print("\n" + "="*80)
print("PART 5: CLUSTER CHARACTERISTICS ANALYSIS")
print("="*80)

for cluster in sorted(df_segmented[cluster_col].unique()):
    cluster_data = df_segmented[df_segmented[cluster_col] == cluster]
    print(f"\n--- Cluster {cluster} (n={len(cluster_data)}) ---")
    
    # Show all numeric columns in the cluster
    numeric_features = cluster_data.select_dtypes(include=[np.number]).columns
    for col in numeric_features:
        if col != cluster_col:
            print(f"  {col:20s}: mean={cluster_data[col].mean():12.2f}, std={cluster_data[col].std():12.2f}")

# ==================== PART 6: KMEANS CONFIGURATION CHECK ====================
print("\n" + "="*80)
print("PART 6: K-MEANS CONFIGURATION")
print("="*80)

# Load clustering results JSON
with open('api_data/clustering_kmeans_500.json', 'r') as f:
    kmeans_results = json.load(f)

print(json.dumps(kmeans_results, indent=2)[:2000])  # Print first 2000 chars

print("\n" + "="*80)
print("SUMMARY OF ISSUES")
print("="*80)

issues = []

# Check for scale issues
feature_ranges = {}
for col in numeric_cols:
    data = df_original[col].dropna()
    feature_ranges[col] = data.max() - data.min()

max_range = max(feature_ranges.values())
min_range = min(feature_ranges.values())
if max_range > 100 * min_range:
    issues.append(f"❌ SCALE ISSUE: Features have wildly different ranges")
    issues.append(f"   Max range: {max(feature_ranges.values()):.2f} vs Min: {min(feature_ranges.values()):.2f}")

# Check for skewed distributions
for col in numeric_cols:
    data = df_original[col].dropna()
    skewness = stats.skew(data)
    if abs(skewness) > 1:
        issues.append(f"⚠️  SKEWED: {col} has skewness={skewness:.2f} (highly skewed)")

# Check cluster separation
if len(cluster_dist) > 0:
    cluster_sizes = cluster_dist.values
    if cluster_sizes.std() / cluster_sizes.mean() > 0.5:
        issues.append(f"⚠️  IMBALANCED CLUSTERS: Cluster sizes vary significantly")

if not issues:
    issues.append("✓ No major issues detected in this analysis")

for issue in issues:
    print(issue)

print("\n" + "="*80)
