from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyweber.models.request import Request
    from pyweber.core.window import Window
    from pyweber.models.cookies import CookieManager

_request_ctx: ContextVar['Request | None'] = ContextVar('pyweber_request', default=None)
_window_ctx: ContextVar['Window | None'] = ContextVar('pyweber_window', default=None)
_visited_routes_ctx: ContextVar[set[str] | None] = ContextVar('pyweber_visited_routes', default=None)
_cookie_manager_ctx: ContextVar[Any] = ContextVar('pyweber_cookie_manager', default=None)


def get_current_request() -> 'Request | None':
    return _request_ctx.get()


def get_current_window() -> 'Window | None':
    return _window_ctx.get()


def get_cookie_manager() -> 'CookieManager | None':
    return _cookie_manager_ctx.get()


def get_visited_routes() -> set[str]:
    visited = _visited_routes_ctx.get()
    if visited is None:
        visited = set()
        _visited_routes_ctx.set(visited)
    return visited


def begin_route_visit_tracking():
    return _visited_routes_ctx.set(set())


def reset_route_visit_tracking(token) -> None:
    _visited_routes_ctx.reset(token)


def set_current_request(request: 'Request'):
    return _request_ctx.set(request)


def reset_current_request(token) -> None:
    _request_ctx.reset(token)


def set_current_window(window: 'Window'):
    return _window_ctx.set(window)


def reset_current_window(token) -> None:
    _window_ctx.reset(token)


def set_cookie_manager(manager: 'CookieManager | None'):
    return _cookie_manager_ctx.set(manager)


def reset_cookie_manager(token) -> None:
    _cookie_manager_ctx.reset(token)
