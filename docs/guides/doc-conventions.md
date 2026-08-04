# Documentation conventions

How PyWeber docs mark **when** something landed and **when** it goes away.

## Added in (version badges)

For features that are not ancient baseline API, put an admonition at the **start of the section** (or page):

```markdown
!!! tip "Added in 1.6.0"
    Optional SQLAlchemy integration via `pyweber[db]`.
```

Rules:

1. Use the **first stable/minor** version where the feature shipped (match [Changelog](../changelog.md) / root `CHANGELOG.md`).
2. Prefer section-level tips over repeating the badge on every subsection.
3. Baseline APIs (Element, Template, `app.route`, …) need no badge.

Examples already in the docs: Database, Session backends, Authentication, identity-preserving `self`, Window timers.

## Deprecated (leaving in 2.0)

```markdown
!!! warning "Deprecated — removed in 2.0"
    Use `normalize_path` instead of `normaize_path`.
```

Full list: [Deprecations](deprecations.md).

## Security / unsupported releases

Versions **≤ 1.3.1** are **not recommended** for production (see [Supported versions](supported-versions.md)). That is separate from API deprecation.
