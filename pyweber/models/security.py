"""OpenAPI security schemes and runtime enforcement."""

from __future__ import annotations

import base64
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Union

from pyweber.models.request import Request


VerifyCallable = Callable[..., Any]


class SecurityError(Exception):
    """Raised by verify callbacks when authentication fails."""

    status_code = 401

    def __init__(self, detail: str = 'Unauthorized', status_code: int | None = None):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail)


class ForbiddenError(SecurityError):
    """Raised by verify callbacks when the principal is authenticated but not allowed."""

    status_code = 403

    def __init__(self, detail: str = 'Forbidden'):
        super().__init__(detail=detail, status_code=403)


@dataclass
class AuthContext:
    scheme: str
    credentials: Any = None
    user: Any = None
    scopes: list[str] = field(default_factory=list)


@dataclass
class SecurityChallenge:
    ok: bool
    status_code: int = 401
    detail: str = 'Unauthorized'
    auth: AuthContext | None = None
    www_authenticate: str | None = None


class SecurityScheme:
    """Base OpenAPI security scheme with credential extraction."""

    type: str = 'http'

    def __init__(self, *, verify: VerifyCallable | None = None, description: str | None = None):
        self.verify = verify
        self.description = description

    def to_openapi(self) -> dict[str, Any]:
        raise NotImplementedError

    def extract(self, request: Request) -> Any | None:
        raise NotImplementedError

    def www_authenticate(self) -> str | None:
        return None


class HTTPBearer(SecurityScheme):
    def __init__(
        self,
        *,
        bearer_format: str | None = 'JWT',
        verify: VerifyCallable | None = None,
        description: str | None = None,
        auto_error: bool = True,
    ):
        super().__init__(verify=verify, description=description)
        self.bearer_format = bearer_format
        self.auto_error = auto_error
        self.scheme = 'bearer'

    def to_openapi(self) -> dict[str, Any]:
        data: dict[str, Any] = {'type': 'http', 'scheme': 'bearer'}
        if self.bearer_format:
            data['bearerFormat'] = self.bearer_format
        if self.description:
            data['description'] = self.description
        return data

    def extract(self, request: Request) -> str | None:
        auth = _header(request, 'authorization')
        if not auth:
            return None
        parts = auth.split(' ', 1)
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        token = parts[1].strip()
        return token or None

    def www_authenticate(self) -> str | None:
        return 'Bearer'


class HTTPBasic(SecurityScheme):
    def __init__(
        self,
        *,
        realm: str = 'Pyweber',
        verify: VerifyCallable | None = None,
        description: str | None = None,
    ):
        super().__init__(verify=verify, description=description)
        self.realm = realm
        self.scheme = 'basic'

    def to_openapi(self) -> dict[str, Any]:
        data: dict[str, Any] = {'type': 'http', 'scheme': 'basic'}
        if self.description:
            data['description'] = self.description
        return data

    def extract(self, request: Request) -> tuple[str, str] | None:
        auth = _header(request, 'authorization')
        if not auth:
            return None
        parts = auth.split(' ', 1)
        if len(parts) != 2 or parts[0].lower() != 'basic':
            return None
        try:
            decoded = base64.b64decode(parts[1].strip()).decode('utf-8')
        except Exception:
            return None
        if ':' not in decoded:
            return None
        username, _, password = decoded.partition(':')
        return username, password

    def www_authenticate(self) -> str | None:
        return f'Basic realm="{self.realm}"'


class APIKeyHeader(SecurityScheme):
    def __init__(
        self,
        *,
        name: str = 'X-API-Key',
        verify: VerifyCallable | None = None,
        description: str | None = None,
    ):
        super().__init__(verify=verify, description=description)
        self.name = name
        self.location = 'header'

    def to_openapi(self) -> dict[str, Any]:
        data: dict[str, Any] = {'type': 'apiKey', 'in': 'header', 'name': self.name}
        if self.description:
            data['description'] = self.description
        return data

    def extract(self, request: Request) -> str | None:
        value = _header(request, self.name.lower())
        return value or None


class APIKeyQuery(SecurityScheme):
    def __init__(
        self,
        *,
        name: str = 'api_key',
        verify: VerifyCallable | None = None,
        description: str | None = None,
    ):
        super().__init__(verify=verify, description=description)
        self.name = name
        self.location = 'query'

    def to_openapi(self) -> dict[str, Any]:
        data: dict[str, Any] = {'type': 'apiKey', 'in': 'query', 'name': self.name}
        if self.description:
            data['description'] = self.description
        return data

    def extract(self, request: Request) -> str | None:
        value = (request.query_params or {}).get(self.name)
        return value or None


class APIKeyCookie(SecurityScheme):
    def __init__(
        self,
        *,
        name: str = 'session',
        verify: VerifyCallable | None = None,
        description: str | None = None,
    ):
        super().__init__(verify=verify, description=description)
        self.name = name
        self.location = 'cookie'

    def to_openapi(self) -> dict[str, Any]:
        data: dict[str, Any] = {'type': 'apiKey', 'in': 'cookie', 'name': self.name}
        if self.description:
            data['description'] = self.description
        return data

    def extract(self, request: Request) -> str | None:
        value = (request.cookies or {}).get(self.name)
        return value or None


def _header(request: Request, name: str) -> str | None:
    headers = request.headers or {}
    # WSGI headers are lowercased; ASGI may preserve case
    for key, value in headers.items():
        if str(key).lower() == name.lower():
            return value
    return None


def normalize_security_requirements(
    security: list[str] | list[dict[str, list[str]]] | None,
) -> list[dict[str, list[str]]] | None:
    """None keeps inheritance; [] means public; list is normalized to OpenAPI security."""
    if security is None:
        return None
    if not security:
        return []

    normalized: list[dict[str, list[str]]] = []
    for item in security:
        if isinstance(item, str):
            normalized.append({item: []})
        elif isinstance(item, dict):
            normalized.append({str(k): list(v) if v else [] for k, v in item.items()})
        else:
            raise TypeError(f'Invalid security requirement: {item!r}')
    return normalized


class SecurityEnforcer:
    def __init__(self, schemes: dict[str, SecurityScheme] | None = None):
        self.schemes = schemes or {}

    def enforce(
        self,
        request: Request,
        requirements: list[dict[str, list[str]]] | None,
    ) -> SecurityChallenge:
        """Enforce OpenAPI-style security (OR across requirement objects).

        Empty list → public. None should be resolved by caller to global/default.
        """
        if not requirements:
            return SecurityChallenge(ok=True)

        last_failure = SecurityChallenge(
            ok=False,
            status_code=401,
            detail='Unauthorized',
        )

        for requirement in requirements:
            if not requirement:
                return SecurityChallenge(ok=True)

            challenge = self._enforce_and_requirement(request, requirement)
            if challenge.ok:
                return challenge
            last_failure = challenge

        return last_failure

    def _enforce_and_requirement(
        self,
        request: Request,
        requirement: dict[str, list[str]],
    ) -> SecurityChallenge:
        # AND across schemes inside one requirement object
        auth_contexts: list[AuthContext] = []
        www = None

        for scheme_name, scopes in requirement.items():
            scheme = self.schemes.get(scheme_name)
            if scheme is None:
                return SecurityChallenge(
                    ok=False,
                    status_code=401,
                    detail=f'Unknown security scheme: {scheme_name}',
                )

            credentials = scheme.extract(request)
            if credentials is None:
                return SecurityChallenge(
                    ok=False,
                    status_code=401,
                    detail='Not authenticated',
                    www_authenticate=scheme.www_authenticate(),
                )

            user = None
            if scheme.verify is not None:
                try:
                    result = self._call_verify(scheme.verify, credentials, request, scopes)
                except ForbiddenError as exc:
                    return SecurityChallenge(
                        ok=False,
                        status_code=403,
                        detail=str(exc.detail),
                        www_authenticate=scheme.www_authenticate(),
                    )
                except SecurityError as exc:
                    return SecurityChallenge(
                        ok=False,
                        status_code=exc.status_code,
                        detail=str(exc.detail),
                        www_authenticate=scheme.www_authenticate(),
                    )
                except Exception as exc:
                    return SecurityChallenge(
                        ok=False,
                        status_code=401,
                        detail=str(exc) or 'Unauthorized',
                        www_authenticate=scheme.www_authenticate(),
                    )

                if result is False or result is None:
                    return SecurityChallenge(
                        ok=False,
                        status_code=401,
                        detail='Invalid credentials',
                        www_authenticate=scheme.www_authenticate(),
                    )
                if isinstance(result, str):
                    return SecurityChallenge(
                        ok=False,
                        status_code=401,
                        detail=result,
                        www_authenticate=scheme.www_authenticate(),
                    )
                if result is not True:
                    user = result

            auth_contexts.append(
                AuthContext(
                    scheme=scheme_name,
                    credentials=credentials,
                    user=user,
                    scopes=list(scopes or []),
                )
            )
            www = scheme.www_authenticate()

        primary = auth_contexts[0] if auth_contexts else None
        return SecurityChallenge(ok=True, auth=primary, www_authenticate=www)

    @staticmethod
    def _call_verify(
        verify: VerifyCallable,
        credentials: Any,
        request: Request,
        scopes: list[str],
    ) -> Any:
        sig = inspect.signature(verify)
        kwargs: dict[str, Any] = {}
        params = list(sig.parameters.values())

        # Positional-friendly: verify(credentials) / verify(credentials, request)
        if not params:
            return verify()

        bound: dict[str, Any] = {}
        names = {p.name for p in params}
        if 'credentials' in names:
            bound['credentials'] = credentials
        if 'request' in names:
            bound['request'] = request
        if 'scopes' in names:
            bound['scopes'] = scopes

        if bound:
            return verify(**{k: v for k, v in bound.items() if k in names})

        # Fall back to positional
        args: list[Any] = [credentials]
        if len(params) >= 2:
            args.append(request)
        if len(params) >= 3:
            args.append(scopes)
        return verify(*args[: len(params)])
