import os
import sys
import pytest

os.environ["VAULT_DIR"] = "/tmp/vault-test-api"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import init_db as _init_db


@pytest.fixture(autouse=True)
def _setup_db():
    _init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestNoteAPI:
    def test_create_note(self, client):
        r = client.post("/api/note", json={"name": "test-api", "content": "# Test\nHello"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test-api"

    def test_get_note_page(self, client):
        client.post("/api/note", json={"name": "test-view", "content": "**Bold** and #tag"})
        r = client.get("/note/test-view")
        assert r.status_code == 200

    def test_search(self, client):
        client.post("/api/note", json={"name": "search-me", "content": "unique phrase xyz123"})
        r = client.get("/api/search?q=xyz123")
        assert r.status_code == 200
        results = r.json()
        assert any(n["name"] == "search-me" for n in results)

    def test_delete_note(self, client):
        client.post("/api/note", json={"name": "to-del", "content": "del"})
        r = client.delete("/api/note/to-del")
        assert r.status_code == 200

    def test_graph_api(self, client):
        r = client.get("/api/graph")
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data
        assert "links" in data

    def test_404_page(self, client):
        r = client.get("/note/nonexistent-note-abc")
        assert r.status_code == 200


class TestBacklinks:
    def test_backlinks_empty(self, client):
        client.post("/api/note", json={"name": "note-a", "content": "# Note A\nNo links here"})
        r = client.get("/api/backlinks/note-a")
        assert r.status_code == 200
        assert r.json() == []

    def test_backlinks_single(self, client):
        client.post("/api/note", json={"name": "note-b", "content": "# Note B\nSee [[note-a]]"})
        r = client.get("/api/backlinks/note-a")
        assert r.status_code == 200
        data = r.json()
        assert "note-b" in data

    def test_backlinks_multiple(self, client):
        client.post("/api/note", json={"name": "note-c", "content": "# C\n[[note-a]] too"})
        client.post("/api/note", json={"name": "note-d", "content": "# D\nAlso [[note-a]]"})
        r = client.get("/api/backlinks/note-a")
        data = r.json()
        assert "note-b" in data
        assert "note-c" in data
        assert "note-d" in data

    def test_backlinks_not_self(self, client):
        """Backlinks should not include the note itself."""
        r = client.get("/api/backlinks/note-a")
        data = r.json()
        assert "note-a" not in data
