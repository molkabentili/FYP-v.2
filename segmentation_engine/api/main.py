#!/usr/bin/env python3
"""FastAPI backend for customer segmentation.

Endpoints:
  POST   /api/preprocess        - Preprocess a CSV dataset
  POST   /api/cluster           - Run clustering algorithm
  POST   /api/compare           - Compare all algorithms
  GET    /api/health            - Health check
  GET    /                       - Root endpoint with documentation
"""

from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import tempfile
from pathlib import Path

from api.models import (
    PreprocessRequest, PreprocessResponse,
    ClusteringRequest, ClusteringResponse,
    CompareAlgorithmsRequest, CompareAlgorithmsResponse,
    HealthCheckResponse, ErrorResponse
)
from api.services import SegmentationService

# Initialize FastAPI app
app = FastAPI(
    title="SmartSeg Segmentation API",
    description="Customer segmentation API with K-Means, Hierarchical, and DBSCAN clustering",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
service = SegmentationService(data_dir="./api_data")


# ============================================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation."""
    return """
    <html>
        <head>
            <title>SmartSeg Segmentation API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1000px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 { color: #333; }
                h2 { color: #666; margin-top: 30px; }
                .endpoint {
                    background: #f9f9f9;
                    padding: 15px;
                    border-left: 4px solid #007bff;
                    margin: 10px 0;
                    border-radius: 4px;
                }
                .method { font-weight: bold; color: #007bff; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .links {
                    margin: 20px 0;
                    padding: 15px;
                    background: #e7f3ff;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 SmartSeg Segmentation API</h1>
                <p>Customer segmentation with machine learning clustering algorithms</p>
                
                <div class="links">
                    <strong>Quick Links:</strong><br>
                    <a href="/docs">📚 Interactive API Docs (Swagger)</a><br>
                    <a href="/redoc">📖 Alternative Docs (ReDoc)</a><br>
                    <a href="/openapi.json">⚙️ OpenAPI Schema</a>
                </div>
                
                <h2>Available Endpoints</h2>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <code>/api/preprocess</code></div>
                    <p>Preprocess a CSV dataset (Remove missing values, normalize numeric features)</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <code>/api/cluster</code></div>
                    <p>Run clustering with K-Means, Hierarchical, or DBSCAN</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <code>/api/compare</code></div>
                    <p>Compare all 3 algorithms automatically</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <code>/api/health</code></div>
                    <p>Health check and system status</p>
                </div>
                
                <h2>Quick Start</h2>
                <ol>
                    <li>Upload CSV via <code>POST /api/preprocess</code></li>
                    <li>Use returned filename in <code>POST /api/cluster</code> or <code>POST /api/compare</code></li>
                    <li>Get cluster assignments and metrics</li>
                </ol>
                
                <h2>Supported Algorithms</h2>
                <ul>
                    <li><strong>K-Means:</strong> Fast, scalable, k centroids (2-5 clusters typical)</li>
                    <li><strong>Hierarchical:</strong> Dendrograms, 4 linkage methods (ward, complete, average, single)</li>
                    <li><strong>DBSCAN:</strong> Density-based, finds arbitrary shapes, no k needed</li>
                </ul>
                
                <h2>API Version</h2>
                <p>SmartSeg API v3.0.0 - Sprint 3 Backend</p>
            </div>
        </body>
    </html>
    """


@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify service status."""
    try:
        from src.pipeline import DataPreprocessor
        from src.clustering import SegmentationEngine
        
        return {
            "status": "healthy",
            "version": "3.0.0",
            "modules": {
                "fastapi": True,
                "preprocessing": True,
                "clustering": True,
                "api_service": True
            },
            "message": "All systems operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "version": "3.0.0",
            "modules": {"error": False},
            "message": str(e)
        }


# ============================================================================
# PREPROCESSING ENDPOINTS
# ============================================================================

@app.post("/api/preprocess", response_model=PreprocessResponse)
async def preprocess(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = Form(default="customer_data")
):
    """Preprocess a CSV dataset.
    
    - Detects numeric vs categorical columns
    - Handles missing values (imputation)
    - Applies StandardScaler normalization
    - Returns file path for downstream clustering
    
    Args:
        file: CSV file to preprocess
        dataset_name: Name for the dataset
        
    Returns:
        Preprocessing results with file path
    """
    try:
        # Save uploaded file to temporary location
        temp_dir = Path("./api_data")
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / file.filename
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Preprocess via service
        result = service.preprocess_dataset(
            input_path=str(temp_path),
            dataset_name=dataset_name
        )
        
        if result.get("success"):
            return PreprocessResponse(**result)
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("message")
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Preprocessing failed: {str(e)}"
        )


# ============================================================================
# CLUSTERING ENDPOINTS
# ============================================================================

@app.post("/api/cluster", response_model=ClusteringResponse)
async def run_clustering(request: ClusteringRequest):
    """Run clustering on preprocessed data.
    
    Supports 3 algorithms:
    - K-Means: Partitions into k clusters
    - Hierarchical: Agglomerative with multiple linkages
    - DBSCAN: Density-based discovery
    
    Args:
        request: Clustering configuration
        
    Returns:
        Cluster assignments, metrics, and statistics
    """
    try:
        # Validate algorithm
        if request.algorithm.lower() not in ["kmeans", "hierarchical", "dbscan"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown algorithm: {request.algorithm}"
            )
        
        # Run clustering
        result = service.run_clustering(
            preprocessed_path=request.preprocessed_file,
            algorithm=request.algorithm,
            n_clusters=request.n_clusters,
            linkage=request.linkage,
            eps=request.eps,
            min_samples=request.min_samples
        )
        
        if result.get("success"):
            # Convert to response format
            response_data = {
                "success": True,
                "algorithm": result["algorithm"],
                "configuration": result["configuration"],
                "n_clusters": result["n_clusters"],
                "labels": result["labels"],
                "metrics": result["metrics"],
                "cluster_statistics": result["cluster_statistics"],
                "output_file": result["output_file"],
                "segmented_csv": result["segmented_csv"],
                "message": result["message"]
            }
            return ClusteringResponse(**response_data)
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("message")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Clustering failed: {str(e)}"
        )


# ============================================================================
# COMPARISON ENDPOINTS
# ============================================================================

@app.post("/api/compare", response_model=CompareAlgorithmsResponse)
async def compare_algorithms(request: CompareAlgorithmsRequest):
    """Compare all 3 clustering algorithms automatically.
    
    Runs K-Means, Hierarchical, and DBSCAN with standard configurations,
    compares quality metrics, and ranks by Silhouette score.
    
    Args:
        request: Path to preprocessed dataset
        
    Returns:
        Ranked comparison of all algorithms
    """
    try:
        result = service.compare_all_algorithms(
            preprocessed_path=request.preprocessed_file
        )
        
        if result.get("success"):
            return CompareAlgorithmsResponse(**result)
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("message")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "error_message": exc.detail,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "error_message": str(exc),
            "path": str(request.url)
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("✅ SmartSeg API Started")
    print("📊 Preprocessing pipeline: Ready")
    print("🎯 Clustering engine: Ready")
    print("📈 API endpoints: Ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 SmartSeg API Shutdown")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
