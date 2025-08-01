from typing import TYPE_CHECKING, Callable
from pyweber.models.create_app import CreatApp
from pyweber.models.request import Request, ClientInfo
from pyweber.connection.websocket import WebSocket
import os

if TYPE_CHECKING: # pragma: no cover
    from pyweber.pyweber.pyweber import Pyweber

WS_RUNNING = False

def run(
        target: Callable = None,
        reload_mode: bool = False,
        cert_file: str = None,
        key_file: str = None,
        host: str = None,
        port: int = None,
        route: str = '/',
        ws_port: int = None,
        disable_ws: bool = False,
        reload_extensions: list[str] = None,
        ignore_reload_time: int = 10,
        **kwargs
    ): # pragma: no cover
    """
    For running the pyweber project.
    ```python
    import pyweber as pw

    def main(app: pw.Pyweber):
        app.add_route(
            route='/',
            template=pw.Template(template='Hello, world', status=200)
        )

    if __name__ == '__main__':
        pw.run(target=main)
    ```

    Or, your can create the project using route decoratores
    ```python
    import pyweber as pw

    app = Pyweber(...)

    @route('/')
    def home():
        return pw.Template(template='Hello, world', status=200)
    
    if __name__ == '__main__':
        pw.run()
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
        'ws_port': ws_port,
        'route': route,
        'disable_ws': disable_ws,
        'reload_extensions': reload_extensions or [],
        'ignore_reload_time': ignore_reload_time,
        **kwargs
    }

    if target and not callable(target):
        raise TypeError('The target must be callable function')

    CreatApp(target=target, **kwargs).run()

async def run_as_asgi(scope, receive, send, app: 'Pyweber', target: Callable = None): # pragma: no cover
    global WS_RUNNING

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
    
    ws_server = WebSocket(app=app, protocol='uvicorn')

    if not WS_RUNNING:
        WS_RUNNING = True

        if target and callable(target):
            target(app)

    if scope.get('type') == 'websocket':
        await ws_server(scope, receive, send)

    elif scope.get('type') == 'lifespan':
        pass

    elif scope.get('type') == 'http':
        os.environ['PYWEBER_WS_PORT'] = str(request.port)
        response = await app.get_response(request=request)
        
        headers = [
            (b'content-type', response.response_type.encode()),
            (b'content-length', str(len(response.response_content)).encode()),
            (b'connection', b'close'),
            (b'date', response.response_date.encode())
        ]

        if app.cookies:
            for cookie in app.cookies:
                headers.append((b'set-cookie', cookie.encode()))

        await send({
            'type': 'http.response.start',
            'status': response.code,
            'headers': headers
        })

        await send({
            'type': 'http.response.body',
            'body': response.response_content
        })