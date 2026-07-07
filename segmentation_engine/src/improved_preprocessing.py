"""
IMPROVED DATA PREPROCESSING PIPELINE FOR CLUSTERING
====================================================

This pipeline should be integrated into Sprint 2 (Data Preprocessing) to fix:
1. Missing StandardScaler normalization
2. No handling of skewed distributions
3. Poor feature selection for telecom segmentation
4. No outlier detection or handling

Usage:
    from improved_preprocessing import SegmentationPreprocessor
    
    preprocessor = SegmentationPreprocessor(domain='telecom')
    X_scaled, feature_names = preprocessor.fit_transform(customer_data)
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, PowerTransformer
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class SegmentationPreprocessor:
    """
    Improved preprocessing for customer segmentation.
    
    Features:
    - Automatic log transformation for skewed features
    - StandardScaler for normalization
    - Outlier detection and capping
    - Domain-informed feature selection
    """
    
    def __init__(self, domain='telecom'):
        self.domain = domain
        self.scaler = StandardScaler()
        self.feature_names = None
        self.skew_threshold = 1.0  # Apply log transform if |skewness| > 1.0
        
    def detect_skewed_features(self, X):
        """Identify features with high skewness."""
        skewed_features = {}
        
        for col in X.select_dtypes(include=[np.number]).columns:
            data = X[col].dropna()
            if len(data) > 0:
                skewness = stats.skew(data)
                if abs(skewness) > self.skew_threshold:
                    skewed_features[col] = skewness
        
        return skewed_features
    
    def handle_outliers(self, X, method='iqr', multiplier=3.0):
        """
        Handle outliers using IQR method.
        
        Args:
            X: DataFrame
            method: 'iqr' (cap to 3*IQR), 'zscore' (remove >3σ)
            multiplier: IQR multiplier (3.0 = 3*IQR = more aggressive)
        
        Returns:
            X_clean: DataFrame with outliers handled
            outlier_report: Dict with outlier counts per feature
        """
        X_clean = X.copy()
        outlier_report = {}
        
        for col in X.select_dtypes(include=[np.number]).columns:
            if col not in X.columns:
                continue
            
            Q1 = X_clean[col].quantile(0.25)
            Q3 = X_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            # Count outliers before handling
            is_outlier = (X_clean[col] < lower_bound) | (X_clean[col] > upper_bound)
            outlier_count = is_outlier.sum()
            
            if outlier_count > 0:
                outlier_report[col] = {
                    'count': outlier_count,
                    'pct': 100 * outlier_count / len(X_clean),
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound,
                }
                
                # Cap outliers instead of removing
                X_clean[col] = X_clean[col].clip(lower=lower_bound, upper=upper_bound)
        
        return X_clean, outlier_report
    
    def apply_log_transform(self, X, columns=None):
        """
        Apply log1p transformation to specified columns.
        
        Args:
            X: DataFrame
            columns: List of column names. If None, auto-detect skewed columns.
        
        Returns:
            X_transformed: DataFrame with new columns (original_log)
        """
        X_transformed = X.copy()
        
        if columns is None:
            # Auto-detect skewed columns
            skewed = self.detect_skewed_features(X)
            columns = list(skewed.keys())
        
        for col in columns:
            if col in X.columns:
                X_transformed[col + '_log'] = np.log1p(X[col])
        
        return X_transformed
    
    def select_features_telecom(self, X):
        """
        Select features optimal for telecom customer segmentation.
        
        Priority order (business importance):
        1. Monetary: monthly_spend, total_charges
        2. Usage: data_consumption, voice_minutes, sms_usage
        3. Behavioral: tenure, churn_risk, recharge_frequency
        4. Engagement: services_subscribed, satisfaction
        
        Returns:
            List of selected feature names
        """
        candidate_features = {
            'monetary': ['monthly_spend', 'total_charges', 'arpu'],
            'usage_primary': ['data_consumption_gb', 'data_usage'],
            'usage_secondary': ['voice_minutes', 'sms_usage', 'roaming_usage'],
            'behavioral': ['tenure_months', 'churn_risk', 'last_recharge_days_ago'],
            'engagement': ['services_subscribed', 'satisfaction_score', 'app_usage_score'],
            'exclude': ['customer_id', 'msisdn', 'age', 'device_age', 'payment_method', 
                       'network_preference', 'complaint_count', 'contract_type'],
        }
        
        selected = []
        
        # Add monetary (after log transform)
        for feat in candidate_features['monetary']:
            if feat in X.columns:
                selected.append(feat + '_log')
            elif feat + '_log' in X.columns:
                selected.append(feat + '_log')
        
        # Add primary usage (after log transform)
        for feat in candidate_features['usage_primary']:
            if feat in X.columns:
                selected.append(feat + '_log')
            elif feat + '_log' in X.columns:
                selected.append(feat + '_log')
        
        # Add secondary usage (after log transform)
        for feat in candidate_features['usage_secondary']:
            if feat in X.columns:
                selected.append(feat + '_log')
            elif feat + '_log' in X.columns:
                selected.append(feat + '_log')
        
        # Add behavioral (after log transform for tenure)
        for feat in candidate_features['behavioral']:
            if feat == 'tenure_months':
                if feat in X.columns:
                    selected.append(feat + '_log')
                elif feat + '_log' in X.columns:
                    selected.append(feat + '_log')
            else:
                if feat in X.columns and X[feat].dtype in [np.float64, np.int64]:
                    selected.append(feat)
        
        # Add engagement
        for feat in candidate_features['engagement']:
            if feat in X.columns:
                selected.append(feat)
        
        # Remove duplicates and keep only available features
        selected = list(dict.fromkeys(selected))  # Remove duplicates while preserving order
        selected = [f for f in selected if f in X.columns]
        
        return selected
    
    def fit_transform(self, X, apply_log=True, handle_outliers=True, 
                     feature_selection='telecom'):
        """
        Complete preprocessing pipeline.
        
        Args:
            X: Input DataFrame
            apply_log: Apply log transformation to skewed features
            handle_outliers: Cap outliers to 3*IQR
            feature_selection: 'telecom' or 'none'
        
        Returns:
            X_scaled: Scaled feature matrix (ndarray)
            feature_names: List of selected feature names
        """
        X_processed = X.copy()
        
        # Step 1: Handle missing values
        numeric_cols = X_processed.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            X_processed[col] = X_processed[col].fillna(X_processed[col].median())
        
        # Step 2: Remove invalid records (e.g., age < 0)
        if 'age' in X_processed.columns:
            X_processed = X_processed[X_processed['age'] >= 0]
        
        # Step 3: Handle outliers
        if handle_outliers:
            X_processed, self.outlier_report = self.handle_outliers(X_processed)
        
        # Step 4: Apply log transformation to skewed features
        if apply_log:
            skewed_features = self.detect_skewed_features(X_processed)
            X_processed = self.apply_log_transform(X_processed, columns=list(skewed_features.keys()))
        
        # Step 5: Select features
        if feature_selection == 'telecom':
            self.feature_names = self.select_features_telecom(X_processed)
        else:
            self.feature_names = [col for col in X_processed.columns 
                                 if col in X_processed.select_dtypes(include=[np.number]).columns]
        
        X_selected = X_processed[self.feature_names]
        
        # Step 6: Scale features
        X_scaled = self.scaler.fit_transform(X_selected)
        
        return X_scaled, self.feature_names
    
    def transform(self, X):
        """Transform new data using fitted scaler and feature names."""
        if self.feature_names is None:
            raise ValueError("Preprocessor not fitted. Call fit_transform first.")
        
        X_processed = X.copy()
        
        # Apply same transformations
        numeric_cols = X_processed.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            X_processed[col] = X_processed[col].fillna(X_processed[col].median())
        
        # Apply log to skewed features
        skewed_features = self.detect_skewed_features(X_processed)
        for col in skewed_features.keys():
            if col not in X_processed.columns:
                X_processed[col + '_log'] = np.log1p(X_processed[col])
        
        X_selected = X_processed[self.feature_names]
        X_scaled = self.scaler.transform(X_selected)
        
        return X_scaled


# ==============================================================================
# EXAMPLE USAGE
# ==============================================================================

if __name__ == '__main__':
    import pandas as pd
    
    # Load sample data
    df = pd.read_csv('api_data/test_data.csv')
    
    # Initialize preprocessor
    prep = SegmentationPreprocessor(domain='telecom')
    
    # Fit and transform data
    X_scaled, features = prep.fit_transform(df, apply_log=True, 
                                            handle_outliers=True, 
                                            feature_selection='telecom')
    
    print(f"Original shape: {df.shape}")
    print(f"Processed shape: {X_scaled.shape}")
    print(f"Selected features ({len(features)}):")
    for i, feat in enumerate(features, 1):
        print(f"  {i}. {feat}")
    
    print(f"\nScaled data statistics:")
    print(f"  Mean: {X_scaled.mean(axis=0).round(4)}")
    print(f"  Std:  {X_scaled.std(axis=0).round(4)}")
    
    # Check for outliers detected
    if hasattr(prep, 'outlier_report') and prep.outlier_report:
        print(f"\nOutliers detected:")
        for feat, info in prep.outlier_report.items():
            print(f"  {feat}: {info['count']} ({info['pct']:.2f}%)")
