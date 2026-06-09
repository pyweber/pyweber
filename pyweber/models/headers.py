import re
from pyweber.utils.types import ContentTypes


class Headers:
    def __init__(
        self,
        url: str,
        method: str = 'GET',
        content_type: ContentTypes = ContentTypes.html,
        content_length: int = None,
        cookie: dict[str, str] = None,
        user_agent: str = None,
        http_version: str = 1.1,
        **headers: str
    ):
        self.url = url
        self.method = method
        self.content_type = content_type
        self.content_length = content_length
        self.cookie = cookie or {}
        self.user_agent = user_agent
        self.http_version = http_version
        self.kwargs = headers
    
    @property
    def cookie(self): return self.__cookie
    @property
    def user_agent(self): return self.__user_agent
    @property
    def content_length(self): return self.__content_length
    @property
    def content_type(self): return self.__content_type
    @property
    def method(self): return self.__method
    @property
    def url(self): return self.__url
    @property
    def http_version(self): return self.__http_version
    @property
    def host(self): return self.__host
    @property
    def path(self): return self.__path

    @http_version.setter
    def http_version(self, value: float):
        if value not in [1.0, 1.1, 2.0]:
            raise ValueError('http_version is not valid, must be 1.0, 1.1 or 2.0 instead')
        
        self.__http_version = f"HTTP/{str(value)}"

    @cookie.setter
    def cookie(self, value: dict[str, str]):
        if value and not isinstance(value, dict):
            raise TypeError(self.__typeerror_sentence(var="cookie", t="dict"))
        
        self.__cookie = "&".join([f"{k}={v}" for k, v in value.items()])
    
    @content_type.setter
    def content_type(self, value: ContentTypes):
        if not value:
            value = ContentTypes.html
        
        if not isinstance(value, ContentTypes):
            raise TypeError(self.__typeerror_sentence(var="content_type", t="ContentTypes"))
        
        self.__content_type = value.value
    
    @user_agent.setter
    def user_agent(self, value: str):
        if value and not isinstance(value, str):
            raise TypeError(self.__typeerror_sentence(var="user_agent", t="str"))
        
        self.__user_agent = value
    
    @content_length.setter
    def content_length(self, value: int):
        if value and not isinstance(value, int):
            raise TypeError(self.__typeerror_sentence(var="content_length", t="int"))
        
        self.__content_length = value or 0
    
    @method.setter
    def method(self, value: str):
        if not value:
            value = "GET"
        
        self.__method = str(value).upper()
    
    @url.setter
    def url(self, value: str):
        if not value:
            raise ValueError('url must not be an empty value')
        
        pattern = r'''
            ^(
                (?:http://|https://|www.|ftp://) # prefix
                (?:
                    (?:[a-zA-Z0-9]*[a-zA-Z0-9\-\.]*[a-zA-Z0-9](?:\.[a-zA-Z]{1,5})) # domain
                    |
                    (?:\d{1,3}(?:\.\d{1,3}){3}|localhost) # host ipv4 
                )
                (?::(\d+))? # port
            )
            (/[^\s]*)?
            $
        '''

        validate_url = re.match(pattern, value, re.VERBOSE)
        if validate_url is None:
            raise ValueError(f"{value} is not valid url")
        
        self.__host = validate_url.group(1)
        self.__path = validate_url.group(3) or "/"
        self.__url = value
    
    @property
    def text(self):
        t = f"{self.method.upper()} {self.path} {self.http_version}\r\n"
        t += f"{str('Host:'):<18} {self.host}\r\n"

        for key, value in self.__dict__.items():
            if value:
                if value in [self.host, self.path, self.url, self.method]:
                    continue

                if isinstance(value, dict):
                    for k, v in value.items():
                        header_name=f"{str(k).removeprefix('_Header__').replace('_', '-').capitalize()}:"
                        t += f"{header_name:<18} {v}\r\n"
                    
                    continue

                header_name=f"{str(key).removeprefix('_Header__').replace('_', '-').capitalize()}:"
                t += f"{header_name:<18} {value}\r\n"
        
        return t
    
    @property
    def json(self) -> dict[str, tuple[str, str]]:
        j, v = {}, []
        for key, value in self.__dict__.items():
            if value:
                if isinstance(value, dict):
                    for k, i in value.items():
                        v.append((str(k).removeprefix("_Header__").replace("_", "-").encode(), str(i).encode()))
                    continue

                v.append((str(key).removeprefix("_Header__").replace("_", "-").encode(), str(value).encode()))
        
        j["headers"] = v

        return j
    
    def __typeerror_sentence(self, var: str, t=str):
        return f"{var} must be a {t} instances, but got {type(var).__name__}"