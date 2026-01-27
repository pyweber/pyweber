import asyncio
import base64
import json
from uuid import uuid4
from threading import Timer
from typing import Callable, Union, Literal
from pyweber.core.events import WindowEvents
from pyweber.connection.websocket import WebsocketManager
from pyweber.utils.types import WindowEventType, OrientationType, BaseStorage

class Orientation: # pragma: no cover
    def __init__(self, angle: int, type: OrientationType, on_change: Callable = None):
        self.angle = angle
        self.on_change = on_change
        self.type = type
    
    @property
    def on_change(self):
        return self.__on_change
    
    @on_change.setter
    def on_change(self, event: Callable):
        if not event:
            self.__on_change = None
            return
        
        if not callable(event):
            raise TypeError('Event_handler must be a callable function')

        self.__on_change = event

class Screen: # pragma: no cover
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

class Location: # pragma: no cover
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

class LocalStorage(BaseStorage): # pragma: no cover
    """Localstorage"""
    def __init__(self, data: dict[str, (int, float)], session_id: str, ws: 'WebsocketManager'):
        super().__init__(data=data)
        self.__ws = ws
        self.sesssion_id = session_id

    def set(self, key: str, value):
        if value:
            self.data[key] = value if not isinstance(value, dict) else json.dumps(value)
            self.__send__()
    
    def clear(self):
        self.data.clear()
        self.__send__()
    
    def pop(self, key: str):
        value = self.data.pop(key, None)
        if value:
            self.__send__()
        
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return value

    def __send__(self):
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self.__ws.send_message(
                data={'localstorage': self.data},
                session_id=self.sesssion_id
            ))
        except RuntimeError:
            asyncio.run(self.__ws.send_message(
                data={'localstorage': self.data},
                session_id=self.sesssion_id
            ))

class SessionStorage(BaseStorage): # pragma: no cover
    """SessionStorage"""
    def __init__(self, data: dict[str, (int, float)], session_id: str, ws: 'WebsocketManager'):
        super().__init__(data=data)
        self.__ws = ws
        self.sesssion_id = session_id

    def set(self, key: str, value):
        if value:
            self.data[key] = value if not isinstance(value, dict) else json.dumps(value)
            self.__send__()
    
    def clear(self):
        self.data.clear()
        self.__send__()
    
    def pop(self, key: str):
        value = self.data.pop(key, None)
        if value:
            self.__send__()
        return value

    def __send__(self):
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self.__ws.send_message(
                data={'sessionstorage': self.data},
                session_id=self.sesssion_id
            ))
        except RuntimeError:
            asyncio.run(self.__ws.send_message(
                data={'sessionstorage': self.data},
                session_id=self.sesssion_id
            ))

class Confirm: # pragma: no cover
    def __init__(self, confirm_result: str, confirm_id: str):
        self.result=confirm_result
        self.id=confirm_id
    
    def __repr__(self):
        return f'result={self.result}, id={self.id}'

class Prompt: # pragma: no cover
    def __init__(self, prompt_result: str, prompt_id: str):
        self.result=prompt_result
        self.id=prompt_id
    
    def __repr__(self):
        return f'result={self.result}, id={self.id}'

class Window: # pragma: no cover
    def __init__(self):
        self.__events_dict: dict[str, Callable] = {}
        self.width: float = 0.0
        self.height: float = 0.0
        self.inner_width: float = 0.0
        self.inner_height: float = 0.0
        self.session_id: str = None
        self.__ws: 'WebsocketManager' = None
        self.scroll_x: float = 0.0
        self.scroll_y: float = 0.0
        self.screen: Screen = None
        self.location: Location = None
        self.events = WindowEvents()
        self.local_storage: LocalStorage = LocalStorage(
            data=None,
            ws=self.__ws,
            session_id=self.session_id
        )
        self.session_storage: SessionStorage = SessionStorage(
            data=None,
            ws=self.__ws,
            session_id=self.session_id
        )
    
    def get_event(self, event_id: str) -> Callable:
        return self.__events_dict.get(event_id, None)
    
    @property
    def get_all_event_ids(self):
        return list(self.__events_dict.keys())
    
    def __set_event_id(self):
        self.__events_dict.clear()
        for event, call in self.events.__dict__.items():
            if call is not None:
                # key = f'_{event}_{id(call)}'
                self.__events_dict[event.removeprefix('on')] = call

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
    
    def add_event(self, event_type: WindowEventType, event: Callable):
        if not isinstance(event_type, WindowEventType):
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
        self.__send__(data={'alert': message})

    async def confirm(self, message: str, timeout: int = 300) -> Confirm:
        """Exibe uma caixa de confirmação."""
        await self.__ws.send_message(
            data={'confirm': message, 'confirm_id': str(str(uuid4()))},
            session_id=self.session_id
        )

        response = await asyncio.create_task(self.__ws.get_window_response(timeout=timeout))

        return Confirm(
            confirm_result=response.get('confirm_result', None),
            confirm_id=response.get('confirm_id')
        )

    async def prompt(self, message: str, default: str = "", timeout: int = 300) -> Prompt:
        """Exibe uma caixa de prompt para entrada do usuário."""
        await self.__ws.send_message(
            data={'prompt': {'message': message, 'default': default}, 'prompt_id': str(uuid4())},
            session_id=self.session_id
        )

        response = await asyncio.create_task(self.__ws.get_window_response(timeout=timeout))

        return Prompt(
            prompt_result=response.get('prompt_result', None),
            prompt_id=response.get('prompt_id', None)
        )

    def open(self, url: str, new_page: bool = False) -> "Window":
        """Open a new window or redirect to new url."""
        self.__send__(data={'open': {'path': url, 'new_page': new_page}})

    def close(self):
        """Close the current window if it was openned with script."""
        self.__send__(data={'close': True})

    def scroll_to(self, x: float = None, y: float = None, behavior: Literal['auto', 'smooth', 'instant'] = 'instant'):
        """Rola a janela para a posição (x, y)."""
        self.scroll_x, self.scroll_y = x, y
        self.__send__(data={'scroll_to': {'x': x or self.scroll_x, 'y': y or self.scroll_y, 'behavior': behavior}})

    def scroll_by(self, x: float = 0, y: float = 0, behavior: Literal['auto', 'smooth', 'instant'] = 'instant'):
        """Rola a janela por um deslocamento (x, y)."""
        self.scroll_x, self.scroll_y = self.scroll_x + x, self.scroll_y + y
        self.__send__(data={'scroll_to': {'x': self.scroll_x, 'y': self.scroll_y, 'behavior': behavior}})
    
    def atob(self, encoded_string: str) -> str:
        """Decodifica uma string codificada em Base64."""
        return base64.b64decode(encoded_string).decode("utf-8")

    def btoa(self, string: str) -> str:
        """Codifica uma string em Base64."""
        return base64.b64encode(string.encode("utf-8")).decode("utf-8")
    
    def set_timeout(self, callback: Callable, delay: int):
        """Executa uma função após um atraso (em milissegundos)."""
        raise NotImplementedError()

    def set_interval(self, callback: Callable, interval: int):
        """Executa uma função repetidamente com um intervalo fixo (em milissegundos)."""
        raise NotImplementedError()

    def clear_timeout(self, timer: Timer):
        """Cancela um timeout."""
        raise NotImplementedError()

    def clear_interval(self, timer: Timer):
        """Cancela um intervalo."""
        raise NotImplementedError()

    def request_animation_frame(self, callback: callable):
        """Agenda uma função para ser executada antes do próximo repaint."""
        raise NotImplementedError()
    
    def cancel_animation_frame(self, frame_id):
        """Cancela um requestAnimationFrame."""
        raise NotImplementedError()
    
    def __send__(self, data: dict[str, (int, float)]):
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self.__ws.send_message(
                data=data,
                session_id=self.session_id
            ))
        except RuntimeError:
            asyncio.run(self.__ws.send_message(
                data=data,
                session_id=self.session_id
            ))

window = Window()