"""Deprecation helpers — warn in minor releases, remove in major (2.0)."""

from __future__ import annotations

import functools
import warnings
from typing import Any, Callable, TypeVar

_warned: set[str] = set()

T = TypeVar('T')


def warn_deprecated(
    name: str,
    *,
    alternative: str,
    removal: str = '2.0',
    stacklevel: int = 3,
) -> None:
    """Emit a one-shot DeprecationWarning for ``name``."""
    if name in _warned:
        return
    _warned.add(name)
    warnings.warn(
        f'{name} is deprecated and will be removed in PyWeber {removal}; '
        f'use {alternative} instead.',
        DeprecationWarning,
        stacklevel=stacklevel,
    )


def deprecated_alias(old_name: str, new_obj: T, *, alternative: str | None = None, removal: str = '2.0') -> T:
    """Wrap a class/callable so accessing/calling it warns once.

    For classes, returns a subclass that warns on instantiation.
    For callables, returns a wrapper that warns on call.
    For other objects, returns the object unchanged (caller should warn at import site).
    """
    alt = alternative or getattr(new_obj, '__name__', str(new_obj))

    if isinstance(new_obj, type):
        class _DeprecatedAlias(new_obj):  # type: ignore[valid-type,misc]
            def __init__(self, *args, **kwargs):
                warn_deprecated(old_name, alternative=alt, removal=removal, stacklevel=4)
                super().__init__(*args, **kwargs)

        _DeprecatedAlias.__name__ = old_name
        _DeprecatedAlias.__qualname__ = old_name
        _DeprecatedAlias.__doc__ = (
            f'Deprecated alias for {alt}. Will be removed in PyWeber {removal}.'
        )
        return _DeprecatedAlias  # type: ignore[return-value]

    if callable(new_obj):
        @functools.wraps(new_obj)
        def _wrapper(*args, **kwargs):
            warn_deprecated(old_name, alternative=alt, removal=removal, stacklevel=3)
            return new_obj(*args, **kwargs)

        return _wrapper  # type: ignore[return-value]

    return new_obj


def deprecated_callable(
    *,
    name: str,
    alternative: str,
    removal: str = '2.0',
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that warns when the wrapped function is called."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            warn_deprecated(name, alternative=alternative, removal=removal, stacklevel=3)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def reset_deprecation_warnings() -> None:
    """Clear the one-shot cache (tests only)."""
    _warned.clear()
