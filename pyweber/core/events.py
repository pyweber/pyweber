from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber
    from pyweber.core.template import Template, Element
    from pyweber.models.ws_message import wsMessage
    from pyweber.core.window import Window

class EventData:
    def __init__(self, event_data: dict[str, int]):
        self.clientX = event_data.get('clientX', None)
        self.clientY = event_data.get('clientY', None)
        self.key = event_data.get('key', None)
        self.deltaX = event_data.get('deltaX', None)
        self.deltaY = event_data.get('deltaY', None)
        self.touches = event_data.get('touches', None)
        self.timestamp = event_data.get('timestamp', None)

    def __repr__(self):
        return f'EventData(key: {self.key}, clientX: {self.clientX}, clientY: {self.clientY}, timestamp: {self.timestamp})'

class EventHandler:
    def __init__(
        self,
        event_type: str,
        route: str,
        element: 'Element',
        template: 'Template',
        window: 'Window',
        event_data: EventData,
        app: 'Pyweber',
        session_id: str,
        update_hander: Callable,
        reload_handler: Callable
    ):
        self.event_type = event_type
        self.route = route
        self.app = app
        self.element = element
        self.template = template
        self.window = window
        self.event_data = event_data
        self.__update = update_hander
        self.__reload = reload_handler
        self.session_id = session_id
    
    def update(self):
        return self.__update(self.session_id)
    
    def reload(self):
        self.__reload(self.session_id)
        return self.update()
    
    def __repr__(self):
        return f'EventHandler(event_type: {self.event_type}, route: {self.route})'

class EventConstrutor:
    def __init__(self, ws_message: 'wsMessage', ws_update: Callable, ws_reload: Callable):
        self.__ws_message = ws_message
        self.__update = ws_update
        self.__reload = ws_reload
    
    @property
    def __template(self) -> 'Template':
        return self.__ws_message.template
    
    @property
    def __window(self) -> 'Window':
        return self.__ws_message.window
    
    @property
    def __target_element(self) -> 'Element':
        return self.__template.getElementByUUID(
            element_uuid=self.__ws_message.target_uuid
        )
    
    @property
    def __app(self) -> 'Pyweber':
        return self.__ws_message._wsMessage__app
    
    @property
    def build_event(self):
        return EventHandler(
            event_type=self.__ws_message.type,
            route=self.__ws_message.route,
            element=self.__target_element,
            template=self.__template,
            window=self.__window,
            event_data=EventData(
                event_data=self.__ws_message.event_data
            ),
            app=self.__app,
            session_id=self.__ws_message.session_id,
            update_hander=self.__update,
            reload_handler=self.__reload
        )

class TemplateEvents:
    def __init__(
        self,
        # Eventos de Mouse
        onclick: Callable = None,
        ondblclick: Callable = None,
        onmousedown: Callable = None,
        onmouseup: Callable = None,
        onmousemove: Callable = None,
        onmouseover: Callable = None,
        onmouseout: Callable = None,
        onmouseenter: Callable = None,
        onmouseleave: Callable = None,
        oncontextmenu: Callable = None,
        onwheel: Callable = None,

        # Eventos de Teclado
        onkeydown: Callable = None,
        onkeyup: Callable = None,
        onkeypress: Callable = None,

        # Eventos de Formulário
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onsubmit: Callable = None,
        onreset: Callable = None,
        onselect: Callable = None,

        # Eventos de Drag & Drop
        ondrag: Callable = None,
        ondragstart: Callable = None,
        ondragend: Callable = None,
        ondragover: Callable = None,
        ondragenter: Callable = None,
        ondragleave: Callable = None,
        ondrop: Callable = None,

        # Eventos de Scroll e Resize
        onscroll: Callable = None,
        onresize: Callable = None,

        # Eventos de Mídia
        onplay: Callable = None,
        onpause: Callable = None,
        onended: Callable = None,
        onvolumechange: Callable = None,
        onseeked: Callable = None,
        onseeking: Callable = None,
        ontimeupdate: Callable = None,

        # Eventos de Rede
        ononline: Callable = None,
        onoffline: Callable = None,

        # Eventos de Toque (Mobile)
        ontouchstart: Callable = None,
        ontouchmove: Callable = None,
        ontouchend: Callable = None,
        ontouchcancel: Callable = None,
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
        onafterprint: Callable = None,
        onbeforeprint: Callable = None,
        onbeforeunload: Callable = None,
        onhashchange: Callable = None,
        onload: Callable = None,
        onunload: Callable = None,
        onpageshow: Callable = None,
        onpagehide: Callable = None,
        onpopstate: Callable = None,
        onDOMContentLoaded: Callable = None,

        # Eventos de Rede
        ononline: Callable = None,
        onoffline: Callable = None,

        # Eventos de Armazenamento
        onstorage: Callable = None,

        # Eventos de Mensagens e Comunicação
        onmessage: Callable = None,
        onmessageerror: Callable = None,

        # Eventos de Animação e Transição
        onanimationstart: Callable = None,
        onanimationend: Callable = None,
        onanimationiteration: Callable = None,
        ontransitionstart: Callable = None,
        ontransitionend: Callable = None,
        ontransitioncancel: Callable = None,

        # Eventos de Fullscreen e Pointer Lock
        onfullscreenchange: Callable = None,
        onfullscreenerror: Callable = None,
        onpointerlockchange: Callable = None,
        onpointerlockerror: Callable = None,

        # Eventos de Dispositivo
        ondevicemotion: Callable = None,
        ondeviceorientation: Callable = None,
        ondeviceorientationabsolute: Callable = None,
        onorientationchange: Callable = None,

        # Eventos de Gamepad
        ongamepadconnected: Callable = None,
        ongamepaddisconnected: Callable = None,

        # Eventos de VR
        onvrdisplayconnect: Callable = None,
        onvrdisplaydisconnect: Callable = None,
        onvrdisplaypresentchange: Callable = None,
        onvrdisplayactivate: Callable = None,
        onvrdisplaydeactivate: Callable = None,
        onvrdisplayblur: Callable = None,
        onvrdisplayfocus: Callable = None,
        onvrdisplaypointerrestricted: Callable = None,
        onvrdisplaypointerunrestricted: Callable = None,

        # Eventos de Service Worker e Cache
        oninstall: Callable = None,
        onactivate: Callable = None,
        onfetch: Callable = None,
        onnotificationclick: Callable = None,
        onnotificationclose: Callable = None,
        onpush: Callable = None,
        onpushsubscriptionchange: Callable = None,
        onsync: Callable = None,
        onperiodicsync: Callable = None,
        onbackgroundfetchsuccess: Callable = None,
        onbackgroundfetchfailure: Callable = None,
        onbackgroundfetchabort: Callable = None,
        onbackgroundfetchclick: Callable = None,
        oncontentdelete: Callable = None,

        # Eventos de Clipboard
        oncut: Callable = None,
        oncopy: Callable = None,
        onpaste: Callable = None,

        # Eventos de Seleção de Texto
        onselectionchange: Callable = None,

        # Eventos de Visibilidade
        onvisibilitychange: Callable = None,

        # Eventos de Rejeição de Promises
        onrejectionhandled: Callable = None,
        onunhandledrejection: Callable = None,

        # Eventos de Segurança
        onsecuritypolicyviolation: Callable = None,
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