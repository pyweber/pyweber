from enum import Enum

class ContentTypes(Enum):
    html = "text/html"
    css = "text/css"
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

    def content_list() -> list:
        return [value.name for value in ContentTypes]

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