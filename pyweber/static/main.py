import pyweber as pw
from datetime import datetime

app = pw.Pyweber()

class Home(pw.Template):
    def __init__(self):
        super().__init__('index.html', year=datetime.now().year)
        self.querySelector('#btn-features').add_event(pw.EventType.CLICK, self.goto_features)

        self.querySelector('.code-block').add_child(
            pw.Element(
                tag='button',
                classes=['copy-btn'],
                content='Copy',
                events=pw.TemplateEvents(onclick=lambda e: pw.PrintLine('Apenas Teste!...'))
            )
        )
    
    def goto_features(self, e: pw.EventHandler):
        e.template.querySelector('#features').scroll_into_view('smooth')
        e.update()

@app.route('/')
def home():
    return Home()

if __name__ == '__main__':
    app.run()