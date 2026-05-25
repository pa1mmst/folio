import os
import re
from datetime import datetime, timezone

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\](?!\])")
TAG_RE = re.compile(r"(?<!\w)#([a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9_\-/]*)")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def vault_dir():
    return os.environ.get("VAULT_DIR") or os.path.join(os.path.dirname(__file__), "vault")


def ensure_vault_dir():
    os.makedirs(vault_dir(), exist_ok=True)


def get_note_path(name):
    safe = name.replace("..", "").strip("/")
    if not safe:
        safe = "untitled"
    return os.path.join(vault_dir(), f"{safe}.md")


def get_folder(name):
    if "/" in name:
        return name.rsplit("/", 1)[0]
    return ""


def _remove_empty_parents(dir_path):
    vd = vault_dir()
    while dir_path and os.path.isdir(dir_path) and dir_path != vd:
        if not os.listdir(dir_path):
            try:
                os.rmdir(dir_path)
            except OSError:
                break
            dir_path = os.path.dirname(dir_path)
        else:
            break


def note_exists(name):
    return os.path.exists(get_note_path(name))


def read_note(name):
    path = get_note_path(name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    stat = os.stat(path)
    return {
        "name": name,
        "folder": get_folder(name),
        "content": content,
        "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
        "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def write_note(name, content):
    ensure_vault_dir()
    path = get_note_path(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existed = os.path.exists(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    stat = os.stat(path)
    return {
        "name": name,
        "folder": get_folder(name),
        "content": content,
        "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat() if existed else datetime.now(tz=timezone.utc).isoformat(),
        "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def delete_note(name):
    path = get_note_path(name)
    if os.path.exists(path):
        os.remove(path)
        _remove_empty_parents(os.path.dirname(path))
        return True
    return False


def list_notes():
    ensure_vault_dir()
    notes = []
    vd = vault_dir()
    for root, dirs, files in os.walk(vd):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, f), vd)
                name = rel_path[:-3]
                note = read_note(name)
                if note:
                    notes.append(note)
    return notes


def get_all_folders():
    folders = set()
    vd = vault_dir()
    for root, dirs, files in os.walk(vd):
        for f in files:
            if f.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, f), vd)
                name = rel_path[:-3]
                folder = get_folder(name)
                if folder:
                    folders.add(folder)
    return sorted(folders)


def parse_tags(content):
    return list(set(TAG_RE.findall(content)))


def parse_wikilinks(content):
    return list(set(WIKILINK_RE.findall(content)))


def strip_frontmatter(content):
    m = FRONTMATTER_RE.match(content)
    if m:
        return content[m.end():]
    return content
