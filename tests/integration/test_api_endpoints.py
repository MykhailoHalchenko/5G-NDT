"""Integration tests for the FastAPI REST API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_response_schema(self):
        response = client.get("/health")
        data = response.json()
        assert set(data.keys()) >= {"status", "service", "version"}


class TestTopologyEndpoints:
    def test_get_topology_empty(self):
        response = client.get("/api/v1/topology/")
        assert response.status_code == 200
        data = response.json()
        assert "gnodebs" in data
        assert "slices" in data
        assert "connections" in data

    def test_list_gnodebs_empty(self):
        response = client.get("/api/v1/topology/gnodebs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_gnodeb_not_found(self):
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/topology/gnodebs/{fake_id}")
        assert response.status_code == 404

    def test_list_slices_empty(self):
        response = client.get("/api/v1/topology/slices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_connections_empty(self):
        response = client.get("/api/v1/topology/connections")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestMetricsEndpoints:
    def test_list_metric_definitions(self):
        response = client.get("/api/v1/metrics/definitions")
        assert response.status_code == 200
        definitions = response.json()
        assert isinstance(definitions, list)
        assert len(definitions) > 0

    def test_metric_definition_schema(self):
        response = client.get("/api/v1/metrics/definitions")
        first = response.json()[0]
        assert "name" in first
        assert "unit" in first
        assert "description" in first

    def test_metrics_for_gnodeb(self):
        response = client.get("/api/v1/metrics/entity/gNodeB")
        assert response.status_code == 200
        metrics = response.json()
        assert isinstance(metrics, list)
        names = [m["name"] for m in metrics]
        assert "latency_ms" in names

    def test_kpi_summary_returns_dict(self):
        import uuid
        entity_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/metrics/{entity_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "entity_id" in data
        assert "kpis" in data


class TestActivationEndpoints:
    def test_list_workflows_empty(self):
        response = client.get("/api/v1/activation/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_submit_workflow(self):
        import uuid
        payload = {
            "workflow_type": "slice_activation",
            "target_entity_id": str(uuid.uuid4()),
            "parameters": {"slice_type": "eMBB"},
        }
        response = client.post("/api/v1/activation/", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert "workflow_id" in data
        assert data["status"] == "pending"

    def test_get_workflow_after_submit(self):
        import uuid
        payload = {
            "workflow_type": "test_workflow",
            "target_entity_id": str(uuid.uuid4()),
        }
        submit_response = client.post("/api/v1/activation/", json=payload)
        assert submit_response.status_code == 202
        workflow_id = submit_response.json()["workflow_id"]

        get_response = client.get(f"/api/v1/activation/{workflow_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == workflow_id

    def test_get_workflow_not_found(self):
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/activation/{fake_id}")
        assert response.status_code == 404

    def test_cancel_nonexistent_workflow_conflict(self):
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.post(f"/api/v1/activation/{fake_id}/cancel")
        assert response.status_code == 409

    def test_submit_invalid_payload(self):
        response = client.post("/api/v1/activation/", json={"invalid": "data"})
        assert response.status_code == 422


class TestOpenAPISchema:
    def test_openapi_json_accessible(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema

    def test_docs_accessible(self):
        response = client.get("/docs")
        assert response.status_code == 200
