from typing import TYPE_CHECKING, Callable, Any
from pyweber.models.create_app import CreatApp
from pyweber.models.request import Request, ClientInfo
from pyweber.connection.websocket import WebsocketManager
import os

if TYPE_CHECKING: # pragma: no cover
    from pyweber.pyweber.pyweber import Pyweber

WS_RUNNING = False
ws_server = WebsocketManager(app=lambda: ..., protocol='uvicorn')

def run(
        target: Callable = None,
        reload_mode: bool = False,
        cert_file: str = None,
        key_file: str = None,
        host: str = None,
        port: int = None,
        route: str = None,
        disable_ws: bool = False,
        reload_extensions: list[str] = None,
        ignore_reload_time: int = 10,
        mobile: bool = False,
        **kwargs
    ): # pragma: no cover
    """
    For running the pyweber project.
    ```python
    import pyweber as pw

    def main(app: pw.Pyweber):
        app.add_route(
            route='/',
            template=pw.Template(template='Hello, world')
        )

    if __name__ == '__main__':
        pw.run(target=main)
    ```

    Or, your can create the project using route decoratores
    ```python
    import pyweber as pw

    app = pw.Pyweber()

    @route('/')
    def home():
        return pw.Template(template='Hello, world')
    
    if __name__ == '__main__':
        app.run()
    ```

    To serve static files, you need to specify all directories as argument when create the app or use **static** method

    ```
    import pyweber as pw

    app = pw.Pyweber('static')

    # Or using Pyweber method to add static directory
    app.static('assets')
    ```
    ---
    More details: https://pyweber.dev
    """

    kwargs = {
        'reload_mode': reload_mode,
        'cert_file': cert_file,
        'key_file': key_file,
        'host': host,
        'port': port,
        'route': route,
        'disable_ws': disable_ws,
        'reload_extensions': reload_extensions or [],
        'ignore_reload_time': ignore_reload_time,
        'mobile': mobile,
        **kwargs
    }

    if target and not callable(target):
        raise TypeError('The target must be callable function')

    CreatApp(target=target, **kwargs).run()

def encode_header(headers: dict[str, Any], /,*ignore_headers: str):
    byte_headers: list[tuple[bytes, bytes]] = []

    for header, value in headers.items():
        header = header.strip().lower()

        if header not in set(map(lambda el: el.strip().lower(), ignore_headers)):
            byte_headers.append((header.encode(), str(value).encode()))
    
    return byte_headers

async def run_as_asgi(scope, receive, send, app: 'Pyweber', target: Callable = None): # pragma: no cover
    global WS_RUNNING
    global ws_server

    body = b""
    if scope["type"] == "http":
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
    
    client_info = scope.get('client', (None, 0))
    request = Request(
        headers=scope,
        body=body,
        client_info=ClientInfo(
            host=client_info[0],
            port=client_info[-1]
        )
    )
    
    ws_server.protocol = 'uvicorn'

    if not WS_RUNNING:
        WS_RUNNING = True

        ws_server.app = app
        app.ws_server = ws_server
        
        if target and callable(target):
            target(app)

    if scope.get('type') == 'websocket':
        await ws_server(scope, receive, send)

    elif scope.get('type') == 'lifespan':
        pass

    elif scope.get('type') == 'http':
        os.environ['PYWEBER_WS_PORT'] = str(request.port)
        response = await app.get_response(request=request)

        headers = encode_header(response['headers'], 'set-cookie', 'code')

        if app.cookies:
            for cookie in app.cookies:
                headers.append((b'set-cookie', cookie.encode()))

        await send({
            'type': 'http.response.start',
            'status': response.status_code,
            'headers': headers
        })

        await send({
            'type': 'http.response.body',
            'body': response.response_content
        })