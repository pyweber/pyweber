import pyweber as pw
from datetime import datetime

app = pw.Pyweber()

@app.route('/')
def home():
    return pw.Template(template='index.html', year=datetime.now().year)

if __name__ == '__main__':
    app.run()