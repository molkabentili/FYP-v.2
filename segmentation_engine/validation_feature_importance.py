"""
Feature Importance Analysis
Identifies which features distinguish each cluster
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
import warnings
warnings.filterwarnings('ignore')

def analyze_feature_importance(X, feature_names=None, n_clusters=3):
    """
    Analyze feature importance for cluster separation
    
    Args:
        X: Feature matrix (should be scaled)
        feature_names: List of feature names
        n_clusters: Number of clusters
        
    Returns:
        Dictionary with importance analysis
    """
    
    print(f"\n{'='*70}")
    print(f"Feature Importance Analysis")
    print(f"{'='*70}\n")
    
    if feature_names is None:
        feature_names = [f"Feature_{i}" for i in range(X.shape[1])]
    
    # Cluster the data
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # For each cluster, compute importance relative to all others
    importance_by_cluster = {}
    
    for target_cluster in range(n_clusters):
        # Binary classification: target cluster vs others
        y_binary = (labels == target_cluster).astype(int)
        
        # Train random forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        rf.fit(X, y_binary)
        
        # Get feature importance
        importances = rf.feature_importances_
        importance_by_cluster[target_cluster] = importances
        
        # Sort by importance
        sorted_indices = np.argsort(importances)[::-1]
        
        print(f"Cluster {target_cluster} - Top 5 Distinguishing Features:")
        print(f"  Cluster size: {np.sum(y_binary)} samples\n")
        
        for rank, idx in enumerate(sorted_indices[:5], 1):
            importance = importances[idx]
            print(f"  {rank}. {feature_names[idx]:<25} - Importance: {importance:.4f}")
        
        print()
    
    # Visualization
    fig, axes = plt.subplots(1, n_clusters, figsize=(5*n_clusters, 6))
    
    if n_clusters == 1:
        axes = [axes]
    
    for cluster_id in range(n_clusters):
        importances = importance_by_cluster[cluster_id]
        sorted_indices = np.argsort(importances)[-10:]  # Top 10 features
        
        ax = axes[cluster_id]
        
        ax.barh([feature_names[i] for i in sorted_indices], 
               importances[sorted_indices],
               color='#2E7D32', edgecolor='black', alpha=0.7)
        
        ax.set_xlabel('Feature Importance', fontweight='bold')
        ax.set_title(f'Cluster {cluster_id}\n(n={np.sum(labels==cluster_id)} samples)', 
                    fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('feature_importance.png', dpi=150, bbox_inches='tight')
    print(f"✅ Visualization saved: feature_importance.png\n")
    plt.close()
    
    return importance_by_cluster

def cluster_characteristics(X, feature_names=None, n_clusters=3):
    """
    Compute and display characteristics of each cluster
    
    Args:
        X: Feature matrix
        feature_names: List of feature names
        n_clusters: Number of clusters
        
    Returns:
        DataFrame with cluster statistics
    """
    
    print(f"\n{'='*70}")
    print(f"Cluster Characteristics (Statistical Profile)")
    print(f"{'='*70}\n")
    
    if feature_names is None:
        feature_names = [f"Feature_{i}" for i in range(X.shape[1])]
    
    # Cluster the data
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Create dataframe with cluster labels
    df = pd.DataFrame(X, columns=feature_names)
    df['Cluster'] = labels
    
    # Compute statistics
    stats = []
    
    for cluster_id in range(n_clusters):
        cluster_data = df[df['Cluster'] == cluster_id][feature_names]
        
        print(f"Cluster {cluster_id}:")
        print(f"  Size: {len(cluster_data)} samples ({len(cluster_data)/len(df)*100:.1f}%)\n")
        print(f"  Statistical Profile:")
        
        for feature in feature_names[:5]:  # Show first 5 features
            mean_val = cluster_data[feature].mean()
            std_val = cluster_data[feature].std()
            print(f"    {feature:.<30} μ={mean_val:>8.4f}, σ={std_val:>8.4f}")
        
        print()
        
        # Add to stats
        means = cluster_data.mean()
        means['Cluster_Size'] = len(cluster_data)
        means['Cluster_ID'] = cluster_id
        stats.append(means)
    
    stats_df = pd.DataFrame(stats)
    
    # Visualization: Cluster means heatmap
    cluster_means = stats_df[feature_names].values
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    im = ax.imshow(cluster_means.T, cmap='RdYlGn', aspect='auto')
    
    ax.set_xticks(range(n_clusters))
    ax.set_xticklabels([f'Cluster {i}' for i in range(n_clusters)])
    ax.set_yticks(range(len(feature_names)))
    ax.set_yticklabels(feature_names, fontsize=9)
    ax.set_title('Cluster Profiles (Feature Means)', fontweight='bold', fontsize=12)
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Standardized Mean Value', fontweight='bold')
    
    # Add values to heatmap
    for i in range(n_clusters):
        for j in range(len(feature_names)):
            text = ax.text(i, j, f'{cluster_means[i, j]:.2f}',
                         ha="center", va="center", color="black", fontsize=8)
    
    plt.tight_layout()
    plt.savefig('cluster_characteristics.png', dpi=150, bbox_inches='tight')
    print(f"✅ Visualization saved: cluster_characteristics.png\n")
    plt.close()
    
    return stats_df

def load_test_data():
    """Load preprocessed test customer data"""
    try:
        data = pd.read_csv('test_preprocessed_for_api.csv')
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        X = data[numeric_cols].values
        
        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        feature_names = list(numeric_cols)
        return X_scaled, feature_names
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Using synthetic data instead...")
        X, _ = make_blobs(n_samples=500, n_features=15, centers=3, random_state=42)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        feature_names = [f"Feature_{i}" for i in range(X.shape[1])]
        return X_scaled, feature_names

if __name__ == "__main__":
    # Load data
    X, feature_names = load_test_data()
    print(f"\n📊 Data shape: {X.shape}")
    print(f"   Samples: {X.shape[0]}, Features: {X.shape[1]}")
    
    # Analyze feature importance
    importance_results = analyze_feature_importance(X, feature_names, n_clusters=3)
    
    # Cluster characteristics
    stats_df = cluster_characteristics(X, feature_names, n_clusters=3)
    
    print(f"\n{'='*70}")
    print(f"FEATURE IMPORTANCE SUMMARY")
    print(f"{'='*70}\n")
    print(f"✅ Identified distinguishing features for each cluster")
    print(f"✅ Computed statistical profiles (mean, std) per cluster")
    print(f"✅ Created heatmap visualization of cluster characteristics")
