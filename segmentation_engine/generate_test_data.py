#!/usr/bin/env python3
"""Generate synthetic customer dataset for Sprint 3 testing."""

import numpy as np
import pandas as pd

# Set seed for reproducibility
np.random.seed(42)

# Generate synthetic data
n_samples = 500  # 500 customer records for real testing

data = {
    'MSISDN': [f'212{np.random.randint(600000000, 699999999)}' for _ in range(n_samples)],
    'age': np.random.normal(35, 15, n_samples).astype(int),
    'tenure_months': np.random.exponential(24, n_samples).astype(int),
    'monthly_spend': np.random.gamma(2, 50, n_samples),
    'sms_usage': np.random.exponential(100, n_samples),
    'voice_minutes': np.random.exponential(200, n_samples),
    'data_consumption_gb': np.random.exponential(3, n_samples),
    'services_subscribed': np.random.randint(1, 6, n_samples),
    'contract_type': np.random.choice(['postpaid', 'prepaid', 'hybrid'], n_samples),
    'churn_risk': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
    'last_recharge_days_ago': np.random.randint(0, 90, n_samples),
    'customer_segment': np.random.choice(['basic', 'standard', 'premium'], n_samples),
    'roaming_usage': np.random.exponential(50, n_samples),
    'app_usage_score': np.random.uniform(0, 100, n_samples),
    'device_age_months': np.random.randint(0, 60, n_samples),
    'payment_method': np.random.choice(['credit_card', 'bank_transfer', 'cash'], n_samples),
    'complaint_count': np.random.poisson(1, n_samples),
    'network_preference': np.random.choice(['4G', '3G', '5G'], n_samples),
    'active_services': np.random.randint(1, 8, n_samples),
    'satisfaction_score': np.random.uniform(1, 5, n_samples),
}

df = pd.DataFrame(data)

# Add some missing values (5%)
for col in ['monthly_spend', 'sms_usage', 'voice_minutes', 'data_consumption_gb']:
    missing_idx = np.random.choice(df.index, size=int(0.05 * len(df)), replace=False)
    df.loc[missing_idx, col] = np.nan

# Save
output_file = 'test_customer_data.csv'
df.to_csv(output_file, index=False)
print(f"✅ Generated synthetic dataset: {len(df)} rows × {len(df.columns)} columns")
print(f"   Location: {output_file}")
print(f"   Missing values: {df.isnull().sum().sum()}")
print(f"   Numeric columns: {df.select_dtypes(include=[np.number]).shape[1]}")
