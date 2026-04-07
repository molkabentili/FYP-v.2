"""Sprint 3: Customer Segmentation using Clustering Algorithms.

This module implements multiple clustering approaches:
- K-Means: Fast, scalable partitioning
- Hierarchical: Dendrograms, multiple linkage methods
- DBSCAN: Density-based, discovers arbitrary cluster shapes

All algorithms operate on preprocessed numeric features from Sprint 2.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.preprocessing import StandardScaler


class SegmentationEngine:
    """Multi-algorithm customer segmentation engine.
    
    Provides flexible clustering with evaluation metrics and cluster analysis.
    """
    
    def __init__(self):
        self.kmeans_model = None
        self.hierarchical_model = None
        self.dbscan_model = None
        self.feature_data = None
        self.scaler = StandardScaler()
        self.results = {}
    
    def segment_with_kmeans(
        self,
        data: pd.DataFrame,
        n_clusters: int = 3,
        random_state: int = 42,
        n_init: int = 10
    ) -> dict[str, Any]:
        """K-Means Clustering: Fast partitioning into k clusters.
        
        Args:
            data: Numeric features (n_samples, n_features)
            n_clusters: Number of clusters to create
            random_state: Reproducibility seed
            n_init: Number of initializations
            
        Returns:
            Dictionary with labels, metrics, and model info
        """
        self.feature_data = data.copy()
        data_scaled = self.scaler.fit_transform(data)
        
        self.kmeans_model = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=n_init,
            verbose=0
        )
        labels = self.kmeans_model.fit_predict(data_scaled)
        
        metrics = self._compute_metrics(data_scaled, labels, "K-Means")
        
        self.results['kmeans'] = {
            'algorithm': 'K-Means',
            'n_clusters': n_clusters,
            'labels': labels.tolist(),
            'inertia': float(self.kmeans_model.inertia_),
            'centroids': self.kmeans_model.cluster_centers_.tolist(),
            'metrics': metrics
        }
        
        return self.results['kmeans']
    
    def segment_with_hierarchical(
        self,
        data: pd.DataFrame,
        n_clusters: int = 3,
        linkage: str = 'ward'
    ) -> dict[str, Any]:
        """Hierarchical Clustering: Bottom-up agglomerative clustering.
        
        Args:
            data: Numeric features
            n_clusters: Number of clusters to create
            linkage: Linkage criterion ('ward', 'complete', 'average', 'single')
            
        Returns:
            Dictionary with labels, metrics, and dendrogram info
        """
        self.feature_data = data.copy()
        data_scaled = self.scaler.fit_transform(data)
        
        self.hierarchical_model = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage=linkage
        )
        labels = self.hierarchical_model.fit_predict(data_scaled)
        
        metrics = self._compute_metrics(data_scaled, labels, "Hierarchical")
        
        self.results['hierarchical'] = {
            'algorithm': 'Hierarchical',
            'linkage': linkage,
            'n_clusters': n_clusters,
            'labels': labels.tolist(),
            'metrics': metrics,
            'n_leaves': self.hierarchical_model.n_leaves_,
            'distance_threshold': None
        }
        
        return self.results['hierarchical']
    
    def segment_with_dbscan(
        self,
        data: pd.DataFrame,
        eps: float = 0.5,
        min_samples: int = 5
    ) -> dict[str, Any]:
        """DBSCAN: Density-based spatial clustering.
        
        Discovers clusters of arbitrary shape without specifying n_clusters.
        Points not in any cluster are labeled as noise (-1).
        
        Args:
            data: Numeric features
            eps: Maximum distance between points in a cluster
            min_samples: Minimum points to form a dense region
            
        Returns:
            Dictionary with labels, metrics, and cluster info
        """
        self.feature_data = data.copy()
        data_scaled = self.scaler.fit_transform(data)
        
        self.dbscan_model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = self.dbscan_model.fit_predict(data_scaled)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        # Silhouette score only valid if n_clusters > 1 and not all noise
        if n_clusters > 1 and n_noise < len(labels):
            metrics = self._compute_metrics(data_scaled, labels, "DBSCAN")
        else:
            metrics = {
                'silhouette': None,
                'davies_bouldin': None,
                'calinski_harabasz': None,
                'notes': 'Insufficient clusters for standard metrics'
            }
        
        self.results['dbscan'] = {
            'algorithm': 'DBSCAN',
            'eps': eps,
            'min_samples': min_samples,
            'labels': labels.tolist(),
            'n_clusters': n_clusters,
            'n_noise_points': n_noise,
            'metrics': metrics
        }
        
        return self.results['dbscan']
    
    def _compute_metrics(
        self,
        data: np.ndarray,
        labels: np.ndarray,
        algorithm_name: str
    ) -> dict[str, float | None]:
        """Compute clustering quality metrics.
        
        Args:
            data: Scaled feature matrix
            labels: Cluster assignments per sample
            algorithm_name: For logging
            
        Returns:
            Dictionary with quality metrics
        """
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        metrics = {}
        
        # Silhouette Score: -1 to 1, higher is better
        if n_clusters > 1:
            try:
                metrics['silhouette'] = float(silhouette_score(data, labels))
            except:
                metrics['silhouette'] = None
        else:
            metrics['silhouette'] = None
        
        # Davies-Bouldin Index: lower is better
        if n_clusters > 1:
            try:
                metrics['davies_bouldin'] = float(davies_bouldin_score(data, labels))
            except:
                metrics['davies_bouldin'] = None
        else:
            metrics['davies_bouldin'] = None
        
        # Calinski-Harabasz Index: higher is better
        if n_clusters > 1:
            try:
                metrics['calinski_harabasz'] = float(calinski_harabasz_score(data, labels))
            except:
                metrics['calinski_harabasz'] = None
        else:
            metrics['calinski_harabasz'] = None
        
        return metrics
    
    def get_cluster_statistics(self, labels: list[int]) -> dict[str, Any]:
        """Compute per-cluster statistics.
        
        Args:
            labels: Cluster assignments
            
        Returns:
            Dictionary with cluster size distribution and center info
        """
        if self.feature_data is None:
            return {}
        
        label_array = np.array(labels)
        unique_labels = set(labels)
        
        stats = {
            'cluster_sizes': {},
            'cluster_means': {},
            'cluster_stds': {}
        }
        
        for cluster_id in sorted(unique_labels):
            if cluster_id == -1:  # Noise in DBSCAN
                continue
            
            mask = label_array == cluster_id
            cluster_data = self.feature_data[mask]
            
            stats['cluster_sizes'][str(cluster_id)] = int(mask.sum())
            stats['cluster_means'][str(cluster_id)] = cluster_data.mean(axis=0).tolist()
            stats['cluster_stds'][str(cluster_id)] = cluster_data.std(axis=0).tolist()
        
        if -1 in unique_labels:
            stats['noise_points'] = int((label_array == -1).sum())
        
        return stats
    
    def get_all_results(self) -> dict[str, Any]:
        """Return all segmentation results from all algorithms.
        
        Returns:
            Dictionary with kmeans, hierarchical, dbscan results
        """
        return self.results.copy()
