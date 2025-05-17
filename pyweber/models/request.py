import re
import cgi
import json
from enum import Enum
from io import BytesIO
from typing import Union
from urllib.parse import parse_qs
from pyweber.utils.types import ContentTypes

class RequestMode(Enum):
    asgi = 'asgi'
    wsgi = 'wsgi'

    def __repr__(self):
        return self.value

class Header:
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
        
        self.__http_version = f'HTTP/{str(value)}'

    @cookie.setter
    def cookie(self, value: dict[str, str]):
        if value and not isinstance(value, dict):
            raise TypeError(self.__typeerror_sentence(var='cookie', t='dict'))
        
        self.__cookie = '&'.join([f'{k}={v}' for k, v in value.items()])
    
    @content_type.setter
    def content_type(self, value: ContentTypes):
        if not value:
            value = ContentTypes.html
        
        if not isinstance(value, ContentTypes):
            raise TypeError(self.__typeerror_sentence(var='content_type', t='ContentTypes'))
        
        self.__content_type = value.value
    
    @user_agent.setter
    def user_agent(self, value: str):
        if value and not isinstance(value, str):
            raise TypeError(self.__typeerror_sentence(var='user_agent', t='str'))
        
        self.__user_agent = value
    
    @content_length.setter
    def content_length(self, value: int):
        if value and not isinstance(value, int):
            raise TypeError(self.__typeerror_sentence(var='content_length', t='int'))
        
        self.__content_length = value or 0
    
    @method.setter
    def method(self, value: str):
        if not value:
            value = 'GET'
        
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
            raise ValueError(f'{value} is not valid url')
        
        self.__host = validate_url.group(1)
        self.__path = validate_url.group(3) or '/'
        self.__url = value
    
    @property
    def text(self):
        t = f'{self.method.upper()} {self.path} {self.http_version}\r\n'
        t += f'{str('Host:'):<18} {self.host}\r\n'

        for key, value in self.__dict__.items():
            if value:
                if value in [self.host, self.path, self.url, self.method]:
                    continue

                if isinstance(value, dict):
                    for k, v in value.items():
                        header_name=f'{str(k).removeprefix('_Header__').replace('_', '-').capitalize()}:'
                        t += f'{header_name:<18} {v}\r\n'
                    
                    continue

                header_name=f'{str(key).removeprefix('_Header__').replace('_', '-').capitalize()}:'
                t += f'{header_name:<18} {value}\r\n'
        
        return t
    
    @property
    def json(self) -> dict[str, tuple[str, str]]:
        j, v = {}, []
        for key, value in self.__dict__.items():
            if value:
                if isinstance(value, dict):
                    for k, i in value.items():
                        v.append((str(k).removeprefix('_Header__').replace('_', '-').encode(), str(i).encode()))
                    continue

                v.append((str(key).removeprefix('_Header__').replace('_', '-').encode(), str(value).encode()))
        
        j['headers'] = v

        return j
    
    def __typeerror_sentence(self, var: str, t=str):
        return f'{var} must be a {t} instances, but got {type(var).__name__}'

class File:
    def __init__(self, file: cgi.FieldStorage):
        self.filename = file.filename
        self.content = file.value
        self.size = len(self.content)
        self.type = file.type
    
    def __len__(self):
        return self.size
    
    def __repr__(self):
        return f'File(filename={self.filename}, size={self.size}, type={self.type})'

class Request:
    def __init__(self, headers: Union[str, dict[str, Union[tuple[str, str], str]]], body: Union[bytes] = None):
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
    def raw_request(self):
        if self.request_mode.value == 'asgi':
            return self.__raw_request_asgi
        
        return self.__raw_request_wsgi
    
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
            return {key: '; '.join(value) for key, value in parse_qs(self.__raw_body).items()}
        elif ContentTypes.form_data.value in self.content_type:
            return self.__parse_form_data_wsgi()
        else:
            return self.__raw_body
    
    @property
    def first_line(self):
        if self.request_mode.value == 'wsgi':
            return self.__raw_headers.split(self.__line_splitter, 1)[0].strip()
        
        full_path = f'{self.path}?{'&'.join([f'{key}={value}' for key, value in self.query_params.items()])}' if self.query_params else self.path
        return f'{self.method} {full_path} {self.scheme}'
    
    def __parse_form_data_wsgi(self) -> dict[str, list[str | File] | str]:
        boundary_match = re.search(r'boundary=(.+)', self.content_type)
        if not boundary_match:
            return {}

        boundary = boundary_match.group(1)
        environ = {
            'REQUEST_METHOD': self.method,
            'CONTENT_TYPE': self.content_type,
            'CONTENT_LENGTH': str(len(self.__raw_body.encode() if isinstance(self.__raw_body, str) else self.__raw_body))
        }

        fp = BytesIO(self.__raw_body.encode() if isinstance(self.__raw_body, str) else self.__raw_body)
        form = cgi.FieldStorage(
            fp=fp,
            environ=environ,
            headers={'content-type': self.content_type},
            keep_blank_values=True
        )

        data: dict[str, list[str | File]] = {}
        for key in form.keys():
            field = form[key]

            if isinstance(field, list):
                # Pode conter arquivos ou campos múltiplos com mesmo nome
                items = []
                for item in field:
                    if item.filename:
                        items.append(File(item))  # seu wrapper
                    else:
                        items.append(item.value)
                data[key] = items
            elif field.filename:
                data[key] = [File(field)]
            else:
                data[key] = field.value

        return data
    
    def __additions_headers(self):
        if self.request_mode.value == 'asgi':
            self.method: str = self.raw_request.get('method')
            self.scheme: str = f"{self.raw_request.get('scheme')}/{self.raw_request.get('http_version')}".lower()
            self.path: str = self.raw_request.get('raw_path', b'').decode()
            self.query_params = {key: ';'.join(val) for key, val in parse_qs(self.raw_request.get('query_string', b'').decode()).items() if val}

        else:
            line_info = self.raw_request.split(self.__line_splitter, 1)[0].split()
            self.method = line_info[0] if len(line_info) > 0 else None
            self.path = line_info[1].split('?', 1)[0] if len(line_info) >= 2 else None
            self.scheme = line_info[2] if len(line_info) >= 3 else None
            self.query_params = {key: ';'.join(val) for key, val in parse_qs(line_info[1].split('?', 1)[-1]).items() if val} if len(line_info) >= 2 else {}
        
    def __parse_headers_wsgi(self) -> dict[str, str]:
        return {header.split(':', 1)[0].strip().lower(): header.split(':', 1)[-1].strip() for header in self.__raw_headers.split(self.__line_splitter)[1::]}
    
    @property
    def __line_splitter(self):
        return '\r\n'
    
    @property
    def request_parts_splitter(self):
        return '\r\n\r\n'

    def __repr__(self):
        return f'Request(method={self.method}, mode={self.request_mode})'

request: Request = None