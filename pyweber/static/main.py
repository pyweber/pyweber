import pyweber as pw

def main(app: pw.Pyweber):
    app.add_route(route='/', template=pw.Template(template='index.html'))

if __name__ == '__main__':
    pw.run(target=main)