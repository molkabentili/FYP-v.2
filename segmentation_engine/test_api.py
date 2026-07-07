"""Test FastAPI backend endpoints."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


AUTH_EMAIL = os.getenv("SMARTSEG_AUTH_EMAIL", "analyst@ooredoo.com")
AUTH_PASSWORD = os.getenv("SMARTSEG_AUTH_PASSWORD", "SmartSeg2026!")
TEST_DATA_FILE = Path(__file__).resolve().parent / "test_customer_data.csv"


@pytest.fixture(scope="module")
def api_base_url():
    host = "127.0.0.1"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        port = sock.getsockname()[1]

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "segmentation_engine.api.main:app",
            "--host",
            host,
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=Path(__file__).resolve().parent.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://{host}:{port}"

    try:
        deadline = time.monotonic() + 30
        last_error = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                response = requests.get(f"{base_url}/api/health", timeout=1)
                if response.status_code == 200:
                    yield base_url
                    return
            except requests.RequestException as exc:
                last_error = exc
            time.sleep(0.25)

        stdout, stderr = process.communicate(timeout=2)
        pytest.fail(
            "FastAPI test server did not start. "
            f"Last error: {last_error}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


@pytest.fixture(scope="module")
def api_session(api_base_url):
    session = requests.Session()

    login_response = session.post(
        f"{api_base_url}/api/auth/login",
        json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        timeout=10,
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})

    return session


@pytest.fixture(scope="module")
def preprocessed_file_fixture(api_session, api_base_url):
    assert TEST_DATA_FILE.exists(), f"test_customer_data.csv not found at {TEST_DATA_FILE}"

    with TEST_DATA_FILE.open("rb") as file_obj:
        response = api_session.post(
            f"{api_base_url}/api/preprocess",
            files={"file": ("test_data.csv", file_obj, "text/csv")},
            data={"dataset_name": "test_customer_data"},
            timeout=30,
        )

    result = response.json()
    assert response.status_code == 200
    assert result["success"] is True
    assert result["output_file"]

    return result["output_file"]


def _json_response(response):
    assert response.headers["content-type"].startswith("application/json")
    return response.json()


def test_health(api_session, api_base_url):
    """Test health check endpoint."""
    response = api_session.get(f"{api_base_url}/api/health", timeout=5)
    data = _json_response(response)

    assert response.status_code == 200
    assert data["status"] == "healthy"
    assert data["modules"]["fastapi"] is True
    assert data["modules"]["preprocessing"] is True
    assert data["modules"]["clustering"] is True


def test_preprocess(preprocessed_file_fixture):
    """Test preprocessing endpoint."""
    output_file = Path(preprocessed_file_fixture)

    assert output_file.name == "test_data_cleaned.csv"
    assert output_file.exists()


def test_clustering(api_session, api_base_url, preprocessed_file_fixture):
    """Test clustering endpoint."""
    payload = {
        "algorithm": "kmeans",
        "preprocessed_file": preprocessed_file_fixture,
        "n_clusters": 3,
    }

    response = api_session.post(f"{api_base_url}/api/cluster", json=payload, timeout=30)
    result = _json_response(response)

    assert response.status_code == 200
    assert result["success"] is True
    assert result["algorithm"] == "kmeans"
    assert result["n_clusters"] == 3
    assert result["metrics"]["silhouette_score"] is not None
    assert len(result["cluster_statistics"]) == 3
    assert sum(cluster["size"] for cluster in result["cluster_statistics"]) > 0
    assert len(result["clusters"]) == 3
    assert len(result["business_segments"]) >= 1
    assert isinstance(result["warnings"], list)
    assert isinstance(result["validation"], dict)
    assert all("business_segment" in cluster for cluster in result["clusters"])
    assert all("source_cluster_ids" in segment for segment in result["business_segments"])


def test_comparison(api_session, api_base_url, preprocessed_file_fixture):
    """Test algorithm comparison endpoint."""
    payload = {"preprocessed_file": preprocessed_file_fixture}

    response = api_session.post(f"{api_base_url}/api/compare", json=payload, timeout=60)
    result = _json_response(response)

    assert response.status_code == 200
    assert result["success"] is True
    assert result["best_algorithm"] in {"K-Means", "Hierarchical", "DBSCAN"}
    assert isinstance(result["best_score"], float)
    assert len(result["comparisons"]) == 3
    assert [comparison["rank"] for comparison in result["comparisons"]] == [1, 2, 3]
