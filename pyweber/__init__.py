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

from .utils.types import (
    ContentTypes,
    EventType,
    HTMLTag,
    HTTPStatusCode,
    JWTAlgorithms,
    NonSelfClosingHTMLTags,
    WebSocketStatusCode,
    WindowEventType,
    Icons,
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
    DoubleFormnat
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
    'Icon',
    'Style',
    'Script',
    'Form',
    'Input',
    'InputButton',
    'InputCheckbox',
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
