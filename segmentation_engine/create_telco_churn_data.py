#!/usr/bin/env python3
"""Create realistic IBM Telco-like dataset with churn labels for model training."""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

n_samples = 7043  # IBM dataset size

print("Creating IBM Telco-like dataset...")

data = {
    'customerID': [f'00{i:05d}' for i in range(n_samples)],
    'gender': np.random.choice(['Male', 'Female'], n_samples),
    'SeniorCitizen': np.random.choice([0, 1], n_samples, p=[0.84, 0.16]),
    'Partner': np.random.choice(['Yes', 'No'], n_samples, p=[0.48, 0.52]),
    'Dependents': np.random.choice(['Yes', 'No'], n_samples, p=[0.30, 0.70]),
    'tenure': np.random.exponential(25, n_samples).astype(int),
    'PhoneService': np.random.choice(['Yes', 'No'], n_samples, p=[0.90, 0.10]),
    'InternetService': np.random.choice(['Fiber optic', 'DSL', 'No'], n_samples, p=[0.40, 0.35, 0.25]),
    'OnlineSecurity': np.random.choice(['Yes', 'No', 'No internet'], n_samples),
    'OnlineBackup': np.random.choice(['Yes', 'No', 'No internet'], n_samples),
    'DeviceProtection': np.random.choice(['Yes', 'No', 'No internet'], n_samples),
    'TechSupport': np.random.choice(['Yes', 'No', 'No internet'], n_samples),
    'StreamingTV': np.random.choice(['Yes', 'No', 'No internet'], n_samples),
    'StreamingMovies': np.random.choice(['Yes', 'No', 'No internet'], n_samples),
    'Contract': np.random.choice(['Month-to-month', 'One year', 'Two year'], n_samples, p=[0.55, 0.22, 0.23]),
    'PaperlessBilling': np.random.choice(['Yes', 'No'], n_samples, p=[0.60, 0.40]),
    'PaymentMethod': np.random.choice(['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'], n_samples),
    'MonthlyCharges': np.random.uniform(18, 120, n_samples),
    'TotalCharges': np.random.uniform(20, 11000, n_samples),
}

df = pd.DataFrame(data)

# Create churn target (binary classification)
# Higher churn risk for: Month-to-month, low tenure, high charges, no internet, electronic check
churn_prob = np.zeros(n_samples)

# Factors affecting churn
for i in range(n_samples):
    p = 0.27  # Base churn rate (~27% like IBM data)
    
    # Reduce churn for long-term contracts and long tenure
    if df.loc[i, 'Contract'] == 'Month-to-month':
        p += 0.25
    elif df.loc[i, 'Contract'] == 'One year':
        p += 0.10
    
    p -= (df.loc[i, 'tenure'] / 100)  # Long tenure = lower churn
    p += (df.loc[i, 'MonthlyCharges'] / 200)  # High charges = higher churn
    
    if df.loc[i, 'InternetService'] == 'Fiber optic':
        p += 0.15  # Higher dissatisfaction
    
    if df.loc[i, 'PaymentMethod'] == 'Electronic check':
        p += 0.10
    
    p = np.clip(p, 0.05, 0.80)  # Keep in realistic range
    churn_prob[i] = p

df['Churn'] = (np.random.uniform(0, 1, n_samples) < churn_prob).astype(int)

# Ensure some numeric columns match IBM structure
df['MonthlyCharges'] = df['MonthlyCharges'].round(2)
df['TotalCharges'] = df['TotalCharges'].round(2)
df['tenure'] = df['tenure'].clip(0, 72)

# Save
output_file = 'telco_customer_churn.csv'
df.to_csv(output_file, index=False)

print(f"✅ Created: {output_file}")
print(f"\nDataset Summary:")
print(f"  Samples: {len(df)}")
print(f"  Features: {len(df.columns) - 1}")  # Exclude customerID
print(f"  Target: Churn")
print(f"\nChurn Distribution:")
print(df['Churn'].value_counts())
print(f"\nChurn %: {100*df['Churn'].mean():.1f}%")
print(f"\nColumn Types:")
print(df.dtypes)
