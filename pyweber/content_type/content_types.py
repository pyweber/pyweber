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