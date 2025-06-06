import pyweber as pw

app = pw.Pyweber()

@app.route('/')
def home():
    return pw.Template(template='index.html')

if __name__ == '__main__':
    app.run()