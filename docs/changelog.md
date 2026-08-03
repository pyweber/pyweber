# Changelog

This page summarizes recent releases in plain language. For the full history, see [CHANGELOG.md on GitHub](https://github.com/pyweber/pyweber/blob/master/CHANGELOG.md).

---

## 1.5.3 — Unreleased

### New

- **Optional ORM** — `pyweber[db]`: SQLAlchemy 2 async (`db` / `Model`), Alembic via `pyweber db …` ([guide](guides/database.md))
- **Session backends** — memory (default) or Redis (`pyweber[redis]`) for multi-replica WS ([guide](guides/session-backends.md))
- **Services refactor** — static/response/template/OpenAPI collaborators under `pyweber.services`
- **Window timers / rAF** — `set_timeout`, `set_interval`, `request_animation_frame` (and clear/cancel)

### Changed

- Static routes resolve in **O(1)**; static paths win over dynamic for the same URL

## 1.5.2 — Unreleased

### Fixed

- **Inline `<script>` / `<style>`** — bodies are no longer HTML-escaped when `sanitize=True` (JS/CSS in head/body stay valid). Other tags still escape by default.

## 1.5.0.dev3 — Unreleased

### New

- **Deprecation policy** — warnings for APIs removed in **2.0** ([guide](guides/deprecations.md))
- **Onion middleware** — `@app.middleware` with `(request, call_next)`
- **Flask-style hooks** — `@app.before_request` / `@app.after_request`, plus `add_before_request` / `add_after_request`
- **`pyweber.auth`** — `@login_required`, password hashing, signed login cookie, lightweight **RBAC** (`register_roles`, `@permission_required`) ([guide](guides/authentication.md))
- **Easier `Response`** — `Response.json(...)`, `.text()`, `.html()`, and `content=` / `status=` without wiring every route argument
- **`TestClient`** — in-process HTTP testing (`pyweber.testing`)
- **Ops** — optional rate limit (429), ETag/304 for static files, gzip, upload MIME validation
- **Configurable CSP** — `PYWEBER_CSP` or `[security].csp` (`off` disables the header)
- Redesigned default **404 / 401 / 500** pages

### Changed

- Route params (`int` / `float` / `bool`) are coerced; bad values → **400**
- Docs/OpenAPI auto-disabled in production unless `expose_in_production=True`
- **`WWW-Authenticate` only when you ask** — not on every 401; schemes / `headers=` set it explicitly
- CORS works correctly under uvicorn (header filtering, OPTIONS preflight when origins are whitelisted)
- **Default CSP allows HTTPS CDNs** (Bootstrap, Google Fonts, jsDelivr) — the old `'self'`-only policy blocked remote CSS
- **`include_uuid=False`** means static HTML: no WS script, no handoff (reactivity needs `include_uuid=True`)

### Fixed

- Landing pages with CDN CSS no longer lose Bootstrap/Fonts because of CSP
- **Form POSTs with `Content-Type: …; charset=UTF-8`** — body/`_csrf` parse correctly (`request.media_type`)
- Static pages no longer get a reactive WS client that rewrites the document and breaks layout
- Client never does `document.documentElement.innerHTML = …` on root diffs
- OpenAPI `int | None` on Python 3.10 (`types.UnionType`)
- `safe_join` rejects absolute / drive escapes on Linux

### Upgrade tips (1.5)

| Topic | Action |
|-------|--------|
| Marketing / static HTML | `Template(..., include_uuid=False)` |
| Tighten CSP | `PYWEBER_CSP=...` or `[security] csp = '...'` |
| After upgrade | Restart the server so new response headers load |
| Middleware | Prefer `@app.middleware(request, call_next)` for cross-cutting work |

---

## 1.4.0.dev0 — Unreleased

### Security (breaking)

- **CORS closed by default** — whitelist via `allowed_origins` / `PYWEBER_ALLOWED_ORIGINS`
- **HTML auto-escape on** (`sanitize=True`); use `sanitize=False` only for trusted markup
- **CSRF** on POST/PUT/PATCH/DELETE (disable with `csrf_enabled = false`)
- Signed WebSocket session cookie; path traversal jail; production 500s hide details
- Security headers + configurable `max_body_size` (413 when exceeded)
- `secure_filename()` for uploads

### New

- OpenAPI 3.0 overhaul, security schemes (`HTTPBearer`, `HTTPBasic`, API keys), runtime enforcement
- Pluggable HTML parser (stdlib by default; `pyweber[fast-html]` for lxml)
- Same path, different HTTP methods without overlapping verbs

### Fixed

- String / postponed OpenAPI annotations no longer crash schema generation
- OpenAPI paths include group prefix (`full_route`)

### Upgrade tips (1.4)

| Topic | Action |
|-------|--------|
| Secret | Set a real `session.secret_key` / `PYWEBER_SECRET_KEY` |
| CORS | List browser origins in `allowed_origins` |
| Forms | `Form(method='POST')` gets `_csrf` automatically |
| Raw HTML | `sanitize=False` or build Element trees |

---

## 1.3.0 — June 2026

### New

- **Template Handoff** — reactive pages register the HTTP-rendered template under a one-time token; WebSocket connect reuses it instead of re-running the route handler ([guide](guides/reactivity.md#template-handoff-http--websocket))
- **`allowed_methods` on responses** — HTTP **405** responses include an accurate `Allow` header for the route

### Changed

- **Route visit tracking** — recursion detection is scoped per HTTP request (ContextVar), not shared across the app instance
- **WebSocket open payload** — first connect sends `handoffToken`; later events omit full-page HTML (smaller messages)

### Fixed

- **False `RecursionError`** between sequential requests to the same route or redirect
- **Wrong status for disallowed methods** — unsupported verb on an existing path returns **405**, not **404**
- **Multi-method routes** — one route per path with `methods=['GET', 'POST', 'DELETE']`; use `update_route()` to add verbs (duplicate path registration still raises `RouteAlreadyExistError`)
- Request / cookie isolation between concurrent clients (`ContextVar`)
- Dev reload noise from static assets; offline startup when no network (`get_local_ip` fallback)
- Element child order when mixing `childs`, `content`, and `{{placeholders}}`

---

## 1.2.0 — March 2026

### New

- **Query parameters in routes** — `/login?session={session}` injects query values into handlers ([guide](guides/routing-advanced.md))
- **File streaming** — `app.stream()` for large uploads without blocking the server ([guide](guides/file-streaming.md))
- **Static directories** — restrict static file serving to declared folders via `Pyweber('static')` or `app.static(...)`
- **Child navigation** — `first_child`, `last_child`, `next_child`, `previous_child`, `index`
- **`include_uuid`** — hide internal UUIDs when exporting HTML
- **Mobile QR code** — optional QR when starting the dev server from CLI
- **OpenAPI** — multipart and octet-stream support for API testing

### Changed

- Static files only served from registered asset directories
- `Response.code` removed — use `status_code`

### Fixed

- Recursion error when running under Uvicorn
- CLI `--route` and config `route` ignored on startup
- `None` values on file inputs
- Query params no longer treated as path params in Swagger

---

## 1.1.x — February 2026

### New

- **`e.target` and `e.current_target`** — clearer event targeting (`e.element` deprecated)
- **Input selection API** — `selection_start`, `selection_end`, `focus`, `blur`, `select`, `click`, `scroll_into_view`
- WebSocket port auto-detection (same host/port as HTTP)

### Changed

- **License** — MIT → **Apache License 2.0** (Pyweber Technology)

### Fixed

- Dynamic value rendering in elements
- LocalStorage sync issues
- WebSocket handshake on deployed sites

---

## 1.0.x — Late 2025

### New

- **Template cache** — stable element UUIDs per route/method
- **Unified WebSocket manager** — HTTP and WS on same address
- **Hot reload** for Python modules with project-aware module filtering
- **`getElement` / `getElements`** — replace deprecated `getElementById`, `getElementByClass`, `getElementByUUID`
- **OpenAPI / Swagger** at `/docs`
- **TemplateDiff** — incremental DOM updates over WebSocket
- **Form components** — `InputText`, `InputFile`, `TextArea`, etc.

---

## Documentation updates (2026)

Recent doc improvements (this site):

- [Deprecations](guides/deprecations.md) — SemVer policy through 2.0
- [Environment](environment.md) — `PYWEBER_CSP`, CORS, CSRF, secrets
- [Template Handoff](guides/reactivity.md#template-handoff-http--websocket) — HTTP→WebSocket without re-running handlers
- [Multi-method routing](guides/routing-advanced.md#multiple-http-methods-on-one-path) — GET/POST/DELETE on a single route, 405 behaviour
- [Element model guide](guides/element-model.md) — `childs`, `content`, and `{{placeholders}}`
- [Reactivity guide](guides/reactivity.md) — `e.update()` and sessions
- [Components](guides/components.md) and [file streaming](guides/file-streaming.md)
- [Deployment](guides/deployment.md) — ASGI and production checklist
- Corrected placeholder syntax (`{{uuid}}`, not `{uuid}`)
- Removed references to deprecated element lookup methods

---

## Upgrade tips

| From | Action |
|------|--------|
| `< 1.5` | Restart after upgrade (CSP headers); use `include_uuid=False` for static landings; see tips above |
| `< 1.4` | Set `secret_key`, configure CORS whitelist, expect CSRF on mutating forms |
| `< 1.3.0` | List every HTTP verb on one `@app.route(..., methods=[...])`; use `update_route()` instead of a second route on the same path |
| `< 1.3.0` | No app changes needed for Template Handoff — enabled automatically on reactive HTML pages |
| `< 1.2.0` | Replace `Response.code` with `status_code` |
| `< 1.1.0` | Prefer `e.target` over `e.element` |
| `< 1.0.2` | Use `getElement(by=GetBy.ID, value='...')` instead of `getElementById` |
| Any | Register static dirs with `app.static()` after 1.2.0 |
