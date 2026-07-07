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
        """Compute distinct per-cluster statistics using real customer metrics."""
        if self.feature_data is None:
            return {}
        
        label_array = np.array(labels)
        unique_labels = sorted(set(labels))
        
        stats = {
            'cluster_sizes': {},
            'cluster_means': {},
            'cluster_stds': {},
            'profiles': {}
        }
        
        # Create a copy and attach labels to guarantee correct alignment
        df_analysis = self.feature_data.copy()
        df_analysis['current_cluster_assignment'] = label_array
        
        # Dynamically map standard telecom metrics (case-insensitive)
        cols = df_analysis.columns
        arpu_col = next((c for c in cols if 'arpu' in c.lower() or 'revenue' in c.lower() or 'total' in c.lower()), None)
        data_col = next((c for c in cols if 'data' in c.lower() or 'gb' in c.lower() or 'volume' in c.lower()), None)
        voice_col = next((c for c in cols if 'voice' in c.lower() or 'min' in c.lower() or 'call' in c.lower()), None)
        tenure_col = next((c for c in cols if 'tenure' in c.lower() or 'month' in c.lower() or 'age' in c.lower()), None)
        churn_col = next((c for c in cols if 'churn' in c.lower() or 'risk' in c.lower()), None)
        
        computed_profiles = []
        
        for cluster_id in unique_labels:
            if cluster_id == -1:  # Ignore DBSCAN noise for primary profiling
                continue
                
            # Strictly slice data belonging ONLY to this specific cluster
            cluster_df = df_analysis[df_analysis['current_cluster_assignment'] == cluster_id]
            drop_cols = ['current_cluster_assignment']
            cluster_numeric = cluster_df.drop(columns=[c for c in drop_cols if c in cluster_df.columns])
            
            means = cluster_numeric.mean(axis=0).to_dict()
            stds = cluster_numeric.std(axis=0).to_dict()
            
            stats['cluster_sizes'][str(cluster_id)] = int(len(cluster_df))
            stats['cluster_means'][str(cluster_id)] = list(means.values())
            stats['cluster_stds'][str(cluster_id)] = list(stds.values())
            
            computed_profiles.append({
                'id': str(cluster_id),
                'size': int(len(cluster_df)),
                'arpu': means.get(arpu_col, 0.0) if arpu_col else 0.0,
                'data': means.get(data_col, 0.0) if data_col else 0.0,
                'voice': means.get(voice_col, 0.0) if voice_col else 0.0,
                'tenure': means.get(tenure_col, 0.0) if tenure_col else 0.0,
                'churn_val': means.get(churn_col, 0.0) if churn_col else 0.0
            })
            
        # Raw clustering metadata only. Business names are assigned centrally in
        # segmentation_engine/api/business_segmentation.py after clustering.
        if computed_profiles:
            # Sort to find the actual structural boundaries of your dataset
            highest_arpu_profile = max(computed_profiles, key=lambda x: x['arpu'])
            highest_data_profile = max(computed_profiles, key=lambda x: x['data'])
            lowest_arpu_profile = min(computed_profiles, key=lambda x: x['arpu'])
            
            for p in computed_profiles:
                cid = p['id']
                name = f"Raw Cluster {cid}"
                strategy = "Use backend business_segments for campaign strategy."
                
                # Rule matrix based on maximum relative metrics
                if False and cid == highest_arpu_profile['id'] and cid == highest_data_profile['id']:
                    name = "👑 Premium Data Elite"
                    strategy = "Introduce premium 5G home streaming bundles and priority customer support lines."
                elif False and cid == highest_arpu_profile['id']:
                    name = "💼 High-Value Professionals"
                    strategy = "Target with value-added corporate roaming packages and postpaid device upgrades."
                elif False and cid == highest_data_profile['id']:
                    name = "📱 Digital Enthusiasts"
                    strategy = "Promote heavy gaming passes, off-peak night bundles, and social media add-ons."
                elif False and cid == lowest_arpu_profile['id']:
                    name = "📉 Budget-Conscious Savers"
                    strategy = "Offer low-cost micro-recharges or targeted voice-only options to drive base migration."
                elif False:
                    name = f"🔄 Standard Core (Segment {cid})"
                    strategy = "Run standard loyalty campaigns and lifestyle balance rewards to secure tenure."
                
                # Churn Risk category definition
                risk_level = "High Risk 🚨" if p['churn_val'] > 0.6 or (p['churn_val'] > 0.3 and p['tenure'] < 6) else ("Medium" if p['churn_val'] > 0.15 else "Low Stability ✅")
                
                stats['profiles'][cid] = {
                    "name": name,
                    "market_share_pct": round((p['size'] / len(labels)) * 100, 1),
                    "customer_count": p['size'],
                    "hero_metrics": {
                        "ARPU": f"{p['arpu']:.2f} TND",
                        "Data Usage": f"{p['data']:.2f} GB/mo",
                        "Voice Traffic": f"{p['voice']:.1f} min/mo",
                        "Account Tenure": f"{p['tenure']:.1f} months"
                    },
                    "risk_assessment": risk_level,
                    "business_strategy": strategy
                }

        if -1 in unique_labels:
            stats['noise_points'] = int((label_array == -1).sum())
            
        return stats
    
    def get_all_results(self) -> dict[str, Any]:
        """Return all segmentation results from all algorithms.
        
        Returns:
            Dictionary with kmeans, hierarchical, dbscan results
        """
        return self.results.copy()
