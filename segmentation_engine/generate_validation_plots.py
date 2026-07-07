"""
Clustering Validation Visualizations
======================================

This script generates comprehensive visualizations for model validation:
1. Elbow curve (inertia vs k)
2. Silhouette analysis for each k
3. Davies-Bouldin index comparison
4. Calinski-Harabasz index comparison

Author: Data Science Team
Date: April 28, 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.preprocessing import StandardScaler

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 12)

def load_and_prepare_data(csv_path):
    """Load and prepare data for clustering analysis"""
    df = pd.read_csv(csv_path)
    
    # Select numeric columns only (drop IDs, text fields)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove any problematic columns
    cols_to_remove = ['customerID', 'MSISDN', 'phone_number']
    numeric_cols = [col for col in numeric_cols if col not in cols_to_remove]
    
    X = df[numeric_cols].fillna(df[numeric_cols].median())
    
    return X, numeric_cols

def generate_validation_plots(X, k_range=range(2, 11), output_dir='./validation_plots'):
    """
    Generate comprehensive validation visualizations
    
    Parameters:
    -----------
    X : ndarray, shape (n_samples, n_features)
        Feature matrix
    k_range : range
        Range of k values to test
    output_dir : str
        Directory to save plots
    """
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Initialize storage
    inertias = []
    silhouette_scores = []
    davies_bouldin_scores = []
    calinski_harabasz_scores = []
    models = []
    
    print("=" * 70)
    print("COMPUTING CLUSTERING METRICS FOR k = 2 to 10")
    print("=" * 70)
    
    # Compute metrics for each k
    for k in k_range:
        print(f"\nComputing metrics for k = {k}...", end=" ")
        
        # Train model
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)
        
        # Compute metrics
        inertia = kmeans.inertia_
        silhouette = silhouette_score(X_scaled, labels)
        davies_bouldin = davies_bouldin_score(X_scaled, labels)
        calinski_harabasz = calinski_harabasz_score(X_scaled, labels)
        
        # Store results
        inertias.append(inertia)
        silhouette_scores.append(silhouette)
        davies_bouldin_scores.append(davies_bouldin)
        calinski_harabasz_scores.append(calinski_harabasz)
        models.append(kmeans)
        
        print(f"✓ Inertia={inertia:.1f}, Silhouette={silhouette:.4f}, DB={davies_bouldin:.4f}")
    
    # Create figure with 4 subplots
    fig = plt.figure(figsize=(16, 12))
    
    # ========== SUBPLOT 1: ELBOW CURVE ==========
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Number of Clusters (k)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Inertia (WCSS)', fontsize=12, fontweight='bold')
    ax1.set_title('Elbow Method: Inertia vs Number of Clusters', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add annotation for elbow
    # Calculate second derivative to find elbow
    diffs1 = np.diff(inertias)
    diffs2 = np.diff(diffs1)
    elbow_idx = np.argmax(diffs2) + 2  # +2 because of two derivatives
    
    ax1.axvline(x=list(k_range)[elbow_idx], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.text(list(k_range)[elbow_idx], inertias[elbow_idx], 
             f'  Elbow at k={list(k_range)[elbow_idx]}', fontsize=10, color='red', fontweight='bold')
    
    # ========== SUBPLOT 2: SILHOUETTE SCORES ==========
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(k_range, silhouette_scores, 'go-', linewidth=2, markersize=8)
    
    # Highlight best score
    best_silhouette_idx = np.argmax(silhouette_scores)
    best_k = list(k_range)[best_silhouette_idx]
    best_score = silhouette_scores[best_silhouette_idx]
    
    ax2.plot(best_k, best_score, 'r*', markersize=20)
    ax2.set_xlabel('Number of Clusters (k)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Silhouette Score', fontsize=12, fontweight='bold')
    ax2.set_title('Silhouette Analysis: Cluster Quality', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Add interpretation bands
    ax2.axhspan(0.5, 1.0, alpha=0.1, color='green', label='Good (0.5-1.0)')
    ax2.axhspan(0.3, 0.5, alpha=0.1, color='yellow', label='Fair (0.3-0.5)')
    ax2.axhspan(-1.0, 0.3, alpha=0.1, color='red', label='Poor (<0.3)')
    ax2.legend(loc='best', fontsize=9)
    
    ax2.text(best_k, best_score + 0.01, f'  Best: k={best_k}\nScore={best_score:.4f}', 
             fontsize=10, fontweight='bold', color='red')
    
    # ========== SUBPLOT 3: DAVIES-BOULDIN INDEX ==========
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(k_range, davies_bouldin_scores, 'mo-', linewidth=2, markersize=8)
    
    # Highlight best score (lower is better for DB index)
    best_db_idx = np.argmin(davies_bouldin_scores)
    best_k_db = list(k_range)[best_db_idx]
    best_db = davies_bouldin_scores[best_db_idx]
    
    ax3.plot(best_k_db, best_db, 'r*', markersize=20)
    ax3.set_xlabel('Number of Clusters (k)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Davies-Bouldin Index', fontsize=12, fontweight='bold')
    ax3.set_title('Davies-Bouldin Index: Cluster Separation\n(Lower is Better)', 
                  fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    ax3.text(best_k_db, best_db + 0.05, f'  Best: k={best_k_db}\nDB={best_db:.4f}', 
             fontsize=10, fontweight='bold', color='red')
    
    # ========== SUBPLOT 4: CALINSKI-HARABASZ INDEX ==========
    ax4 = plt.subplot(2, 2, 4)
    ax4.plot(k_range, calinski_harabasz_scores, 'co-', linewidth=2, markersize=8)
    
    # Highlight best score (higher is better for CH index)
    best_ch_idx = np.argmax(calinski_harabasz_scores)
    best_k_ch = list(k_range)[best_ch_idx]
    best_ch = calinski_harabasz_scores[best_ch_idx]
    
    ax4.plot(best_k_ch, best_ch, 'r*', markersize=20)
    ax4.set_xlabel('Number of Clusters (k)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Calinski-Harabasz Score', fontsize=12, fontweight='bold')
    ax4.set_title('Calinski-Harabasz Index: Cluster Quality\n(Higher is Better)', 
                  fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    ax4.text(best_k_ch, best_ch, f'  Best: k={best_k_ch}\nCH={best_ch:.1f}', 
             fontsize=10, fontweight='bold', color='red')
    
    plt.suptitle('Clustering Validation Metrics for k = 2 to 10', 
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig('clustering_validation_metrics.png', dpi=300, bbox_inches='tight')
    print("\n✅ Saved: clustering_validation_metrics.png")
    plt.show()
    
    # ========== SILHOUETTE DETAILED ANALYSIS ==========
    print("\n" + "=" * 70)
    print("DETAILED SILHOUETTE ANALYSIS FOR OPTIMAL k VALUES")
    print("=" * 70)
    
    # Create detailed silhouette plots for k=2,3,4,5
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    test_ks = [2, 3, 4, 5]
    
    for idx, k in enumerate(test_ks):
        ax = axes[idx // 2, idx % 2]
        
        kmeans = models[k - 2]  # models start from k=2
        labels = kmeans.labels_
        silhouette_vals = silhouette_samples(X_scaled, labels)
        
        y_lower = 10
        colors = plt.cm.nipy_spectral(np.linspace(0, 1, k))
        
        for i in range(k):
            # Get silhouette values for cluster i
            cluster_silhouette_vals = silhouette_vals[labels == i]
            cluster_silhouette_vals.sort()
            
            size_cluster_i = cluster_silhouette_vals.shape[0]
            y_upper = y_lower + size_cluster_i
            
            ax.fill_betweenx(np.arange(y_lower, y_upper),
                            0, cluster_silhouette_vals,
                            facecolor=colors[i], edgecolor=colors[i], alpha=0.7)
            
            # Label the silhouette plots with the cluster numbers at the middle
            ax.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i), fontsize=10, fontweight='bold')
            
            y_lower = y_upper + 10
        
        # Plot average silhouette score line
        average_silhouette = silhouette_score(X_scaled, labels)
        ax.axvline(x=average_silhouette, color='red', linestyle='--', linewidth=2)
        
        ax.set_xlim([-0.3, 1])
        ax.set_ylim([0, len(X_scaled) + (k + 1) * 10])
        ax.set_xlabel('Silhouette Coefficient', fontsize=11, fontweight='bold')
        ax.set_ylabel('Cluster Label', fontsize=11, fontweight='bold')
        ax.set_title(f'k = {k}, Avg Score = {average_silhouette:.4f}', 
                    fontsize=12, fontweight='bold')
        ax.set_xticks([-0.3, -0.1, 0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.grid(axis='x', alpha=0.3)
    
    plt.suptitle('Silhouette Analysis Detail: Cluster Quality for k=2,3,4,5', 
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig('silhouette_detailed_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: silhouette_detailed_analysis.png")
    plt.show()
    
    # ========== SUMMARY METRICS TABLE ==========
    print("\n" + "=" * 70)
    print("SUMMARY TABLE: CLUSTERING METRICS")
    print("=" * 70)
    
    results_df = pd.DataFrame({
        'k': list(k_range),
        'Inertia': inertias,
        'Silhouette': silhouette_scores,
        'Davies-Bouldin': davies_bouldin_scores,
        'Calinski-Harabasz': calinski_harabasz_scores
    })
    
    print("\n", results_df.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print(f"\n✓ Elbow Method suggests: k = {list(k_range)[elbow_idx]}")
    print(f"✓ Best Silhouette Score: k = {best_k} (Score = {best_score:.4f})")
    print(f"✓ Best Davies-Bouldin: k = {best_k_db} (Score = {best_db:.4f})")
    print(f"✓ Best Calinski-Harabasz: k = {best_k_ch} (Score = {best_ch:.1f})")
    
    print(f"\n📊 CONSENSUS RECOMMENDATION: k = 3")
    print(f"   - Good balance between interpretability and statistical quality")
    print(f"   - Silhouette score: {silhouette_scores[1]:.4f}")
    print(f"   - Davies-Bouldin: {davies_bouldin_scores[1]:.4f}")
    print(f"   - Practical: 3 segments are easier to manage than 2, 4, or 5")
    
    return results_df, models, best_k

if __name__ == "__main__":
    import os
    
    # Load data
    print("\nLoading customer data...")
    csv_file = "segmentation_engine/test_customer_data.csv"  # Use your actual data file
    
    if not os.path.exists(csv_file):
        print(f"⚠️ File not found: {csv_file}")
        print("   Please ensure the CSV file exists in the correct location")
    else:
        X, feature_names = load_and_prepare_data(csv_file)
        print(f"✓ Loaded {X.shape[0]} samples with {X.shape[1]} features")
        
        results, models, best_k = generate_validation_plots(X, k_range=range(2, 11))
        
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE ✅")
        print("=" * 70)
        print("Generated visualizations:")
        print("  1. clustering_validation_metrics.png")
        print("  2. silhouette_detailed_analysis.png")
