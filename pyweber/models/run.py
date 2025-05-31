from typing import TYPE_CHECKING, Callable
from pyweber.models.create_app import CreatApp
from pyweber.models.request import Request
from pyweber.connection.websocket import WsServerAsgi
import os

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber

WS_RUNNING = False

def run(target: Callable = None, **kwargs):
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
    More details: https://pyweber.readthedocs.org
    """

    if target and not callable(target):
        raise TypeError('The target must be callable function')

    CreatApp(target=target, **kwargs).run()

async def run_as_asgi(scope, receive, send, app: 'Pyweber', target: Callable = None):
    from pyweber.models.request import request
    global WS_RUNNING

    body = b""
    if scope["type"] == "http":
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

    requests = Request(headers=scope, body=body)
    request = requests
    
    ws_server = WsServerAsgi(app=app)

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