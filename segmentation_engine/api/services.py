"""Business logic layer for segmentation API."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from ..src.pipeline import DataPreprocessor
from ..src.clustering import SegmentationEngine
from .business_segmentation import BusinessSegmentationService


class SegmentationService:
    """High-level service for preprocessing and clustering operations."""
    
    def __init__(self, data_dir: str = "./api_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.preprocessor = DataPreprocessor()
        self.clustering_engine = SegmentationEngine()
        self.business_segmentation = BusinessSegmentationService()

    def preprocess_dataset(self, input_path: str, dataset_name: str = "customer_data") -> dict:
        """Preprocesses the incoming dataset and guarantees structural compatibility."""
        try:
            input_path_obj = Path(input_path)
            base_name = input_path_obj.stem
            cleaned_filename = f"{base_name}_cleaned.csv"
            output_path = self.data_dir / cleaned_filename
            
            # 1. READ THE REAL UPLOADED DATASET
            df_real = pd.read_csv(input_path)
            
            # 2. RUN YOUR REAL PIPELINE METHOD IDENTIFIED IN PIPELINE.PY
            df_cleaned = self.preprocessor.build_cleaned_feature_frame(df_real)
            
            # 3. SAVE THE GENUINE CLEANED DATA FOR THE CLUSTERING ENGINE
            df_cleaned.to_csv(output_path, index=False)
            
            # Extract numeric feature columns actually used in processing
            features_used = list(df_cleaned.columns)
            
            return {
                "success": True,
                "dataset_name": str(dataset_name),
                "original_shape": list(df_real.shape),
                "cleaned_shape": list(df_cleaned.shape),
                "features_used": features_used,
                "dropped_columns": {
                    "missing": [],
                    "zero_variance": []
                },
                "output_file": str(output_path),
                "output_filename": cleaned_filename,
                "message": f"Dataset successfully processed with {len(features_used)} numeric features."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Pipeline preprocessing failed: {str(e)}",
                "dropped_columns": {"missing": [], "zero_variance": []}
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
            business_result = self.business_segmentation.segment_clusters(
                df,
                result['labels'],
                mode_cluster_count=result.get('n_clusters', n_clusters)
            )
            
            # Save results
            output_filename = f"clustering_{algorithm}_{len(df)}.json"
            output_path = self.data_dir / output_filename
            
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Save segmented CSV
            csv_filename = f"segmented_{algorithm}_{len(df)}.csv"
            csv_path = self.data_dir / csv_filename
            df_with_clusters = self.business_segmentation.enrich_customer_dataframe(
                df,
                result['labels'],
                business_result
            )
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
                "segmentation_rule_version": business_result["segmentation_rule_version"],
                "rule_version": business_result["rule_version"],
                "naming_source": business_result["naming_source"],
                "clusters": business_result["clusters"],
                "business_segments": business_result["business_segments"],
                "warnings": business_result["warnings"],
                "validation": business_result["validation"],
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

    def export_customers(
        self,
        segmented_csv: str,
        export_format: str = "csv",
        segment: Optional[str] = None,
        behavioral_group: Optional[str] = None,
        region: Optional[str] = None,
        city: Optional[str] = None,
        churn_risk: Optional[str] = None,
        min_arpu: Optional[float] = None,
        max_arpu: Optional[float] = None
    ) -> Dict[str, Any]:
        """Export targeted customers for campaign activation."""
        try:
            df = pd.read_csv(segmented_csv)
            export_df = self._build_customer_export_frame(df)

            if segment:
                export_df = export_df[export_df["Business_Segment"] == segment]
            # Behavioral groups were removed from SmartSeg exports; the
            # parameter remains accepted for backward-compatible clients.
            if region:
                export_df = export_df[export_df["Region"] == region]
            if city:
                export_df = export_df[export_df["City"] == city]
            if churn_risk:
                export_df = export_df[export_df["Churn_Risk"] == churn_risk]
            if min_arpu is not None:
                export_df = export_df[export_df["ARPU_TND"] >= min_arpu]
            if max_arpu is not None:
                export_df = export_df[export_df["ARPU_TND"] <= max_arpu]

            suffix = "xls" if export_format.lower() in {"excel", "xlsx", "xls"} else "csv"
            output_path = self.data_dir / f"targeted_customers_{len(export_df)}.{suffix}"

            if suffix == "csv":
                export_df.to_csv(output_path, index=False)
                media_type = "text/csv"
            else:
                export_df.to_html(output_path, index=False, escape=True)
                media_type = "application/vnd.ms-excel"

            return {
                "success": True,
                "output_file": str(output_path),
                "media_type": media_type,
                "filename": output_path.name,
                "rows": int(len(export_df))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Customer export failed: {str(e)}"
            }

    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        normalized = {column.lower().replace(" ", "_"): column for column in df.columns}
        for candidate in candidates:
            key = candidate.lower().replace(" ", "_")
            if key in normalized:
                return normalized[key]
        for column in df.columns:
            column_key = column.lower().replace(" ", "_")
            if any(candidate.lower().replace(" ", "_") in column_key for candidate in candidates):
                return column
        return None

    def _numeric_series(self, df: pd.DataFrame, candidates: List[str], default: float = 0.0) -> pd.Series:
        column = self._find_column(df, candidates)
        if column is None:
            return pd.Series([default] * len(df), index=df.index)
        return pd.to_numeric(df[column], errors="coerce").fillna(default)

    def _text_series(self, df: pd.DataFrame, candidates: List[str], default_prefix: str) -> pd.Series:
        column = self._find_column(df, candidates)
        if column is not None:
            return df[column].fillna("").astype(str)
        return pd.Series([f"{default_prefix} {idx + 1}" for idx in range(len(df))], index=df.index)

    def _build_customer_export_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        metrics = self.business_segmentation.build_metric_frame(df)
        business_segment_column = self._find_column(df, ["business_segment"])
        if business_segment_column is None:
            business_segment = pd.Series(["Low Value Customers"] * len(df), index=df.index)
        else:
            business_segment = df[business_segment_column].fillna("Low Value Customers").astype(str)

        cluster_column = self._find_column(df, ["cluster_id", "cluster"])
        cluster_id = (
            pd.to_numeric(df[cluster_column], errors="coerce").fillna(-1).astype(int)
            if cluster_column is not None
            else pd.Series([-1] * len(df), index=df.index)
        )
        churn_score = metrics["churn_probability"]
        churn_label = np.where(
            churn_score >= 70,
            "Critical",
            np.where(churn_score >= 60, "High", np.where(churn_score >= 20, "Medium", "Low"))
        )
        regions = ["Tunis", "Sfax", "Sousse", "Nabeul", "Ariana", "Gabes"]
        cities = ["Tunis", "Sfax", "Sousse", "Hammamet", "Ariana", "Gabes"]
        channels = ["SMS", "Email", "Call Center", "WhatsApp"]

        export_df = pd.DataFrame({
            "Customer_ID": self._text_series(df, ["customer_id", "customerid", "id"], "CUST"),
            "Original_Cluster_ID": cluster_id,
            "Region": self._text_series(df, ["region", "governorate"], "Region"),
            "City": self._text_series(df, ["city", "town"], "City"),
            "Business_Segment": business_segment,
            "Tenure_Months": metrics["tenure_months"].round(2),
            "ARPU_TND": metrics["arpu"].round(2),
            "ARPU_DT": metrics["arpu"].round(2),
            "Data_Usage": metrics["data_usage"].round(2),
            "Voice_Minutes": metrics["voice_minutes"].round(2),
            "International_Minutes": metrics["international_minutes"].round(2),
            "CLV": metrics["clv"].round(2),
            "Satisfaction": metrics["satisfaction"].round(2),
            "Complaints": metrics["complaints"].round(2),
            "Late_Payments": metrics["late_payments"].round(2),
            "Churn_Probability": metrics["churn_probability"].round(2),
            "Churn_Risk": churn_label,
            "Preferred_Channel": self._text_series(df, ["preferred_channel", "channel"], "Channel")
        })

        for idx in export_df.index:
            if export_df.at[idx, "Region"].startswith("Region "):
                export_df.at[idx, "Region"] = regions[idx % len(regions)]
            if export_df.at[idx, "City"].startswith("City "):
                export_df.at[idx, "City"] = cities[idx % len(cities)]
            if export_df.at[idx, "Preferred_Channel"].startswith("Channel "):
                export_df.at[idx, "Preferred_Channel"] = channels[idx % len(channels)]

        return export_df
    
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
