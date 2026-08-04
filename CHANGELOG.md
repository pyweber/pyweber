# PyWeber Changelog

## [1.6.0] - Unreleased

### Added

- **`pyweber.db`** (extra `pyweber[db]`) — async SQLAlchemy 2 wrapper (`db`, `Model`, `db.session()`), config/`PYWEBER_DATABASE_URL`, driver extras (`db-sqlite`, `db-pg`, `db-mysql`, `db-mssql`). CLI: `pyweber db init|revision|migrate|upgrade|downgrade` (`migrate` = apply all pending / `upgrade head`). See [docs/guides/database.md](docs/guides/database.md).
- **`pyweber.session_store`** — `SessionStore` protocol, `MemorySessionStore` (default), `RedisSessionStore` (`pyweber[redis]`), `session.backend` / `PYWEBER_REDIS_URL`. See [docs/guides/session-backends.md](docs/guides/session-backends.md).
- **`pyweber.services`** collaborators — `StaticFilesService`, `ResponsePipeline`, `TemplateService`, `OpenAPISetup`. `Pyweber` keeps the flat public API (`app.route`, `app.set_cookie`, …) via mixins, but CSRF/gzip/ETag/static/OpenAPI logic lives in composed services.
- **`Window.set_timeout` / `set_interval` / `clear_*` / `request_animation_frame` / `cancel_animation_frame`** — aligned with the existing WebSocket protocol in `static/js.js`. Timer responses no longer steal the confirm/prompt Future.
- Declarative HTML inputs — shared `_EXTRA_ATTRS` / `_sync_attrs` on `Input`; text-like and date/time families share internal bases (public class names unchanged).
- **Safe redirects** (`1.6.0.dev2`) — `Window.open` / `to_url` / `launch_url` allow relative `/…` or hosts in `allowed_redirect_hosts` / `PYWEBER_ALLOWED_REDIRECT_HOSTS`.

### Changed

- **Routing** — static paths resolve in **O(1)** via exact dict lookup; only `{param}` patterns are scanned. Static paths win over dynamic patterns for the same URL (e.g. `/users/me` before `/users/{id}`).
- **`Window.scroll_by`** sends a true `scroll_by` payload (delta), matching the client handler.
- Default `[database]` / `session.backend` keys in shipped `config.toml` for optional persistence.
- **WS DOM sync** — client outerHTML is **merged by uuid** into the existing Python tree (no wholesale `parse_html` replace). Handoff **moves** the same `Template` instance into the session. `Element`/`Template.clone` preserve subclass type; route `Element`s are adopted without HTML round-trip. Bound handlers can use `self` after the first render. See [docs/guides/reactivity.md](docs/guides/reactivity.md).
- Docs: **Added in X.Y** tips on feature pages; expanded [deprecations](docs/guides/deprecations.md); [supported versions](docs/guides/supported-versions.md) marks **≤1.3.1** as not recommended (PyPI **yank** for install warnings — not expressible in `pyproject.toml`).
- **EventBook lifecycle** (`1.6.0.dev2`) — cleanup by element uuid when a session is removed.
- **WS `close`/`send`** (`1.6.0.dev2`) — no discarded coroutines from `remove_connection` / `send_all`.
- **`wsMessage.template`** (`1.6.0.dev2`) — lazy `ensure_template()` (no un-awaited coroutine in `__init__`).
- **`JWTAlgorithms`** (`1.6.0.dev2`) — public import warns; enum-only until **2.0**.

### Fixed

- Duplicate `InputCheckbox` export in `components.__all__` / package `__all__`.
- **`self` orphaned after WS connect** — session tree no longer replaced by a fresh parse; subclass refs (`self.label`, etc.) stay live.
- **Reactive WS events** (`1.6.0.dev3`) — end-to-end fixes so clicks/`e.update()` work again:
  - **`Form`/`Input` `Element.clone`** — subclass `attrs` setters no longer abort clone (empty diffs / lost handlers).
  - **`Template.clone`** — bound methods (`self.handler`) and Element refs (`self.page_title`) rebind onto the clone so `clone_template` / reconnect still mutate the live tree.
  - **Document event dispatch** — call the callable on `element.events` (EventBook id lookup never matched callables).
  - **`process_ws_message_handler`** — no longer drop clicks/`handoff` when `template` is null and the session is not yet registered; require the JS key contract instead of an inverted allowlist.
  - **WSGI consumer** — `async for` on `WebsocketServer` plus a single long-lived handler task (sync `for` exited after the first drain).
  - **Session bind before template sync** — reuse `ws_server.id` / cookie so a second frame with `sessionId: null` does not mint another session + `setSessionId` (UUID mismatch → handlers never found).
  - **Form `values` on clicks** — `insert_values` always runs when the payload has `values`, even with `template: null` (input text was ignored before `e.update()`).
  - **`e.update()` from sync handlers** — schedule `send_message` on the WS event loop via `run_coroutine_threadsafe` (ThreadPoolExecutor had no running loop).
  - **Client `setSessionId`** — always accept the server id; apply it before flushing buffered window events.
  - **JS-injected DOM** — debounced `MutationObserver` + `window.__pyweber_adopt(el)` / `__pyweber_resyncDom()` stamp uuids and `merge_client_dom` grafts into the session; disable with `<meta name="pyweber-dom-watch" content="off">`.

### Removed

- **`Element.update()`** stub (`1.6.0.dev2`) — use `e.update()`; surgical per-element WS push remains out of scope.

## [1.5.2] - Unreleased

### Fixed

- **`<script>` / `<style>` bodies are not HTML-escaped** under `sanitize=True`. Escaping turned `>`/`&`/`<` into entities and broke inline JS/CSS in `<head>` and `<body>` (e.g. `if (n > 0)` → `if (n &gt; 0)`). Attribute values on those tags are still escaped. Other elements keep default XSS escaping.

## [1.5.1] - Unreleased

### Added

- **Deprecation framework** (`pyweber.utils.deprecation`) — one-shot `DeprecationWarning`s; removals targeted at **2.0**. See [deprecations guide](docs/guides/deprecations.md).
- **Onion middleware**: `@app.middleware` with `(request, call_next)`.
- **Flask-style hooks**: `@app.before_request` / `@app.after_request` (with or without `()`), plus `add_before_request` / `add_after_request`. Legacy `status_code=` / `process_response=` on those decorators are deprecated until **2.0**.
- **`Response.json` / `.text` / `.html`** and ergonomic constructor (`content=`, `status=`, optional `request` / `headers=`). Legacy aliases `response_content` / `code` / `response_type` still work.
- **`pyweber.testing.TestClient`** — in-process HTTP client (`get`/`post`/…, cookies, CSRF helpers).
- **Rate limiting** (opt-in): `[security] rate_limit_enabled` / `rate_limit_rpm` (or env). Returns **429** + `Retry-After`.
- **ETag / 304** for static assets; **gzip** compression when `Accept-Encoding: gzip` (configurable).
- **Upload MIME sniffing**: `File.validate()` / `pyweber.utils.mime.validate_upload`.
- Preferred module `pyweber.models.stream_stats` (re-exports `strem_stats`).
- `Icons` moved to `pyweber.utils.icons` (still importable from `types` with a deprecation warning).
- Redesigned default **404 / 401 / 500** error pages (shared visual language).
- Configurable **Content-Security-Policy** via `PYWEBER_CSP` or `[security].csp` (`off` / `false` / `none` omits the header).
- **`pyweber.auth`** — `@login_required`, `login_user` / `logout_user` / `current_user`, `hash_password` / `check_password` (PBKDF2). See [authentication guide](docs/guides/authentication.md).
- **RBAC** — `register_roles` / `define_role`, `@permission_required` / `@role_required`, `permissions=` / `roles_all=` on `@login_required`, helpers `has_role` / `has_permission` / `user_permissions` (wildcards `*` / `ns:*`).
- `OpenAPIConfig.docs_security` — optional security schemes on `/docs` and OpenAPI routes.
- Opt-in upload MIME sniffing: `PYWEBER_VALIDATE_UPLOADS` / `[security] validate_uploads`.

### Changed

- Route path parameters annotated as `int`/`float`/`bool` are **coerced** at runtime (bad values → **400**).
- `update_route` only sets known `Route` attributes; unknown keys merge into `route.kwargs`.
- `/docs` and `/openapi.json` are **auto-disabled in production** unless `OpenAPIConfig(expose_in_production=True)`.
- Typo fixes with aliases: `DoubleFormat` (`DoubleFormnat` deprecated), `normalize_path` (`normaize_path`), `CreateApp` (`CreatApp`), `toggle_class` (`toogle_class`).
- **`WWW-Authenticate` is no longer auto-added on every 401.** Set it via `Response(..., headers=...)` / `set_header`, or let OpenAPI schemes (`HTTPBasic` / `HTTPBearer`) attach it when that scheme rejects the request. HTML `Accept` may serve `page_unauthorized` instead of JSON `{detail}`.
- **CORS on uvicorn/ASGI**: internal bookkeeping headers stripped from the wire; `Access-Control-Request-Headers` lookup is case-insensitive; whitelisted `OPTIONS` preflight returns **204** with CORS headers early.
- **Default CSP is CDN-friendly**: `style-src` / `script-src` / `font-src` / `img-src` include `https:` so Bootstrap, Google Fonts, jsDelivr, etc. load. The previous `'self'`-only policy blocked remote stylesheets and broke layouts that depend on CDNs.
- **`include_uuid=False` is a clear static contract**: no reactive WS script injection, no handoff token. Apps that need reactivity keep `include_uuid=True`.

### Fixed

- **`Content-Type: …; charset=UTF-8`** — request body sniffing uses `Request.media_type` / `is_media()` (strips parameters). Without this, form POSTs from browsers miss `_csrf` and look like CSRF failures.
- **Layout break with CDN CSS** — CSP no longer refuses stylesheets from `cdn.jsdelivr.net` / `fonts.googleapis.com` by default.
- **Static pages + WebSocket** — with `include_uuid=False`, the WS client is not injected; handoff is skipped; client `outerHTML` with invented UUIDs does not overwrite the server template.
- **Client DOM safety** — `applyDifferences` never rewrites `document.documentElement.innerHTML` (that destroyed CSS/Bootstrap). Missing UUID targets are ignored; `stampMissingUuids` only runs when stable UUIDs already exist on the page.
- **OpenAPI `int | None` on Python 3.10** — `schema_for_type` / `annotation_type_name` handle `types.UnionType` (PEP 604), not only `typing.Union`.
- **`safe_join`** — absolute / drive / UNC path segments are rejected (`None`) instead of being stripped and joined under the base (Linux path-escape false negatives).

### Notes for upgraders (1.5)

- Landing / marketing pages: use `Template(..., include_uuid=False)` when you do not need reactivity.
- If you self-host all assets, tighten CSP: `PYWEBER_CSP="default-src 'self'; …"` or set `csp` under `[security]`.
- Restart the app process after upgrading so response headers (CSP) are reloaded from the new package.
- Prefer `@app.middleware(request, call_next)` for cross-cutting concerns; Flask-style before/after remain supported.

## [1.4.0.dev0] - Unreleased

### Security (breaking)

- **CORS is closed by default.** Responses no longer reflect arbitrary `Origin` with credentials. Configure `security.allowed_origins` (or `PYWEBER_ALLOWED_ORIGINS`) to opt in.
- **HTML auto-escape is on by default** (`sanitize=True` on `Element`). Attribute values, content, id/class/style are escaped via `html.escape` at serialize time. Pass `sanitize=False` only for trusted markup.
- **CSRF protection** for POST/PUT/PATCH/DELETE (double-submit cookie + `X-CSRF-Token` / `_csrf`). Disable with `security.csrf_enabled = false` or `PYWEBER_CSRF_ENABLED=false`. Framework routes under `/_pyweber/` are exempt.
- **`get_csrf_token()`** — returns the token that matches cookie `pyweber_csrf`; `Form(method='POST')` uses it for the hidden `_csrf` field (avoids minting a mismatched token).
- **WebSocket sessions** bind to signed HttpOnly cookie `pyweber_sid` (HMAC with `session.secret_key`). Client-supplied `sessionId` alone is no longer trusted.
- **Static file path traversal** blocked via `realpath`/`commonpath` jail under registered static roots.
- **Production 500 pages** hide exception details when `session.env` / `PYWEBER_ENV` is `production`/`prod`.
- Default **security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy` (HSTS when HTTPS enabled).
- Configurable **`security.max_body_size`** (default 10 MiB); oversized bodies get HTTP 413.
- Upload filenames are sanitized with **`secure_filename()`** (also exported publicly).

### Changed

- **HTML parser is now pluggable.** Default backend is the stdlib `html.parser` (pure Python, Vercel/serverless friendly). `lxml` is no longer a required dependency.
- Optional extra: `pip install 'pyweber[fast-html]'` to enable the `lxml` backend.
- Select backend with `set_html_parser_backend('stdlib'|'lxml')` or env `PYWEBER_HTML_PARSER=stdlib|lxml`.
- **Same path, different HTTP methods** — you can register separate handlers for the same path when methods do not overlap (e.g. `@app.route('/x', methods=['GET'])` and `@app.route('/x', methods=['POST'])`). Overlapping methods still raise `RouteAlreadyExistError`.
- **OpenAPI 3.0 overhaul** — `OpenAPIConfig`, live `/openapi.json`, typed responses / `response_model`, tags, description, `operationId`, `components.schemas` (`$ref`), security schemes in Swagger, and optional disabling of `/docs`.
- Minimum test coverage gate raised to **87.5%**.

### Added

- Security helpers: `HTTPBearer`, `HTTPBasic`, `APIKeyHeader`, `APIKeyQuery`, `APIKeyCookie`.
- Runtime **security enforcement** for schemes declared on routes / global config (`request.auth`, 401/403).
- Route OpenAPI fields: `tags`, `description`, `responses`, `response_model`, `security`, `deprecated`, `include_in_schema`, `operation_id`.
- Config section `[security]` (`allowed_origins`, `max_body_size`, `csrf_enabled`).
- Public helpers: `secure_filename`, `safe_join`, `sign_value`, `unsign_value`, `generate_csrf_token`.

### Fixed

- **OpenAPI / Swagger** — string and postponed annotations (`"str"`, `"int | None"`, `from __future__ import annotations`, common AI-generated type strings) no longer crash schema generation (`'str' object has no attribute '__name__'`).
- OpenAPI paths now use `full_route` (group prefix included).
- Duplicate `update_app_template` definition removed from `WebsocketManager`.

### Notes for upgraders

- Set a real `session.secret_key` (or `PYWEBER_SECRET_KEY`); the placeholder `TOKEN_HEX` is rejected in production.
- Apps that inject raw HTML must use `sanitize=False` or build Element trees.
- Cross-origin browser clients need `allowed_origins` configured.
- POST forms built with `Form(method='POST')` receive an automatic `_csrf` hidden field.
- If you relied on `lxml` being installed transitively via Pyweber, install `pyweber[fast-html]` (or `lxml` yourself) and set `PYWEBER_HTML_PARSER=lxml`.
- Duplicate registration of the **same** path + method still raises `RouteAlreadyExistError`; different methods on the same path are allowed.
- Swagger UI loads `/openapi.json` (pinned `swagger-ui-dist@5.17.14`). Set `OpenAPIConfig(docs_url=None, openapi_url=None)` to disable docs in production.
- Global `security=` on `OpenAPIConfig` applies to all routes unless a route sets `security=[]` (public) or its own schemes.
- `HTTPStatusCode.FORBIDDEN` is corrected to **403** (was wrongly 402); `PAYMENT_REQUIRED` (402) was added.

## [1.3.0] - 2026-06-09

### Added

- **Template Handoff** — on reactive HTML responses, Pyweber stores the rendered template under a one-time token and injects `<meta name="pyweber-handoff" content="...">` in the page. When the browser opens WebSocket, it sends `handoffToken` so the server reuses the HTTP template instead of calling `clone_template()` (which re-executes the route handler). See [reactivity guide](docs/guides/reactivity.md#template-handoff-http--websocket).
- **`TemplateResult.allowed_methods`** — populated on 405 responses; `Response` sets the `Allow` header from this list.

### Changed

- **Per-request route visit tracking** — `_check_recursion()` uses a `ContextVar` set in `get_response()` instead of a shared set on the `Pyweber` instance.
- **WebSocket client** — `js.js` sends `handoffToken` on connect; event payloads keep `template: null` after the first message (smaller frames).

### Fixed

- **False `RecursionError`** when two requests hit the same route or redirect in sequence.
- **405 vs 404** — HTTP method not in `route.methods` returns **405 Method Not Allowed** with `Allow: GET, POST, ...` instead of 404.
- **Request context isolation** — `Request` and cookies use `ContextVar`; fixes cross-request leakage and `request=None` in handlers after install.
- **Element ordering** — correct HTML order when combining `childs`, `content`, and `{{placeholders}}`.
- **Dev reload** — static file changes no longer cascade full server reload; Python/config changes still reload the app.
- **Offline startup** — `get_local_ip()` no longer blocks when the network is unavailable.
- **WebSocket session bootstrap** — accepts first message without full template when session already exists.

### Notes for upgraders

- You **can** register two routes on the same path with different methods (as of 1.4.0). Overlapping methods still raise `RouteAlreadyExistError`. You may also use one route with `methods=['GET', 'POST', 'DELETE']` or `app.update_route('/path', methods=[...])`.
- `clone_template()` remains as a fallback when handoff token is missing or expired (5 minute TTL, single use).

## [1.2.0] - 2026-03-06

### Added
- Element has new methods to get childs. We added this methods: `next_childs`, `previous_childs`, `index`, `last_child`, `first_child`
- Added support for `multipart/form-data` and `application/octet-stream` in swegger documentation for API tests purpose
- Added `include_uuid` attribute to include or ignore uuid when converting pyweber Element to Html tree.
- Added `mobile` argument in `run` and `Pywber CLI` if need include QrCode when starting run project
- Added suport to query parameters in pywber routes.
- Added support to create routes with query_parameters. Now you can create route with query parameters and placeholder to user as attributes in template handler.
```python
import pyweber as pw
app = pw.Pyweber()

@app.route('/login?session={session}')
def login(session: str):
  pass
```
- Added support to stream files withou blocking server using websocket server protocol do request chunks and http server to receive chunks.
```python
import pyweber as pw
import asyncio

app = pw.Pyweber()

class Form(pw.Element):
    def __init__(self):
        super().__init__(tag='div', classes=['container'])
        self.childs = [
            pw.InputFile(name='files', accept='*/*', multiple=True),
            pw.InputButton(name='submit', onclick=self.get_file)
        ]

    async def save_file(self, e: pw.EventHandler, file: pw.File):
        chunks = app.stream(file=file,session_id=e.session.session_id,max_size=1024*1024*50)
        content = b''
        async for chunk in chunks:
            content += chunk

        if len(content) != file.size:
            raise ValueError(f'File Incomplete {len(content)}/{file.size}')

        with open(f'assets/{pw.secure_filename(file.filename)}', 'wb') as f:
            f.write(content)

    async def get_file(self, e: pw.EventHandler):
        inputs = [input_file for input_file in e.template.querySelectorAll('input') if input_file.files]

        for inpt in inputs:
            for file in inpt.files:
                asyncio.create_task(self.save_file(e, file))

@app.route('/')
def upload():
    return Form()

if __name__ == '__main__':
    app.run()
```

### Changed
- Now, only can acess assets project of directory specified when the Pyweber App is created. To specify the directory assets, you can do as show bellow:
```python
import pyweber as pw

app = Pyweber('static') # where **statict** is the static project directory
```
```python
import pyweber as pw

app = pw.Pyweber()
app.static('static')
```

You can choose more that one asset directory
```python
import pyweber as pw

app = Pyweber('assets', 'static', 'images')
```


## Fixed
- Fixed `Recursion Error` when you use uvicorn to run server.
- Fixed ignored server `route` then specify in CLI (`pyweber run --route=...`) or defined in pyweber config file.
- Fixed value as None when the input is File Type
- Fixed query parameters placeholder considered as path placeholders in swegger.

## Removed
- Removed `code` properity has been removed from the Response class. If you want to acess the integer http status_code, use `status_code` instead

## [1.1.1] - 2026-03-02

### Added
- Added new `EventData` attributes.
- Added new `Element` proprities. Now you can get `selection_start` and `selection_end` values. This properites refers to cursor position in input ou textearea's elements.
- Added new `Element` methods based in javascript methods. The new methods include `focus`, `blur`, `select`, `set_selection_range`, `remove` and `click`, `scrool_into_view`
- Added `target` and `current_target` in `EventHandler` attributes. The `target` attribute replaces the `element` attribute that will be remove in version **version 1.2.0**. The `current_target` refers to real element that has the event included while `target` referes to target that caused the event.


```python
import pyweber as pw

def get_selection_values(self, e: pw.EventHandler):
  e.target.selection_start # get where the text seleciton start
  e.target.selection_end # get where the text selection end

  text_input = e.template.querySelection("#input")

  text_input.select() # select element values
  text_input.blur() # remove focus
  text_input.set_selection_range(10,10) # select specified text section in the element value

  text_input.focus() # set focus

  text_input.remove() # remove element in your parent

  e.update()
```

### Changed

- **License** — project relicensed from MIT to **Apache License 2.0** (copyright Pyweber Technology)
- WebSocket port auto-detection (same host/port as HTTP)

### Fixed
- Fixed render dynamic values in `Element` instances.
- Fixed error for localstorage management
- Fixed error in javascript functions when it get a string variable
- Fixed error in websocket handshake deployed website

## [1.1.0] - 2026-01-23

### Added
- Added cache template to ensure that all requests with same route has same uuid to elements;
- Created new Websocket manager go manage websocket connections. Now, http and websocket servers run on same address (host and port).
- Added `preventDefaults` in javascript submit event
- Added `string type` in event_data key sending with client
- Added `Headers type` in client request
- Added TemplateView if server get Error
- Added `accept_control_request_headers` properity do get client request headers

### Changed
- Fix Route Not Found when try to acess /docs
- Changed buffer size in http request. Now it's possible receive until 254 kb of buffer data at once.
- Changed some response headers in HTTP Pyweber Response.

### Fixed
- Fix `update_all` method. Now you can share template states with other connected clients.
- Fix response with incorrect method if cache template was enable.
- Fix get incomplete message in websocket if message sended by client is long.
- Fixed github issue ([#3](https://github.com/pyweber/pyweber/issues/3)). `Component` isn't Pyweber class.

## [1.0.3] - 2025-10-27

### Changed
- Responde headers update. Now, headers has CORS enabled

### Fixed
- Fixed CLI command redirecting to Python console instead of running the project in Linux systems
- Fixed static file loading on Linux systems by improving path resolution logic

## [1.0.2] - 2025-10-26

### Added
- Added `project_modules()` helper to dynamically identify and filter all Python modules that belong to the project scope, excluding third-party or system modules.
- Introduced `project_path` property to resolve the root path of the active project, improving dynamic module resolution.
- Added `get_mime_type()` in ContentTypes to get string content types in files.
- Added the getElement and getElements methods to replace the `getElementbyClass`, `getElementbyUUID`, and `getElementbyID` methods.

### Changed
- Enhanced `reload_modules()` to reload all modules belonging to the project instead of only the changed module. This ensures dependent modules are also refreshed when a file change is detected, improving consistency during development.
- Refactored internal module reload mechanism to support smarter updates using project-aware introspection.
- Moved logic for determining the main module into a reusable method (`get_main_module()`), which ensures clean initialization of the app.
- Updated `path_to_module()` to work in conjunction with the new `project_path` abstraction.
- `getElements()` and `getElements()` in Element instance, now get Element with `attrs` or `style` only
- Removed the `getElementbyClass`, `getElementbyUUID`, and `getElementbyID` methods from the Templates instance.

### Fixed
- Prevented unnecessary reload attempts on non-project modules by validating module origin through absolute path checks.
- Fixed change template if remove class elements.
- Fixed an issue where the `queryselector` and `queryselectorAll` methods for the Element instance returned None or []

### Notes
- Modules with top-level side effects (e.g., global DB connections) will be re-executed during reload Developers should encapsulate such logic within callable functions or use lazy initialization to avoid performance or state issues.

## [1.0.0] - 2025-07-29
---
### Improvements
- Changed return if static template does not exist. Now, if static file not exist will be returned `Error Page Template`
- Added **hot reload for Python modules**. Now, changes to backend Python code automatically refresh the browser without restarting the server.

### Bug Fixes
- Solved NoneType Error when the route have no return middleware
- Solved not show title defined in route if route return Template instances.
- Solved multiple adding elements if use `e.update()` more than once.

## [0.9.98] - 2025-07-12
---
### New features
- Created loading screen, acessed adding `spinner` in Element's classes.

### Improvements
- Changed value type in `InputCheckBox` Element to Literal['on', 'off'] to str. `name` and `value` are now mandatory attribues for this Element.
- Changed pyweber official ico

## [0.9.97] - 2025-07-10
---
### New features
- **OpenAPI/Swagger Integration**: Full automatic OpenAPI 3.0 documentation generation with Swagger UI interface accessible at `/docs` endpoint
- **Multi-Type Model Support**: Automatic detection and processing of Pydantic models, dataclasses, and vanilla Python classes in route parameters
- **Smart Parameter Resolution**: Intelligent separation between path parameters and request body fields with automatic type inference
- **Dynamic Schema Generation**: Real-time OpenAPI schema creation based on function signatures and type annotations
- **Automatic Documentation**: Zero-configuration API documentation with interactive Swagger UI, including examples and validation schemas
- Added `files` attribute in `Element` instances. It is available only on `Input Elements` with type `file`
- Now you can get all files content loaded in real-time using event-handlers. Now, is not necessary post-request to get files
- Added `search_name_by_code` in HttpStatusCode instance. Now, you can get the http status_code description

### Technical Improvements
- **OpenApiProcessor Class**: New dedicated class for handling OpenAPI specification generation and type mapping
- **Enhanced Type System**: Comprehensive mapping between Python types and OpenAPI/JSON Schema types with format support
- **UUID-based Cache Busting**: Dynamic UUID generation for OpenAPI endpoint URLs to prevent caching issues
- **Flexible Model Instantiation**: Automatic object instantiation from request data regardless of model type (Pydantic, dataclass, or vanilla class)


## [0.9.96] - 2025-07-05
---
### Improvements

- Enhanced `<select>` and `<option>` support:
  - Fixed issue where `<option>` values were lost during server-client sync.
  - Options now preserve their `value` and `selected` states automatically without requiring manual `.value` assignment.
  - Defining `.value` on a `<select>` automatically sets the corresponding `<option>` as selected and removes `selected` from others.
  - `.value` getter on `<select>` returns the `value` of the selected `<option>`, or the first available one if none are explicitly selected.
  - Aligned with native HTML select behavior, reducing need for manual loops.

- Standardized `<textarea>` handling:
  - `.value` can now be used to both get and set values in `<textarea>`, while `.content` still works for initialization.
  - Calling `.value = "..."` on `<textarea>` also sets `.content`, ensuring two-way consistency.
  - `.value` getter returns `.content` for `<textarea>` elements.

- Cleaner task editing logic:
  - Editing forms now use direct `.value` assignments for `<select>`, `<textarea>`, and other fields — no longer requires iterating manually over options to apply `selected`.

- Backend-frontend synchronization improved:
  - Data reflection in inputs is now more consistent during updates and form submissions, especially when dynamically modifying templates.

### New features
- Added `Element.has_attr(name)`:
  - Utility method to check if a DOM element has a specific attribute.
  - Example usage: `if element.has_attr("selected")`.
  - Improves readability and encapsulates attribute logic more cleanly.

## [0.9.95] - 2025-07-04
---
### New features
- Allowed `ValueError` when create route with empty template value
- Added `remove_before_middleware` and `remove_after_middleware` methods in MiddlewareManager instance do allow remove specific middleware.
- Added `behavior` parameter in scroll window methods. Now, you can choose one of options: `auto`, `smooth` or `instant`
- Changed return type from tuple to `MiddlewareResult` for process_middleware method in MiddlewareManager.
- Changed `childs` type for Element to `ChildElements` instances. Now you can use list methods e.g: `append`, `remove`, `extend`, `pop`, to manipulate childs without problem.

### Bug Fixes
- Fixed duplicate send events allways that target has document and window events. Now, window events only will be sent if it was created before.

## [0.9.94] - 2025-07-02
---
### New features
- Added `request` method in `Pyweber` to acess all request's methods in all program.
- Added `get_group_and_route` method in `Pyweber` to acess group and route on full route
- Added `sanitize` attribute an `sanitize_values` method to prevent XSS atack.
- Added `title` attribute in `Route` instances to define title in html templates if not exists.
- Added `raw_body` properity in Request instances for get brute bodies received from client-side
- Renamed `raw_request` to `raw_headers` to get headers received from client request
- Added `process_response` in Route instance to allow create or no the Template for all routes responses.
- Added the possibility to create a log file using Printline
- Improved terminal logs status now categorized into `INFO`, `ERROR` and `WARNING`

### Bug Fixes
- Fixed get correct selected value in `Select` Element
- Fixes get values checked in CheckBox and Radio Elements
- Fixed `TypeError` when try to replace variables in html
- Fixed `TypeError` when try to set attribute without value

## [0.9.93] - 2025-06-06
---
### Bug Fixes
- Fixed virtualdom error when trying to parse incompatible elements of the `div` and `tr` type
- Added the `data` parameter to the element
- Added return in the `pop_child` method of the Element

## [0.9.92] - 2025-05-29
---
### Bug Fixes
- Fixed request validation method using https methods
- Fixed error when accessing static files

## [0.9.90] - 2025-05-24
---
### Bug Fixes
- Fixed error when serializing form data to form data dict using
- Fixed error when trying to redirect dynamic routes.
- Fixed error with `value` attribute of Elements that have events defined

## [0.9.7] - 2025-04-19
---
### New Features
- Implemented TemplateDiff system for efficient DOM updates:
  - Added intelligent diffing algorithm to detect exact changes between templates
  - Implemented efficient client-side patching to apply only necessary DOM updates
  - Reduced network traffic by sending only changed elements instead of full templates
- Added comprehensive deep cloning system for Element and Template objects:
  - Introduced `.clone` property for creating independent copies with preserved structure
  - Implemented support for cloning of nested elements with proper parent references
- Added component-based architecture with new HTML form elements:
  - Introduced `InputText`, `InputPassword`, `InputNumber`, `InputFile`, and other form components
  - Added comprehensive `TextArea` component with proper event handling
  - Implemented proper attribute management for all form components
- Enhanced WebSocket communication with optimized payload structure

### Improvements
- Optimized template rendering pipeline for better performance
- Improved event handling system with better event targeting
- Enhanced session management system for multiple browser tabs
- Refined UUID-based element tracking for more precise DOM manipulation
- Updated client-side JavaScript for efficient template diff application

### Bug Fixes
- Fix `pyweber run` and `pyweber -r` commands to run pyweber projects in linux system
- Fixed event handling for dynamically created elements
- Resolved issues with component attribute inheritance

## [0.9.6] - 2025-04-14
---
### Bug Fixes
- Resolved a `FileNotFoundError` that occurred when loading static files on Linux systems.

### New Features
- Added support for managing both `LocalStorage` and `SessionStorage`.
I- ntroduced support for native browser window methods such as `alert`, `prompt`, `confirm`, `atob`, `btoa`, `open`, `close`, and `scroll events`.
- Implemented a non-blocking system for handling both synchronous and asynchronous events, ensuring the main thread remains responsive.
- Server configuration can now be set directly in the run method. Parameters such as `ws_port`, `host`, `port`, key_file, and `cert_file` can be passed using `**kwargs` via `app.run()` or `pw.run()`.

### Improvements
- The window object is now globally accessible through the main module via `pw.window`.
- Removed window access from the app object — it is no longer available via `app.window`.

## [0.9.4] - 2025-04-08
---
### Bug Fixes
- Fixed `SyntaxError` when format f-string in non-windows systems

## [0.9.3] - 2025-04-08
---
### New Features
- Added `Icon Element` as pre-builded Elements called `Components`
- Added Bootstrap Icons. You need to import before on html or css to use it.
- Added Uvicorn and Gunicorn servers.

## [0.9.2] - 2025-04-07
---
### Bug Fixes
- Fixed the non-updating of values ​​when creating the config file

## [0.9.1] - 2025-04-07
---
### New Features
- Added `set_header()` method to Response class for modifying existing headers
- Added `add_header()` method to Response class for adding new headers
- Added support for asynchronous `after_request` middleware
- Improved HTML rendering with conditional DOCTYPE handling:
  - DOCTYPE is now only added when the root element is `<html>`
  - Fixed nested template rendering issues

### Improvements
- Enhanced Response class with better header management
- Optimized template rendering for dynamic content
- Better error handling and logging for HTTP responses
- Improved middleware processing with support for both synchronous and asynchronous functions
- Fixed reload mode detection to properly handle string environment variables:
  - Now correctly recognizes 'True', '1', True, and 1 as valid values
  - Ensures consistent behavior when setting reload mode via environment variables

### Bug Fixes
- Fixed issue with duplicate DOCTYPE declarations in nested templates
- Fixed middleware processing to properly handle both Request and Response objects
- Corrected HTTP version handling in Response headers
- Fixed content length calculation when response content is modified
- Resolved inconsistency in reload mode activation when set via environment variables

### Documentation
- Updated Response class documentation with new methods
- Added examples for asynchronous middleware usage
- Improved template rendering documentation

### Internal Changes
- Refactored Response class for better maintainability
- Improved type annotations throughout the codebase
- Enhanced middleware processing pipeline
- Added proper timezone handling for HTTP Date headers

## [0.9.0] - 2025-04-07
---
### New Features
- Added HTTPS/SSL support for secure connections:
  - Implemented SSL context configuration for HTTP server
  - Added WSS (WebSocket Secure) support for real-time connections
  - Support for custom certificates and self-signed certificates
  - Auto-generation of development certificates
- Added configuration options for SSL in both HTTP and WebSocket servers
- Improved CLI with SSL configuration options
- Added comprehensive environment variables support:
  - `PYWEBER_RELOAD_MODE` for controlling hot reload
  - `PYWEBER_HTTPS_ENABLED` for enabling/disabling HTTPS
  - `PYWEBER_CERT_FILE` and `PYWEBER_KEY_FILE` for SSL certificates
  - `PYWEBER_SERVER_HOST` and `PYWEBER_SERVER_PORT` for server configuration
  - `PYWEBER_WS_PORT` for WebSocket server port

### Improvements
- Enhanced security with proper SSL implementation
- Better error handling for SSL-related issues
- Improved WebSocket connection stability over secure connections
- Added detailed logging for connection issues
- Environment variables now take precedence over configuration files
- Added new CLI commands for certificate management:
  - `cert check-mkcert` to verify mkcert installation
  - `cert mkcert` to generate locally-trusted certificates
- Enhanced `run` command with additional server configuration options

### Documentation
- Added new documentation for environment variables
- Updated SSL/HTTPS setup guides
- Added certificate management instructions

## [0.8.4] - 2025-04-06
---
### Fixed
- Fixed `TypeError` when serializing HTML templates with comments ([#1](https://github.com/pyweber/pyweber/issues/1))

### New Features
- Added support for additional MIME types:
  - Office document formats (`doc`, `docx`, `xls`, `xlsx`, `pptx`, etc.)
  - Additional image formats (`bmp`, `webp`, `tif`, `tiff`)
- Introduced new `comment` Element tag for proper HTML comment handling
- Added support for dynamic templates with variable interpolation:
  - Template values can now be injected using `{{variable_name}}` syntax
  - Elements can be passed as template variables and will be properly rendered
  - Dynamic values can be provided via constructor kwargs
- Added environment variable `PYWEBER_RELOAD_MODE` to manage reload mode independently from configuration file

### Improvements
- Enhanced HTML parsing to properly handle and preserve comments
- Improved template rendering with more robust variable substitution
- Better error handling for malformed templates
- CLI now uses environment variables for reload mode, reducing dependency on configuration files


## [0.8.3] - 2025-04-05
---
### Fixed
- Fixed `FileNotFoundError` when try run on reload_mode if config file not exists

## [0.8.2] - 2025-04-05
---
### New Features
- Added comprehensive configuration management system
- Introduced interactive configuration editor via CLI
- Added support for custom configuration file paths and names
- Implemented `create-config-file` command for generating configuration files
- Added `add-section` command for managing configuration sections
- Enhanced project creation with `--with-config` flag
- Improved Window API with comprehensive browser interaction capabilities
- Added support for screen orientation detection and events

### Improvements
- Replaced Router with more powerful PyWeber class
- Enhanced CLI with more intuitive commands and options
- Improved hot reload functionality
- Added support for asynchronous event handlers
- Enhanced element manipulation API
- Improved error handling and reporting
- Updated documentation with comprehensive examples

### Fixed
- Fixed issues with WebSocket connections
- Resolved template rendering inconsistencies
- Fixed path handling in configuration system
- Addressed event propagation issues

## [0.8.1] - 2025-03-28
---

### New Features
- Added support for custom middleware
- Implemented session management
- Added cookie handling capabilities
- Introduced basic authentication helpers

### Improvements
- Enhanced routing system with parameter extraction
- Improved template rendering performance
- Added more DOM manipulation methods
- Enhanced event handling system

### Fixed
- Fixed static file serving issues
- Resolved template parsing errors
- Fixed WebSocket connection stability issues

## [0.8.0] - 2025-03-21
---

### New Features
- Initial release of PyWeber framework
- Implemented core Template system
- Added Element manipulation API
- Created event handling system
- Implemented basic routing
- Added WebSocket support for real-time updates
- Introduced hot reload for development
- Created CLI for project management

### Known Issues
- Limited middleware support
- Basic error handling
- Limited configuration options
