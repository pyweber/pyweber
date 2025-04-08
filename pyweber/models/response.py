from pyweber.utils.types import ContentTypes, HTTPStatusCode
from pyweber.models.request import Request, RequestASGI
from pyweber.config.config import config
from pyweber.utils.utils import PrintLine, Colors
from datetime import datetime, timezone

class Response:
    def __init__(
        self,
        request: Request | RequestASGI,
        response_content: bytes,
        code: int,
        cookies: list[str],
        response_type: ContentTypes,
        route: str
    ):
        self.__request = request
        self.__body = response_content
        self.__headers: dict[str, bytes] = {
            "Content-Type": f"{response_type.value}; charset=UTF-8",
            "Content-Length": len(response_content),
            "Connection": 'Close',
            "Method": request.method,
            "Http-Version": request._get_line_method_.split(' ')[2] if isinstance(request, Request) else 'HTTP/1.1', 
            "Status": code,
            "Server": 'Pyweber/1.0',
            "Date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "Set-Cookie": cookies,
            "Request-Path": request.path,
            "Response-Path": route
        }
    
    @property
    def headers(self) -> dict[str, (int, str, bytes)]:
        return self.__headers
    
    @property
    def request(self) -> Request | RequestASGI:
        return self.__request
    
    @property
    def http_version(self) -> str:
        return self.headers.get('Http-Version', None)
    
    @property
    def response_date(self) -> str:
        return self.headers.get('Date', None)
    
    @property
    def response_type(self) -> str:
        return self.headers.get('Content-Type', 'text/html')
    
    @property
    def response_content(self) -> bytes:
        return self.__body
    
    @property
    def cookies(self) -> list[str]:
        return self.headers.get('Set-Cookie', [])
    
    @property
    def code(self) -> int:
        return self.headers.get('Status', None)
    
    @property
    def request_path(self) -> str:
        return self.headers.get('Request-Path', None)
    
    @property
    def response_path(self) -> str:
        return self.headers.get('Response-Path', None)
    
    @property
    def status_code(self) -> str:
        http_code: str = HTTPStatusCode.search_by_code(self.code)
        
        if http_code.startswith('3'):
            return f'{http_code}\r\nLocation: {self.response_path}'
        
        if http_code.startswith('4'):
            if http_code.startswith('401'):
                return f"{http_code}\r\nWWW-Authenticate: Basic realm={config.get('app', 'name')}"
            
            if http_code.startswith('405'):
                return f'{http_code}\r\nAllow: GET, POST, PUT, DELETE'
        
        if http_code.startswith('5'):
            if http_code.startswith('503'):
                return f'{http_code}\r\nRetry-After: 60'
        
        return http_code
    
    def __getitem__(self, key: str = None):
        if not key:
            return {'headers': self.headers, 'body': self.response_content}
        
        elif key == 'headers':
            return self.headers
        
        elif key == 'body':
            return self.response_content
        else:
            return {}
    
    def add_header(self, key: str, value: str):
        self.__headers[key] = value
    
    def set_header(self, key: str, /, value: str | bytes | int | float):
        if key in self.__headers:
            self.__headers[key] = value
    
    def new_content(self, value: bytes):
        if isinstance(value, bytes):
            self.__body = value
            self.__headers['Content-Length'] = len(value)

    @property
    def build_response(self) -> bytes:
        response = f'{self.http_version} {self.status_code}\r\n'
        reset_color = Colors.RESET
        bold_white_color = Colors.BOLD_WHITE
        bold_red_color = Colors.BOLD_RED
        bold_green_color = Colors.GREEN
        status_color = bold_red_color if self.code in [404, 500, 503] else bold_green_color

        for key, value in self.headers.items():
            if key == 'Set-Cookie':
                for cookie in value:
                    response += f'{key}: {cookie}\r\n'
            
            elif key == 'Response':
                pass
            
            else:
                response += f'{key}: {value}\r\n'
        
        response += '\r\n'

        PrintLine(text=f"{bold_white_color}{self.request._get_line_method_} {status_color}{self.status_code.replace(repr('\r\n'), ' ')}{reset_color}")
        return response.encode() + self.response_content