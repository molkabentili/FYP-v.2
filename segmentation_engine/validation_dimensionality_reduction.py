"""
Dimensionality Reduction: PCA and UMAP for Cluster Visualization
Reduces high-dimensional customer data to 2D for visual analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
import warnings
warnings.filterwarnings('ignore')

try:
    from umap import UMAP
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False
    print("Note: UMAP not installed. Install with: pip install umap-learn")

def pca_analysis(X, n_clusters=3):
    """
    Perform PCA and visualize clusters in 2D space
    
    Args:
        X: Feature matrix (scaled)
        n_clusters: Number of clusters
        
    Returns:
        Dictionary with PCA results
    """
    
    print(f"\n{'='*70}")
    print(f"PCA (Principal Component Analysis)")
    print(f"{'='*70}\n")
    
    # Fit PCA
    pca = PCA(n_components=min(X.shape[1], 10))
    X_pca = pca.fit_transform(X)
    
    # Explained variance
    cumsum_var = np.cumsum(pca.explained_variance_ratio_)
    
    print(f"Variance Explained:")
    for i in range(min(5, len(pca.explained_variance_ratio_))):
        print(f"  PC{i+1}: {pca.explained_variance_ratio_[i]:.4f} "
              f"({cumsum_var[i]:.2%} cumulative)")
    
    print(f"\n✅ First 2 components explain: {cumsum_var[1]:.2%} of variance")
    
    # Cluster the data
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Project cluster centers to PCA space
    centers_pca = pca.transform(kmeans.cluster_centers_)
    
    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: 2D PCA colored by clusters
    scatter = axes[0].scatter(X_pca[:, 0], X_pca[:, 1], c=labels, 
                              cmap='viridis', s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    # Plot cluster centers
    axes[0].scatter(centers_pca[:, 0], centers_pca[:, 1], 
                   c='red', marker='X', s=300, edgecolors='black', linewidth=2,
                   label='Cluster Centers', zorder=5)
    
    axes[0].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontweight='bold')
    axes[0].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontweight='bold')
    axes[0].set_title(f'K-Means Clusters (PCA Space)', fontweight='bold', fontsize=12)
    
    cbar = plt.colorbar(scatter, ax=axes[0])
    cbar.set_label('Cluster', fontweight='bold')
    axes[0].legend(['Cluster Centers'], loc='best')
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Scree plot (variance explained)
    axes[1].plot(range(1, len(cumsum_var) + 1), cumsum_var * 100, 'o-', 
                linewidth=2, markersize=8, color='#2E7D32')
    axes[1].axhline(y=80, color='red', linestyle='--', label='80% variance threshold')
    axes[1].axhline(y=90, color='orange', linestyle='--', label='90% variance threshold')
    axes[1].set_xlabel('Number of Components', fontweight='bold')
    axes[1].set_ylabel('Cumulative Explained Variance (%)', fontweight='bold')
    axes[1].set_title('PCA Scree Plot', fontweight='bold', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xticks(range(1, min(11, len(cumsum_var) + 1)))
    
    plt.tight_layout()
    plt.savefig('pca_analysis.png', dpi=150, bbox_inches='tight')
    print(f"\n✅ Visualization saved: pca_analysis.png\n")
    plt.close()
    
    return {
        'pca': pca,
        'X_pca': X_pca,
        'labels': labels,
        'explained_variance': pca.explained_variance_ratio_,
        'cumsum_variance': cumsum_var
    }

def umap_analysis(X, n_clusters=3):
    """
    Perform UMAP and visualize clusters
    
    Args:
        X: Feature matrix (scaled)
        n_clusters: Number of clusters
        
    Returns:
        Dictionary with UMAP results
    """
    
    if not HAS_UMAP:
        print("\n⚠️  UMAP not available. Install: pip install umap-learn")
        return None
    
    print(f"\n{'='*70}")
    print(f"UMAP (Uniform Manifold Approximation and Projection)")
    print(f"{'='*70}\n")
    
    # Fit UMAP
    umap_reducer = UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
    X_umap = umap_reducer.fit_transform(X)
    
    print(f"✅ UMAP embedding computed")
    print(f"   Input shape: {X.shape}")
    print(f"   Output shape: {X_umap.shape}")
    
    # Cluster the data
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Visualization
    fig, ax = plt.subplots(figsize=(12, 8))
    
    scatter = ax.scatter(X_umap[:, 0], X_umap[:, 1], c=labels, 
                        cmap='viridis', s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('UMAP Dimension 1', fontweight='bold')
    ax.set_ylabel('UMAP Dimension 2', fontweight='bold')
    ax.set_title(f'K-Means Clusters (UMAP Space)', fontweight='bold', fontsize=14)
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Cluster', fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('umap_analysis.png', dpi=150, bbox_inches='tight')
    print(f"✅ Visualization saved: umap_analysis.png\n")
    plt.close()
    
    return {
        'umap': umap_reducer,
        'X_umap': X_umap,
        'labels': labels
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
        scaler = StandardScaler()
        return scaler.fit_transform(X)

if __name__ == "__main__":
    # Load data
    X = load_test_data()
    print(f"\n📊 Data shape: {X.shape}")
    print(f"   Samples: {X.shape[0]}, Features: {X.shape[1]}")
    
    # PCA Analysis
    pca_results = pca_analysis(X, n_clusters=3)
    
    # UMAP Analysis
    if HAS_UMAP:
        umap_results = umap_analysis(X, n_clusters=3)
    else:
        print("\n⚠️  Skipping UMAP. Install with: pip install umap-learn")
    
    print(f"\n{'='*70}")
    print(f"DIMENSIONALITY REDUCTION SUMMARY")
    print(f"{'='*70}\n")
    
    print(f"✅ PCA captured {pca_results['cumsum_variance'][1]:.2%} of variance in 2 dimensions")
    print(f"✅ Both PCA and UMAP enable visual cluster interpretation")
    print(f"✅ Visualizations saved for presentation")
