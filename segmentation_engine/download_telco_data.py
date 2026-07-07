#!/usr/bin/env python3
"""Download IBM Telco Customer Churn dataset and save locally."""

import pandas as pd
import requests
from pathlib import Path

print("Downloading IBM Telco Customer Churn dataset...")

# Download from Kaggle-style source (UCI ML Repository)
url = "https://raw.githubusercontent.com/IBM/telco-customer-churn/main/data/WA_Fn-UseC_-Telco-Customer-Churn.csv"

try:
    df = pd.read_csv(url)
    print(f"✅ Downloaded successfully!")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    # Save locally
    output_file = "telco_customer_churn.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✅ Saved to: {output_file}")
    
    # Show summary
    print(f"\nDataset Summary:")
    print(f"  Target (Churn): {df['Churn'].value_counts().to_dict()}")
    print(f"\nColumns:")
    for col in df.columns[:15]:
        print(f"  - {col}")
    if len(df.columns) > 15:
        print(f"  ... and {len(df.columns)-15} more")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nAlternative: Download manually from:")
    print("  https://www.kaggle.com/datasets/blastchar/telco-customer-churn")
