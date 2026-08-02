import inspect
import json
import os
import re
import webbrowser
import traceback
import logging
import asyncio
from typing import Union, Callable, Any, AsyncGenerator
from dataclasses import dataclass
from pyweber.utils.types import WindowEventType
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.utils.types import ContentTypes, StaticFilePath, HTTPStatusCode
from pyweber.utils.loads import LoadStaticFiles
from pyweber.core.window import window
from pyweber.connection.websocket import WebsocketManager
from pyweber.models.context import (
    get_current_request,
    set_current_request,
    reset_current_request,
    get_visited_routes,
    begin_route_visit_tracking,
    reset_route_visit_tracking,
)
from pyweber.models.handoff import handoff_registry, inject_handoff_token

from pyweber.models.middleware import MiddlewareManager
from pyweber.models.error_pages import ErrorPages
from pyweber.models.cookies import CookieManager
from pyweber.models.routes import (
    Route,
    RedirectRoute,
    RouteManager,
)

from pyweber.models.openapi import OpenApiProcessor, OpenAPIConfig, OpenAPIBuilder
from pyweber.models.security import SecurityEnforcer, normalize_security_requirements
from pyweber.core.events import WindowBookEvents

from pyweber.utils.utils import PrintLine
from pyweber.utils.exceptions import ParameterConversionError
from pyweber.utils.security import (
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    CSRF_FORM_FIELD,
    CSRF_HEADER,
    csrf_enabled,
    generate_csrf_token,
    generate_session_id,
    is_production,
    safe_join,
    sign_value,
    unsign_value,
    verify_csrf_token,
    https_enabled,
)
from pyweber.models.file import File
from pyweber.models.strem_stats import AdaptiveController
from pyweber.models.file_stream import (
    FileResult,
    file_chunk_manager
)

@dataclass
class StateResult:
    template: Any
    status_code: int
    content_type: ContentTypes
    redirect_path: str
    process_response: bool
    kwargs: dict[str, Any]
    callback: Callable[..., Any]

    def update(
        self,
        template = None,
        status_code = None,
        content_type = None,
        redirect_path = None,
        process_response = None,
        callback = None,
        kwargs = {}
    ):
        self.template = template if template else self.template
        self.status_code = status_code if status_code else self.status_code
        self.content_type = content_type if content_type else self.content_type
        self.redirect_path = redirect_path if redirect_path else self.redirect_path
        self.process_response = process_response if process_response is not None else self.process_response
        self.callback = callback if callback is not None else self.callback
        self.kwargs = kwargs if kwargs else self.kwargs

        return self

@dataclass
class TemplateResult:
    status_code: int
    content_type: ContentTypes
    redirect_path: str
    process_response: bool
    template: Union[Template, Element, dict, list, str]
    allowed_methods: list[str] = None

@dataclass
class ContentResult:
    content: bytes
    content_type: ContentTypes

    def __post__init__(self):
        if not isinstance(self.content_type, ContentTypes):
            raise TypeError(f"content_type must be ContentTypes, got {type(self.content_type).__name__}")

        if not isinstance(self.content, bytes):
            raise TypeError(f"content must be bytes, got {type(self.content).__name__}")

class Pyweber(
    ErrorPages,
    CookieManager,
    MiddlewareManager,
    RouteManager
):
    def __init__(self, *assets_directories, **data: Any):
        """Pyweber
        Args:
            assets_directories (*args): description
            data (**kwargs): description
        """
        MiddlewareManager.__init__(self)
        RouteManager.__init__(self)
        CookieManager.__init__(self)
        ErrorPages.__init__(self)
        self.__update_handler: Callable = data.pop('update_handler', None)
        self.openapi: OpenAPIConfig = data.pop('openapi', None) or OpenAPIConfig()
        self.__add_framework_routes()
        self._setup_openapi_routes()
        self.data = data
        self.__cache_templates: dict[str, tuple[ContentResult, TemplateResult]] = {}
        self.__static_directories: set[str] = set(assets_directories)

    # Request
    @property
    def request(self):
        return get_current_request()

    # Project Run
    @property
    def run(self):
        from pyweber.models.run import run
        return run

    def clear_cache_templates(self):
        self.__cache_templates.clear()

    @property
    def ws_server(self): return self.__ws_server

    @ws_server.setter
    def ws_server(self, value: WebsocketManager):
        assert isinstance(value, WebsocketManager)
        self.__ws_server = value

    def events(self, event_type: WindowEventType, route: str = None):
        assert isinstance(event_type, WindowEventType)
        def decorator(handler: Callable[..., Any]):
            async def wrapper(e):
                response = await handler(e) if inspect.iscoroutinefunction(handler) else handler(e)
                return response

            WindowBookEvents[f'event_{id(handler)}'] = {
                'type': event_type.value
            }

            return wrapper
        return decorator

    def static(self, *directories: str):
        self.__static_directories.update(directories)

    async def _receive_chunk(self, file_id: str, timeout: float) -> tuple[bytes, float]:
        loop = asyncio.get_event_loop()
        t_start = loop.time()

        result: FileResult = await file_chunk_manager.get(file_id, timeout=timeout)

        elapsed_ms = (loop.time() - t_start) * 1000

        if result.code != 200 or result.status == 'error' or not result.data:
            return b'', elapsed_ms
        return result.data, elapsed_ms

    async def stream(
        self,
        file: File,
        session_id: str,
        max_size: int = 1024 * 64,
        timeout: float = 30.0,
    ) -> AsyncGenerator[bytes, None]:

        controller = AdaptiveController(max_size=max_size)
        offset = 0
        file_id = file.file_id

        while offset < file.size:
            file_chunk_manager.register(file_id=file.file_id)

            data = {
                'request_file': file_id,
                'start': offset,
                'end': min(offset + controller.chunk_size, file.size)
            }

            await self.ws_server.send_message(data=data, session_id=session_id)

            chunk, elapsed_ms = await self._receive_chunk(file_id=file_id, timeout=timeout)
            if not chunk: break

            yield chunk

            received = len(chunk)
            offset += received
            controller.update(received_bytes=received, elapsed_ms=elapsed_ms)

            await asyncio.sleep(0)

    def __special_routes(self):
        return ['/_pyweber/file_chunk']

    # Response
    async def get_response(self, request: Request) -> Response:
        if not isinstance(request, Request):
            raise TypeError(f'request must be a Request instances, but got {type(request).__name__}')

        req_token = set_current_request(request)
        visit_token = begin_route_visit_tracking()
        self.cookies.clear()

        try:
            csrf_failure = self._enforce_csrf(request)
            if csrf_failure is not None:
                return csrf_failure

            rate_limited = self._enforce_rate_limit(request)
            if rate_limited is not None:
                return rate_limited

            self._ensure_session_cookie(request)
            self._ensure_csrf_cookie(request)

            async def produce_response() -> Response:
                return await self._produce_response(request)

            if self.get_onion_middlewares:
                result = await self.run_onion(request, produce_response)
                if isinstance(result, Response):
                    return self._finalize_response(request, result)
                if hasattr(result, 'content') and isinstance(result.content, Response):
                    return self._finalize_response(request, result.content)

            return await produce_response()
        finally:
            self.cookies.clear()
            reset_current_request(req_token)
            reset_route_visit_tracking(visit_token)

    def _finalize_response(self, request: Request, response: Response) -> Response:
        return self._apply_gzip(request, response)

    async def _produce_response(self, request: Request) -> Response:
        _route, _ = self.resolve_path(route=request.path)
        title = None
        _route_method = f"{_route}_{request.method}"

        if _route_method in self.__cache_templates:
            content_result, template_result = self.__cache_templates[_route_method]

        else:
            if _route in self.list_routes + self.__special_routes():
                title = self.get_route_by_path(route=_route).title

            before_request_response = await self.process_middleware(
                resp=request,
                middlewares=self.get_before_request_middlewares
            )

            if before_request_response:
                template_result = await self._process_templates(
                    state_result=StateResult(
                        template=before_request_response.content,
                        status_code=before_request_response.status_code,
                        process_response=before_request_response.process_response,
                        content_type=ContentTypes.html,
                        redirect_path=request.path,
                        callback=None,
                        kwargs=request.query_params
                    )
                )

            else:
                template_result = await self.get_template(
                    route=request.path,
                    method=request.method,
                    **request.query_params
                )

            if self._should_register_handoff(template_result):
                template_result.template = self._ensure_template_object(
                    template_result.template,
                    title=title,
                )
                token = handoff_registry.create(
                    template=template_result.template,
                    route=_route,
                )
                inject_handoff_token(template_result.template, token)

            content_result = self.template_to_bytes(
                template=template_result.template,
                content_type=template_result.content_type,
                title=title,
                process_response=template_result.process_response
            )

        response = Response(
            request=request,
            response_content=content_result.content,
            response_type=content_result.content_type,
            code=template_result.status_code,
            cookies=dict(self.cookies),
            route=template_result.redirect_path,
            allowed_methods=template_result.allowed_methods,
        ) if not isinstance(content_result, Response) else content_result

        response = self._apply_static_etag(request, response, template_result)

        after_request_response = await self.process_middleware(
            resp=response,
            middlewares=self.get_after_request_middlewares
        )

        final = after_request_response.content
        return self._finalize_response(request, final)

    def _enforce_rate_limit(self, request: Request) -> Response | None:
        from pyweber.models.rate_limit import rate_limit_enabled, get_rate_limiter

        if not rate_limit_enabled():
            return None
        host = getattr(request.client_info, 'host', None) or 'unknown'
        path = request.path or '/'
        allowed, retry_after = get_rate_limiter().allow(f'{host}:{path}')
        if allowed:
            return None
        response = Response(
            request=request,
            response_content=b'{"detail":"Too Many Requests"}',
            code=429,
            cookies={},
            response_type=ContentTypes.json,
            route=path,
        )
        response.set_header('Retry-After', str(int(retry_after) + 1))
        return response

    def _apply_static_etag(self, request: Request, response: Response, template_result) -> Response:
        import hashlib

        # Only for successful static-ish binary/text assets
        if response.status_code != 200:
            return response
        ctype = str(response.response_type or '')
        if 'html' in ctype and 'text/html' in ctype:
            # dynamic HTML — skip
            if getattr(template_result, 'process_response', False):
                return response

        body = response.response_content or b''
        if not isinstance(body, (bytes, bytearray)) or len(body) == 0:
            return response

        # Apply ETag for non-HTML or static file responses
        is_html = 'text/html' in ctype
        route = request.path or ''
        if is_html and not self.is_static_file(route) and not route.startswith('/_pyweber/static/'):
            return response

        etag = '"' + hashlib.sha256(bytes(body)).hexdigest()[:32] + '"'
        response.set_header('ETag', etag)
        response.set_header('Cache-Control', 'public, max-age=3600')
        inm = None
        for key, value in request.headers.items():
            if key.lower() == 'if-none-match':
                inm = value.strip()
                break
        if inm and inm == etag:
            response = Response(
                request=request,
                response_content=b'',
                code=304,
                cookies=dict(self.cookies),
                response_type=ContentTypes.txt,
                route=template_result.redirect_path if template_result else route,
            )
            response.set_header('ETag', etag)
            response.set_header('Cache-Control', 'public, max-age=3600')
        return response

    def _apply_gzip(self, request: Request, response: Response) -> Response:
        import gzip as gzip_mod
        import os
        from pyweber.config.config import config as app_config

        enabled = os.environ.get('PYWEBER_GZIP_ENABLED')
        if enabled is not None:
            gzip_on = enabled.strip().lower() in {'1', 'true', 'yes', 'on'}
        else:
            val = app_config.get('security', 'gzip_enabled', default=True)
            gzip_on = str(val).lower() in {'1', 'true', 'yes', 'on'} if isinstance(val, str) else bool(val)

        if not gzip_on or response.status_code in {204, 304}:
            return response

        accept = ''
        for key, value in request.headers.items():
            if key.lower() == 'accept-encoding':
                accept = value.lower()
                break
        if 'gzip' not in accept:
            return response

        body = response.response_content or b''
        if not isinstance(body, (bytes, bytearray)):
            return response
        threshold = int(app_config.get('security', 'gzip_min_bytes', default=500) or 500)
        if len(body) < threshold:
            return response
        if response.headers.get('Content-Encoding'):
            return response

        compressed = gzip_mod.compress(bytes(body), compresslevel=6)
        response.new_content(compressed)
        response.set_header('Content-Encoding', 'gzip')
        vary = str(response.headers.get('Vary') or '')
        if 'Accept-Encoding' not in vary:
            response.set_header('Vary', f'{vary}, Accept-Encoding'.strip(', '))
        return response

    def _csrf_exempt(self, path: str) -> bool:
        return path.startswith('/_pyweber/')

    def _enforce_csrf(self, request: Request) -> Response | None:
        method = (request.method or 'GET').upper()
        if not csrf_enabled() or method in {'GET', 'HEAD', 'OPTIONS', 'TRACE'}:
            return None
        if self._csrf_exempt(request.path or ''):
            return None

        header_token = None
        for key, value in request.headers.items():
            if key.lower() == CSRF_HEADER.lower():
                header_token = value
                break

        body_token = None
        try:
            body = request.body
            if isinstance(body, dict):
                body_token = body.get(CSRF_FORM_FIELD)
        except Exception:
            body_token = None

        token = header_token or body_token
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        if verify_csrf_token(token or '', cookie_token):
            return None

        return Response(
            request=request,
            response_content=b'{"detail":"CSRF token missing or invalid"}',
            code=403,
            cookies={},
            response_type=ContentTypes.json,
            route=request.path or '/',
        )

    def _ensure_session_cookie(self, request: Request) -> str:
        signed = request.cookies.get(SESSION_COOKIE_NAME)
        sid = unsign_value(signed) if signed else None
        if not sid:
            sid = generate_session_id()
            signed = sign_value(sid)
            self.set_cookie(
                cookie_name=SESSION_COOKIE_NAME,
                cookie_value=signed,
                httponly=True,
                secure=https_enabled(),
                samesite='Strict',
            )
        elif SESSION_COOKIE_NAME not in self.cookies:
            # Refresh cookie on response so clients keep a valid signed value
            self.set_cookie(
                cookie_name=SESSION_COOKIE_NAME,
                cookie_value=signed,
                httponly=True,
                secure=https_enabled(),
                samesite='Strict',
            )
        return sid

    def _ensure_csrf_cookie(self, request: Request) -> str | None:
        if not csrf_enabled():
            return None
        existing = request.cookies.get(CSRF_COOKIE_NAME)
        if existing and unsign_value(existing):
            token = existing
        else:
            token = generate_csrf_token()
        self.set_cookie(
            cookie_name=CSRF_COOKIE_NAME,
            cookie_value=token,
            httponly=False,
            secure=https_enabled(),
            samesite='Strict',
        )
        return token

    def static_roots(self) -> list[str]:
        roots = [os.path.realpath(str(StaticFilePath.favicon_path.value.parent))]
        for directory in self.__static_directories:
            roots.append(os.path.realpath(directory))
        return roots

    def resolve_safe_static_path(self, path: str) -> str | None:
        if not path:
            return None
        roots = self.static_roots()
        # Absolute / already-resolved filesystem path (e.g. Route templates)
        abs_candidate = path
        if os.path.isfile(abs_candidate):
            real = os.path.realpath(abs_candidate)
            for root in roots:
                try:
                    if os.path.commonpath([root, real]) == root:
                        return real
                except ValueError:
                    continue
            return None

        stripped = path.replace('\\', '/').lstrip('/')
        framework_static = roots[0]

        if stripped.startswith('_pyweber/static/'):
            remainder = stripped[len('_pyweber/static/'):]
            joined = safe_join(framework_static, remainder)
            if joined and os.path.isfile(joined):
                return joined

        for directory in self.__static_directories:
            name = directory.replace('\\', '/').strip('/')
            prefix = f'{name}/'
            if stripped == name or stripped.startswith(prefix):
                remainder = '' if stripped == name else stripped[len(name) + 1:]
                joined = safe_join(os.path.realpath(directory), remainder)
                if joined and os.path.isfile(joined):
                    return joined
        return None


    # Utils
    def _should_register_handoff(self, template_result: 'TemplateResult') -> bool:
        if not (
            template_result.process_response
            and template_result.content_type == ContentTypes.html
            and 200 <= template_result.status_code < 300
        ):
            return False

        template = template_result.template
        return not isinstance(template, (dict, list, set))

    def _ensure_template_object(
        self,
        template: Union[Template, Element, str],
        title: str = None,
    ) -> Template:
        if isinstance(template, Template):
            return template
        if isinstance(template, Element):
            return Template(template=template.to_html(), title=title)
        return Template(template=str(template), title=title)

    def template_to_bytes(
        self,
        template: Union[Template, Element, dict, list, set, str, bytes],
        content_type: ContentTypes = ContentTypes.html,
        title: str = None,
        process_response: bool = False
    ):
        if isinstance(template, Template):
            return self._process_template_object(template=template, title=title, content_type=content_type)

        elif isinstance(template, Element):
            return self._process_element_object(
                element=template,
                title=title,
                content_type=content_type,
                process_template=process_response
            )

        elif isinstance(template, (dict, set, list)):
            return self._process_json_object(template=template)

        elif isinstance(template, bytes):
            return self._process_byte_object(data=template, content_type=content_type)

        elif isinstance(template, Response):
            return template

        else:
            return self._process_string_object(
                data=template,
                title=title,
                content_type=content_type,
                process_response=process_response
            )

    def _process_byte_object(self, data: bytes, content_type: ContentTypes):
        return ContentResult(content=data, content_type=content_type)

    def _process_json_object(self, template: Union[dict, list, set]):
        return ContentResult(content=json.dumps(template).encode(), content_type=ContentTypes.json)

    def _process_template_object(self, template: Template, title: str, content_type: ContentTypes):
        template.title = title if title else template.title
        return ContentResult(content=template.build_html().encode(), content_type=content_type)

    def _process_element_object(
        self,
        element: Element,
        title: str,
        content_type: ContentTypes,
        process_template: bool
    ):
        if process_template:
            return ContentResult(
                content=Template(template=element.to_html(), title=title).build_html().encode(),
                content_type=content_type
            )

        return ContentResult(content=element.to_html().encode(), content_type=content_type)

    def _process_string_object(
        self,
        data: str,
        title: str,
        content_type: ContentTypes,
        process_response: bool
    ):
        if not isinstance(data, str):
            data = str(data)

        if process_response and content_type == ContentTypes.html:
            return ContentResult(
                content=Template(template=data, title=title).build_html().encode(),
                content_type=content_type
            )

        return ContentResult(content=data.encode(), content_type=content_type)

    def get_content_type(self, route: str) -> ContentTypes:
        if self.is_file_requested(route=route):
            extension = route.split('?')[0].split('/')[-1].split('.')[-1]
            for ext in ContentTypes.content_list():
                if extension == ext:
                    return getattr(ContentTypes, ext)
            return ContentTypes.unkown
        return ContentTypes.html

    async def get_template(self, route: str, method: str = 'GET', **kwargs):
        if get_current_request() is None:
            stub = Request.stub(method=method, path=route, query_params=kwargs)
            token = set_current_request(stub)
            try:
                return await self._get_template(route=route, method=method, **kwargs)
            finally:
                reset_current_request(token)

        return await self._get_template(route=route, method=method, **kwargs)

    async def _get_template(self, route: str, method: str = 'GET', **kwargs):
        path, kwd = self.resolve_path(route=route)

        kwargs = {**kwargs, **kwd}

        state_result = StateResult(
            template=None,
            status_code=404,
            content_type=ContentTypes.html,
            process_response=True,
            kwargs=kwargs,
            callback=None,
            redirect_path=path
        )

        if self.exists(route=path):
            _route = self.get_route_by_path(route=path, method=method)

            if _route is None:
                allowed_list = self.get_allowed_methods(path)
                # Redirect targets: resolve without method filter for method checks
                if not allowed_list and self.is_redirected(route=path):
                    target = self.get_route_by_path(route=path)
                    allowed_list = list(target.methods) if target else []

                allowed = ', '.join(allowed_list)
                state_result.update(
                    template=Template(
                        template=(
                            f'<h1>405 Method Not Allowed</h1>'
                            f'<p>Method {method} is not allowed for {path}.</p>'
                            f'<p>Allowed: {allowed}</p>'
                        ),
                        status_code=HTTPStatusCode.METHOD_NOT_ALLOWED.code,
                    ),
                    status_code=HTTPStatusCode.METHOD_NOT_ALLOWED.code,
                    process_response=False,
                    content_type=ContentTypes.html,
                    redirect_path=path,
                )
                result = await self._process_templates(state_result=state_result)
                result.allowed_methods = list(allowed_list)
                return result

            if method not in _route.methods:
                allowed_list = self.get_allowed_methods(path) or list(_route.methods)
                allowed = ', '.join(allowed_list)
                state_result.update(
                    template=Template(
                        template=(
                            f'<h1>405 Method Not Allowed</h1>'
                            f'<p>Method {method} is not allowed for {path}.</p>'
                            f'<p>Allowed: {allowed}</p>'
                        ),
                        status_code=HTTPStatusCode.METHOD_NOT_ALLOWED.code,
                    ),
                    status_code=HTTPStatusCode.METHOD_NOT_ALLOWED.code,
                    process_response=False,
                    content_type=ContentTypes.html,
                    redirect_path=path,
                )
                result = await self._process_templates(state_result=state_result)
                result.allowed_methods = list(allowed_list)
                return result

            if self.is_redirected(route=path):
                redirect_route = self.get_redirected_route(route=path)
                kwargs = redirect_route.kwargs or redirect_route.route.kwargs

                state_result.update(
                    kwargs=kwargs,
                    status_code=redirect_route.status_code,
                    redirect_path=self.build_route(_route.full_route, **kwargs),
                    template=_route.template,
                    process_response=_route.process_response,
                    content_type=_route.content_type,
                    callback=_route.callback
                )
            else:
                state_result.update(
                    template=_route.template,
                    process_response=_route.process_response,
                    status_code=_route.status_code,
                    content_type=_route.content_type,
                    callback=_route.callback,
                    kwargs=kwargs
                )

            # OpenAPI security enforcement (docs + runtime)
            request = get_current_request()
            if request is not None and not self.is_redirected(route=path):
                requirements = normalize_security_requirements(getattr(_route, 'security', None))
                if requirements is None:
                    requirements = self.openapi.normalized_security()

                challenge = SecurityEnforcer(self.openapi.security_schemes or {}).enforce(
                    request=request,
                    requirements=requirements,
                )
                if not challenge.ok:
                    state_result.update(
                        template={'detail': challenge.detail},
                        status_code=challenge.status_code,
                        content_type=ContentTypes.json,
                        process_response=False,
                        callback=None,
                        redirect_path=path,
                    )
                    return await self._process_templates(state_result=state_result)

                request.auth = challenge.auth

            if _route.middlewares:
                middleware_result = await self.process_route_middleware(
                    resp=self.request,
                    middlewares=_route.middlewares,
                    status_code=_route.status_code
                )

                if middleware_result:
                    state_result.update(
                        template=middleware_result.content,
                        status_code=middleware_result.status_code,
                        process_response=middleware_result.process_response
                    )

        if not state_result.template or isinstance(state_result.template, str):
            path = state_result.template or path

            safe_path = self.resolve_safe_static_path(path)
            if safe_path or self.is_file_requested(route=path):
                content_type = self.get_content_type(route=self.normalize_path(route=path))
                if safe_path:
                    state_result.update(
                        template=self.load_static_files(path=safe_path),
                        content_type=content_type,
                        status_code=200
                    )
                else:
                    state_result.update(
                        template=b'File not found',
                        status_code=404,
                        content_type=content_type if self.is_file_requested(route=path) else ContentTypes.txt
                    )
            else:
                content_type = self.get_content_type(route=path)

                state_result.update(
                    template=self.page_not_found,
                    content_type=self.get_content_type(route=route),
                    process_response=False if content_type.value != ContentTypes.html.value else True
                )

        return await self._process_templates(state_result=state_result)

    def _check_recursion(self, route: str):
        visited = get_visited_routes()
        if route in visited:
            raise RecursionError(f'Recursion detected for route {route}')
        visited.add(route)

    async def _process_redirect_route(
        self,
        state: StateResult,
        redirect_route: RedirectRoute,
        redirect_path: str,
        **kwargs
    ):
        if redirect_route.route.middlewares:
            middleware_result = await self.process_route_middleware(
                resp=self.request,
                middlewares=redirect_route.route.middlewares,
                status_code=redirect_route.status_code
            )

            if middleware_result:
                return state.update(
                    status_code=middleware_result.status_code,
                    process_response=middleware_result.process_response,
                    template=middleware_result.content
                )

        return state.update(
            template=redirect_route.route.template,
            status_code=redirect_route.status_code,
            content_type=redirect_route.route.content_type,
            redirect_path=redirect_path,
            process_response=redirect_route.route.process_response,
            callback=redirect_route.route.callback,
            kwargs=redirect_route.kwargs or kwargs
        )

    async def _process_templates(self, state_result: StateResult):
        try:
            template = state_result.template

            kwargs = {
                **(self.request.body if self.request else {}),
                **(self.request.query_params if self.request else {}),
            }
            if self.request:
                kwargs['request'] = self.request
            while callable(template) or isinstance(template, RedirectRoute):
                kwargs = {**kwargs, **state_result.kwargs}

                if callable(template):
                    kwargs = {
                        **kwargs,
                        **OpenApiProcessor.prepare_callback_kwargs(callback=state_result.callback, **kwargs)
                    }

                    template = await template(**kwargs) if inspect.iscoroutinefunction(template) else template(**kwargs)

                if isinstance(template, RedirectRoute):
                    kwargs = {**kwargs, **template.kwargs}
                    redirect_path = self.build_route(route=template.route.full_route_with_params, **kwargs)

                    self._check_recursion(route=redirect_path)
                    state_result = await self._process_redirect_route(
                        state=state_result,
                        redirect_route=template,
                        redirect_path=redirect_path,
                        **kwargs
                    )

                    template = state_result.template

                if isinstance(template, FileResult):
                    state_result.status_code = template.code
                    template = {
                        'file_id': template.file_id,
                        'status': template.status,
                        'message': template.data if template.code != 200 else 'OK'
                    }

        except ParameterConversionError as error:
            template = {'detail': str(error)}
            state_result.status_code = HTTPStatusCode.BAD_REQUEST.code
            state_result.content_type = ContentTypes.json
            state_result.process_response = False

        except Exception as error:
            error_details = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc(),
                'line': traceback.extract_tb(error.__traceback__)[-1].lineno
            }

            logging.error(traceback.format_exc())

            if is_production():
                error_message = 'An unexpected error occurred.'
            else:
                error_message = f'{error_details["message"]}, line {error_details["line"]}'

            template = Template(
                template=self.page_server_error.build_html(),
                error=error_message
            )
            state_result.status_code = HTTPStatusCode.INTERNAL_SERVER_ERROR.code
            state_result.content_type = ContentTypes.html

        return TemplateResult(
            status_code=state_result.status_code,
            content_type=state_result.content_type,
            redirect_path=state_result.redirect_path,
            process_response=state_result.process_response,
            template=template
        )

    async def process_route_middleware(self, resp: str, middlewares: list[Callable], status_code: int):
        return await self.process_middleware(
            resp=resp,
            middlewares=[
                {
                    'status_code': status_code,
                    'middleware': middleware,
                    'process_middleware': False,
                    'order': None
                } for middleware in middlewares
            ]
        )

    def is_file_requested(self, route: str):
        return re.match(r".*(\.[a-zA-Z0-9]+)+$", route.split('?')[0].split('/')[-1]) is not None

    def is_static_file(self, route: str):
        return self.resolve_safe_static_path(route) is not None

    def normalize_path(self, route: str):
        return os.path.normpath(path=route.removeprefix('/'))

    def normaize_path(self, route: str):
        from pyweber.utils.deprecation import warn_deprecated
        warn_deprecated('normaize_path', alternative='normalize_path', removal='2.0')
        return self.normalize_path(route)

    def load_static_files(self, path: str):
        return LoadStaticFiles(path=path, allowed_roots=self.static_roots()).load

    def __add_framework_routes(self):
        self.add_group_routes(
            routes=[
                Route(
                    route='/_pyweber/file_chunk?file_id={file_id}&status={status}',
                    template=file_chunk_manager.resolve,
                    title='Get File Chunks',
                    process_response=False,
                    methods=['post'],
                    content_type=ContentTypes.json,
                    security=[],
                    include_in_schema=False,
                ),
                Route(
                    route='/_pyweber/check-cookies',
                    template={'message': 'OK'},
                    methods=['get'],
                    title='Get Cookies',
                    process_response=False,
                    content_type=ContentTypes.json,
                    security=[],
                    include_in_schema=False,
                ),
                Route(
                    route='/_pyweber/static/favicon.ico',
                    template=str(StaticFilePath.favicon_path.value.joinpath('favicon.ico')),
                    content_type=ContentTypes.ico,
                    security=[],
                    include_in_schema=False,
                ),
                Route(
                    route='/_pyweber/static/{uuid}/.css',
                    template=str(StaticFilePath.pyweber_css.value),
                    content_type=ContentTypes.css,
                    security=[],
                    include_in_schema=False,
                ),
                Route(
                    route='/_pyweber/static/{uuid}/.js',
                    template=str(StaticFilePath.js_base.value),
                    content_type=ContentTypes.js,
                    security=[],
                    include_in_schema=False,
                )
            ]
        )

    def _setup_openapi_routes(self):
        """Register /docs and openapi.json from OpenAPIConfig (callable schema)."""
        config = self.openapi or OpenAPIConfig()
        routes: list[Route] = []

        expose = bool(getattr(config, 'expose_in_production', False))
        if is_production() and not expose:
            return

        if config.docs_url:
            routes.append(
                Route(
                    route=config.docs_url,
                    template=StaticFilePath.pyweber_docs.value,
                    title='Pyweber Documentation',
                    security=[],
                    include_in_schema=False,
                )
            )

        if config.openapi_url:
            routes.append(
                Route(
                    route=config.openapi_url,
                    template=self.get_openapi_schema,
                    content_type=ContentTypes.json,
                    process_response=False,
                    security=[],
                    include_in_schema=False,
                    title='OpenAPI Schema',
                )
            )
            # Backward-compatible alias used by older docs.html clients
            routes.append(
                Route(
                    route='/_pyweber/{uuid}/openapi.json',
                    template=self.get_openapi_schema,
                    content_type=ContentTypes.json,
                    process_response=False,
                    security=[],
                    include_in_schema=False,
                    title='OpenAPI Schema',
                )
            )

        if routes:
            self.add_group_routes(routes)

    def get_openapi_schema(self, **kwargs):
        return OpenAPIBuilder(self).build()

    def __get_routes(self):
        return self.get_openapi_schema()

    async def clone_template(self, route: str):
        template_result = await self.get_template(route=route)

        if not isinstance(template_result.template, Template):
            template_result.template = Template(template=str(template_result.template))

        return template_result.template.clone()

    def update(self, changed_file: str = None):
        return self.__update_handler(module=changed_file) if self.__update_handler else None

    def launch_url(self, url: str, new_page: bool = False):
        return webbrowser.open(url=url, new=new_page)

    def to_url(self, url: str, new_page: bool = False, message: str = None):
        window.open(url=url, new_page=new_page)
        return Element(
            tag='p',
            content=message or f"Redirected to {Element( tag='a', attrs={'href': url}, content=url).to_html()}"
        )

    async def __call__(self, scope, receive, send):
        from pyweber.models.run import run_as_asgi

        await run_as_asgi(scope, receive, send, app=self)

    def __repr__(self):
        return f'Pyweber(routes={len(self.list_routes)})'
