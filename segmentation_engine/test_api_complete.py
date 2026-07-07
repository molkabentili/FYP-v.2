"""Integration tests for the FastAPI segmentation backend."""

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
PREPROCESSED_FILE = Path(__file__).resolve().parent / "test_preprocessed_for_api.csv"


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

    response = session.get(f"{api_base_url}/api/health", timeout=5)
    assert response.status_code == 200
    health = response.json()
    assert health["status"] == "healthy"

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
def preprocessed_file_path():
    assert PREPROCESSED_FILE.exists(), f"Preprocessed fixture not found: {PREPROCESSED_FILE}"
    return str(PREPROCESSED_FILE)


def _json_response(response):
    assert response.headers["content-type"].startswith("application/json")
    return response.json()


def test_health_check(api_session, api_base_url):
    response = api_session.get(f"{api_base_url}/api/health", timeout=5)
    result = _json_response(response)

    assert response.status_code == 200
    assert result["status"] == "healthy"
    assert result["modules"]["fastapi"] is True
    assert result["modules"]["preprocessing"] is True
    assert result["modules"]["clustering"] is True
    assert result["modules"]["api_service"] is True


@pytest.mark.parametrize(
    ("payload", "expected_algorithm"),
    [
        (
            {"algorithm": "kmeans", "n_clusters": 3},
            "kmeans",
        ),
        (
            {"algorithm": "hierarchical", "n_clusters": 3, "linkage": "ward"},
            "hierarchical",
        ),
        (
            {"algorithm": "dbscan", "eps": 0.5, "min_samples": 5},
            "dbscan",
        ),
    ],
)
def test_clustering_algorithms(
    api_session,
    api_base_url,
    preprocessed_file_path,
    payload,
    expected_algorithm,
):
    request_payload = {
        **payload,
        "preprocessed_file": preprocessed_file_path,
    }

    response = api_session.post(f"{api_base_url}/api/cluster", json=request_payload, timeout=30)
    result = _json_response(response)

    assert response.status_code == 200
    assert result["success"] is True
    assert result["algorithm"] == expected_algorithm
    assert isinstance(result["n_clusters"], int)
    assert isinstance(result["labels"], list)
    assert len(result["labels"]) > 0
    assert "silhouette_score" in result["metrics"]

    if expected_algorithm != "dbscan":
        assert result["n_clusters"] == 3
        assert len(result["cluster_statistics"]) == 3
        assert sum(cluster["size"] for cluster in result["cluster_statistics"]) > 0
        assert len(result["clusters"]) == 3
        assert len(result["business_segments"]) >= 1
        assert isinstance(result["warnings"], list)
        assert isinstance(result["validation"], dict)


def test_algorithm_comparison(api_session, api_base_url, preprocessed_file_path):
    payload = {"preprocessed_file": preprocessed_file_path}

    response = api_session.post(f"{api_base_url}/api/compare", json=payload, timeout=60)
    result = _json_response(response)

    assert response.status_code == 200
    assert result["success"] is True
    assert result["best_algorithm"] in {"K-Means", "Hierarchical", "DBSCAN"}
    assert isinstance(result["best_score"], float)
    assert len(result["comparisons"]) == 3

    ranks = [comparison["rank"] for comparison in result["comparisons"]]
    assert ranks == [1, 2, 3]
