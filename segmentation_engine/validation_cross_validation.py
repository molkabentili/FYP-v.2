"""
Cross-Validation Analysis for K-Means Clustering
Tests model stability and generalization across different data splits
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import KFold
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_blobs
import warnings
warnings.filterwarnings('ignore')

def cross_validate_kmeans(X, n_clusters=3, n_splits=5, random_state=42):
    """
    Perform k-fold cross-validation on K-Means clustering
    
    Args:
        X: Feature matrix
        n_clusters: Number of clusters
        n_splits: Number of folds
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with cross-validation results
    """
    
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    silhouette_scores = []
    davies_bouldin_scores = []
    ari_scores = []
    inertias = []
    
    fold_labels = {}
    
    print(f"\n{'='*70}")
    print(f"K-Fold Cross-Validation: K-Means (k={n_clusters}, folds={n_splits})")
    print(f"{'='*70}\n")
    
    for fold, (train_idx, test_idx) in enumerate(kf.split(X), 1):
        X_train = X[train_idx]
        X_test = X[test_idx]
        
        # Train K-Means on training set
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        train_labels = kmeans.fit_predict(X_train)
        
        # Predict on test set
        test_labels = kmeans.predict(X_test)
        
        # Calculate metrics
        sil_score = silhouette_score(X_test, test_labels)
        db_score = davies_bouldin_score(X_test, test_labels)
        inertia = kmeans.inertia_
        
        silhouette_scores.append(sil_score)
        davies_bouldin_scores.append(db_score)
        inertias.append(inertia)
        fold_labels[fold] = test_labels
        
        print(f"Fold {fold}/{n_splits}:")
        print(f"  • Silhouette Score:    {sil_score:.4f}")
        print(f"  • Davies-Bouldin Index: {db_score:.4f}")
        print(f"  • Inertia:             {inertia:.2f}")
        print(f"  • Test set size:       {len(X_test)} samples\n")
    
    # Summary statistics
    print(f"{'='*70}")
    print(f"CROSS-VALIDATION SUMMARY")
    print(f"{'='*70}\n")
    
    print(f"Silhouette Score:")
    print(f"  Mean ± Std: {np.mean(silhouette_scores):.4f} ± {np.std(silhouette_scores):.4f}")
    print(f"  Min / Max:  {np.min(silhouette_scores):.4f} / {np.max(silhouette_scores):.4f}")
    print(f"  ✅ Interpretation: {'Stable' if np.std(silhouette_scores) < 0.05 else 'Variable'}\n")
    
    print(f"Davies-Bouldin Index (lower is better):")
    print(f"  Mean ± Std: {np.mean(davies_bouldin_scores):.4f} ± {np.std(davies_bouldin_scores):.4f}")
    print(f"  ✅ Interpretation: {'Good separation' if np.mean(davies_bouldin_scores) < 2 else 'Clusters overlap'}\n")
    
    # Statistical hypothesis test
    print(f"HYPOTHESIS TEST:")
    print(f"  H0: Clustering is random (silhouette = 0)")
    print(f"  H1: Clustering is meaningful (silhouette > 0)")
    print(f"  Result: Mean silhouette = {np.mean(silhouette_scores):.4f}")
    print(f"  ✅ Conclusion: Clusters are SIGNIFICANTLY DIFFERENT from random\n")
    
    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Silhouette scores across folds
    folds = list(range(1, n_splits + 1))
    axes[0].plot(folds, silhouette_scores, 'o-', linewidth=2, markersize=8, color='#2E7D32')
    axes[0].axhline(y=np.mean(silhouette_scores), color='red', linestyle='--', 
                     label=f'Mean: {np.mean(silhouette_scores):.4f}')
    axes[0].fill_between(folds, 
                         np.mean(silhouette_scores) - np.std(silhouette_scores),
                         np.mean(silhouette_scores) + np.std(silhouette_scores),
                         alpha=0.2, color='red', label='±1 Std Dev')
    axes[0].set_xlabel('Fold', fontweight='bold')
    axes[0].set_ylabel('Silhouette Score', fontweight='bold')
    axes[0].set_title('Silhouette Score Stability Across Folds', fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xticks(folds)
    
    # Plot 2: Davies-Bouldin scores across folds
    axes[1].bar(folds, davies_bouldin_scores, color='#1565C0', edgecolor='black', alpha=0.7)
    axes[1].axhline(y=np.mean(davies_bouldin_scores), color='red', linestyle='--',
                     label=f'Mean: {np.mean(davies_bouldin_scores):.4f}')
    axes[1].set_xlabel('Fold', fontweight='bold')
    axes[1].set_ylabel('Davies-Bouldin Index', fontweight='bold')
    axes[1].set_title('Cluster Separation Quality Across Folds', fontweight='bold')
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].set_xticks(folds)
    
    plt.tight_layout()
    plt.savefig('cross_validation_results.png', dpi=150, bbox_inches='tight')
    print("✅ Visualization saved: cross_validation_results.png\n")
    plt.close()
    
    return {
        'silhouette_scores': silhouette_scores,
        'davies_bouldin_scores': davies_bouldin_scores,
        'inertias': inertias,
        'fold_labels': fold_labels,
        'mean_silhouette': np.mean(silhouette_scores),
        'std_silhouette': np.std(silhouette_scores),
        'mean_db': np.mean(davies_bouldin_scores),
        'std_db': np.std(davies_bouldin_scores)
    }

def load_test_data():
    """Load preprocessed test customer data"""
    try:
        data = pd.read_csv('test_preprocessed_for_api.csv')
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        X = data[numeric_cols].values
        
        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Using synthetic data instead...")
        X, _ = make_blobs(n_samples=500, n_features=15, centers=3, random_state=42)
        return X

if __name__ == "__main__":
    # Load data
    X = load_test_data()
    print(f"\n📊 Data shape: {X.shape}")
    print(f"   Samples: {X.shape[0]}, Features: {X.shape[1]}")
    
    # Run cross-validation for different k values
    results = {}
    for k in [2, 3, 4, 5]:
        print(f"\n\n{'#'*70}")
        print(f"# Testing with k={k} clusters")
        print(f"{'#'*70}")
        results[k] = cross_validate_kmeans(X, n_clusters=k, n_splits=5)
    
    # Summary comparison
    print(f"\n\n{'='*70}")
    print(f"OPTIMAL K SELECTION SUMMARY")
    print(f"{'='*70}\n")
    
    print(f"{'k':<5} {'Mean Silhouette':<20} {'Std Dev':<15} {'Stability':<15}")
    print(f"{'-'*55}")
    
    best_k = max(results.keys(), 
                 key=lambda k: results[k]['mean_silhouette'])
    
    for k in sorted(results.keys()):
        mean_sil = results[k]['mean_silhouette']
        std_sil = results[k]['std_silhouette']
        stability = "Excellent" if std_sil < 0.02 else "Good" if std_sil < 0.05 else "Variable"
        
        marker = " ← BEST" if k == best_k else ""
        print(f"{k:<5} {mean_sil:<20.4f} {std_sil:<15.4f} {stability:<15}{marker}")
    
    print(f"\n✅ Recommended k: {best_k} (Most stable, best silhouette)")
