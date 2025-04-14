from typing import TYPE_CHECKING, Callable
from pyweber.models.create_app import CreatApp
from pyweber.models.request import RequestASGI
from pyweber.connection.websocket import WsServerAsgi
from pyweber.config.config import config
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
    global WS_RUNNING

    request = RequestASGI(raw_request=scope)
    os.environ['PYWEBER_WS_PORT'] = str(request.port)
    
    ws_server = WsServerAsgi(app=app)
    __response = await app.get_route(request=request)

    if not WS_RUNNING:
        WS_RUNNING = True

        if target and callable(target):
            target(app)

    if scope.get('type') == 'websocket':
        await ws_server(scope, receive, send)

    elif scope.get('type') == 'lifespan':
        pass

    elif scope.get('type') == 'http':
        os.environ['PYWEBER_WS_PORT'] = str(request.port) or str(10000)
        
        headers = [
            (b'content-type', __response.response_type.encode()),
            (b'content-length', str(len(__response.response_content)).encode()),
            (b'connection', b'close'),
            (b'date', __response.response_date.encode())
        ]

        if app.cookies:
            for cookie in app.cookies:
                headers.append((b'set-cookie', cookie.encode()))

        await send({
            'type': 'http.response.start',
            'status': __response.code,
            'headers': headers
        })

        await send({
            'type': 'http.response.body',
            'body': __response.response_content
        })