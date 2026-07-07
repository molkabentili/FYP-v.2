import json
import sqlite3

from segmentation_engine.api import database


def test_init_db_creates_users_and_analyses_tables_with_env_path(tmp_path, monkeypatch):
    db_path = tmp_path / "smartseg_test.db"
    monkeypatch.setenv("SMARTSEG_DB_PATH", str(db_path))
    monkeypatch.setenv("SMARTSEG_AUTH_EMAIL", "analyst@ooredoo.com")

    database.init_db()

    assert db_path.exists()
    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert "users" in tables
    assert "analyses" in tables
    assert database.get_user_by_email("analyst@ooredoo.com") is not None


def test_save_list_and_get_analysis_store_metadata_result_json_only(tmp_path, monkeypatch):
    db_path = tmp_path / "smartseg_test.db"
    monkeypatch.setenv("SMARTSEG_DB_PATH", str(db_path))
    database.init_db()
    user = database.get_user_by_email("analyst@ooredoo.com")

    saved = database.save_analysis(
        user["id"],
        {
            "title": "K-Means k=5",
            "dataset_name": "demo.csv",
            "algorithm": "kmeans",
            "n_clusters": 5,
            "result": {
                "business_segments": [{"business_segment": "Premium Customers"}],
                "segmented_csv": "api_data/segmented_kmeans_100.csv",
            },
        },
    )

    analyses = database.list_analyses(user["id"])
    loaded = database.get_analysis(saved["id"], user["id"])
    other_user_loaded = database.get_analysis(saved["id"], user["id"] + 999)

    assert len(analyses) == 1
    assert analyses[0]["title"] == "K-Means k=5"
    assert analyses[0]["dataset_name"] == "demo.csv"
    assert analyses[0]["algorithm"] == "kmeans"
    assert analyses[0]["n_clusters"] == 5
    assert loaded is not None
    assert json.loads(loaded["result_json"])["business_segments"][0]["business_segment"] == "Premium Customers"
    assert other_user_loaded is None
