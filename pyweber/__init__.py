# pyweber run
from .models.run import (
    run,
    run_as_asgi
)

# pyweber sessions
from .connection.session import sessions

# pyweber config
from .config.config import config

# pyweber app
from .pyweber.pyweber import Pyweber

# pyweber core
from .core.element import Element
from .core.template import Template
from .core.window import window

# pyweber models
from .models.response import Response
from .models.routes import (
    Route,
    RedirectRoute
)

from .models.request import Request
from .models.field import Field
from .models.file import File
from .models.field_storage import FieldStorage
from .models.headers import Headers

from .models.file_stream import (
    file_chunk_manager,
    FileResult
)
from .models.strem_stats import (
    AdaptiveController,
    StreamStats
)
from .models.openapi import (
    OpenApiProcessor,
    OpenAPIConfig,
    OpenAPIBuilder,
    HTTPBearer,
    HTTPBasic,
    APIKeyHeader,
    APIKeyQuery,
    APIKeyCookie,
)
from .models.security import (
    AuthContext,
    SecurityEnforcer,
    SecurityError,
    ForbiddenError,
)

# pyweber events
from .core.events import (
    EventHandler,
    TemplateEvents,
    WindowEvents
)

# pyweber utils
from .utils.loads import LoadStaticFiles
from .utils.utils import (
    PrintLine,
    WriteLine,
    Colors
)
from .utils.security import (
    secure_filename,
    safe_join,
    sign_value,
    unsign_value,
    generate_csrf_token,
    get_csrf_token,
)
from .utils.icons import Icons
from .utils.deprecation import warn_deprecated
from .testing import TestClient
from .auth import (
    login_required,
    login_user,
    logout_user,
    current_user,
    get_user_id,
    hash_password,
    check_password,
    permission_required,
    role_required,
    register_roles,
    clear_roles,
    define_role,
    has_role,
    has_all_roles,
    has_permission,
    user_permissions,
)

from .utils.types import (
    ContentTypes,
    EventType,
    HTMLTag,
    HTTPStatusCode,
    JWTAlgorithms,
    NonSelfClosingHTMLTags,
    WebSocketStatusCode,
    WindowEventType,
    GetBy,
    DateFormat,
    DateTimeFormat,
    PasswordFormat,
    ByteFormat,
    EmailFormat,
    UuidFormat,
    UrlFormat,
    HostnameFormat,
    Ipv4Format,
    Ipv6Format,
    Int32Format,
    Int64Format,
    FloatFormat,
    DoubleFormat,
    DoubleFormnat,
)
from .utils.exceptions import (
    InvalidRouteFormatError,
    RouteAlreadyExistError,
    InvalidTemplateError,
    RouteNotFoundError,
    RouterError
)

# Pyweber Components
from .components.form import Form
from .components.general import (
    Icon,
    Style,
    Script,
    Label,
    TextArea
)

from .components.input import (
    Input,
    InputButton,
    InputCheckbox,
    InputColor,
    InputDate,
    InputEmail,
    InputFile,
    InputHidden,
    InputNumber,
    InputPassword,
    InputRadio,
    InputReset,
    InputRange,
    InputSearch,
    InputSubmit,
    InputTel,
    InputText,
    InputTime,
    InputUrl
)

def session_id() -> str | None:
    from pyweber.models.context import get_current_window

    ctx_window = get_current_window()
    if ctx_window and ctx_window.session_id:
        return ctx_window.session_id

    PrintLine(text='This is an experimental feature', level='WARNING')
    return None

def session():
    sid = session_id()
    if not sid:
        PrintLine(text='This is an experimental feature', level='WARNING')
        return None
    return sessions.get_session(sid)

__all__ = [
    'Template',
    'Pyweber',
    'run',
    'run_as_asgi',
    'Route',
    'RedirectRoute',
    'Headers',
    'File',
    'FieldStorage',
    'Field',
    'Request',
    'file_chunk_manager',
    'FileResult',
    'AdaptiveController',
    'StreamStats',
    'Response',
    'TemplateEvents',
    'WindowEvents',
    'EventHandler',
    'Element',
    'sessions',
    'session',
    'session_id',
    'window',
    'config',
    'Colors',
    'PrintLine',
    'WriteLine',
    'LoadStaticFiles',
    'secure_filename',
    'safe_join',
    'sign_value',
    'unsign_value',
    'generate_csrf_token',
    'get_csrf_token',
    'ContentTypes',
    'EventType',
    'HTMLTag',
    'GetBy',
    'Icons',
    'DateFormat',
    'DateTimeFormat',
    'PasswordFormat',
    'ByteFormat',
    'EmailFormat',
    'UuidFormat',
    'UrlFormat',
    'HostnameFormat',
    'Ipv4Format',
    'Ipv6Format',
    'Int32Format',
    'Int64Format',
    'FloatFormat',
    'DoubleFormat',
    'DoubleFormnat',
    'HTTPStatusCode',
    'JWTAlgorithms',
    'NonSelfClosingHTMLTags',
    'WebSocketStatusCode',
    'WindowEventType',
    'InvalidRouteFormatError',
    'RouteAlreadyExistError',
    'InvalidTemplateError',
    'RouteNotFoundError',
    'RouterError',
    'TestClient',
    'warn_deprecated',
    'OpenApiProcessor',
    'OpenAPIConfig',
    'OpenAPIBuilder',
    'HTTPBearer',
    'HTTPBasic',
    'APIKeyHeader',
    'APIKeyQuery',
    'APIKeyCookie',
    'AuthContext',
    'SecurityEnforcer',
    'SecurityError',
    'ForbiddenError',
    'login_required',
    'login_user',
    'logout_user',
    'current_user',
    'get_user_id',
    'hash_password',
    'check_password',
    'permission_required',
    'role_required',
    'register_roles',
    'clear_roles',
    'define_role',
    'has_role',
    'has_all_roles',
    'has_permission',
    'user_permissions',
    'Icon',
    'Style',
    'Script',
    'Form',
    'Input',
    'InputButton',
    'InputCheckbox',
    'InputColor',
    'InputDate',
    'InputEmail',
    'InputFile',
    'InputHidden',
    'InputNumber',
    'InputPassword',
    'InputRadio',
    'InputReset',
    'InputRange',
    'InputSearch',
    'InputSubmit',
    'InputTel',
    'InputText',
    'InputTime',
    'InputUrl',
    'Label',
    'TextArea',
]
