# Deprecations

PyWeber follows a simple SemVer deprecation policy:

| Change type | When |
|-------------|------|
| **Deprecate** (keep working + `DeprecationWarning`) | Minor / patch releases (e.g. 1.5) |
| **Remove** | Next **major** release (2.0) |

## Rules for app authors

1. Prefer the documented replacement as soon as you see a warning.
2. Run tests/CI with `PYTHONWARNINGS=default::DeprecationWarning` (or `error`) to catch usage early.
3. Aliases such as `DoubleFormnat`, `normaize_path`, and one-argument middlewares remain until **2.0**.

## Emitting warnings (contributors)

Use helpers from `pyweber.utils.deprecation`:

```python
from pyweber.utils.deprecation import warn_deprecated, deprecated_alias, deprecated_callable

warn_deprecated('old_name', alternative='new_name', removal='2.0')
```

Warnings are **deduplicated per process** (one warning per deprecated name) to avoid log spam.
