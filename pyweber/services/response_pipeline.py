"""HTTP response cross-cutting concerns: CSRF, CORS, rate limit, gzip, ETag."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from pyweber.models.rate_limit import get_rate_limiter, rate_limit_enabled
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.utils.security import (
    CSRF_COOKIE_NAME,
    CSRF_FORM_FIELD,
    CSRF_HEADER,
    SESSION_COOKIE_NAME,
    csrf_enabled,
    generate_csrf_token,
    generate_session_id,
    get_allowed_origins,
    https_enabled,
    sign_value,
    unsign_value,
    verify_csrf_token,
)
from pyweber.utils.types import ContentTypes

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber


class ResponsePipeline:
    """Delegates cookie/session mutations to the owning ``Pyweber`` app."""

    def __init__(self, app: Pyweber):
        self.app = app

    def finalize(self, request: Request, response: Response) -> Response:
        return self.apply_gzip(request, response)

    def enforce_rate_limit(self, request: Request) -> Response | None:
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

    def apply_static_etag(self, request: Request, response: Response, template_result) -> Response:
        import hashlib

        if response.status_code != 200:
            return response
        ctype = str(response.response_type or '')
        if 'html' in ctype and 'text/html' in ctype:
            if getattr(template_result, 'process_response', False):
                return response

        body = response.response_content or b''
        if not isinstance(body, (bytes, bytearray)) or len(body) == 0:
            return response

        is_html = 'text/html' in ctype
        route = request.path or ''
        if is_html and not self.app.is_static_file(route) and not route.startswith('/_pyweber/static/'):
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
                cookies=dict(self.app.cookies),
                response_type=ContentTypes.txt,
                route=template_result.redirect_path if template_result else route,
            )
            response.set_header('ETag', etag)
            response.set_header('Cache-Control', 'public, max-age=3600')
        return response

    def apply_gzip(self, request: Request, response: Response) -> Response:
        import gzip as gzip_mod
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

    def csrf_exempt(self, path: str) -> bool:
        return path.startswith('/_pyweber/')

    def enforce_csrf(self, request: Request) -> Response | None:
        method = (request.method or 'GET').upper()
        if not csrf_enabled() or method in {'GET', 'HEAD', 'OPTIONS', 'TRACE'}:
            return None
        if self.csrf_exempt(request.path or ''):
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

    def ensure_session_cookie(self, request: Request) -> str:
        signed = request.cookies.get(SESSION_COOKIE_NAME)
        sid = unsign_value(signed) if signed else None
        if not sid:
            sid = generate_session_id()
            signed = sign_value(sid)
            self.app.set_cookie(
                cookie_name=SESSION_COOKIE_NAME,
                cookie_value=signed,
                httponly=True,
                secure=https_enabled(),
                samesite='Strict',
            )
        elif SESSION_COOKIE_NAME not in self.app.cookies:
            self.app.set_cookie(
                cookie_name=SESSION_COOKIE_NAME,
                cookie_value=signed,
                httponly=True,
                secure=https_enabled(),
                samesite='Strict',
            )
        return sid

    def ensure_csrf_cookie(self, request: Request) -> str | None:
        if not csrf_enabled():
            return None
        existing = request.cookies.get(CSRF_COOKIE_NAME)
        if existing and unsign_value(existing):
            token = existing
        else:
            token = generate_csrf_token()
        self.app.set_cookie(
            cookie_name=CSRF_COOKIE_NAME,
            cookie_value=token,
            httponly=False,
            secure=https_enabled(),
            samesite='Strict',
        )
        return token

    def prefers_html(self, request: Request) -> bool:
        accept = (request.headers.get('accept') or '').lower()
        if 'text/html' not in accept:
            return False
        if 'application/json' not in accept:
            return True
        return accept.find('text/html') <= accept.find('application/json')

    def cors_preflight_response(self, request: Request) -> Response | None:
        method = (request.method or '').upper()
        if method != 'OPTIONS':
            return None
        origin = request.origin
        allowed = get_allowed_origins()
        if not origin or origin.rstrip('/') not in allowed:
            return None
        return Response(
            content=b'',
            status=204,
            request=request,
            cookies={},
            content_type=ContentTypes.txt,
            route=request.path or '/',
        )
