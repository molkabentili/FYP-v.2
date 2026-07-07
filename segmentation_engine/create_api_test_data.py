#!/usr/bin/env python3
"""Create preprocessed test data for API testing."""

import pandas as pd
import numpy as np
from pathlib import Path

# Load raw test data
raw_data = pd.read_csv('test_customer_data.csv')

print(f"Raw data shape: {raw_data.shape}")
print(f"Data types:\n{raw_data.dtypes}\n")

# Preprocess using the pipeline
from src.pipeline import DataPreprocessor

preprocessor = DataPreprocessor()
cleaned_df = preprocessor.build_cleaned_feature_frame(raw_data)

print(f"Cleaned data shape: {cleaned_df.shape}")
print(f"Data types:\n{cleaned_df.dtypes}\n")

# Save for API testing
output_file = "test_preprocessed_for_api.csv"
cleaned_df.to_csv(output_file, index=False)

print(f"✅ Saved preprocessed test data: {output_file}")
print(f"   Rows: {len(cleaned_df)}")
print(f"   Columns: {len(cleaned_df.columns)}")
print(f"   All numeric: {cleaned_df.dtypes.unique()}")
