# Changelog

This page summarizes recent releases in plain language. For the full history, see [CHANGELOG.md on GitHub](https://github.com/pyweber/pyweber/blob/master/CHANGELOG.md).

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
| `< 1.3.0` | List every HTTP verb on one `@app.route(..., methods=[...])`; use `update_route()` instead of a second route on the same path |
| `< 1.3.0` | No app changes needed for Template Handoff — enabled automatically on reactive HTML pages |
| `< 1.2.0` | Replace `Response.code` with `status_code` |
| `< 1.1.0` | Prefer `e.target` over `e.element` |
| `< 1.0.2` | Use `getElement(by=GetBy.ID, value='...')` instead of `getElementById` |
| Any | Register static dirs with `app.static()` after 1.2.0 |
