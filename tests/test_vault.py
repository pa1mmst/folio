import os
import sys
import pytest

os.environ["VAULT_DIR"] = "/tmp/vault-test"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vault import (
    parse_tags, parse_wikilinks, strip_frontmatter,
    write_note, read_note, delete_note, note_exists,
    get_folder, get_all_folders, list_notes,
)


class TestParseTags:
    def test_single_tag(self):
        assert parse_tags("Hello #world") == ["world"]

    def test_multiple_tags(self):
        tags = parse_tags("#python #web #api")
        assert set(tags) == {"python", "web", "api"}

    def test_cyrillic_tags(self):
        tags = parse_tags("привет #мир #python")
        assert set(tags) == {"мир", "python"}

    def test_no_tags(self):
        assert parse_tags("Hello world") == []

    def test_tag_with_numbers(self):
        tags = parse_tags("#web2 #ai3")
        assert set(tags) == {"web2", "ai3"}

    def test_tags_deduplicated(self):
        tags = parse_tags("#web #web #web")
        assert tags == ["web"]


class TestParseWikilinks:
    def test_single_link(self):
        assert parse_wikilinks("See [[Other Note]]") == ["Other Note"]

    def test_multiple_links(self):
        links = parse_wikilinks("See [[A]] and [[B]]")
        assert set(links) == {"A", "B"}

    def test_no_links(self):
        assert parse_wikilinks("No links here") == []


class TestStripFrontmatter:
    def test_with_frontmatter(self):
        text = "---\ntitle: Test\n---\n# Hello"
        assert strip_frontmatter(text) == "# Hello"

    def test_without_frontmatter(self):
        text = "# Hello"
        assert strip_frontmatter(text) == "# Hello"


class TestVaultFiles:
    def setup_method(self):
        os.makedirs("/tmp/vault-test", exist_ok=True)

    def test_write_and_read(self):
        note = write_note("test-note", "# Hello\nContent here")
        assert note["name"] == "test-note"
        assert note["content"] == "# Hello\nContent here"
        read = read_note("test-note")
        assert read is not None
        assert read["content"] == "# Hello\nContent here"

    def test_read_nonexistent(self):
        assert read_note("does-not-exist") is None

    def test_delete(self):
        write_note("to-delete", "content")
        assert note_exists("to-delete")
        delete_note("to-delete")
        assert not note_exists("to-delete")

    def test_note_exists_false(self):
        assert not note_exists("ghost-note")


class TestVaultFolders:
    def setup_method(self):
        os.makedirs("/tmp/vault-test", exist_ok=True)

    def test_get_folder_from_name(self):
        assert get_folder("projects/idea") == "projects"
        assert get_folder("a/b/c") == "a/b"
        assert get_folder("root-note") == ""

    def test_write_note_in_folder(self):
        note = write_note("test-folder/my-note", "# Hello folder")
        assert note["name"] == "test-folder/my-note"
        assert note["folder"] == "test-folder"
        read = read_note("test-folder/my-note")
        assert read is not None
        assert read["folder"] == "test-folder"
        assert read["content"] == "# Hello folder"

    def test_write_note_in_nested_folder(self):
        note = write_note("a/b/c/nested-note", "Nested content")
        assert note["folder"] == "a/b/c"
        read = read_note("a/b/c/nested-note")
        assert read is not None
        assert read["folder"] == "a/b/c"

    def test_list_notes_includes_folder_notes(self):
        write_note("list-folder/n1", "n1")
        write_note("list-folder/n2", "n2")
        notes = list_notes()
        names = [n["name"] for n in notes]
        assert "list-folder/n1" in names
        assert "list-folder/n2" in names

    def test_get_all_folders(self):
        write_note("folders-test/x", "x")
        write_note("folders-test/sub/y", "y")
        folders = get_all_folders()
        assert "folders-test" in folders
        assert "folders-test/sub" in folders

    def test_delete_cleans_folders(self):
        write_note("delete-test/sub/deep/note", "content")
        assert note_exists("delete-test/sub/deep/note")
        delete_note("delete-test/sub/deep/note")
        assert not note_exists("delete-test/sub/deep/note")
        assert not os.path.exists("/tmp/vault-test/delete-test/sub/deep")
        assert os.path.exists("/tmp/vault-test")

    def test_delete_only_empties_empty_dirs(self):
        write_note("sibling-test/a", "a")
        write_note("sibling-test/sub/b", "b")
        assert note_exists("sibling-test/a")
        delete_note("sibling-test/a")
        assert os.path.exists("/tmp/vault-test/sibling-test")
        assert os.path.exists("/tmp/vault-test/sibling-test/sub")
