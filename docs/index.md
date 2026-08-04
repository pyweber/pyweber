# Pyweber Documentation

Pyweber is a Python web framework for **reactive** applications: you manipulate HTML elements in Python, and the browser updates in real time over WebSocket — without writing JavaScript for every interaction.

[![PyPI](https://img.shields.io/pypi/v/pyweber.svg)](https://pypi.org/project/pyweber/) [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

!!! danger "Use a supported release"
    **≤ 1.3.1 is not recommended** (security). Prefer `pip install -U 'pyweber>=1.5'`. See [Supported versions](guides/supported-versions.md).

## Start here

New to Pyweber? Follow this path:

1. **[Installation](installation.md)** — install, create a project, run the dev server
2. **[Element model](guides/element-model.md)** — how `childs`, `content`, and `{{placeholders}}` work *(read this early — it prevents most template bugs)*
3. **[Templates](ui/template.md)** — pages from HTML files or strings
4. **[Reactivity](guides/reactivity.md)** — event handlers and `e.update()`
5. **[Routing](guides/routing-advanced.md)** — URLs, path params, query params

## Guides

Practical topics not covered in the API reference:

| Guide | Topics |
|-------|--------|
| [Element model](guides/element-model.md) | Child order, placeholders, HTML vs Python |
| [Reactivity](guides/reactivity.md) | `e.update()`, sessions, TemplateDiff, **Template Handoff** |
| [Components](guides/components.md) | Inputs, forms, icons |
| [File streaming](guides/file-streaming.md) | Large uploads via WebSocket |
| [Routing advanced](guides/routing-advanced.md) | Query params, **multi-method routes**, 405, OpenAPI |
| [Authentication](guides/authentication.md) | Login cookie, RBAC, SQLAlchemy User example *(Added in 1.5)* |
| [Database](guides/database.md) | Optional SQLAlchemy 2 + Alembic (`pyweber[db]`) *(Added in 1.6)* |
| [Session backends](guides/session-backends.md) | Memory / Redis for multi-replica WS *(Added in 1.6)* |
| [Deployment](guides/deployment.md) | ASGI, HTTPS, production |
| [Supported versions](guides/supported-versions.md) | Security policy; yank ≤1.3.1 |
| [Deprecations](guides/deprecations.md) | What leaves in **2.0** |

## Quick example

```python
import pyweber as pw

class Counter(pw.Element):
    def __init__(self):
        super().__init__(tag='div', classes=['counter'])
        self.childs = [
            pw.Element('span', id='count', content='0'),
            pw.Element(
                'button',
                content='+1',
                events=pw.TemplateEvents(onclick=self.increment),
            ),
        ]

    async def increment(self, e: pw.EventHandler):
        el = e.template.querySelector('#count')
        el.content = str(int(el.content) + 1)
        e.update()

app = pw.Pyweber()

@app.route('/')
def home():
    return Counter()

if __name__ == '__main__':
    app.run(reload=True)
```

```bash
pip install pyweber
python main.py
# or: pyweber run --reload
```

## Reference

- **[Pyweber application](core/pyweber.md)** — app class, middleware, static files
- **[Elements](ui/element.md)** — DOM API, classes, styles, cloning
- **[Events](interaction/events.md)** — EventHandler, event types
- **[Routes](routing/route.md)** — Route class details
- **[CLI](cli.md)** — command-line tools
- **[Changelog](changelog.md)** — release notes (human-readable)

## What makes Pyweber different?

| Feature | Pyweber | Typical Python frameworks |
|---------|---------|---------------------------|
| Live UI updates | WebSocket diffs | Full page reload or separate SPA |
| DOM API | Python `Element` tree | Jinja/HTML + JavaScript |
| Forms | Reactive `Input*` components | Manual HTML |
| API docs | Auto OpenAPI at `/docs` | Manual or add-on |

## Get help

- [GitHub Issues](https://github.com/pyweber/pyweber/issues)
- [Examples repository](https://github.com/pyweber-examples)
- [YouTube — DevPythonMZ](https://youtube.com/@devpythonMZ)

## Contributing

See [CONTRIBUTING.md](https://github.com/pyweber/pyweber/blob/master/CONTRIBUTING.md) on GitHub. Documentation source lives in the `docs/` folder of the repository.
