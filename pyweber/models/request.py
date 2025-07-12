import json
from enum import Enum
from typing import Union
from urllib.parse import parse_qs
from dataclasses import dataclass

from pyweber.utils.types import ContentTypes
from pyweber.models.field_storage import FieldStorage
from pyweber.models.headers import Headers
from pyweber.models.file import File

class RequestMode(Enum): # pragma: no cover
    asgi = 'asgi'
    wsgi = 'wsgi'

    def __repr__(self):
        return self.value

@dataclass
class ClientInfo: # pragma: no cover
    host: str
    port: int

class Request: # pragma: no cover
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