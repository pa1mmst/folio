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


class TestEditor:
    def test_editor_page_renders(self, client):
        r = client.get("/edit/test-editor")
        assert r.status_code == 200
        assert "editor-layout" in r.text
        assert "toolbar" in r.text
        assert "preview-pane" in r.text
        assert "editor" in r.text
        assert 'id="preview"' in r.text
        assert 'id="editor"' in r.text

    def test_editor_has_toolbar_buttons(self, client):
        r = client.get("/edit/test-editor")
        assert r.status_code == 200
        assert 'data-cmd="bold"' in r.text
        assert 'data-cmd="italic"' in r.text
        assert 'data-cmd="h1"' in r.text
        assert 'data-cmd="h2"' in r.text
        assert 'data-cmd="h3"' in r.text
        assert 'data-cmd="link"' in r.text
        assert 'data-cmd="code"' in r.text
        assert 'data-cmd="list"' in r.text
        assert 'data-cmd="quote"' in r.text

    def test_editor_has_debounce(self, client):
        r = client.get("/edit/test-editor")
        assert r.status_code == 200
        assert "debounceTimer" in r.text
        assert "setTimeout(updatePreview, 300)" in r.text

    def test_editor_has_save_function(self, client):
        r = client.get("/edit/test-editor")
        assert r.status_code == 200
        assert "saveNote" in r.text
        assert "/api/note" in r.text

    def test_editor_has_keyboard_shortcuts(self, client):
        r = client.get("/edit/test-editor")
        assert r.status_code == 200
        assert "Ctrl+B" in r.text or "metaKey" in r.text
        assert "b:'bold'" in r.text or "i:'italic'" in r.text or "Ctrl+I" in r.text

    def test_editor_new_note_has_default_content(self, client):
        r = client.get("/edit/new")
        assert r.status_code == 200
        assert "Start writing" in r.text

    def test_editor_existing_note_has_content(self, client):
        client.post("/api/note", json={"name": "test-editor-content", "content": "# Existing\n\nNote body"})
        r = client.get("/edit/test-editor-content")
        assert r.status_code == 200
        assert "Existing" in r.text
        assert "Note body" in r.text

    def test_markdown_to_html_via_api(self, client):
        r = client.post("/api/note", json={"name": "md-test", "content": "# Heading\n\n**Bold** and *italic*\n\n- Item 1\n- Item 2\n\n> A quote\n\n`code` here\n\n[[wiki-link]]\n\n#tag"})
        assert r.status_code == 200
        r2 = client.get("/note/md-test")
        assert r2.status_code == 200
        assert "Heading" in r2.text
        assert "wiki-link" in r2.text

    def test_editor_has_cancel_link(self, client):
        r = client.get("/edit/test-editor")
        assert r.status_code == 200
        assert "Cancel" in r.text
        assert "/note/test-editor" in r.text or "href=" in r.text

    def test_editor_links_static_css(self, client):
        r = client.get("/edit/test-editor")
        assert r.status_code == 200
        assert "style.css" in r.text or "/static/" in r.text

    def test_static_css_served(self, client):
        r = client.get("/static/style.css")
        assert r.status_code == 200
        assert "toolbar" in r.text
