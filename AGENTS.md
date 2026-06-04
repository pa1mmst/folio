# AGENTS.md — Folio

## Commit Convention (ОБЯЗАТЕЛЬНО)

Все коммиты ДОЛЖНЫ следовать Conventional Commits:

```
<type>: <краткое описание ЧТО изменилось>
```

### Типы и их эффект на версию:

| Тип | Бамп | Пример |
|-----|------|--------|
| `feat:` | MINOR (0.X.0) | `feat: add backlinks panel` |
| `fix:` | PATCH (0.0.X) | `fix: editor JS syntax error` |
| `perf:` | PATCH (0.0.X) | `perf: lazy load attachments` |
| `chore:` | без бампа | `chore: update dependencies` |
| `docs:` | без бампа | `docs: update README` |
| `refactor:` | без бампа | `refactor: extract helper` |
| `test:` | без бампа | `test: add editor tests` |
| `style:` | без бампа | `style: format CSS` |
| `feat!:` или `BREAKING CHANGE:` в теле | MAJOR (X.0.0) | `feat!: redesign API` |

### Правила:
- Заголовок — на английском, в повелительном наклонении, без точки в конце
- Длина заголовка — до 72 символов
- НЕ использовать `[OpenCode]` или другие префиксы в коммитах
- НЕ писать `FIX:`, `FEAT:` и т.д. капсом — только строчные `fix:`, `feat:`
- Мёрж-коммиты автоматически генерируются — не нужно их делать руками

### Примеры правильных коммитов:
```
feat: add folder tree in sidebar
fix: photos from other notes appear in editor
refactor: extract note rendering to function
chore: add pyproject.toml for semantic-release
```

### Примеры НЕПРАВИЛЬНЫХ коммитов:
```
[OpenCode] Fix: something        ← префикс [OpenCode] запрещён
FIX: something                   ← капс запрещён
some random message              ← нет типа
WIP                              ← нет типа и описания
```
