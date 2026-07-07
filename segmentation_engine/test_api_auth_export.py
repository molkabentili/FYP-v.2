import asyncio
import json

from segmentation_engine.api import main as api_main
from segmentation_engine.api.services import SegmentationService


async def call_api(method: str, path: str, payload: dict, headers: dict[str, str] | None = None):
    body = json.dumps(payload).encode("utf-8")
    request_messages = [{"type": "http.request", "body": body, "more_body": False}]
    response_messages = []
    raw_headers = [(b"content-type", b"application/json")]

    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    async def receive():
        return request_messages.pop(0)

    async def send(message):
        response_messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": raw_headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    await api_main.app(scope, receive, send)

    start = next(message for message in response_messages if message["type"] == "http.response.start")
    content = b"".join(
        message.get("body", b"")
        for message in response_messages
        if message["type"] == "http.response.body"
    )
    return start["status"], dict(start.get("headers", [])), content


def post_json(path: str, payload: dict, headers: dict[str, str] | None = None):
    return asyncio.run(call_api("POST", path, payload, headers=headers))


def login_headers() -> dict[str, str]:
    status_code, _headers, content = post_json(
        "/api/auth/login",
        {
            "email": api_main.AUTH_EMAIL,
            "password": api_main.AUTH_PASSWORD,
        },
    )

    assert status_code == 200
    payload = json.loads(content)
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == api_main.AUTH_EMAIL

    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_protected_export_endpoint_rejects_missing_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SMARTSEG_DB_PATH", str(tmp_path / "smartseg.db"))

    status_code, _headers, content = post_json(
        "/api/export/customers",
        {
            "segmented_csv": str(tmp_path / "missing.csv"),
            "export_format": "csv",
        },
    )

    assert status_code == 401
    assert json.loads(content)["error_message"] == "Authentication required"


def test_login_returns_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SMARTSEG_DB_PATH", str(tmp_path / "smartseg.db"))

    headers = login_headers()

    assert headers["Authorization"].startswith("Bearer ")


def test_export_selected_segment_works_with_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SMARTSEG_DB_PATH", str(tmp_path / "smartseg.db"))
    monkeypatch.setattr(
        api_main,
        "service",
        SegmentationService(data_dir=str(tmp_path / "api_data")),
    )
    segmented_csv = tmp_path / "segmented.csv"
    segmented_csv.write_text(
        "\n".join(
            [
                "customer_id,cluster_id,business_segment,monthly_spend,data_consumption_gb,voice_minutes,tenure_months,churn_risk",
                "C001,0,Premium Customers,180,120,300,24,0.1",
                "C002,1,Medium Value Customers,45,30,120,12,0.2",
            ]
        ),
        encoding="utf-8",
    )
    headers = login_headers()

    status_code, _headers, content = post_json(
        "/api/export/customers",
        {
            "segmented_csv": str(segmented_csv),
            "export_format": "csv",
            "segment": "Premium Customers",
        },
        headers=headers,
    )

    assert status_code == 200
    body = content.decode("utf-8")
    assert "Business_Segment" in body
    assert "Premium Customers" in body
    assert "Medium Value Customers" not in body
    assert "C001" in body
    assert "C002" not in body
