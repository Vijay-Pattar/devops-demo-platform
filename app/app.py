"""
DevOps Demo Platform — a small Flask service used to demonstrate a full
CI/CD + containerization + Kubernetes + observability workflow.

The app itself is intentionally simple; the interesting part is everything
around it (Docker, Helm, CI/CD, Prometheus). It exposes:

    GET /            -> service info
    GET /health      -> liveness probe
    GET /ready       -> readiness probe
    GET /api/tasks   -> list in-memory tasks
    POST /api/tasks  -> create a task  {"title": "..."}
    GET /metrics     -> Prometheus metrics
"""
from __future__ import annotations

import os
import time
from threading import Lock

from flask import Flask, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
START_TIME = time.time()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "app_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)

# ---------------------------------------------------------------------------
# Tiny in-memory "database" (thread-safe). No external storage on purpose.
# ---------------------------------------------------------------------------
_tasks: list[dict] = []
_tasks_lock = Lock()
_next_id = 1


@app.before_request
def _start_timer() -> None:
    request._start_time = time.time()  # type: ignore[attr-defined]


@app.after_request
def _record_metrics(response):
    endpoint = request.endpoint or "unknown"
    latency = time.time() - getattr(request, "_start_time", time.time())
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        http_status=response.status_code,
    ).inc()
    return response


@app.route("/")
def index():
    return jsonify(
        service="devops-demo-platform",
        version=APP_VERSION,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


@app.route("/health")
def health():
    """Liveness probe — is the process up?"""
    return jsonify(status="ok"), 200


@app.route("/ready")
def ready():
    """Readiness probe — is the app ready to serve traffic?"""
    return jsonify(status="ready"), 200


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    with _tasks_lock:
        return jsonify(tasks=list(_tasks), count=len(_tasks))


@app.route("/api/tasks", methods=["POST"])
def create_task():
    global _next_id
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify(error="'title' is required"), 400

    with _tasks_lock:
        task = {"id": _next_id, "title": title, "done": False}
        _tasks.append(task)
        _next_id += 1
    return jsonify(task), 201


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":  # pragma: no cover
    port = int(os.getenv("PORT", "8000"))
    # Binding to all interfaces is required so the service is reachable from
    # outside its container/pod. This is the expected pattern for containerized
    # apps; access is controlled at the network/ingress layer. nosec B104
    app.run(host="0.0.0.0", port=port)  # nosec B104
