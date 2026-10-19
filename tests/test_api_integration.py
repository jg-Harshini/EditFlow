import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_ready_endpoints():
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    r_ready = client.get("/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "ready"


def test_ssrf_blocked_on_url_ingest():
    """Integration Standard 7: SSRF protection blocks loopback/metadata IPs."""
    payload = {"url": "http://127.0.0.1:8000/secret.mp4"}
    res = client.post("/api/v1/media/ingest-url", json=payload)
    assert res.status_code == 400
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] in ("SSRF_BLOCKED", "DOWNLOAD_FAILED")


def test_create_session_and_step_lifecycle():
    """Tests session creation, step execution, and background render job."""
    # 1. Create Session
    create_res = client.post(
        "/api/v1/sessions",
        json={"video_uri": "test_pack/assets/short_test.mp4"},
    )
    assert create_res.status_code == 201
    s_data = create_res.json()
    session_id = s_data["session_id"]
    assert "timeline_hash" in s_data

    # 2. Execute Step (Cut)
    step_res = client.post(
        f"/api/v1/sessions/{session_id}/steps",
        json={"say": "Cut the first 2 seconds"},
    )
    assert step_res.status_code == 200
    step_data = step_res.json()
    assert step_data["status"] == "applied"
    assert "timeline_hash" in step_data

    # 3. Trigger Render -> Background Job (HTTP 202)
    render_res = client.post(
        f"/api/v1/sessions/{session_id}/steps",
        json={"say": "render"},
        headers={"Idempotency-Key": "test-key-12345"},
    )
    assert render_res.status_code == 202
    job_data = render_res.json()
    job_id = job_data["job_id"]
    assert "poll_url" in job_data

    # 4. Check Safe Retries / Idempotency
    repeat_res = client.post(
        f"/api/v1/sessions/{session_id}/steps",
        json={"say": "render"},
        headers={"Idempotency-Key": "test-key-12345"},
    )
    assert repeat_res.status_code == 202
    assert repeat_res.json()["job_id"] == job_id  # Same job returned!

    # 5. Poll Job Status
    job_status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert job_status_res.status_code == 200
    assert job_status_res.json()["status"] in ("queued", "running", "succeeded")


def test_structured_json_error_format():
    """Integration Standard 5: Clear errors formatted as UPPER_SNAKE_CASE JSON."""
    res = client.get("/api/v1/sessions/non-existent-uuid")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"
    assert isinstance(data["error"]["retryable"], bool)
    assert "details" in data["error"]
