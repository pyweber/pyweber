from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pyweber.utils.types import ContentTypes, HTTPStatusCode
from pyweber.models.request import Request
from pyweber.utils.utils import PrintLine, Colors
from pyweber.utils.security import (
    DEFAULT_CSP,
    get_allowed_origins,
    https_enabled,
    resolve_csp,
)

# Re-export for callers that imported DEFAULT_CSP from response
__all_csp__ = (DEFAULT_CSP, resolve_csp)

# Internal bookkeeping headers — stripped on ASGI wire format
INTERNAL_RESPONSE_HEADERS = frozenset({
    'method',
    'http-version',
    'status',
    'request-path',
    'response-path',
    'set-cookie',  # handled separately
    'code',
})


def _coerce_body_and_type(
    content: Any,
    content_type: ContentTypes | str | None,
) -> tuple[bytes, ContentTypes]:
    if content is None:
        body = b''
        inferred = ContentTypes.txt
    elif isinstance(content, bytes):
        body = content
        inferred = ContentTypes.unkown
    elif isinstance(content, dict) or isinstance(content, list):
        body = json.dumps(content).encode('utf-8')
        inferred = ContentTypes.json
    elif isinstance(content, str):
        body = content.encode('utf-8')
        stripped = content.lstrip().lower()
        inferred = ContentTypes.html if stripped.startswith('<') else ContentTypes.txt
    else:
        body = str(content).encode('utf-8')
        inferred = ContentTypes.txt

    if content_type is None:
        return body, inferred
    if isinstance(content_type, ContentTypes):
        return body, content_type
    # string mime → best-effort enum match
    for ct in ContentTypes:
        if ct.value == content_type or content_type.startswith(ct.value):
            return body, ct
    return body, inferred


class Response:
    def __init__(
        self,
        content: Any = None,
        status: int = 200,
        *,
        request: Request | None = None,
        cookies: dict[str, str] | None = None,
        content_type: ContentTypes | str | None = None,
        route: str | None = None,
        headers: dict[str, Any] | None = None,
        allowed_methods: list[str] | None = None,
        # Legacy aliases (still supported)
        response_content: bytes | None = None,
        code: int | None = None,
        response_type: ContentTypes | None = None,
    ):
        if response_content is not None and content is None:
            content = response_content
        if code is not None:
            status = code
        if response_type is not None and content_type is None:
            content_type = response_type

        body, resolved_type = _coerce_body_and_type(content, content_type)

        if request is None:
            request = Request.stub(method='GET', path=route or '/')

        cookies = cookies if cookies is not None else {}
        route = route if route is not None else (getattr(request, 'path', None) or '/')

        request_headers = (
            request.accept_control_request_headers
            or "Content-Type, Authorization, X-Requested-With, Accept, X-CSRF-Token"
        )
        self.__request = request
        self.__allowed_methods = allowed_methods
        self.__body = body
        self.__headers: dict[str, Any] = {
            "Content-Type": f"{resolved_type.value}; charset=UTF-8",
            "Content-Length": len(body),
            "Connection": 'Close',
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Vary": "Accept-Encoding",
            "Method": request.method,
            "Http-Version": request.scheme,
            "Status": status,
            "Server": 'Pyweber/1.0',
            "Date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "Set-Cookie": cookies,
            "Request-Path": request.full_path,
            "Response-Path": route,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Forwarded-Proto": "https" if https_enabled() else "http",
            "X-Forwarded-Host": getattr(request, 'host', None) or 'localhost',
        }

        csp = resolve_csp()
        if csp:
            self.__headers["Content-Security-Policy"] = csp

        if https_enabled():
            self.__headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        self._apply_cors(request, request_headers)

        if headers:
            for key, value in headers.items():
                if value is None:
                    self.__headers.pop(key, None)
                else:
                    self.__headers[key] = value

        self.http_status_code = HTTPStatusCode.search_by_code(status)
        self.__check_status_code()

    @classmethod
    def json(cls, data: Any, status: int = 200, **kwargs) -> Response:
        return cls(content=data, status=status, content_type=ContentTypes.json, **kwargs)

    @classmethod
    def text(cls, data: str, status: int = 200, **kwargs) -> Response:
        return cls(content=data, status=status, content_type=ContentTypes.txt, **kwargs)

    @classmethod
    def html(cls, data: str, status: int = 200, **kwargs) -> Response:
        return cls(content=data, status=status, content_type=ContentTypes.html, **kwargs)

    def _apply_cors(self, request: Request, request_headers: str):
        origin = request.origin
        allowed = get_allowed_origins()
        if origin and origin.rstrip('/') in allowed:
            self.__headers["Access-Control-Allow-Origin"] = origin
            self.__headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            self.__headers["Access-Control-Allow-Headers"] = request_headers
            self.__headers["Access-Control-Allow-Credentials"] = 'true'
            vary = self.__headers.get("Vary", "")
            if "Origin" not in str(vary):
                self.__headers["Vary"] = f"{vary}, Origin" if vary else "Origin"

    def __check_status_code(self):
        aditional_code: tuple[str, str] = ()

        # WWW-Authenticate is NOT auto-added; set via headers= or set_header / security schemes

        if self.status_code == 405:
            allow = ', '.join(self.__allowed_methods) if self.__allowed_methods else 'GET, POST, PUT, DELETE'
            aditional_code = ('Allow', allow)

        elif self.status_code == 503:
            aditional_code = ('Retry-After', '60')

        elif self.status_code in range(300, 400):
            aditional_code = ('Location', self.response_path)

        if self.status_code not in range(300, 400):
            self.set_header('Response-Path', self.request_path)

        if aditional_code:
            self.set_header(aditional_code[0], aditional_code[-1])
            self.http_status_code += f"\r\n{': '.join(aditional_code)}"

    @property
    def headers(self) -> dict[str, Any]:
        return self.__headers

    @property
    def request(self) -> Request:
        return self.__request

    @property
    def http_version(self) -> str:
        return self.headers.get('Http-Version', None)

    @property
    def response_date(self) -> str:
        return self.headers.get('Date', None)

    @property
    def response_type(self) -> str:
        return self.headers.get('Content-Type', 'text/html')

    @property
    def response_content(self) -> bytes:
        return self.__body

    @property
    def cookies(self) -> list | dict:
        return self.headers.get('Set-Cookie', [])

    @property
    def request_path(self) -> str:
        return self.headers.get('Request-Path', None)

    @property
    def response_path(self) -> str:
        return self.headers.get('Response-Path', None)

    @property
    def status_code(self) -> int:
        return self.headers.get('Status', None)

    def __getitem__(self, key: str = None):
        if not key:
            return {'headers': self.headers, 'body': self.response_content}

        elif key == 'headers':
            return self.headers

        elif key == 'body':
            return self.response_content
        else:
            return {}

    def set_header(self, key: str, value: str):
        """Add new header in Response"""
        self.__headers[key] = value

    def update_header(self, key: str, /, value: str | bytes | int | float):
        """Update header value if it exist in Response"""
        if key in self.__headers:
            self.__headers[key] = value

    def new_content(self, value: bytes):
        if isinstance(value, bytes):
            self.__body = value
            self.__headers['Content-Length'] = len(value)

    @property
    def build_response(self) -> bytes:
        response = f'{self.http_version} {self.http_status_code}\r\n'
        reset_color = Colors.RESET
        bold_white_color = Colors.BOLD_WHITE
        bold_red_color = Colors.BOLD_RED
        bold_green_color = Colors.GREEN
        bold_yellow_color = Colors.BOLD_YELLOW
        bold_blue_color = Colors.BOLD_BLUE

        if self.status_code >= 400:
            status_color = bold_red_color
        elif self.status_code >= 300:
            status_color = bold_yellow_color
        elif self.status_code >= 200:
            status_color = bold_green_color
        else:
            status_color = bold_blue_color

        for key, value in self.headers.items():
            if key == 'Set-Cookie':
                for cookie in value:
                    response += f'{key}: {value[cookie]}\r\n'

            elif key == 'Response':
                pass

            else:
                response += f'{key}: {value}\r\n'

        response += '\r\n'

        to_replace = '\r\n'
        clear_status_code = self.http_status_code.replace(to_replace, ' ')
        PrintLine(text=f"{bold_white_color}{self.request.first_line} {status_color}{clear_status_code}{reset_color}")
        return response.encode() + self.response_content
