from enum import Enum
import os
from importlib.resources import files

class JWTAlgorithms(Enum):
    HS256 = 'HS256'
    HS384 = 'HS384'
    HS512 = 'HS512'
    RS256 = 'RS256'
    RS384 = 'RS384'
    RS512 = 'RS512'
    ES256 = 'ES256'
    ES384 = 'ES384'
    ES512 = 'ES512'
    PS256 = 'PS256'
    PS384 = 'PS384'
    PS512 = 'PS512'

class ContentTypes(Enum):
    html = "text/html"
    css = "text/css"
    unkown = 'application/octet-stream'
    js = "application/javascript"
    json = "application/json"
    png = "image/png"
    jpg = "image/jpeg"
    jpeg = "image/jpeg"
    gif = "image/gif"
    svg = "image/svg+xml"
    ico = "image/x-icon"
    woff = "font/woff"
    woff2 = "font/woff2"
    ttf = "font/ttf"
    otf = "font/otf"
    eot = "application/vnd.ms-fontobject"
    mp4 = "video/mp4"
    webm = "video/webm"
    ogv = "video/ogg"
    avi = "video/x-msvideo"
    mov = "video/quicktime"
    flv = "video/x-flv"
    mkv = "video/x-matroska"
    zip = 'application/zip'
    zip7 = 'application/x-7z-compressed'

    def content_list() -> list[str]:
        return [value.name for value in ContentTypes]

class StaticFilePath(Enum):
    html_base = files(anchor='pyweber').joinpath(os.path.join('static', 'html.html'))
    html_404 = files(anchor='pyweber').joinpath(os.path.join('static', 'html404.html'))
    html_401 = files(anchor='pyweber').joinpath(os.path.join('static', 'html401.html'))
    js_base = files(anchor='pyweber').joinpath(os.path.join('static', 'js.js'))
    css_base = files(anchor='pyweber').joinpath(os.path.join('static', 'css.css'))
    main_base = files(anchor='pyweber').joinpath(os.path.join('static', 'main.py'))
    favicon_path = files(anchor='pyweber').joinpath(os.path.join('static', 'favicon'))

class WebSocketStatusCode(Enum):
    NORMAL_CLOSURE = "1000 Normal Closure"
    GOING_AWAY = "1001 Going Away"
    PROTOCOL_ERROR = "1002 Protocol Error"
    UNSUPPORTED_DATA = "1003 Unsupported Data"
    NO_STATUS_RECEIVED = "1005 No Status Received"
    ABNORMAL_CLOSURE = "1006 Abnormal Closure"
    INVALID_FRAME_PAYLOAD_DATA = "1007 Invalid Frame Payload Data"
    POLICY_VIOLATION = "1008 Policy Violation"
    MESSAGE_TOO_BIG = "1009 Message Too Big"
    MANDATORY_EXTENSION = "1010 Mandatory Extension"
    INTERNAL_SERVER_ERROR = "1011 Internal Server Error"
    SERVICE_RESTART = "1012 Service Restart"
    TRY_AGAIN_LATER = "1013 Try Again Later"
    BAD_GATEWAY = "1014 Bad Gateway"
    TLS_HANDSHAKE = "1015 TLS Handshake Failure"

    def content_list() -> list[int]:
        return [int(value.value.split(' ')[0]) for value in WebSocketStatusCode]
    
    def search_by_code(code: int):
        for value in WebSocketStatusCode:
            return value.value if str(code) in value.value else WebSocketStatusCode.INTERNAL_SERVER_ERROR.value

class HTTPStatusCode(Enum):
    # Informational Responses (1xx)
    CONTINUE = "100 Continue"
    SWITCHING_PROTOCOLS = "101 Switching Protocols"
    PROCESSING = "102 Processing"

    # Successful Responses (2xx)
    OK = "200 OK"
    CREATED = "201 Created"
    ACCEPTED = "202 Accepted"
    NON_AUTHORITATIVE_INFORMATION = "203 Non-Authoritative Information"
    NO_CONTENT = "204 No Content"
    RESET_CONTENT = "205 Reset Content"
    PARTIAL_CONTENT = "206 Partial Content"

    # Redirection Messages (3xx)
    MULTIPLE_CHOICES = "300 Multiple Choices"
    MOVED_PERMANENTLY = "301 Moved Permanently"
    FOUND = "302 Found"
    SEE_OTHER = "303 See Other"
    NOT_MODIFIED = "304 Not Modified"
    USE_PROXY = "305 Use Proxy"
    TEMPORARY_REDIRECT = "307 Temporary Redirect"
    PERMANENT_REDIRECT = "308 Permanent Redirect"

    # Client Error Responses (4xx)
    BAD_REQUEST = "400 Bad Request"
    UNAUTHORIZED = "401 Unauthorized"
    FORBIDDEN = "402 Forbidden"
    NOT_FOUND = "404 Not Found"
    METHOD_NOT_ALLOWED = "405 Method Not Allowed"
    NOT_ACCEPTABLE = "406 Not Acceptable"
    PROXY_AUTHENTICATION_REQUIRED = "407 Proxy Authentication Required"
    REQUEST_TIMEOUT = "408 Request Timeout"
    CONFLICT = "409 Conflict"
    GONE = "410 Gone"
    LENGTH_REQUIRED = "411 Length Required"
    PRECONDITION_FAILED = "412 Precondition Failed"
    PAYLOAD_TOO_LARGE = "413 Payload Too Large"
    URI_TOO_LONG = "414 URI Too Long"
    UNSUPPORTED_MEDIA_TYPE = "415 Unsupported Media Type"
    RANGE_NOT_SATISFIABLE = "416 Range Not Satisfiable"
    EXPECTATION_FAILED = "417 Expectation Failed"
    IM_A_TEAPOT = "418 I'm a teapot (joke HTTP status code)"
    MISDIRECTED_REQUEST = "421 Misdirected Request"
    UNPROCESSABLE_ENTITY = "422 Unprocessable Entity"
    LOCKED = "423 Locked"
    FAILED_DEPENDENCY = "424 Failed Dependency"
    TOO_EARLY = "425 Too Early"
    UPGRADE_REQUIRED = "426 Upgrade Required"
    PRECONDITION_REQUIRED = "428 Precondition Required"
    TOO_MANY_REQUESTS = "429 Too Many Requests"
    REQUEST_HEADER_FIELDS_TOO_LARGE = "431 Request Header Fields Too Large"
    UNAVAILABLE_FOR_LEGAL_REASONS = "451 Unavailable For Legal Reasons"

    # Server Error Responses (5xx)
    INTERNAL_SERVER_ERROR = "500 Internal Server Error"
    NOT_IMPLEMENTED = "501 Not Implemented"
    BAD_GATEWAY = "502 Bad Gateway"
    SERVICE_UNAVAILABLE = "503 Service Unavailable"
    GATEWAY_TIMEOUT = "504 Gateway Timeout"
    VERSION_NOT_SUPPORTED = "505 Version Not Supported"
    VARIANT_ALSO_NEGOTIATES = "506 Variant Also Negotiates"
    INSUFFICIENT_STORAGE = "507 Insufficient Storage"
    LOOP_DETECTED = "508 Loop Detected"
    NOT_EXTENDED = "510 Not Extended"
    NETWORK_AUTHENTICATION_REQUIRED = "511 Network Authentication Required"

    def code_list() -> list[int]:
        return [int(value.value.split(' ')[0]) for value in HTTPStatusCode]
    
    def search_by_code(code: int) -> str:
        for value in HTTPStatusCode:
            if str(code) in value.value:
                return value.value
        
        return HTTPStatusCode.NOT_FOUND.value

class EventType(Enum):
    # Mouse Events
    CLICK = "onclick"
    DBLCLICK = "ondblclick"
    MOUSEDOWN = "onmousedown"
    MOUSEUP = "onmouseup"
    MOUSEMOVE = "onmousemove"
    MOUSEOVER = "onmouseover"
    MOUSEOUT = "onmouseout"
    MOUSEENTER = "onmouseenter"
    MOUSELEAVE = "onmouseleave"
    CONTEXTMENU = "oncontextmenu"
    WHEEL = "onwheel"

    # Keyboard Events
    KEYDOWN = "onkeydown"
    KEYUP = "onkeyup"
    KEYPRESS = "onkeypress"

    # Form Events
    FOCUS = "onfocus"
    BLUR = "onblur"
    CHANGE = "onchange"
    INPUT = "oninput"
    SUBMIT = "onsubmit"
    RESET = "onreset"
    SELECT = "onselect"

    # Drag & Drop Events
    DRAG = "ondrag"
    DRAGSTART = "ondragstart"
    DRAGEND = "ondragend"
    DRAGOVER = "ondragover"
    DRAGENTER = "ondragenter"
    DRAGLEAVE = "ondragleave"
    DROP = "ondrop"

    # Scroll & Resize Events
    SCROLL = "onscroll"
    RESIZE = "onresize"

    # Media Events
    PLAY = "onplay"
    PAUSE = "onpause"
    ENDED = "onended"
    VOLUMECHANGE = "onvolumechange"
    SEEKED = "onseeked"
    SEEKING = "onseeking"
    TIMEUPDATE = "ontimeupdate"

    # Network Events
    ONLINE = "ononline"
    OFFLINE = "onoffline"

    # Touch Events (Mobile)
    TOUCHSTART = "ontouchstart"
    TOUCHMOVE = "ontouchmove"
    TOUCHEND = "ontouchend"
    TOUCHCANCEL = "ontouchcancel"


class Events:
    def __init__(
        self,
        # Eventos de Mouse
        onclick: callable = None,
        ondblclick: callable = None,
        onmousedown: callable = None,
        onmouseup: callable = None,
        onmousemove: callable = None,
        onmouseover: callable = None,
        onmouseout: callable = None,
        onmouseenter: callable = None,
        onmouseleave: callable = None,
        oncontextmenu: callable = None,
        onwheel: callable = None,

        # Eventos de Teclado
        onkeydown: callable = None,
        onkeyup: callable = None,
        onkeypress: callable = None,

        # Eventos de Formulário
        onfocus: callable = None,
        onblur: callable = None,
        onchange: callable = None,
        oninput: callable = None,
        onsubmit: callable = None,
        onreset: callable = None,
        onselect: callable = None,

        # Eventos de Drag & Drop
        ondrag: callable = None,
        ondragstart: callable = None,
        ondragend: callable = None,
        ondragover: callable = None,
        ondragenter: callable = None,
        ondragleave: callable = None,
        ondrop: callable = None,

        # Eventos de Scroll e Resize
        onscroll: callable = None,
        onresize: callable = None,

        # Eventos de Mídia
        onplay: callable = None,
        onpause: callable = None,
        onended: callable = None,
        onvolumechange: callable = None,
        onseeked: callable = None,
        onseeking: callable = None,
        ontimeupdate: callable = None,

        # Eventos de Rede
        ononline: callable = None,
        onoffline: callable = None,

        # Eventos de Toque (Mobile)
        ontouchstart: callable = None,
        ontouchmove: callable = None,
        ontouchend: callable = None,
        ontouchcancel: callable = None,
    ):
        # Eventos de Mouse
        self.onclick = onclick
        self.ondblclick = ondblclick
        self.onmousedown = onmousedown
        self.onmouseup = onmouseup
        self.onmousemove = onmousemove
        self.onmouseover = onmouseover
        self.onmouseout = onmouseout
        self.onmouseenter = onmouseenter
        self.onmouseleave = onmouseleave
        self.oncontextmenu = oncontextmenu
        self.onwheel = onwheel

        # Eventos de Teclado
        self.onkeydown = onkeydown
        self.onkeyup = onkeyup
        self.onkeypress = onkeypress

        # Eventos de Formulário
        self.onfocus = onfocus
        self.onblur = onblur
        self.onchange = onchange
        self.oninput = oninput
        self.onsubmit = onsubmit
        self.onreset = onreset
        self.onselect = onselect

        # Eventos de Drag & Drop
        self.ondrag = ondrag
        self.ondragstart = ondragstart
        self.ondragend = ondragend
        self.ondragover = ondragover
        self.ondragenter = ondragenter
        self.ondragleave = ondragleave
        self.ondrop = ondrop

        # Eventos de Scroll e Resize
        self.onscroll = onscroll
        self.onresize = onresize

        # Eventos de Mídia
        self.onplay = onplay
        self.onpause = onpause
        self.onended = onended
        self.onvolumechange = onvolumechange
        self.onseeked = onseeked
        self.onseeking = onseeking
        self.ontimeupdate = ontimeupdate

        # Eventos de Rede
        self.ononline = ononline
        self.onoffline = onoffline

        # Eventos de Toque (Mobile)
        self.ontouchstart = ontouchstart
        self.ontouchmove = ontouchmove
        self.ontouchend = ontouchend
        self.ontouchcancel = ontouchcancel

    def __repr__(self):
        """Representação legível dos eventos."""
        events = {k: v for k, v in self.__dict__.items() if v is not None}
        return f"Events({events})"