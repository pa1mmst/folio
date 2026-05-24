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
    def test_backlinks_api_empty(self, client):
        r = client.get("/api/backlinks/nonexistent")
        assert r.status_code == 200
        assert r.json() == []

    def test_backlinks_api(self, client):
        client.post("/api/note", json={"name": "note-a", "content": "Links to [[note-b]] and [[note-c]]"})
        client.post("/api/note", json={"name": "note-d", "content": "Also links to [[note-b]]"})
        r = client.get("/api/backlinks/note-b")
        assert r.status_code == 200
        data = r.json()
        names = [d["source_note"] for d in data]
        assert "note-a" in names
        assert "note-d" in names
        assert len(names) == 2

    def test_backlinks_note_page_shows_panel(self, client):
        client.post("/api/note", json={"name": "linker", "content": "See [[target-note]]"})
        client.post("/api/note", json={"name": "target-note", "content": "Target content"})
        r = client.get("/note/target-note")
        assert r.status_code == 200
        assert "backlinks-panel" in r.text
        assert "linker" in r.text

    def test_backlinks_note_page_no_backlinks(self, client):
        client.post("/api/note", json={"name": "orphan", "content": "No links to me"})
        r = client.get("/note/orphan")
        assert r.status_code == 200
        assert "backlinks-panel" in r.text
        assert "No backlinks" in r.text
