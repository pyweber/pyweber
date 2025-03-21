from enum import Enum
import os
from importlib.resources import files

class Colors(Enum):
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"

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
            if str(code) in value.value:
                return value.value
        
        return WebSocketStatusCode.INTERNAL_SERVER_ERROR.value

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

from enum import Enum

class WindowEventType(Enum):
    # Eventos de Janela e Navegação
    AFTER_PRINT = "onafterprint"
    BEFORE_PRINT = "onbeforeprint"
    BEFORE_UNLOAD = "onbeforeunload"
    HASH_CHANGE = "onhashchange"
    LOAD = "onload"
    UNLOAD = "onunload"
    PAGE_SHOW = "onpageshow"
    PAGE_HIDE = "onpagehide"
    POP_STATE = "onpopstate"
    DOM_CONTENT_LOADED = "onDOMContentLoaded"

    # Eventos de Rede
    ONLINE = "ononline"
    OFFLINE = "onoffline"

    # Eventos de Armazenamento
    STORAGE = "onstorage"

    # Eventos de Mensagens e Comunicação
    MESSAGE = "onmessage"
    MESSAGE_ERROR = "onmessageerror"

    # Eventos de Animação e Transição
    ANIMATION_START = "onanimationstart"
    ANIMATION_END = "onanimationend"
    ANIMATION_ITERATION = "onanimationiteration"
    TRANSITION_START = "ontransitionstart"
    TRANSITION_END = "ontransitionend"
    TRANSITION_CANCEL = "ontransitioncancel"

    # Eventos de Fullscreen e Pointer Lock
    FULLSCREEN_CHANGE = "onfullscreenchange"
    FULLSCREEN_ERROR = "onfullscreenerror"
    POINTER_LOCK_CHANGE = "onpointerlockchange"
    POINTER_LOCK_ERROR = "onpointerlockerror"

    # Eventos de Dispositivo
    DEVICE_MOTION = "ondevicemotion"
    DEVICE_ORIENTATION = "ondeviceorientation"
    DEVICE_ORIENTATION_ABSOLUTE = "ondeviceorientationabsolute"
    ORIENTATION_CHANGE = "onorientationchange"

    # Eventos de Gamepad
    GAMEPAD_CONNECTED = "ongamepadconnected"
    GAMEPAD_DISCONNECTED = "ongamepaddisconnected"

    # Eventos de VR
    VR_DISPLAY_CONNECT = "onvrdisplayconnect"
    VR_DISPLAY_DISCONNECT = "onvrdisplaydisconnect"
    VR_DISPLAY_PRESENT_CHANGE = "onvrdisplaypresentchange"
    VR_DISPLAY_ACTIVATE = "onvrdisplayactivate"
    VR_DISPLAY_DEACTIVATE = "onvrdisplaydeactivate"
    VR_DISPLAY_BLUR = "onvrdisplayblur"
    VR_DISPLAY_FOCUS = "onvrdisplayfocus"
    VR_DISPLAY_POINTER_RESTRICTED = "onvrdisplaypointerrestricted"
    VR_DISPLAY_POINTER_UNRESTRICTED = "onvrdisplaypointerunrestricted"

    # Eventos de Service Worker e Cache
    INSTALL = "oninstall"
    ACTIVATE = "onactivate"
    FETCH = "onfetch"
    NOTIFICATION_CLICK = "onnotificationclick"
    NOTIFICATION_CLOSE = "onnotificationclose"
    PUSH = "onpush"
    PUSH_SUBSCRIPTION_CHANGE = "onpushsubscriptionchange"
    SYNC = "onsync"
    PERIODIC_SYNC = "onperiodicsync"
    BACKGROUND_FETCH_SUCCESS = "onbackgroundfetchsuccess"
    BACKGROUND_FETCH_FAILURE = "onbackgroundfetchfailure"
    BACKGROUND_FETCH_ABORT = "onbackgroundfetchabort"
    BACKGROUND_FETCH_CLICK = "onbackgroundfetchclick"
    CONTENT_DELETE = "oncontentdelete"

    # Eventos de Clipboard
    CUT = "oncut"
    COPY = "oncopy"
    PASTE = "onpaste"

    # Eventos de Seleção de Texto
    SELECTION_CHANGE = "onselectionchange"

    # Eventos de Visibilidade
    VISIBILITY_CHANGE = "onvisibilitychange"

    # Eventos de Rejeição de Promises
    REJECTION_HANDLED = "onrejectionhandled"
    UNHANDLED_REJECTION = "onunhandledrejection"

    # Eventos de Segurança
    SECURITY_POLICY_VIOLATION = "onsecuritypolicyviolation"

class HTMLTag(Enum):
    # Tags Semânticas e de Estruturação
    html = "html"
    head = "head"
    body = "body"
    title = "title"
    script = "script"
    noscript = "noscript"
    section = "section"
    nav = "nav"
    article = "article"
    aside = "aside"
    header = "header"
    footer = "footer"
    address = "address"
    main = "main"
    div = "div"
    span = "span"
    
    # Tags de Formatação de Texto
    p = "p"
    h1 = "h1"
    h2 = "h2"
    h3 = "h3"
    h4 = "h4"
    h5 = "h5"
    h6 = "h6"
    b = "b"
    strong = "strong"
    i = "i"
    em = "em"
    mark = "mark"
    small = "small"
    DEL = "del"
    ins = "ins"
    sub = "sub"
    sup = "sup"
    blockquote = "blockquote"
    cite = "cite"
    q = "q"
    code = "code"
    pre = "pre"
    kbd = "kbd"
    samp = "samp"
    var = "var"
    
    # Tags de Listas
    ul = "ul"
    ol = "ol"
    li = "li"
    dl = "dl"
    dt = "dt"
    dd = "dd"
    
    # Tags de Tabelas
    table = "table"
    caption = "caption"
    thead = "thead"
    tbody = "tbody"
    tfoot = "tfoot"
    tr = "tr"
    th = "th"
    td = "td"
    
    # Tags de Formulário
    form = "form"
    label = "label"
    input = "input"
    textarea = "textarea"
    button = "button"
    fieldset = "fieldset"
    legend = "legend"
    select = "select"
    optgroup = "optgroup"
    option = "option"
    datalist = "datalist"
    output = "output"
    progress = "progress"
    meter = "meter"
    
    # Tags de Mídia e Integração
    audio = "audio"
    video = "video"
    source = "source"
    track = "track"
    object = "object"
    param = "param"
    embed = "embed"
    iframe = "iframe"
    canvas = "canvas"
    svg = "svg"
    math = "math"
    
    # Tags de Metadados
    base = "base"
    link = "link"
    meta = "meta"
    style = "style"
    
    # Tags de Conteúdo Interativo
    details = "details"
    summary = "summary"
    dialog = "dialog"
    menu = "menu"
    menuitem = "menuitem"

class NonSelfClosingHTMLTags(Enum):
    # Tags Semânticas e de Estruturação
    html = "html"
    head = "head"
    body = "body"
    title = "title"
    script = "script"
    style = "style"
    noscript = "noscript"
    section = "section"
    nav = "nav"
    article = "article"
    aside = "aside"
    header = "header"
    footer = "footer"
    address = "address"
    main = "main"
    div = "div"
    span = "span"
    
    # Tags de Formatação de Texto
    p = "p"
    h1 = "h1"
    h2 = "h2"
    h3 = "h3"
    h4 = "h4"
    h5 = "h5"
    h6 = "h6"
    b = "b"
    strong = "strong"
    i = "i"
    em = "em"
    mark = "mark"
    small = "small"
    DEL = "del"
    ins = "ins"
    sub = "sub"
    sup = "sup"
    blockquote = "blockquote"
    cite = "cite"
    q = "q"
    code = "code"
    pre = "pre"
    kbd = "kbd"
    samp = "samp"
    var = "var"
    
    # Tags de Listas
    ul = "ul"
    ol = "ol"
    li = "li"
    dl = "dl"
    dt = "dt"
    dd = "dd"
    
    # Tags de Tabelas
    table = "table"
    caption = "caption"
    thead = "thead"
    tbody = "tbody"
    tfoot = "tfoot"
    tr = "tr"
    th = "th"
    td = "td"
    
    # Tags de Formulário
    form = "form"
    label = "label"
    textarea = "textarea"
    button = "button"
    fieldset = "fieldset"
    legend = "legend"
    select = "select"
    optgroup = "optgroup"
    option = "option"
    datalist = "datalist"
    output = "output"
    progress = "progress"
    meter = "meter"
    
    # Tags de Mídia e Integração
    audio = "audio"
    video = "video"
    object = "object"
    iframe = "iframe"
    canvas = "canvas"
    svg = "svg"
    math = "math"
    
    # Tags de Conteúdo Interativo
    details = "details"
    summary = "summary"
    dialog = "dialog"
    menu = "menu"
    menuitem = "menuitem"

    def non_autoclosing_tags() -> list[str]:
        return [val.value for val in NonSelfClosingHTMLTags]

class getBy(Enum):
    tag = 'tag'
    classes = 'classes'
    id = 'id'
    content = 'content'
    value = 'value'
    attrs = 'attrs'
    style = 'style'
    uuid = 'uuid'

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

class WindowEvents:
    def __init__(
        self,
        # Eventos de Janela e Navegação
        onafterprint: callable = None,
        onbeforeprint: callable = None,
        onbeforeunload: callable = None,
        onhashchange: callable = None,
        onload: callable = None,
        onunload: callable = None,
        onpageshow: callable = None,
        onpagehide: callable = None,
        onpopstate: callable = None,
        onDOMContentLoaded: callable = None,

        # Eventos de Rede
        ononline: callable = None,
        onoffline: callable = None,

        # Eventos de Armazenamento
        onstorage: callable = None,

        # Eventos de Mensagens e Comunicação
        onmessage: callable = None,
        onmessageerror: callable = None,

        # Eventos de Animação e Transição
        onanimationstart: callable = None,
        onanimationend: callable = None,
        onanimationiteration: callable = None,
        ontransitionstart: callable = None,
        ontransitionend: callable = None,
        ontransitioncancel: callable = None,

        # Eventos de Fullscreen e Pointer Lock
        onfullscreenchange: callable = None,
        onfullscreenerror: callable = None,
        onpointerlockchange: callable = None,
        onpointerlockerror: callable = None,

        # Eventos de Dispositivo
        ondevicemotion: callable = None,
        ondeviceorientation: callable = None,
        ondeviceorientationabsolute: callable = None,
        onorientationchange: callable = None,

        # Eventos de Gamepad
        ongamepadconnected: callable = None,
        ongamepaddisconnected: callable = None,

        # Eventos de VR
        onvrdisplayconnect: callable = None,
        onvrdisplaydisconnect: callable = None,
        onvrdisplaypresentchange: callable = None,
        onvrdisplayactivate: callable = None,
        onvrdisplaydeactivate: callable = None,
        onvrdisplayblur: callable = None,
        onvrdisplayfocus: callable = None,
        onvrdisplaypointerrestricted: callable = None,
        onvrdisplaypointerunrestricted: callable = None,

        # Eventos de Service Worker e Cache
        oninstall: callable = None,
        onactivate: callable = None,
        onfetch: callable = None,
        onnotificationclick: callable = None,
        onnotificationclose: callable = None,
        onpush: callable = None,
        onpushsubscriptionchange: callable = None,
        onsync: callable = None,
        onperiodicsync: callable = None,
        onbackgroundfetchsuccess: callable = None,
        onbackgroundfetchfailure: callable = None,
        onbackgroundfetchabort: callable = None,
        onbackgroundfetchclick: callable = None,
        oncontentdelete: callable = None,

        # Eventos de Clipboard
        oncut: callable = None,
        oncopy: callable = None,
        onpaste: callable = None,

        # Eventos de Seleção de Texto
        onselectionchange: callable = None,

        # Eventos de Visibilidade
        onvisibilitychange: callable = None,

        # Eventos de Rejeição de Promises
        onrejectionhandled: callable = None,
        onunhandledrejection: callable = None,

        # Eventos de Segurança
        onsecuritypolicyviolation: callable = None,
    ):
        # Eventos de Janela e Navegação
        self.onafterprint = onafterprint
        self.onbeforeprint = onbeforeprint
        self.onbeforeunload = onbeforeunload
        self.onhashchange = onhashchange
        self.onload = onload
        self.onunload = onunload
        self.onpageshow = onpageshow
        self.onpagehide = onpagehide
        self.onpopstate = onpopstate
        self.onDOMContentLoaded = onDOMContentLoaded

        # Eventos de Rede
        self.ononline = ononline
        self.onoffline = onoffline

        # Eventos de Armazenamento
        self.onstorage = onstorage

        # Eventos de Mensagens e Comunicação
        self.onmessage = onmessage
        self.onmessageerror = onmessageerror

        # Eventos de Animação e Transição
        self.onanimationstart = onanimationstart
        self.onanimationend = onanimationend
        self.onanimationiteration = onanimationiteration
        self.ontransitionstart = ontransitionstart
        self.ontransitionend = ontransitionend
        self.ontransitioncancel = ontransitioncancel

        # Eventos de Fullscreen e Pointer Lock
        self.onfullscreenchange = onfullscreenchange
        self.onfullscreenerror = onfullscreenerror
        self.onpointerlockchange = onpointerlockchange
        self.onpointerlockerror = onpointerlockerror

        # Eventos de Dispositivo
        self.ondevicemotion = ondevicemotion
        self.ondeviceorientation = ondeviceorientation
        self.ondeviceorientationabsolute = ondeviceorientationabsolute
        self.onorientationchange = onorientationchange

        # Eventos de Gamepad
        self.ongamepadconnected = ongamepadconnected
        self.ongamepaddisconnected = ongamepaddisconnected

        # Eventos de VR
        self.onvrdisplayconnect = onvrdisplayconnect
        self.onvrdisplaydisconnect = onvrdisplaydisconnect
        self.onvrdisplaypresentchange = onvrdisplaypresentchange
        self.onvrdisplayactivate = onvrdisplayactivate
        self.onvrdisplaydeactivate = onvrdisplaydeactivate
        self.onvrdisplayblur = onvrdisplayblur
        self.onvrdisplayfocus = onvrdisplayfocus
        self.onvrdisplaypointerrestricted = onvrdisplaypointerrestricted
        self.onvrdisplaypointerunrestricted = onvrdisplaypointerunrestricted

        # Eventos de Service Worker e Cache
        self.oninstall = oninstall
        self.onactivate = onactivate
        self.onfetch = onfetch
        self.onnotificationclick = onnotificationclick
        self.onnotificationclose = onnotificationclose
        self.onpush = onpush
        self.onpushsubscriptionchange = onpushsubscriptionchange
        self.onsync = onsync
        self.onperiodicsync = onperiodicsync
        self.onbackgroundfetchsuccess = onbackgroundfetchsuccess
        self.onbackgroundfetchfailure = onbackgroundfetchfailure
        self.onbackgroundfetchabort = onbackgroundfetchabort
        self.onbackgroundfetchclick = onbackgroundfetchclick
        self.oncontentdelete = oncontentdelete

        # Eventos de Clipboard
        self.oncut = oncut
        self.oncopy = oncopy
        self.onpaste = onpaste

        # Eventos de Seleção de Texto
        self.onselectionchange = onselectionchange

        # Eventos de Visibilidade
        self.onvisibilitychange = onvisibilitychange

        # Eventos de Rejeição de Promises
        self.onrejectionhandled = onrejectionhandled
        self.onunhandledrejection = onunhandledrejection

        # Eventos de Segurança
        self.onsecuritypolicyviolation = onsecuritypolicyviolation

    def __repr__(self):
        """Representação legível dos eventos."""
        events = {k: v for k, v in self.__dict__.items() if v is not None}
        return f"WindowEvents({events})"