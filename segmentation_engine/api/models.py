"""Pydantic models for API request/response validation."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST MODELS
# ============================================================================

class PreprocessRequest(BaseModel):
    """Request to preprocess a dataset."""
    filename: str = Field(..., description="Name of the uploaded CSV file")
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "customer_data.csv"
            }
        }


class ClusteringRequest(BaseModel):
    """Request to run clustering on preprocessed data."""
    algorithm: str = Field(
        ...,
        description="Clustering algorithm: 'kmeans', 'hierarchical', or 'dbscan'"
    )
    preprocessed_file: str = Field(
        ...,
        description="Path to preprocessed CSV file"
    )
    n_clusters: Optional[int] = Field(
        default=3,
        description="Number of clusters for k-means/hierarchical (default: 3)"
    )
    linkage: Optional[str] = Field(
        default="ward",
        description="Linkage criterion for hierarchical: 'ward', 'complete', 'average', 'single'"
    )
    eps: Optional[float] = Field(
        default=0.5,
        description="Epsilon parameter for DBSCAN (default: 0.5)"
    )
    min_samples: Optional[int] = Field(
        default=5,
        description="Min samples for DBSCAN (default: 5)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "algorithm": "kmeans",
                "preprocessed_file": "preprocessed_data.csv",
                "n_clusters": 3
            }
        }


class CompareAlgorithmsRequest(BaseModel):
    """Request to compare all clustering algorithms."""
    preprocessed_file: str = Field(
        ...,
        description="Path to preprocessed CSV file"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "preprocessed_file": "preprocessed_data.csv"
            }
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PreprocessResponse(BaseModel):
    """Response from preprocessing."""
    success: bool
    dataset_name: str
    original_shape: List[int]
    cleaned_shape: List[int]
    features_used: List[str]
    dropped_columns: Dict[str, List[str]]
    output_file: str
    message: str


class ClusterMetrics(BaseModel):
    """Clustering quality metrics."""
    silhouette_score: Optional[float]
    davies_bouldin_score: Optional[float]
    calinski_harabasz_score: Optional[float]


class ClusterStatistics(BaseModel):
    """Per-cluster statistics."""
    cluster_id: int
    size: int
    percentage: float
    mean_values: Dict[str, float]


class ClusteringResponse(BaseModel):
    """Response from clustering."""
    success: bool
    algorithm: str
    configuration: Dict[str, Any]
    n_clusters: int
    labels: List[int]
    metrics: ClusterMetrics
    cluster_statistics: List[ClusterStatistics]
    output_file: str
    segmented_csv: str
    message: str


class AlgorithmComparison(BaseModel):
    """Comparison of a single algorithm result."""
    algorithm: str
    configuration: Dict[str, Any]
    silhouette_score: Optional[float]
    davies_bouldin_score: Optional[float]
    n_clusters: int
    rank: int
    status: str


class CompareAlgorithmsResponse(BaseModel):
    """Response from comparing all algorithms."""
    success: bool
    preprocessed_file: str
    data_shape: List[int]
    comparisons: List[AlgorithmComparison]
    best_algorithm: str
    best_score: float
    detailed_report: str


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    modules: Dict[str, bool]
    message: str
