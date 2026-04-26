from pyweber.utils.types import ContentTypes, HTTPStatusCode
from pyweber.models.request import Request
from pyweber.config.config import config
from pyweber.utils.utils import PrintLine, Colors
from datetime import datetime, timezone

class Response:
    def __init__(
        self,
        request: Request,
        response_content: bytes,
        code: int,
        cookies: dict[str, str],
        response_type: ContentTypes,
        route: str
    ):
        request_headers = request.accept_control_request_headers or "Content-Type, Authorization, X-Requested-With, Accept"
        self.__request = request
        self.__body = response_content
        self.__headers: dict[str, bytes] = {
            "Content-Type": f"{response_type.value}; charset=UTF-8",
            "Content-Length": len(response_content),
            "Connection": 'Close',
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Vary": "Accept-Encoding",
            "Method": request.method,
            "Http-Version": request.scheme,
            "Status": code,
            "Server": 'Pyweber/1.0',
            "Date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "Set-Cookie": cookies,
            "Request-Path": request.path,
            "Response-Path": route,
            "Access-Control-Allow-Origin": request.origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": request_headers,
            "Access-Control-Allow-Credentials": 'true',
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": request.host,
        }

        self.http_status_code = HTTPStatusCode.search_by_code(code)
        self.__check_status_code()

    def __check_status_code(self):
        aditional_code: tuple[str, str] = ()

        if self.status_code == 401:
            aditional_code = ('WWW-Authenticate', f"Basic realm={config.get('app', 'name')}")

        elif self.status_code == 405:
            aditional_code = ('Allow', 'GET, POST, PUT, DELETE')

        elif self.status_code == 503:
            aditional_code = ('Retry-After', '60')

        elif self.status_code in range(300,400):
            aditional_code = ('Location', self.response_path)

        if self.status_code not in range(300,400):
            self.set_header('Response-Path', self.request_path)

        if aditional_code:
            self.set_header(aditional_code[0], aditional_code[-1])
            self.http_status_code += f"\r\n{': '.join(aditional_code)}"

    @property
    def headers(self) -> dict[str, (int, str, bytes)]:
        return self.__headers

    @property
    def request(self) -> Request:
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
    def request_path(self) -> str:
        return self.headers.get('Request-Path', None)

    @property
    def response_path(self) -> str:
        return self.headers.get('Response-Path', None)

    @property
    def status_code(self) -> int:
        return self.headers.get('Status', None)

    def __getitem__(self, key: str = None):
        if not key:
            return {'headers': self.headers, 'body': self.response_content}

        elif key == 'headers':
            return self.headers

        elif key == 'body':
            return self.response_content
        else:
            return {}

    def set_header(self, key: str, value: str):
        """Add new header in Response"""
        self.__headers[key] = value

    def update_header(self, key: str, /, value: str | bytes | int | float):
        """Update header value if it exist in Response"""
        if key in self.__headers:
            self.__headers[key] = value

    def new_content(self, value: bytes):
        if isinstance(value, bytes):
            self.__body = value
            self.__headers['Content-Length'] = len(value)

    @property
    def build_response(self) -> bytes:
        response = f'{self.http_version} {self.http_status_code}\r\n'
        reset_color = Colors.RESET
        bold_white_color = Colors.BOLD_WHITE
        bold_red_color = Colors.BOLD_RED
        bold_green_color = Colors.GREEN
        bold_yellow_color = Colors.BOLD_YELLOW
        bold_blue_color = Colors.BOLD_BLUE

        if self.status_code >= 400:
            status_color = bold_red_color
        elif self.status_code >= 300:
            status_color = bold_yellow_color
        elif self.status_code >= 200:
            status_color = bold_green_color
        else:
            status_color = bold_blue_color

        for key, value in self.headers.items():
            if key == 'Set-Cookie':
                for cookie in value:
                    response += f'{key}: {value[cookie]}\r\n'

            elif key == 'Response':
                pass

            else:
                response += f'{key}: {value}\r\n'

        response += '\r\n'

        to_replace = '\r\n'
        clear_status_code = self.http_status_code.replace(to_replace, ' ')
        PrintLine(text=f"{bold_white_color}{self.request.first_line} {status_color}{clear_status_code}{reset_color}")
        return response.encode() + self.response_content
