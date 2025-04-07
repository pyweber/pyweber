from threading import Thread
from typing import TYPE_CHECKING
from pyweber.models.create_app import CreatApp
from pyweber.models.request import RequestASGI

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber

WS_RUNNING = False

def run(target: callable = None):
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

    CreatApp(target=target).run()

async def run_as_asgi(scope, response, send, app: 'Pyweber', target: callable = None):
    global WS_RUNNING

    create_app = CreatApp(target=None)
    ws_server = create_app.ws_server
    request = RequestASGI(raw_request=scope)
    __response = await app.get_route(request=request)

    if not WS_RUNNING:
        WS_RUNNING = True
        ws_server.app = app

        if target:
            target(app)

        Thread(target=ws_server.ws_start, daemon=True).start()

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