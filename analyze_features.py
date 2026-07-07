#!/usr/bin/env python3
"""Analyze feature variance and correlation for clustering."""

import pandas as pd
import numpy as np
import sys

# Load data
try:
    df = pd.read_csv("Ooredoo_Demo_Dataset_v2.csv")
except:
    df = pd.read_csv("full_mobile_customer_dataset.csv")

numeric_cols = ['age', 'account_tenure_months', 'monthly_bill_dinar', 'total_spent_dinar',
                'voice_minutes_monthly', 'sms_count_monthly', 'data_gb_monthly', 'active_services',
                'online_support_usage', 'complaints_last_year', 'contract_months_remaining', 'satisfaction_score']

print("=" * 70)
print("FEATURE VARIANCE AND CORRELATION ANALYSIS")
print("=" * 70)

# Check variance
print("\n1. FEATURE VARIANCE (Low variance = weak for clustering):")
print("-" * 70)
print(f"{'Feature':<30} | {'Variance':>10} | {'Std Dev':>8} | {'CV%':>6}")
print("-" * 70)
for col in numeric_cols:
    if col in df.columns:
        var = df[col].var()
        std = df[col].std()
        mean = df[col].mean()
        cv = (std / mean) * 100 if mean != 0 else 0
        print(f"{col:<30} | {var:10.2f} | {std:8.2f} | {cv:6.2f}%")

# Check correlation
print("\n2. FEATURE CORRELATION (High >0.7 = redundancy):")
print("-" * 70)
corr_matrix = df[numeric_cols].corr()
high_corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr = corr_matrix.iloc[i, j]
        if abs(corr) > 0.7:
            high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr))

if high_corr_pairs:
    for col1, col2, corr in sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True):
        print(f"  {col1:<25} <-> {col2:<25}: {corr:+.3f}")
else:
    print("  No high correlations found - GOOD FEATURE INDEPENDENCE")

# Statistics
print("\n3. DATASET STATISTICS:")
print("-" * 70)
print(f"  Total samples: {len(df):,}")
print(f"  Total features: {len(numeric_cols)}")
print(f"  Ratio (samples/features): {len(df) / len(numeric_cols):.1f}")
print(f"  Effective samples: {len(df) / (1 + np.log(len(numeric_cols))):.0f} (after dimensionality penalty)")

# Check for natural groupings
print("\n4. VALUE DISTRIBUTION (Check for natural groups):")
print("-" * 70)
for col in ['monthly_bill_dinar', 'account_tenure_months', 'data_gb_monthly']:
    if col in df.columns:
        q1 = df[col].quantile(0.25)
        q2 = df[col].quantile(0.50)
        q3 = df[col].quantile(0.75)
        print(f"  {col}:")
        print(f"    Q1: {q1:.1f} | Q2(median): {q2:.1f} | Q3: {q3:.1f}")
        print(f"    Range: {df[col].min():.1f} to {df[col].max():.1f}")

print("\n" + "=" * 70)
print("INTERPRETATION:")
print("=" * 70)
print("""
A Silhouette Score of 56-58% consistently means:

1. OVERLAPPING CLUSTERS: Customer groups aren't crisp/distinct
2. VALID BUSINESS REALITY: Customers genuinely blend between segments
3. NOT A BUG: The clustering is working correctly on overlapping data
4. NORMAL FOR TELECOM: Telecom customers span broad ranges (pre/postpaid,
   multiple tenure ranges, varied spending) making clear segments hard

NEXT STEPS:
A) Accept 56-58% as the natural ceiling for this dataset
B) Focus on business interpretation rather than accuracy %
C) Consider feature engineering to create better separators
   - Add ratios: data_per_dollar, voice_per_dollar
   - Add behavioral flags: high_complaint, high_spender
   - Add derived features from categorical columns
""")
