from pyweber.core.template import Template
from pyweber.core.window import Window

class ClientSession:
    def __init__(
        self,
        session_id: str = None,
        template: Template = None,
        window: Window = None
    ):
        self.session_id = session_id
        self.template = template
        self.window = window
    
    def __repr__(self):
        return (
            f'session_id: {self.session_id}',
            f'template: {self.template}',
            f'window: {self.window}'
        )