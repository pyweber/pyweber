# Supported versions & security

## Recommendation

| Versions | Status |
|----------|--------|
| **Latest 1.5+ / 1.6+** | Recommended |
| **1.4.x** | Use only if you cannot upgrade yet; prefer latest patch |
| **≤ 1.3.1** | **Not recommended** — treat as insecure for internet-facing apps |

!!! danger "Do not deploy ≤ 1.3.1"
    Technical audit findings (CORS, CSRF, XSS/sanitize edges, path traversal, unsigned WS session cookies, missing security headers, body limits, etc.) apply to the **≤ 1.3.1** line. Later releases addressed those classes of issues. Prefer `pip install -U pyweber` (or pin `pyweber>=1.5`).

Always install a current release:

```bash
pip install -U 'pyweber>=1.5'
```

Pinning an old insecure line for “stability” is a false economy on a web framework.

## Can `pyproject.toml` warn on `pip install pyweber==1.3.1`?

**No.** Metadata in today’s `pyproject.toml` only describes the package **you are publishing now**. It cannot change how pip behaves when someone installs an **already published** wheel from 2025.

What **does** work on PyPI:

### Yanking (recommended for ≤ 1.3.1)

[Yank](https://docs.pypi.org/project-management/yanking/) each insecure release on PyPI with a clear reason, e.g.:

> Security: versions ≤1.3.1 are not recommended; upgrade to ≥1.5. See https://pyweber.dev/guides/supported-versions/

Effects:

- `pip install pyweber` **ignores** yanked versions and picks a newer one.
- `pip install pyweber==1.3.1` **still installs** that exact pin, but pip prints:

  `WARNING: The candidate selected for download or install is a yanked version … Reason: …`

That is the closest thing to “heeey…” on install. Yanking is done in the PyPI web UI (or API), **not** via `pyproject.toml`.

### Optional: delete

Deletion is harsher (breaks lockfiles that pin forever). Prefer yank + reason.

## Maintainer checklist (yank ≤ 1.3.1)

1. Open [PyPI releases](https://pypi.org/manage/project/pyweber/releases/) for `pyweber`.
2. For each release **1.0.0 … 1.3.1** (and any `.dev` / RC in that range you want blocked): **Options → Yank**.
3. Paste the security reason (same text for all).
4. Confirm `pip install pyweber` resolves to a current non-yanked version.
5. Confirm `pip install pyweber==1.3.1` shows the yanked warning.

## See also

- [Installation](../installation.md)
- [Deprecations](deprecations.md) (API removals in 2.0 — different topic)
- Root audit notes: `AUDITORIA_TECNICA_PYWEBER.md` in the repository
