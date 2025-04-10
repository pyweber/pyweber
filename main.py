import pyweber as pw
from pyweber import Icons

app = pw.Pyweber()

buttons_title = ['Dashboard', 'Overview', 'Events', 'Services', 'Contact', 'Support']
button_icons = [Icons.GRID, Icons.MENU_APP, Icons.CALENDAR2_DAY, Icons.SERVER, Icons.ENVELOPE, Icons.QUESTION_CIRCLE]

class Style(pw.Element):
    def __init__(self):
        super().__init__(tag='link')
        self.attrs={'rel': 'stylesheet', 'href': '../src/style/style.css'}

class Button(pw.Element):
    def __init__(self, icon: pw.Icons, title: str):
        super().__init__(tag='li', classes=['sidebar-button'])
        self.childs = [
            pw.Icon(value=icon),
            pw.Element(
                tag='a',
                attrs={'href': '#', 'title': title},
                content=title,
                events=pw.TemplateEvents(onclick=self.print_hello)
            )
        ]
    
    def print_hello(self, e: pw.EventHandler):
        print(e.window.session_storage)

class SideBarButtons(pw.Element):
    def __init__(self):
        super().__init__(tag='ul', classes=['sidebar-buttons'])
        self.childs = [
            Button(icon=button_icons[i], title=title) for i, title in enumerate(buttons_title)
        ]

class SideBarTitle(pw.Element):
    def __init__(self):
        super().__init__(tag='div', classes=['title'])
        self.childs = [
            pw.Element(tag='img', attrs={'src': pw.config.get('app', 'icon')}),
            pw.Element(tag='div', content=pw.config.get('app', 'name'))
        ]

class Container(pw.Element):
    def __init__(self):
        super().__init__(tag='div', classes=['container'])
        self.childs=[
            SideBarTitle(),
            SideBarButtons()
        ]

class SideBar(pw.Template):
    def __init__(self):
        super().__init__(template='')
        self.querySelector('head').add_child(Style())
        self.querySelector('body').add_child(Container())

@app.route('/')
def sidebar():
    return SideBar()

async def run_as_asgi(scope, receive, send):
    return await pw.run_as_asgi(scope, receive, send, app)

if __name__ == '__main__':
    import uvicorn
    # uvicorn.run(app=run_as_asgi, port=8800, ws='websockets')
    app.run()