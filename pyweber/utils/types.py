import os
from enum import Enum
from importlib.resources import files

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Cores básicas
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    # Cores em fundo
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Cores com negrito
    BOLD_RED = "\033[1;91m"
    BOLD_GREEN = "\033[1;92m"
    BOLD_YELLOW = "\033[1;93m"
    BOLD_BLUE = "\033[1;94m"
    BOLD_MAGENTA = "\033[1;95m"
    BOLD_CYAN = "\033[1;96m"
    BOLD_WHITE = "\033[1;97m"

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

class OrientationType(Enum):
    LANDSCAPE_PRIMARY = "landscape-primary"
    LANDSCAPE_SECONDARY = "landscape-secondary"
    PORTRAIT_PRIMARY = "portrait-primary"
    PORTRAIT_SECONDARY = "portrait-secondary"

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
    html_500 = files(anchor='pyweber').joinpath(os.path.join('static', 'html500.html'))
    html_401 = files(anchor='pyweber').joinpath(os.path.join('static', 'html401.html'))
    js_base = files(anchor='pyweber').joinpath(os.path.join('static', 'js.js'))
    css_base = files(anchor='pyweber').joinpath(os.path.join('static', 'css.css'))
    main_base = files(anchor='pyweber').joinpath(os.path.join('static', 'main.py'))
    favicon_path = files(anchor='pyweber').joinpath(os.path.join('static', 'favicon'))
    config_default = files(anchor='pyweber').joinpath(os.path.join('static', 'config.toml'))
    pyweber_css = files(anchor='pyweber').joinpath(os.path.join('static', 'pyweber.css'))

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

class GetBy(Enum):
    tag = 'tag'
    classes = 'classes'
    id = 'id'
    content = 'content'
    value = 'value'
    attrs = 'attrs'
    style = 'style'
    uuid = 'uuid'