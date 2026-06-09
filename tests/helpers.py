class RecvSocket:
    """Socket fake que devolve bytes pré-carregados em recv()."""

    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0
        self.sent = b''
        self.closed = False
        self._timeout = None

    def recv(self, n: int) -> bytes:
        chunk = self._data[self._pos:self._pos + n]
        self._pos += len(chunk)
        return chunk

    def sendall(self, data: bytes):
        self.sent += data

    def close(self):
        self.closed = True

    def getpeername(self):
        return ('127.0.0.1', 49152)

    def settimeout(self, value):
        self._timeout = value

    def setblocking(self, flag: bool):
        pass


def make_http_request(method: str = 'GET', path: str = '/', body: bytes = b'', extra_headers: str = '') -> bytes:
    headers = (
        f'{method} {path} HTTP/1.1\r\n'
        f'Host: localhost:8800\r\n'
        f'Content-Length: {len(body)}\r\n'
        f'{extra_headers}'
        f'\r\n'
    ).encode('iso-8859-1')
    return headers + body


def make_ws_upgrade_request(key: str = 'dGhlIHNhbXBsZSBub25jZQ==') -> bytes:
    return (
        f'GET / HTTP/1.1\r\n'
        f'Host: localhost\r\n'
        f'Connection: Upgrade\r\n'
        f'Upgrade: websocket\r\n'
        f'Sec-WebSocket-Key: {key}\r\n'
        f'\r\n'
    ).encode('iso-8859-1')


def make_masked_frame(payload: bytes, opcode: int = 1, fin: bool = True) -> bytes:
    mask = b'\x00\x01\x02\x03'
    masked = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
    header = bytearray()
    header.append((0x80 if fin else 0) | opcode)
    length = len(payload)
    if length <= 125:
        header.append(0x80 | length)
    elif length <= 65535:
        header.append(0x80 | 126)
        header.extend(length.to_bytes(2, 'big'))
    else:
        header.append(0x80 | 127)
        header.extend(length.to_bytes(8, 'big'))
    header.extend(mask)
    header.extend(masked)
    return bytes(header)
