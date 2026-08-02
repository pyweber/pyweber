"""In-process TestClient for PyWeber apps."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlencode

from pyweber.models.request import Request, ClientInfo
from pyweber.models.response import Response
from pyweber.utils.security import CSRF_COOKIE_NAME, CSRF_FORM_FIELD, CSRF_HEADER, generate_csrf_token


class TestClient:
    """Minimal HTTP client that calls ``app.get_response`` in-process."""

    def __init__(self, app, *, raise_server_exceptions: bool = True):
        self.app = app
        self.raise_server_exceptions = raise_server_exceptions
        self.cookies: dict[str, str] = {}

    def _build_headers(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None,
        body: bytes,
        content_type: str | None,
    ) -> str:
        hdrs = {
            'Host': 'testserver',
            'Content-Length': str(len(body)),
            **(headers or {}),
        }
        if content_type:
            hdrs.setdefault('Content-Type', content_type)
        if self.cookies:
            cookie_str = '; '.join(f'{k}={v}' for k, v in self.cookies.items())
            existing = hdrs.get('Cookie')
            hdrs['Cookie'] = f'{existing}; {cookie_str}' if existing else cookie_str

        lines = [f'{method.upper()} {path} HTTP/1.1']
        for key, value in hdrs.items():
            lines.append(f'{key}: {value}')
        return '\r\n'.join(lines) + '\r\n\r\n'

    def _store_cookies(self, response: Response) -> None:
        raw = response.cookies
        if isinstance(raw, dict):
            for name, cookie in raw.items():
                part = str(cookie).split(';', 1)[0]
                if '=' in part:
                    k, v = part.split('=', 1)
                    self.cookies[k.strip()] = v.strip()

    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | bytes | None = None,
        json: dict | list | None = None,
        content_type: str | None = None,
    ) -> Response:
        body = b''
        if json is not None:
            import json as json_lib
            body = json_lib.dumps(json).encode('utf-8')
            content_type = content_type or 'application/json'
        elif isinstance(data, dict):
            body = urlencode(data).encode('utf-8')
            content_type = content_type or 'application/x-www-form-urlencoded'
        elif isinstance(data, (bytes, bytearray)):
            body = bytes(data)

        raw_headers = self._build_headers(method, path, headers, body, content_type)
        request = Request(
            headers=raw_headers,
            body=body,
            client_info=ClientInfo(host='127.0.0.1', port=0),
        )
        response = await self.app.get_response(request)
        self._store_cookies(response)
        return response

    def request_sync(self, *args, **kwargs) -> Response:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(lambda: asyncio.run(self.request(*args, **kwargs))).result()
            return loop.run_until_complete(self.request(*args, **kwargs))
        except RuntimeError:
            return asyncio.run(self.request(*args, **kwargs))

    async def get(self, path: str, **kwargs) -> Response:
        return await self.request('GET', path, **kwargs)

    async def post(self, path: str, **kwargs) -> Response:
        return await self.request('POST', path, **kwargs)

    async def put(self, path: str, **kwargs) -> Response:
        return await self.request('PUT', path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Response:
        return await self.request('PATCH', path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Response:
        return await self.request('DELETE', path, **kwargs)

    def enable_csrf(self) -> str:
        token = generate_csrf_token()
        self.cookies[CSRF_COOKIE_NAME] = token
        return token

    def csrf_headers(self, token: str | None = None) -> dict[str, str]:
        token = token or self.cookies.get(CSRF_COOKIE_NAME) or self.enable_csrf()
        return {CSRF_HEADER: token}

    def csrf_form(self, data: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
        token = token or self.cookies.get(CSRF_COOKIE_NAME) or self.enable_csrf()
        payload = dict(data or {})
        payload[CSRF_FORM_FIELD] = token
        return payload
