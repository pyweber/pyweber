import re
import json
from enum import Enum
from typing import Union, Optional
from urllib.parse import parse_qs
from pyweber.utils.types import ContentTypes
from dataclasses import dataclass

class RequestMode(Enum):
    asgi = 'asgi'
    wsgi = 'wsgi'

    def __repr__(self):
        return self.value

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

@dataclass
class Field:
    name: Optional[str] = None
    filename: Optional[str] = None
    value: Optional[bytes] = b''
    content_type: Optional[str] = None

    def __repr__(self):
        return f"Field(name={self.name}, value_length={len(self.value)})"

class File:
    def __init__(self, field: Field):
        self.filename = field.filename
        self.content = field.value
        self.size = len(self.content)
        self.content_type = field.content_type
    
    def __len__(self):
        return self.size
    
    def __repr__(self):
        return f"File(filename={self.filename}, size={self.size}, type={self.content_type})"

class FieldStorage:
    def __init__(self, content_type: str, callbacks: bytes):
        self.boundary = content_type
        self.callbacks = callbacks
    
    @property
    def boundary(self) -> str: return self.__boundary

    @boundary.setter
    def boundary(self, value: str):
        boundary = re.search(f"boundary=(.+)", value)
        if not boundary:
            raise TypeError('None boundary was detected')
        
        self.__boundary = boundary.group(1)
    
    @property
    def callbacks(self): return self.__callbacks

    @callbacks.setter
    def callbacks(self, value: bytes):
        if not value or not isinstance(value, bytes):
            raise TypeError('callbacks must be bytes instances')
        
        if not value.startswith(f"--{self.boundary}\r\n".encode()) and not value.endswith(f"--{self.boundary}--\r\n".encode()):
            raise ValueError(f'callbacks invalid for boundary {self.boundary}')
        
        self.__callbacks = value
    
    def fields(self) -> list[Field]:
        init_delimiter = f"--{self.boundary}\r\n"
        end_delimiter = f"--{self.boundary}--\r\n"

        values = [
            b.removesuffix("\r\n".encode()) for b in self.callbacks.removeprefix(
                init_delimiter.encode()
            ).removesuffix(
                end_delimiter.encode()
            ).split(init_delimiter.encode())
        ]

        fids: list[Field] = []

        for value in values:
            k, _, v = value.partition("\r\n\r\n".encode())
            keys = k.decode()

            name = re.search(r"name=\"(.+)\"", keys)
            filename = re.search(r"filename=\"(.+)\"", keys)
            content_type = re.search(r"Content-Type: (.+)", keys)
            field = Field()

            if filename:
                field.content_type = content_type.group(1)
                field.name = name.group(1).split('";')[0]
                field.filename = filename.group(1)
                field.value = v

                fids.append(field)
            elif name:
                field.name = name.group(1)
                field.content_type = None
                field.value = v.decode()
                field.filename = None
                fids.append(field)
        
        return fids
    
    def __len__(self):
        return len(self.fields())
    
    def __repr__(self):
        return f'FileStorage(files={self.__len__()})'

@dataclass
class ClientInfo:
    host: str
    port: int

class Request:
    def __init__(
        self,
        headers: Union[str, dict[str, Union[tuple[str, str], str]]],
        body: Union[bytes] = None,
        client_info: ClientInfo = None
    ):
        if isinstance(headers, Headers):
            headers = headers.text

        if isinstance(headers, str):
            self.request_mode = RequestMode.wsgi
            self.__raw_request_wsgi = headers
            self.__raw_headers = headers
            self.__raw_body = body

        elif isinstance(headers, dict):
            self.request_mode = RequestMode.asgi
            self.__raw_request_asgi = headers
            self.__raw_body = body or b''
            self.__raw_headers: list[tuple[bytes, bytes]] = headers.get('headers', [])
            
        else:
            raise TypeError('Request type does not valid')
        
        self.client_info = client_info
        self.__additions_headers()
    
    @property
    def request_mode(self):
        return self.__request_mode
    
    @request_mode.setter
    def request_mode(self, value):
        if not isinstance(value, RequestMode):
            raise TypeError('Request mode does not valid')
        
        self.__request_mode = value
    
    @property
    def client_info(self): return self.__client_info

    @client_info.setter
    def client_info(self, value: ClientInfo):
        if value and not isinstance(value, ClientInfo):
            raise TypeError('client_info must be a ClientInfo instances')
        
        self.__client_info = value or ClientInfo(host=None, port=0)
        
    @property
    def raw_headers(self):
        if self.request_mode.value == 'asgi':
            return self.__raw_request_asgi
        
        return self.__raw_request_wsgi
    
    @property
    def raw_body(self):
        return self.__raw_body
    
    @property
    def host(self):
        return self.headers.get('host')
    
    @property
    def port(self):
        try:
            return int(self.headers.get('host', '0').split(':')[-1])
        except:
            return 0
    
    @property
    def content_length(self):
        return int(self.headers.get('content-length'))
    
    @property
    def content_type(self):
        return self.headers.get('content-type', '')
    
    @property
    def user_agent(self):
        return self.headers.get('user-agent')
    
    @property
    def origin(self):
        return self.headers.get('origin')
    
    @property
    def referrer(self):
        return self.headers.get('referrer')
    
    @property
    def accept(self):
        return [val.strip().split(';') for val in self.headers.get('accept', '').split(',') if val]
    
    @property
    def accept_encoding(self):
        return [val.strip().split(';') for val in self.headers.get('accept-encoding', '').split(',') if val]
    
    @property
    def accept_language(self):
        return [val.strip().split(';') for val in self.headers.get('accept-language', '').split(',') if val]
    
    @property
    def cookies(self):
        return {cookie.split('=')[0]: cookie.split('=')[-1] for cookie in self.headers.get('cookie', '').split(';') if cookie}

    @property
    def headers(self):
        if self.request_mode.value == 'asgi':
            return {header[0].decode(): header[1].decode() for header in self.__raw_headers}
        
        return self.__parse_headers_wsgi()
    
    @property
    def body(self) -> Union[str, dict[str, Union[list[File], str]]]:
        if self.content_type == ContentTypes.json.value:
            return json.loads(self.__raw_body)
        elif self.content_type == ContentTypes.form_encode.value:
            return {key.decode(): '; '.join([v.decode() for v in value]) for key, value in parse_qs(self.__raw_body).items()}
        elif ContentTypes.form_data.value in self.content_type:
            return self.__parse_form_data()
        else:
            return {}
    
    @property
    def first_line(self):
        if self.request_mode.value == 'wsgi':
            return self.__raw_headers.split(self.__line_splitter, 1)[0].strip()
        
        full_path = f"{self.path}?{'&'.join(['{key}={value}'.format(key=key, value=value) for key, value in self.query_params.items()])}" if self.query_params else self.path
        return f"{self.method} {full_path} {self.scheme}"

    def __parse_form_data(self):
        fs = FieldStorage(self.content_type, callbacks=self.__raw_body)
        body: dict[str, list[File] | str] = {}

        for field in fs.fields():
            if field.filename:
                body.setdefault(field.name, []).append(
                    File(field)
                )
            else:
                if field.name in body:
                    if not isinstance(body.get(field.name), list):
                        last_value = body.pop(field.name)
                        body.setdefault(field.name, []).append(last_value)

                    body[field.name].append(field.value)
                else:
                    body[field.name] = field.value 
                
        return body
    
    def __additions_headers(self):
        if self.request_mode.value == 'asgi':
            self.method: str = self.raw_headers.get('method')
            self.scheme: str = f"{self.raw_headers.get('scheme')}/{self.raw_headers.get('http_version')}".lower()
            self.path: str = self.raw_headers.get('raw_path', b'').decode()
            self.query_params = {key: ';'.join(val) for key, val in parse_qs(self.raw_headers.get('query_string', b'').decode()).items() if val}

        else:
            line_info = self.raw_headers.split(self.__line_splitter, 1)[0].split()
            self.method = line_info[0] if len(line_info) > 0 else None
            self.path = line_info[1].split('?', 1)[0] if len(line_info) >= 2 else None
            self.scheme = line_info[2] if len(line_info) >= 3 else None
            self.query_params = {
                key: ';'.join(val) for key, val in parse_qs(line_info[1].split('?', 1)[-1]).items() if val
            } if len(line_info) >= 2 else {}
        
    def __parse_headers_wsgi(self) -> dict[str, str]:
        return {header.split(':', 1)[0].strip().lower(): header.split(':', 1)[-1].strip() for header in self.__raw_headers.split(self.__line_splitter)[1::]}
    
    @property
    def __line_splitter(self):
        return '\r\n'
    
    @property
    def request_parts_splitter(self):
        return '\r\n\r\n'

    def __repr__(self):
        return f"Request(method={self.method}, mode={self.request_mode})"

request: Request = None