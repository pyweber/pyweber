from urllib.parse import urlparse, parse_qs

class Request:
    def __init__(self, raw_request: str):
        self.__raw_request = raw_request.strip().splitlines()
        self.method: str = self.__get_method
        self.path: str = self.__get_path
        self.netloc: str = self.__get_netloc
        self.user_agent: str = self.__get_user_agent
        self.host: str = self.__get_host
        self.cookies: dict[str, str] = self.__get_cookies
        self.referer: str = self.__get_referer
        self.accept: list[str] = self.__get_accept
        self.accept_encoding: list[str] = self.__get_accept_encoding
        self.accept_language: list[str] = self.__get_accept_language
        self.authorization: str = self.__get_authorization
        self.params: dict[str, None] = self.__get_params
        self.fragment: str = self.__get_fragment
        self.session_id: str = self.__get_session_id
    
    @property
    def __get_method(self):
        lines = self.__split_lines().split()
        if lines:
            method = lines[0].strip()
            return  method if method in self.__http_methods else None
        
        return None
    
    @property
    def __get_path(self):
        if self.method:
            path_line = self.__split_lines(splitter=self.method).split()
            if self.__get_netloc and not any('/' in l for l in path_line):
                return '/'
            
            return self.include_scheme(path_line[0]).path.strip() if path_line else None

        return None
    
    @property
    def __get_params(self):
        if self.method:
            path_line = self.__split_lines(splitter=self.method).split()
            params = path_line[0].split('?')

            if len(params) > 1:
                par = params[-1].split('#')[0]
                return {val.split('=')[0]:val.split('=')[1] for val in par.split('&')}
        
        return {}
    
    @property
    def __get_fragment(self):
        if self.method:
            path_line = self.__split_lines(splitter=self.method).split()
            params = path_line[0].split('#')

            if len(params) > 1:
                    return params[-1]
        
        return None
    
    @property
    def __get_netloc(self):
        if self.method:
            path_line = self.__split_lines(splitter=self.method).split()
            return self.include_scheme(path_line[0]).netloc.strip() if path_line else None
        return None
    
    @property
    def __get_host(self):
        return self.__split_lines(splitter='Host:') or None

    @property
    def __get_user_agent(self):
        return self.__split_lines('User-Agent:') or None
    
    @property
    def __get_referer(self):
        return self.__split_lines('Referer:') or None
    
    @property
    def __get_authorization(self):
        return self.__split_lines('Authorization:') or None
    
    @property
    def __get_session_id(self):
        return self.__split_lines('Session-ID:') or None
    
    @property
    def __get_cookies(self) -> dict[str, str]:
        cookies = self.__split_lines('Cookie:')
        if cookies:
            return {cookie.split('=')[0]: cookie.split('=')[1].strip() for cookie in cookies.split(';')}
        
        return {}
    
    @property
    def __get_accept(self) -> list[str]:
        return self.__split_list(splitter='Accept:', sep=',')
    
    @property
    def __get_accept_encoding(self):
        return self.__split_list(splitter='Accept-Encoding:', sep=',')
    
    @property
    def __get_accept_language(self) -> list[str]:
        return self.__split_list(splitter='Accept-Language:', sep=',')
    
    @property
    def __http_methods(self) -> list[str]:
        return ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT"]
    
    def __split_list(self, splitter: str, sep: str) -> list[str]:
        value_string = self.__split_lines(splitter=splitter)
        if value_string:
            return [value.strip() for value in value_string.split(sep=sep)]

        return []

    def __split_lines(self, splitter: str = '') -> str:
        for line in self.__raw_request:
            if splitter in line:
                return line.removeprefix(splitter).strip()
        
        return ''
    
    @property
    def _get_line_method_(self):
        return self.__split_lines()
    
    @property
    def get_url(self):
        return self.__split_lines(splitter=self.method).split()[0]
    
    def include_scheme(self, url: str):
        if not url.startswith(('https://', 'http://')):
            url = 'http://' + url
        
        return urlparse(url)
    
    def __repr__(self):
        return f"""
Request(
    method= {self.method}
    path= {self.path}
    net_loc= {self.netloc}
    host= {self.host}
    user_agent= {self.user_agent}
    referer= {self.referer}
    url= {self.get_url}
    cookies= {self.cookies}
    accept= {self.accept}
    accept_encoding= {self.accept_encoding}
    accept_language= {self.accept_language}
    params= {self.params}
    fragment= {self.fragment}
)""".strip()

class RequestASGI:
    def __init__(self, raw_request: dict):
        self.__raw_request = raw_request
        self.method: str = self.__get_method()
        self.path: str = self.__get_path()
        self.netloc: str = self.__get_netloc()
        self.host: str = self.__get_host()
        self.port: str = self.__get_port()
        self.user_agent: str = self.__get_user_agent()
        self.referer: str = self.__get_referer()
        self.cookies: dict[str, str] = self.__get_cookies()
        self.accept: list[str] = self.__get_accept()
        self.accept_encoding: list[str] = self.__get_accept_encoding()
        self.accept_language: list[str] = self.__get_accept_language()
        self.authorization: str = self.__get_authorization()
        self.params: dict[str, list[str]] = self.__get_params()
        self.fragment: str = self.__get_fragment()
        self.session_id: str = self.__get_session_id()
    
    def __get_method(self):
        return self.__raw_request.get("method", "").upper()
    
    def __get_path(self) -> str:
        return self.__raw_request.get("path", "")
    
    def __get_netloc(self):
        scheme = self.__get_path().split(':', 1)[0]
        return scheme if scheme in ['http', 'https'] else None
    
    def __get_host(self):
        for key, value in self.__raw_request.get("headers", []):
            if key == b"host":
                return value.decode().split(":")[0]
        return ""
    
    def __get_port(self):
        return self.__raw_request.get('server')[-1]
    
    def __get_user_agent(self):
        return self.__get_header(b"user-agent")
    
    def __get_referer(self):
        return self.__get_header(b"referer")
    
    def __get_authorization(self):
        return self.__get_header(b"authorization")
    
    def __get_session_id(self):
        return self.__get_header(b"session-id")
    
    def __get_cookies(self):
        cookie_header = self.__get_header(b"cookie")
        if cookie_header:
            return {c.split("=")[0]: c.split("=")[1] for c in cookie_header.split("; ")}
        return {}
    
    def __get_accept(self):
        return self.__split_header(b"accept", ",")
    
    def __get_accept_encoding(self):
        return self.__split_header(b"accept-encoding", ",")
    
    def __get_accept_language(self):
        return self.__split_header(b"accept-language", ",")
    
    def __get_params(self):
        query_string = self.__raw_request.get("query_string", b"").decode()
        return parse_qs(query_string)
    
    def __get_fragment(self):
        return None  # ASGI requests geralmente não incluem fragmentos
    
    def __get_header(self, key: bytes):
        for h_key, h_value in self.__raw_request.get("headers", []):
            if h_key == key:
                return h_value.decode()
        return ""
    
    def __split_header(self, key: bytes, separator: str):
        header_value = self.__get_header(key)
        return [v.strip() for v in header_value.split(separator)] if header_value else []
    
    def __repr__(self):
        return f"""
RequestASGI(
    method={self.method}
    path={self.path}
    netloc={self.netloc}
    host={self.host}
    user_agent={self.user_agent}
    referer={self.referer}
    url={self.path}
    cookies={self.cookies}
    accept={self.accept}
    accept_encoding={self.accept_encoding}
    accept_language={self.accept_language}
    params={self.params}
    fragment={self.fragment}
)""".strip()