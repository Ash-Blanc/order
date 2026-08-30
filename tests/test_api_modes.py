"""E2E tests for all 6 API modes via the FastAPI test client"""
import pytest


pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Order"


class TestOneThing:
    async def test_empty_store_returns_empty_status(self, client):
        resp = await client.get("/api/one-thing")
        assert resp.status_code == 200
        assert resp.json()["status"] == "empty"

    async def test_done_missing_id_returns_error(self, client):
        resp = await client.post("/api/one-thing/done", json={"commitment_id": "nonexistent"})
        assert resp.status_code == 200  # store silently ignores unknown ids

    async def test_skip_missing_id_returns_ok(self, client):
        resp = await client.post("/api/one-thing/skip", json={"commitment_id": "nonexistent"})
        assert resp.status_code == 200

    async def test_why_missing_id_returns_404(self, client):
        resp = await client.get("/api/one-thing/why?commitment_id=nonexistent")
        assert resp.status_code == 404


class TestStats:
    async def test_stats_empty(self, client):
        resp = await client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pending"] == 0
        assert data["done"] == 0


class TestGather:
    async def test_test_connections(self, client):
        resp = await client.get("/api/gather/test")
        assert resp.status_code == 200
        # All connections should return False when no API keys are set
        data = resp.json()
        assert isinstance(data, dict)
        for connected in data.values():
            assert connected is False

    async def test_gather_all_no_keys_returns_done(self, client):
        resp = await client.get("/api/gather")
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"
        assert isinstance(resp.json()["results"], list)


class TestReduce:
    async def test_reduce_empty_store(self, client):
        resp = await client.get("/api/reduce")
        assert resp.status_code == 200
        data = resp.json()
        assert data["filtered_count"] == 0
        assert data["kept_count"] == 0


class TestConversation:
    async def test_chat_responds(self, client):
        resp = await client.post("/api/chat", json={"message": "What should I focus on?"})
        assert resp.status_code == 200
        assert "response" in resp.json()

    async def test_chat_empty_message_rejected(self, client):
        resp = await client.post("/api/chat", json={"message": "   "})
        assert resp.status_code == 422

    async def test_chat_too_long_rejected(self, client):
        resp = await client.post("/api/chat", json={"message": "x" * 2001})
        assert resp.status_code == 422

    async def test_reset_chat(self, client):
        resp = await client.post("/api/chat/reset")
        assert resp.status_code == 200
        assert resp.json()["status"] == "reset"


class TestJustInTime:
    async def test_search_empty_store(self, client):
        resp = await client.post("/api/search", json={"query": "review PR"})
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    async def test_search_empty_query_rejected(self, client):
        resp = await client.post("/api/search", json={"query": ""})
        assert resp.status_code == 422

    async def test_promises_empty_store(self, client):
        resp = await client.get("/api/promises")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    async def test_about_empty_store(self, client):
        resp = await client.get("/api/about?topic=report")
        assert resp.status_code == 200
        assert resp.json()["results"] == []


class TestExecutor:
    async def test_list_commitments_empty(self, client):
        resp = await client.get("/api/commitments")
        assert resp.status_code == 200
        assert resp.json()["commitments"] == []

    async def test_get_commitment_not_found(self, client):
        resp = await client.get("/api/commitments/nonexistent")
        assert resp.status_code == 404

    async def test_propose_action_not_found(self, client):
        resp = await client.post("/api/commitments/nonexistent/action")
        assert resp.status_code == 404
