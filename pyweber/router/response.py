from pyweber.utils.types import ContentTypes, HTTPStatusCode
from pyweber.utils.request import Request

class ResponseBuilder:
    def __init__(self, request: Request, response_content: bytes, code: int, cookies: list[str], response_type: ContentTypes, route: str):
        self.code = code
        self.response_content = response_content
        self.cookies = cookies
        self.response_type = response_type
        self.request = request
        self.route = route
    
    @property
    def build_respose(self):
        response = (
            f'HTTP/1.1 {self.status_code}\r\n'
            f'Content-Type: {self.response_type.value}; charset=UTF-8\r\n'
            f'Content-Length: {len(self.response_content)}\r\n'
            f'Connection: close\r\n'
        )

        if self.cookies:
            for cookie in self.cookies:
                response += cookie
        
        response += '\r\n'

        print(f'{self.request._get_line_method_} {self.status_code}')

        return response.encode() + self.response_content
    
    @property
    def status_code(self):
        http_code: str = HTTPStatusCode.search_by_code(self.code)
        
        if http_code.startswith('3'):
            return f'{http_code}\r\nLocation: {self.route}'
        
        if http_code.startswith('4'):
            if http_code.startswith('401'):
                return f'{http_code}\r\nWWW-Authenticate: Basic realm=PyweberApp'
            
            if http_code.startswith('405'):
                return f'{http_code}\r\nAllow: GET, POST, PUT, DELETE'
        
        if http_code.startswith('5'):
            if http_code.startswith('503'):
                return f'{http_code}\r\nRetry-After: 60'
        
        return http_code