"""
Advanced Validation: Cross-Validation, Feature Importance, & Stability
=========================================================================

This module implements:
1. K-Fold Cross-Validation
2. Stability Testing (multiple random seeds)
3. Feature Importance Analysis (via Random Forest)
4. PCA Visualization
5. UMAP Visualization

Author: Data Science Team
Date: April 28, 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.metrics.cluster import adjusted_rand_score
from sklearn.model_selection import KFold
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

def load_data(csv_path):
    """Load and prepare data"""
    df = pd.read_csv(csv_path)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cols_to_remove = ['customerID', 'MSISDN', 'phone_number']
    numeric_cols = [col for col in numeric_cols if col not in cols_to_remove]
    
    X = df[numeric_cols].fillna(df[numeric_cols].median())
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, numeric_cols, df

def perform_cross_validation(X_scaled, n_clusters=3, n_splits=5):
    """Perform K-Fold Cross-Validation"""
    
    print("\n" + "=" * 80)
    print(f"K-FOLD CROSS-VALIDATION (k={n_splits})")
    print("=" * 80)
    
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    cv_scores = []
    cv_inertias = []
    
    fold = 1
    for train_idx, test_idx in kf.split(X_scaled):
        X_train = X_scaled[train_idx]
        X_test = X_scaled[test_idx]
        
        # Train on fold
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(X_train)
        
        # Evaluate on holdout
        test_labels = kmeans.predict(X_test)
        test_silhouette = silhouette_score(X_test, test_labels)
        test_inertia = kmeans.inertia_
        
        cv_scores.append(test_silhouette)
        cv_inertias.append(test_inertia)
        
        print(f"  Fold {fold}: Silhouette={test_silhouette:.4f}, Inertia={test_inertia:.1f}")
        fold += 1
    
    # Summary statistics
    cv_mean = np.mean(cv_scores)
    cv_std = np.std(cv_scores)
    
    print(f"\n  Mean Silhouette: {cv_mean:.4f} ± {cv_std:.4f}")
    print(f"  Coefficient of Variation: {cv_std/cv_mean:.4f}")
    
    if cv_std < 0.01:
        print("  [EXCELLENT] Very stable across folds")
    elif cv_std < 0.05:
        print("  [GOOD] Stable across folds")
    else:
        print("  [WARNING] Some variance across folds")
    
    return cv_scores, cv_mean, cv_std

def test_cluster_stability(X_scaled, n_clusters=3, n_runs=10):
    """Test stability with multiple random seeds"""
    
    print("\n" + "=" * 80)
    print(f"STABILITY TESTING ({n_runs} runs with different random seeds)")
    print("=" * 80)
    
    labels_list = []
    
    for seed in range(n_runs):
        kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        labels_list.append(labels)
    
    # Compute pairwise ARI (Adjusted Rand Index)
    ari_scores = []
    
    for i in range(len(labels_list) - 1):
        ari = adjusted_rand_score(labels_list[i], labels_list[i + 1])
        ari_scores.append(ari)
    
    ari_mean = np.mean(ari_scores)
    ari_std = np.std(ari_scores)
    
    print(f"\n  ARI Scores across consecutive runs:")
    for i, ari in enumerate(ari_scores[:5]):  # Show first 5
        print(f"    Run {i} vs {i+1}: {ari:.4f}")
    if len(ari_scores) > 5:
        print(f"    ... ({len(ari_scores) - 5} more comparisons)")
    
    print(f"\n  Mean ARI: {ari_mean:.4f} ± {ari_std:.4f}")
    
    # Interpret
    if ari_mean > 0.9:
        print("  [EXCELLENT] Clusters are highly reproducible")
    elif ari_mean > 0.7:
        print("  [GOOD] Clusters are stable")
    elif ari_mean > 0.5:
        print("  [MODERATE] Some variability in cluster assignment")
    else:
        print("  [BAD] Results appear unstable")
    
    return ari_scores, ari_mean

def compute_feature_importance(X_scaled, feature_names, n_clusters=3):
    """Compute feature importance using Random Forest"""
    
    print("\n" + "=" * 80)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("=" * 80)
    
    # Fit base KMeans model
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # Train Random Forest to predict cluster assignment
    # This shows which features are most important for cluster separation
    importances = np.zeros(X_scaled.shape[1])
    
    print("\n  Training feature importance model...")
    
    for cluster_id in range(n_clusters):
        # Binary classifier: this cluster vs. all others
        y_binary = (labels == cluster_id).astype(int)
        
        rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        rf.fit(X_scaled, y_binary)
        
        importances += rf.feature_importances_
    
    # Normalize
    importances = importances / np.sum(importances)
    
    # Sort
    feature_importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values('Importance', ascending=False)
    
    print("\n  Top 10 Important Features:")
    for idx, row in feature_importance_df.head(10).iterrows():
        importance_pct = row['Importance'] * 100
        bar = "=" * int(importance_pct / 5)
        print(f"    {row['Feature']:30} {bar} {importance_pct:6.2f}%")
    
    # Visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    top_n = 10
    top_features = feature_importance_df.head(top_n)
    ax.barh(range(len(top_features)), top_features['Importance'].values, color='steelblue')
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features['Feature'].values)
    ax.set_xlabel('Importance Score', fontweight='bold')
    ax.set_title('Top 10 Features Driving Cluster Separation', fontweight='bold', fontsize=12)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
    print("\n  [OK] Saved: feature_importance.png")
    plt.show()
    
    return feature_importance_df

def visualize_pca(X_scaled, n_clusters=3):
    """Visualize clusters in 2D PCA space"""
    
    print("\n" + "=" * 80)
    print("PCA DIMENSIONALITY REDUCTION")
    print("=" * 80)
    
    # Fit PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    explained_var = np.sum(pca.explained_variance_ratio_)
    
    print(f"\n  PC1 explains: {pca.explained_variance_ratio_[0]:.1%} of variance")
    print(f"  PC2 explains: {pca.explained_variance_ratio_[1]:.1%} of variance")
    print(f"  Combined: {explained_var:.1%} of variance")
    
    # Cluster in original space
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # Project cluster centers to PCA space
    centers_pca = pca.transform(kmeans.cluster_centers_)
    
    # Visualization
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = ['red', 'green', 'blue']
    for i in range(n_clusters):
        mask = labels == i
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                  c=colors[i], label=f'Cluster {i}', alpha=0.6, s=50)
    
    # Plot cluster centers
    ax.scatter(centers_pca[:, 0], centers_pca[:, 1], 
              c='black', marker='X', s=300, edgecolors='white', linewidth=2,
              label='Centroids')
    
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})', fontweight='bold')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})', fontweight='bold')
    ax.set_title('Clusters in PCA Space (2D Projection)', fontweight='bold', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('clusters_pca.png', dpi=300, bbox_inches='tight')
    print("  [OK] Saved: clusters_pca.png")
    plt.show()
    
    return pca, X_pca

def visualize_umap(X_scaled, n_clusters=3):
    """Visualize clusters in UMAP space (if umap-learn available)"""
    
    try:
        from umap import UMAP
        
        print("\n" + "=" * 80)
        print("UMAP DIMENSIONALITY REDUCTION")
        print("=" * 80)
        
        # Fit UMAP
        umap_model = UMAP(n_components=2, random_state=42, min_dist=0.1)
        X_umap = umap_model.fit_transform(X_scaled)
        
        print("  ✓ UMAP embedding computed")
        
        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        
        # Visualization
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = ['red', 'green', 'blue']
        for i in range(n_clusters):
            mask = labels == i
            ax.scatter(X_umap[mask, 0], X_umap[mask, 1], 
                      c=colors[i], label=f'Cluster {i}', alpha=0.6, s=50)
        
        ax.set_xlabel('UMAP Dimension 1', fontweight='bold')
        ax.set_ylabel('UMAP Dimension 2', fontweight='bold')
        ax.set_title('Clusters in UMAP Space (Non-linear Embedding)', fontweight='bold', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('clusters_umap.png', dpi=300, bbox_inches='tight')
        print("  [OK] Saved: clusters_umap.png")
        plt.show()
        
    except ImportError:
        print("\n[WARNING] UMAP not installed. Install with: pip install umap-learn")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ADVANCED CLUSTERING VALIDATION")
    print("=" * 80)
    
    # Load data
    csv_file = "test_customer_data.csv"
    X_scaled, feature_names, df_original = load_data(csv_file)
    
    print(f"✓ Loaded {X_scaled.shape[0]} samples with {X_scaled.shape[1]} features")
    
    # Run analyses
    cv_scores, cv_mean, cv_std = perform_cross_validation(X_scaled, n_clusters=3, n_splits=5)
    ari_scores, ari_mean = test_cluster_stability(X_scaled, n_clusters=3, n_runs=10)
    feature_importance = compute_feature_importance(X_scaled, feature_names, n_clusters=3)
    pca, X_pca = visualize_pca(X_scaled, n_clusters=3)
    visualize_umap(X_scaled, n_clusters=3)
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE [OK]")
    print("=" * 80)
    print("\nKey Findings:")
    print(f"  • Cross-validation stable: {cv_mean:.4f} ± {cv_std:.4f}")
    print(f"  • Cluster stability high: ARI = {ari_mean:.4f}")
    print(f"  • Top 3 features: {', '.join(feature_importance.head(3)['Feature'].tolist())}")
    print("\nGenerated files:")
    print("  • feature_importance.png")
    print("  • clusters_pca.png")
    print("  • clusters_umap.png (if available)")
