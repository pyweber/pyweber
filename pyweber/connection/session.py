from typing import TYPE_CHECKING
from time import time

if TYPE_CHECKING:
    from pyweber.core.template import Template
    from pyweber.core.window import Window

class Session:
    def __init__(self, template: 'Template', window: 'Window', session_id: str):
        self.template = template
        self.window = window
        self.session_id = session_id
        self.create_at = time()

class SessionManager:
    def __init__(self):
        self.__sessions: dict[str, Session] = {}
    
    @property
    def sessions(self):
        return self.__sessions

    @property
    def lenght(self):
        return len(self.sessions)
    
    @property
    def all_sessions(self):
        return list(self.sessions.keys())
    
    def add_session(self, session_id: str, Session: Session):
        self.sessions[session_id] = Session
    
    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_session(self, session_id: str):
        return self.sessions.get(session_id, None)
    
    def __getitem__(self, session_id: str):
        return self.get_session(session_id=session_id)

sessions = SessionManager()