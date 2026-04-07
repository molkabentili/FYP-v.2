"""Business logic layer for segmentation API."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.pipeline import DataPreprocessor
from src.clustering import SegmentationEngine


class SegmentationService:
    """High-level service for preprocessing and clustering operations."""
    
    def __init__(self, data_dir: str = "./api_data"):
        """Initialize service with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.preprocessor = DataPreprocessor()
        self.clustering_engine = SegmentationEngine()
    
    def preprocess_dataset(
        self,
        input_path: str,
        dataset_name: str = "dataset"
    ) -> Dict[str, Any]:
        """Preprocess a CSV dataset.
        
        Args:
            input_path: Path to input CSV
            dataset_name: Name for the dataset
            
        Returns:
            Dictionary with preprocessing results
        """
        try:
            # Load data
            df = pd.read_csv(input_path)
            original_shape = df.shape
            
            # Preprocess
            cleaned_df = self.preprocessor.build_cleaned_feature_frame(df)
            cleaned_shape = cleaned_df.shape
            
            # Save preprocessed data
            output_filename = f"preprocessed_{dataset_name.replace('.csv', '')}.csv"
            output_path = self.data_dir / output_filename
            cleaned_df.to_csv(output_path, index=False)
            
            # Get preprocessing info
            schema = self.preprocessor._analyze_schema(df)
            prep_info = self.preprocessor._prepare_features(df, schema)
            
            return {
                "success": True,
                "dataset_name": dataset_name,
                "original_shape": list(original_shape),
                "cleaned_shape": list(cleaned_shape),
                "features_used": prep_info["used_features"],
                "dropped_missing": prep_info["dropped_missing_columns"],
                "dropped_variance": prep_info["dropped_zero_variance_columns"],
                "output_file": str(output_path),
                "output_filename": output_filename,
                "message": f"Preprocessed {original_shape[0]} rows, kept {len(cleaned_df.columns)} numeric features"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Preprocessing failed: {str(e)}"
            }
    
    def run_clustering(
        self,
        preprocessed_path: str,
        algorithm: str = "kmeans",
        n_clusters: int = 3,
        linkage: str = "ward",
        eps: float = 0.5,
        min_samples: int = 5
    ) -> Dict[str, Any]:
        """Run clustering on preprocessed data.
        
        Args:
            preprocessed_path: Path to preprocessed CSV
            algorithm: 'kmeans', 'hierarchical', or 'dbscan'
            n_clusters: Number of clusters
            linkage: Hierarchical linkage criterion
            eps: DBSCAN epsilon
            min_samples: DBSCAN min samples
            
        Returns:
            Dictionary with clustering results
        """
        try:
            # Load preprocessed data
            df = pd.read_csv(preprocessed_path)
            
            # Run clustering
            if algorithm.lower() == "kmeans":
                result = self.clustering_engine.segment_with_kmeans(
                    df,
                    n_clusters=n_clusters
                )
                config = {"algorithm": "kmeans", "n_clusters": n_clusters}
            
            elif algorithm.lower() == "hierarchical":
                result = self.clustering_engine.segment_with_hierarchical(
                    df,
                    n_clusters=n_clusters,
                    linkage=linkage
                )
                config = {
                    "algorithm": "hierarchical",
                    "n_clusters": n_clusters,
                    "linkage": linkage
                }
            
            elif algorithm.lower() == "dbscan":
                result = self.clustering_engine.segment_with_dbscan(
                    df,
                    eps=eps,
                    min_samples=min_samples
                )
                config = {
                    "algorithm": "dbscan",
                    "eps": eps,
                    "min_samples": min_samples
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown algorithm: {algorithm}",
                    "message": f"Algorithm must be 'kmeans', 'hierarchical', or 'dbscan'"
                }
            
            # Get cluster statistics
            cluster_stats = self._compute_cluster_statistics(
                df,
                result['labels'],
                algorithm
            )
            
            # Save results
            output_filename = f"clustering_{algorithm}_{len(df)}.json"
            output_path = self.data_dir / output_filename
            
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Save segmented CSV
            csv_filename = f"segmented_{algorithm}_{len(df)}.csv"
            csv_path = self.data_dir / csv_filename
            df_with_clusters = df.copy()
            df_with_clusters['cluster'] = result['labels']
            df_with_clusters.to_csv(csv_path, index=False)
            
            return {
                "success": True,
                "algorithm": algorithm,
                "configuration": config,
                "n_clusters": result.get('n_clusters', n_clusters),
                "labels": result['labels'][:100],  # First 100 for preview
                "labels_full_count": len(result['labels']),
                "metrics": {
                    "silhouette_score": result['metrics'].get('silhouette'),
                    "davies_bouldin_score": result['metrics'].get('davies_bouldin'),
                    "calinski_harabasz_score": result['metrics'].get('calinski_harabasz')
                },
                "cluster_statistics": cluster_stats,
                "output_file": str(output_path),
                "segmented_csv": str(csv_path),
                "message": f"Clustering complete: {result.get('n_clusters', n_clusters)} clusters found"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Clustering failed: {str(e)}"
            }
    
    def compare_all_algorithms(
        self,
        preprocessed_path: str
    ) -> Dict[str, Any]:
        """Compare all 3 clustering algorithms.
        
        Args:
            preprocessed_path: Path to preprocessed CSV
            
        Returns:
            Dictionary with comparison results and ranking
        """
        try:
            df = pd.read_csv(preprocessed_path)
            comparisons = []
            
            # Test K-Means (k=3)
            kmeans_result = self.clustering_engine.segment_with_kmeans(df, n_clusters=3)
            comparisons.append({
                "algorithm": "K-Means",
                "configuration": {"n_clusters": 3},
                "silhouette_score": kmeans_result['metrics'].get('silhouette'),
                "davies_bouldin_score": kmeans_result['metrics'].get('davies_bouldin'),
                "n_clusters": 3
            })
            
            # Test Hierarchical (ward, k=3)
            hierarchical_result = self.clustering_engine.segment_with_hierarchical(
                df,
                n_clusters=3,
                linkage="ward"
            )
            comparisons.append({
                "algorithm": "Hierarchical",
                "configuration": {"linkage": "ward", "n_clusters": 3},
                "silhouette_score": hierarchical_result['metrics'].get('silhouette'),
                "davies_bouldin_score": hierarchical_result['metrics'].get('davies_bouldin'),
                "n_clusters": 3
            })
            
            # Test DBSCAN (eps=0.5)
            dbscan_result = self.clustering_engine.segment_with_dbscan(
                df,
                eps=0.5,
                min_samples=5
            )
            comparisons.append({
                "algorithm": "DBSCAN",
                "configuration": {"eps": 0.5, "min_samples": 5},
                "silhouette_score": dbscan_result['metrics'].get('silhouette'),
                "davies_bouldin_score": dbscan_result['metrics'].get('davies_bouldin'),
                "n_clusters": dbscan_result['n_clusters']
            })
            
            # Rank by silhouette score
            ranked = sorted(
                comparisons,
                key=lambda x: x['silhouette_score'] if x['silhouette_score'] else -1,
                reverse=True
            )
            
            # Add rank to results
            for rank, comp in enumerate(ranked, 1):
                comp['rank'] = rank
                comp['status'] = 'success'
            
            # Generate report text
            report = self._generate_comparison_report(ranked, df.shape)
            
            return {
                "success": True,
                "preprocessed_file": preprocessed_path,
                "data_shape": list(df.shape),
                "comparisons": ranked,
                "best_algorithm": ranked[0]['algorithm'],
                "best_score": ranked[0]['silhouette_score'],
                "detailed_report": report,
                "message": f"Compared 3 algorithms on {len(df)} samples"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Comparison failed: {str(e)}"
            }
    
    def _compute_cluster_statistics(
        self,
        data: pd.DataFrame,
        labels: List[int],
        algorithm: str
    ) -> List[Dict[str, Any]]:
        """Compute per-cluster statistics.
        
        Args:
            data: Feature dataframe
            labels: Cluster assignments
            algorithm: Algorithm name (for context)
            
        Returns:
            List of cluster statistics
        """
        stats = []
        labels_array = np.array(labels)
        unique_labels = sorted(set(labels))
        
        for cluster_id in unique_labels:
            if cluster_id == -1:  # Skip noise (DBSCAN)
                continue
            
            mask = labels_array == cluster_id
            cluster_size = int(mask.sum())
            percentage = 100 * cluster_size / len(labels_array)
            
            # Compute means for numeric columns
            cluster_data = data[mask]
            means = cluster_data.mean(axis=0).to_dict()
            
            # Round to 3 decimals
            means = {k: round(v, 3) for k, v in means.items()}
            
            stats.append({
                "cluster_id": int(cluster_id),
                "size": cluster_size,
                "percentage": round(percentage, 2),
                "mean_values": means
            })
        
        return stats
    
    def _generate_comparison_report(
        self,
        comparisons: List[Dict[str, Any]],
        data_shape: Tuple[int, int]
    ) -> str:
        """Generate human-readable comparison report.
        
        Args:
            comparisons: Ranked algorithm results
            data_shape: (n_samples, n_features)
            
        Returns:
            Report text
        """
        lines = [
            "ALGORITHM COMPARISON REPORT",
            "=" * 60,
            f"\nDataset: {data_shape[0]} samples × {data_shape[1]} features",
            f"\nRankings (by Silhouette Score):",
            "-" * 60
        ]
        
        for comp in comparisons:
            rank = comp['rank']
            algo = comp['algorithm']
            silhouette = comp['silhouette_score']
            davies = comp['davies_bouldin_score']
            n_clusters = comp['n_clusters']
            
            medal = ['🥇', '🥈', '🥉'][rank-1] if rank <= 3 else f"  #{rank}"
            silhouette_str = f"{silhouette:.4f}" if silhouette else "N/A"
            davies_str = f"{davies:.4f}" if davies else "N/A"
            
            lines.append(
                f"\n{medal} Rank {rank}: {algo}"
            )
            lines.append(f"   Clusters: {n_clusters}")
            lines.append(f"   Silhouette: {silhouette_str}")
            lines.append(f"   Davies-Bouldin: {davies_str}")
        
        lines.extend([
            "\n" + "=" * 60,
            f"Recommended: {comparisons[0]['algorithm']}",
            f"Score: {comparisons[0]['silhouette_score']:.4f}",
        ])
        
        return "\n".join(lines)
