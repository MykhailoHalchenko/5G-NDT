"""Unit tests for the FastAPI application and async OpenAPI endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from src.api.app import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous TestClient — works for sync and async FastAPI endpoints."""
    return TestClient(app, raise_server_exceptions=True)


# ── Health probe ──────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_returns_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ── OpenAPI schema ────────────────────────────────────────────────────────────


class TestOpenAPISchema:
    def test_openapi_json_accessible(self, client: TestClient):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "5G Network Digital Twin API"
        assert schema["info"]["version"] == "0.1.0"

    def test_docs_accessible(self, client: TestClient):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self, client: TestClient):
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_contains_topology_paths(self, client: TestClient):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/topology/" in paths

    def test_openapi_contains_metrics_paths(self, client: TestClient):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/metrics/definitions" in paths

    def test_openapi_contains_activation_paths(self, client: TestClient):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/activation/workflows" in paths


# ── Topology endpoints ────────────────────────────────────────────────────────


class TestTopologyEndpoints:
    def test_get_topology_returns_200(self, client: TestClient):
        response = client.get("/api/v1/topology/")
        assert response.status_code == 200
        data = response.json()
        assert "gnodebs" in data
        assert "slices" in data
        assert "connections" in data

    def test_list_gnodebs_returns_list(self, client: TestClient):
        response = client.get("/api/v1/topology/gnodebs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_gnodeb_returns_404(self, client: TestClient):
        response = client.get(f"/api/v1/topology/gnodebs/{uuid4()}")
        assert response.status_code == 404

    def test_list_slices_returns_list(self, client: TestClient):
        response = client.get("/api/v1/topology/slices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_slice_returns_404(self, client: TestClient):
        response = client.get(f"/api/v1/topology/slices/{uuid4()}")
        assert response.status_code == 404

    def test_list_connections_returns_list(self, client: TestClient):
        response = client.get("/api/v1/topology/connections")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── Metrics endpoints ─────────────────────────────────────────────────────────


class TestMetricsEndpoints:
    def test_get_definitions_returns_non_empty_list(self, client: TestClient):
        response = client.get("/api/v1/metrics/definitions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_metric_definition_has_required_fields(self, client: TestClient):
        response = client.get("/api/v1/metrics/definitions")
        first = response.json()[0]
        assert "name" in first
        assert "unit" in first
        assert "description" in first

    def test_get_definitions_for_gnodeb(self, client: TestClient):
        response = client.get("/api/v1/metrics/definitions/gNodeB")
        assert response.status_code == 200
        names = [m["name"] for m in response.json()]
        assert "latency_ms" in names

    def test_get_kpi_summary_returns_dict(self, client: TestClient):
        response = client.get(f"/api/v1/metrics/summary/{uuid4()}")
        assert response.status_code == 200
        data = response.json()
        assert "entity_id" in data
        assert "kpis" in data

    def test_get_kpi_snapshots_returns_list(self, client: TestClient):
        response = client.get(f"/api/v1/metrics/snapshots/{uuid4()}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── Activation endpoints ──────────────────────────────────────────────────────


class TestActivationEndpoints:
    def test_list_workflows_returns_list(self, client: TestClient):
        response = client.get("/api/v1/activation/workflows")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_submit_workflow_returns_202(self, client: TestClient):
        payload = {
            "workflow_type": "slice_activation",
            "target_entity_id": str(uuid4()),
            "parameters": {"slice_type": "eMBB"},
        }
        response = client.post("/api/v1/activation/workflows", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert "workflow_id" in data
        assert data["status"] == "pending"

    def test_get_submitted_workflow_returns_200(self, client: TestClient):
        payload = {
            "workflow_type": "gnb_reconfig",
            "target_entity_id": str(uuid4()),
        }
        submit_resp = client.post("/api/v1/activation/workflows", json=payload)
        wf_id = submit_resp.json()["workflow_id"]
        get_resp = client.get(f"/api/v1/activation/workflows/{wf_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == wf_id

    def test_get_nonexistent_workflow_returns_404(self, client: TestClient):
        response = client.get(f"/api/v1/activation/workflows/{uuid4()}")
        assert response.status_code == 404

    def test_cancel_workflow_returns_result(self, client: TestClient):
        payload = {
            "workflow_type": "test_cancel",
            "target_entity_id": str(uuid4()),
        }
        submit_resp = client.post("/api/v1/activation/workflows", json=payload)
        wf_id = submit_resp.json()["workflow_id"]
        cancel_resp = client.delete(f"/api/v1/activation/workflows/{wf_id}/cancel")
        assert cancel_resp.status_code == 200
        assert "cancelled" in cancel_resp.json()

    def test_rollback_workflow_returns_result(self, client: TestClient):
        payload = {
            "workflow_type": "test_rollback",
            "target_entity_id": str(uuid4()),
        }
        submit_resp = client.post("/api/v1/activation/workflows", json=payload)
        wf_id = submit_resp.json()["workflow_id"]
        rb_resp = client.post(f"/api/v1/activation/workflows/{wf_id}/rollback")
        assert rb_resp.status_code == 200
        assert "rolled_back" in rb_resp.json()
