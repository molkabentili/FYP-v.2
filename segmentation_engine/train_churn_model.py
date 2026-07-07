#!/usr/bin/env python3
"""Sprint 3+: Build and train real ML model for Telco Churn Prediction.

This is REAL supervised learning:
- Train/test split: 80/20
- Model: Logistic Regression + Random Forest
- Metrics: Accuracy, Precision, Recall, F1, AUC-ROC
- Hyperparameter tuning: GridSearchCV
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report, roc_curve
)
import json
from pathlib import Path


class ChurnPredictor:
    """ML model for telecom customer churn prediction."""
    
    def __init__(self):
        self.lr_model = None
        self.rf_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_importance = None
        self.results = {}
    
    def load_and_prepare_data(self, filepath):
        """Load and prepare data for training."""
        print("\n" + "="*70)
        print("STEP 1: LOAD & PREPARE DATA")
        print("="*70)
        
        df = pd.read_csv(filepath)
        print(f"\n✓ Loaded {filepath}")
        print(f"  Shape: {df.shape}")
        print(f"  Churn distribution:\n{df['Churn'].value_counts()}")
        
        # Separate features and target
        X = df.drop(['customerID', 'Churn'], axis=1)
        y = df['Churn']
        
        print(f"\n✓ Features: {X.shape[1]}")
        print(f"  Numeric: {X.select_dtypes(include=[np.number]).shape[1]}")
        print(f"  Categorical: {X.select_dtypes(include=['object']).shape[1]}")
        
        # Encode categorical variables
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            self.label_encoders[col] = le
        
        print(f"\n✓ Encoded {len(categorical_cols)} categorical features")
        
        return X, y
    
    def split_and_scale(self, X, y):
        """Split data and scale features."""
        print("\n" + "="*70)
        print("STEP 2: TRAIN/TEST SPLIT & SCALING")
        print("="*70)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42,
            stratify=y
        )
        
        print(f"\n✓ Train set: {X_train.shape[0]} samples")
        print(f"✓ Test set: {X_test.shape[0]} samples")
        print(f"✓ Train churn rate: {y_train.mean():.1%}")
        print(f"✓ Test churn rate: {y_test.mean():.1%}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print(f"\n✓ Applied StandardScaler")
        print(f"  Mean (train): {X_train_scaled.mean():.4f}")
        print(f"  Std (train): {X_train_scaled.std():.4f}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_logistic_regression(self, X_train, X_test, y_train, y_test):
        """Train Logistic Regression with hyperparameter tuning."""
        print("\n" + "="*70)
        print("STEP 3A: TRAIN LOGISTIC REGRESSION")
        print("="*70)
        
        # Hyperparameter grid
        param_grid = {
            'C': [0.001, 0.01, 0.1, 1.0, 10.0],
            'max_iter': [200, 500, 1000],
            'solver': ['lbfgs', 'liblinear']
        }
        
        print(f"\n✓ GridSearchCV with {len(param_grid['C']) * len(param_grid['max_iter']) * len(param_grid['solver'])} configurations")
        
        grid_search = GridSearchCV(
            LogisticRegression(random_state=42),
            param_grid,
            cv=5,
            scoring='roc_auc',
            n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        self.lr_model = grid_search.best_estimator_
        
        print(f"\n✓ Best parameters: {grid_search.best_params_}")
        print(f"✓ Best CV score: {grid_search.best_score_:.4f}")
        
        # Evaluate
        y_pred = self.lr_model.predict(X_test)
        y_pred_proba = self.lr_model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'auc_roc': roc_auc_score(y_test, y_pred_proba)
        }
        
        print(f"\n✓ Test Set Performance:")
        for metric, value in metrics.items():
            print(f"  {metric.upper():<12}: {value:.4f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.lr_model, X_train, y_train, cv=5, scoring='roc_auc')
        print(f"\n✓ Cross-validation ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        self.results['logistic_regression'] = metrics
        return metrics
    
    def train_random_forest(self, X_train, X_test, y_train, y_test):
        """Train Random Forest with hyperparameter tuning."""
        print("\n" + "="*70)
        print("STEP 3B: TRAIN RANDOM FOREST")
        print("="*70)
        
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [10, 20, 30],
            'min_samples_split': [5, 10],
            'min_samples_leaf': [2, 4]
        }
        
        print(f"\n✓ GridSearchCV with {len(param_grid['n_estimators']) * len(param_grid['max_depth']) * len(param_grid['min_samples_split']) * len(param_grid['min_samples_leaf'])} configurations")
        
        grid_search = GridSearchCV(
            RandomForestClassifier(random_state=42, n_jobs=-1),
            param_grid,
            cv=5,
            scoring='roc_auc',
            n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        self.rf_model = grid_search.best_estimator_
        
        print(f"\n✓ Best parameters: {grid_search.best_params_}")
        print(f"✓ Best CV score: {grid_search.best_score_:.4f}")
        
        # Evaluate
        y_pred = self.rf_model.predict(X_test)
        y_pred_proba = self.rf_model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'auc_roc': roc_auc_score(y_test, y_pred_proba)
        }
        
        print(f"\n✓ Test Set Performance:")
        for metric, value in metrics.items():
            print(f"  {metric.upper():<12}: {value:.4f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X_train.columns if hasattr(X_train, 'columns') else [f'feature_{i}' for i in range(X_train.shape[1])],
            'importance': self.rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n✓ Top 10 Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']:<20}: {row['importance']:.4f}")
        
        self.feature_importance = feature_importance
        self.results['random_forest'] = metrics
        return metrics
    
    def compare_models(self):
        """Compare both models."""
        print("\n" + "="*70)
        print("MODEL COMPARISON")
        print("="*70)
        
        lr_metrics = self.results['logistic_regression']
        rf_metrics = self.results['random_forest']
        
        print(f"\nLogistic Regression vs Random Forest:")
        print("-" * 70)
        
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'auc_roc']:
            lr_val = lr_metrics[metric]
            rf_val = rf_metrics[metric]
            winner = "RF" if rf_val > lr_val else "LR" if lr_val > rf_val else "TIE"
            
            print(f"{metric.upper():<12}")
            print(f"  LR:   {lr_val:.4f}")
            print(f"  RF:   {rf_val:.4f}")
            print(f"  Winner: {winner}\n")
        
        # Determine best model
        best_model = 'random_forest' if rf_metrics['auc_roc'] > lr_metrics['auc_roc'] else 'logistic_regression'
        print(f"\n🏆 BEST MODEL: {best_model.upper()}")
        print(f"   ROC-AUC: {self.results[best_model]['auc_roc']:.4f}")
        
        return best_model
    
    def save_results(self, output_file='churn_model_results.json'):
        """Save training results."""
        output = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'models_trained': list(self.results.keys()),
            'logistic_regression': self.results.get('logistic_regression'),
            'random_forest': self.results.get('random_forest'),
            'feature_importance': self.feature_importance.head(10).to_dict('records') if self.feature_importance is not None else None
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")


def main():
    """Main training pipeline."""
    print("\n" + "="*70)
    print("TELCO CHURN PREDICTION: MODEL TRAINING")
    print("="*70)
    
    predictor = ChurnPredictor()
    
    # Load & prepare
    X, y = predictor.load_and_prepare_data('telco_customer_churn.csv')
    
    # Split & scale
    X_train, X_test, y_train, y_test = predictor.split_and_scale(X, y)
    
    # Train model 1
    predictor.train_logistic_regression(X_train, X_test, y_train, y_test)
    
    # Train model 2
    predictor.train_random_forest(X_train, X_test, y_train, y_test)
    
    # Compare
    best_model = predictor.compare_models()
    
    # Save
    predictor.save_results()
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("1. Deploy best model via API endpoint")
    print("2. Make predictions on new customers")
    print("3. Monitor model performance in production")
    print("="*70)


if __name__ == '__main__':
    main()
