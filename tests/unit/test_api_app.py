"""Unit tests for the aiohttp application and async OpenAPI endpoints.

Uses ``aiohttp.test_utils.TestClient`` driven by pytest-asyncio so every test
is a plain ``async def`` function that ``await``s HTTP calls — no blocking I/O.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from uuid import uuid4
from aiohttp.test_utils import TestClient, TestServer

from src.api.app import create_app

# All async tests in this module are automatically recognised by pytest-asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def client() -> TestClient:
    """Create a running aiohttp TestClient for the application."""
    app = create_app()
    server = TestServer(app)
    async with TestClient(server) as c:
        yield c


# ── Health probe ──────────────────────────────────────────────────────────────


class TestHealth:
    async def test_health_returns_ok(self, client: TestClient):
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data == {"status": "ok"}


# ── OpenAPI schema ────────────────────────────────────────────────────────────


class TestOpenAPISchema:
    async def test_openapi_json_accessible(self, client: TestClient):
        resp = await client.get("/openapi.json")
        assert resp.status == 200
        schema = await resp.json()
        assert schema["info"]["title"] == "5G Network Digital Twin API"
        assert schema["info"]["version"] == "0.1.0"

    async def test_docs_accessible(self, client: TestClient):
        resp = await client.get("/docs")
        assert resp.status == 200
        text = await resp.text()
        assert "swagger-ui" in text

    async def test_openapi_contains_topology_paths(self, client: TestClient):
        schema = await (await client.get("/openapi.json")).json()
        assert "/api/v1/topology/" in schema["paths"]

    async def test_openapi_contains_metrics_paths(self, client: TestClient):
        schema = await (await client.get("/openapi.json")).json()
        assert "/api/v1/metrics/definitions" in schema["paths"]

    async def test_openapi_contains_activation_paths(self, client: TestClient):
        schema = await (await client.get("/openapi.json")).json()
        assert "/api/v1/activation/workflows" in schema["paths"]


# ── Topology endpoints ────────────────────────────────────────────────────────


class TestTopologyEndpoints:
    async def test_get_topology_returns_200(self, client: TestClient):
        resp = await client.get("/api/v1/topology/")
        assert resp.status == 200
        data = await resp.json()
        assert "gnodebs" in data
        assert "slices" in data
        assert "connections" in data

    async def test_list_gnodebs_returns_list(self, client: TestClient):
        resp = await client.get("/api/v1/topology/gnodebs")
        assert resp.status == 200
        assert isinstance(await resp.json(), list)

    async def test_get_nonexistent_gnodeb_returns_404(self, client: TestClient):
        resp = await client.get(f"/api/v1/topology/gnodebs/{uuid4()}")
        assert resp.status == 404

    async def test_list_slices_returns_list(self, client: TestClient):
        resp = await client.get("/api/v1/topology/slices")
        assert resp.status == 200
        assert isinstance(await resp.json(), list)

    async def test_get_nonexistent_slice_returns_404(self, client: TestClient):
        resp = await client.get(f"/api/v1/topology/slices/{uuid4()}")
        assert resp.status == 404

    async def test_list_connections_returns_list(self, client: TestClient):
        resp = await client.get("/api/v1/topology/connections")
        assert resp.status == 200
        assert isinstance(await resp.json(), list)


# ── Metrics endpoints ─────────────────────────────────────────────────────────


class TestMetricsEndpoints:
    async def test_get_definitions_returns_non_empty_list(self, client: TestClient):
        resp = await client.get("/api/v1/metrics/definitions")
        assert resp.status == 200
        data = await resp.json()
        assert len(data) > 0

    async def test_metric_definition_has_required_fields(self, client: TestClient):
        resp = await client.get("/api/v1/metrics/definitions")
        first = (await resp.json())[0]
        assert "name" in first
        assert "unit" in first
        assert "description" in first

    async def test_get_definitions_for_gnodeb(self, client: TestClient):
        resp = await client.get("/api/v1/metrics/definitions/gNodeB")
        assert resp.status == 200
        names = [m["name"] for m in await resp.json()]
        assert "latency_ms" in names

    async def test_get_kpi_summary_returns_dict(self, client: TestClient):
        resp = await client.get(f"/api/v1/metrics/summary/{uuid4()}")
        assert resp.status == 200
        data = await resp.json()
        assert "entity_id" in data
        assert "kpis" in data

    async def test_get_kpi_snapshots_returns_list(self, client: TestClient):
        resp = await client.get(f"/api/v1/metrics/snapshots/{uuid4()}")
        assert resp.status == 200
        assert isinstance(await resp.json(), list)


# ── Activation endpoints ──────────────────────────────────────────────────────


class TestActivationEndpoints:
    async def test_list_workflows_returns_list(self, client: TestClient):
        resp = await client.get("/api/v1/activation/workflows")
        assert resp.status == 200
        assert isinstance(await resp.json(), list)

    async def test_submit_workflow_returns_202(self, client: TestClient):
        payload = {
            "workflow_type": "slice_activation",
            "target_entity_id": str(uuid4()),
            "parameters": {"slice_type": "eMBB"},
        }
        resp = await client.post("/api/v1/activation/workflows", json=payload)
        assert resp.status == 202
        data = await resp.json()
        assert "workflow_id" in data
        assert data["status"] == "pending"

    async def test_get_submitted_workflow_returns_200(self, client: TestClient):
        payload = {"workflow_type": "gnb_reconfig", "target_entity_id": str(uuid4())}
        submit_resp = await client.post("/api/v1/activation/workflows", json=payload)
        wf_id = (await submit_resp.json())["workflow_id"]
        get_resp = await client.get(f"/api/v1/activation/workflows/{wf_id}")
        assert get_resp.status == 200
        assert (await get_resp.json())["id"] == wf_id

    async def test_get_nonexistent_workflow_returns_404(self, client: TestClient):
        resp = await client.get(f"/api/v1/activation/workflows/{uuid4()}")
        assert resp.status == 404

    async def test_cancel_workflow_returns_result(self, client: TestClient):
        payload = {"workflow_type": "test_cancel", "target_entity_id": str(uuid4())}
        submit_resp = await client.post("/api/v1/activation/workflows", json=payload)
        wf_id = (await submit_resp.json())["workflow_id"]
        cancel_resp = await client.delete(f"/api/v1/activation/workflows/{wf_id}/cancel")
        assert cancel_resp.status == 200
        assert "cancelled" in await cancel_resp.json()

    async def test_rollback_workflow_returns_result(self, client: TestClient):
        payload = {"workflow_type": "test_rollback", "target_entity_id": str(uuid4())}
        submit_resp = await client.post("/api/v1/activation/workflows", json=payload)
        wf_id = (await submit_resp.json())["workflow_id"]
        rb_resp = await client.post(f"/api/v1/activation/workflows/{wf_id}/rollback")
        assert rb_resp.status == 200
        assert "rolled_back" in await rb_resp.json()
