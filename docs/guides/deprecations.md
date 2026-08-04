# Deprecations

PyWeber follows a simple SemVer deprecation policy:

| Change type | When |
|-------------|------|
| **Deprecate** (keep working + `DeprecationWarning`) | Minor / patch releases (e.g. 1.5+) |
| **Remove** | Next **major** release (**2.0**) |

## Rules for app authors

1. Prefer the documented replacement as soon as you see a warning.
2. Run tests/CI with `PYTHONWARNINGS=default::DeprecationWarning` (or `error`) to catch usage early.
3. Items in the table below remain until **2.0** unless noted otherwise.

## Inventory (removed in 2.0)

| Deprecated | Use instead | Where |
|------------|-------------|--------|
| `CreatApp` | `CreateApp` | `pyweber.models.create_app` |
| `normaize_path` | `normalize_path` | `Pyweber` |
| `toogle_class` | `toggle_class` | Element class helpers |
| `DoubleFormnat` | `DoubleFormat` | `pyweber.utils.types` |
| `pyweber.utils.types.Icons` | `pyweber.utils.icons.Icons` | Icons enum |
| `before_request(status_code=…, process_response=…)` | Return a `Response` / `Template` with the desired status from the hook | Middleware |
| `after_request(status_code=…, process_response=…)` | Same — set status on the response object | Middleware |
| `add_before_request_middleware` | `add_before_request` | Middleware |
| `add_after_request_middleware` | `add_after_request` | Middleware |
| One-arg / legacy middleware shapes where warned | Onion `@app.middleware` with `(request, call_next)` | Middleware |
| `e.element` (docs / old samples) | `e.target` | Event handlers |
| `Response` ctor aliases `response_content` / `code` / `response_type` (still accepted) | `content` / `status` / helpers | Prefer `Response.json` / `.html` / `.text` |
| `JWTAlgorithms` / `pyweber.JWTAlgorithms` | `pyjwt` (or similar) + `pyweber.auth` for sessions | Algorithm-name enum only; public import warns |
| `Element.update()` | `e.update()` | **Removed** in 1.6 (was `NotImplementedError`) |

!!! warning "Removed in 2.0"
    Do not start new code on the left column. CI with `DeprecationWarning` as error is the safest upgrade path.

## Emitting warnings (contributors)

Use helpers from `pyweber.utils.deprecation`:

```python
from pyweber.utils.deprecation import warn_deprecated, deprecated_alias, deprecated_callable

warn_deprecated('old_name', alternative='new_name', removal='2.0')
```

Warnings are **deduplicated per process** (one warning per deprecated name) to avoid log spam.

## Doc convention

In feature pages:

- New APIs: `!!! tip "Added in X.Y.Z"` (see [Doc conventions](doc-conventions.md))
- Leaving APIs: `!!! warning "Deprecated — removed in 2.0"` next to the old name
