from pyweber.utils.types import WindowEventType, OrientationType
from pyweber.core.events import WindowEvents

from threading import Timer

class Orientation:
    def __init__(self, angle: int, type: OrientationType, on_change: callable = None):
        self.angle = angle
        self.on_change = on_change
        self.type = type
    
    @property
    def on_change(self):
        return self.__on_change
    
    @on_change.setter
    def on_change(self, event: callable):
        if not event:
            self.__on_change = None
            return
        
        if not callable(event):
            raise TypeError('Event_handler must be a callable function')

        self.__on_change = event

class Screen:
    def __init__(
        self,
        width: float,
        height: float,
        colorDepth: int,
        pixelDepth: int,
        screenX: float,
        screenY: float,
        orientation: Orientation
    ):
        self.width = width
        self.height = height
        self.colorDepth = colorDepth
        self.pixelDepth = pixelDepth
        self.orientation = orientation
        self.screenX = screenX
        self.screenY = screenY

class Location:
    def __init__(
        self,
        host: str,
        url: str,
        origin: str,
        route: str,
        protocol: str
    ):
        self.host = host
        self.url = url
        self.origin = origin
        self.route = route
        self.protocol = protocol

class LocalStorage:
    """Localstorage"""

class SessionStorage:
    """SessionStorage"""


class Window:
    def __init__(self):
        self.__events_dict: dict[str, callable] = {}
        self.width: float = 0.0
        self.height: float = 0.0
        self.inner_width: float = 0.0
        self.inner_height: float = 0.0
        self.local_storage: LocalStorage = {}
        self.session_storage: SessionStorage = {}
        self.scroll_x: float = 0.0
        self.scroll_y: float = 0.0
        self.screen: Screen = None
        self.location: Location = None
        self.events = WindowEvents()
    
    def get_event(self, event_id: str) -> callable:
        return self.__events_dict.get(event_id, None)
    
    @property
    def get_all_event_ids(self):
        return list(self.__events_dict.keys())
    
    def __set_event_id(self):
        self.__events_dict.clear()
        for event, call in self.events.__dict__.items():
            if call is not None:
                key = f'{event}_{id(call)}'
                self.__events_dict[key] = call

    def __repr__(self):
        """Representação legível da janela."""
        return (
            f"Window(width={self.width}, height={self.height}, "
            f"inner_width={self.inner_width}, inner_height={self.inner_height}, "
            f"scroll_x={self.scroll_x}, scroll_y={self.scroll_y})"
        )
    
    @property
    def events(self):
        return self.__events
    
    @events.setter
    def events(self, event: WindowEvents):
        if not isinstance(event, WindowEvents):
            raise TypeError('Event_handler must be an Events instance')
        
        self.__events = event
        self.__set_event_id()
    
    def add_event(self, event_type: WindowEventType, event: callable):
        if not isinstance(event_type, event):
            raise TypeError('Event_type must be an EventType instance')
        
        if not callable(event):
            raise TypeError('Event_handler must be a callable function')
        
        setattr(self.__events, event_type.value, event)
        self.__set_event_id()
    
    def remove_event(self, event_type: WindowEventType):
        if not isinstance(event_type, WindowEventType):
            raise TypeError('Event_type must be a EventType instance')
        
        setattr(self.__events, event_type.value, None)
        self.__set_event_id()

    # Métodos da janela
    def alert(self, message: str):
        """Exibe um alerta na janela."""
        print(f"ALERT: {message}")

    def confirm(self, message: str) -> bool:
        """Exibe uma caixa de confirmação."""
        response = input(f"CONFIRM: {message} (y/n): ").strip().lower()
        return response == "y"

    def prompt(self, message: str, default: str = "") -> str:
        """Exibe uma caixa de prompt para entrada do usuário."""
        return input(f"PROMPT: {message} [{default}]: ") or default

    def open(self, url: str, target: str = "_blank", features: str = "") -> "Window":
        """Abre uma nova janela."""
        print(f"Opening {url} in {target} with features: {features}")
        return Window()

    def close(self):
        """Fecha a janela."""
        print("Window closed.")

    def scroll_to(self, x: float, y: float):
        """Rola a janela para a posição (x, y)."""
        self.scroll_x = x
        self.scroll_y = y
        print(f"Scrolled to ({x}, {y}).")

    def scroll_by(self, x: float, y: float):
        """Rola a janela por um deslocamento (x, y)."""
        self.scroll_x += x
        self.scroll_y += y
        print(f"Scrolled by ({x}, {y}).")

    def set_timeout(self, callback: callable, delay: int):
        """Executa uma função após um atraso (em milissegundos)."""
        Timer(delay / 1000, callback).start()

    def set_interval(self, callback: callable, interval: int):
        """Executa uma função repetidamente com um intervalo fixo (em milissegundos)."""
        def interval_callback():
            callback()
            Timer(interval / 1000, interval_callback).start()
        interval_callback()

    def clear_timeout(self, timer: Timer):
        """Cancela um timeout."""
        timer.cancel()

    def clear_interval(self, timer: Timer):
        """Cancela um intervalo."""
        timer.cancel()

    def request_animation_frame(self, callback: callable):
        """Agenda uma função para ser executada antes do próximo repaint."""
        import time
        time.sleep(0.016)  # Simula 60 FPS
        callback()

    def cancel_animation_frame(self, frame_id):
        """Cancela um requestAnimationFrame."""
        print(f"Cancelled animation frame {frame_id}.")

    def atob(self, encoded_string: str) -> str:
        """Decodifica uma string codificada em Base64."""
        import base64
        return base64.b64decode(encoded_string).decode("utf-8")

    def btoa(self, string: str) -> str:
        """Codifica uma string em Base64."""
        import base64
        return base64.b64encode(string.encode("utf-8")).decode("utf-8")