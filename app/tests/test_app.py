"""Unit tests for the demo Flask service."""
import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["service"] == "devops-demo-platform"
    assert "version" in body


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ready"


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    # Prometheus exposition format includes our custom metric name
    assert b"app_http_requests_total" in resp.data


def test_create_and_list_tasks(client):
    create = client.post("/api/tasks", json={"title": "deploy to kind"})
    assert create.status_code == 201
    task = create.get_json()
    assert task["title"] == "deploy to kind"
    assert task["done"] is False

    listing = client.get("/api/tasks")
    assert listing.status_code == 200
    body = listing.get_json()
    assert body["count"] >= 1
    assert any(t["title"] == "deploy to kind" for t in body["tasks"])


def test_create_task_validation(client):
    resp = client.post("/api/tasks", json={"title": "   "})
    assert resp.status_code == 400
    assert "error" in resp.get_json()
