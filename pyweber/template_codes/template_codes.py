WS_CONNECT = """<!-- Websocket connection code. Automatically injected -->
<script>
    function connectWebSocket() {
        const socket = new WebSocket('ws://localhost:8765');

        socket.onopen = function() {
            console.log('Conectado ao WebSocket!');
        };

        socket.onerror = function(error) {
            console.error('Erro na conexão WebSocket:', error);
        };

        socket.onclose = function() {
            console.log('Conexão WebSocket fechada. Tentando reconectar em 1 segundo...');
            setTimeout(connectWebSocket, 1000); // Tenta reconectar após 1 segundo
            location.reload();
        };

        //replace here
    }

    // Inicia a conexão WebSocket
    connectWebSocket();
</script>
</body>
"""

WS_RELOAD = """
        socket.onmessage = function(event) {
            if (event.data === 'reload') {
                location.reload();
            } else {
                console.log(JSON.parse(event.data))
            }
        };

        //replace here
        
"""

WS_EVENTS = """
        // Função para capturar o valor de elementos
        function getElementValue(element) {
            const tagName = element.tagName.toLowerCase();

            if (tagName === 'input') {
                const inputType = element.type;
                switch (inputType) {
                    case 'checkbox':
                        return element.checked;  // true ou false
                    case 'radio':
                        return element.checked ? element.value : null;  // Valor do botão selecionado
                    case 'file':
                        return Array.from(element.files).map(file => file.name);  // Lista de nomes de arquivos
                    default:
                        return element.value;  // Valor padrão para outros tipos de input
                }
            } else if (tagName === 'textarea') {
                return element.value;
            } else if (tagName === 'select') {
                return element.options[element.selectedIndex].value;
            }

            return null;  // Para outros elementos, retorna null
        }

        // Função para construir o objeto element
        function buildElementObject(element) {
            const tagName = element.tagName.toLowerCase();

            // Se for um <script> com conteúdo, ignoramos
            if (tagName === 'script' && element.textContent.trim() !== "") {
                return null;
            }
            
            let uuid = element.getAttribute('uuid') || null;
            const content = element.children.length === 0 ? element.textContent : null;
            const children = Array.from(element.children)
                .map(child => buildElementObject(child))
                .filter(child => child !== null); // Remove elementos nulos

            return {
                id: element.id || null,
                class_name: element.className || null,
                uuid: uuid || null,
                name: tagName,
                content: content,
                value: getElementValue(element),  // Usa a função getElementValue
                attributes: Array.from(element.attributes).reduce((attrs, attr) => {
                    if (attr.name !== 'class' && attr.name !== 'id' && attr.name !== 'uuid' && attr.name !== 'value' && !attr.name.startsWith('_')) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }, {}),
                events: Array.from(element.attributes).reduce((events, attr) => {
                    if (attr.name.startsWith('_')) {
                        events[attr.name] = attr.value;
                    }
                    return events;
                }, {}),
                parent_uuid: element.parentElement ? element.parentElement.getAttribute('uuid') || null : null,  // Apenas o parent_uuid
                childs: children  // Inclui os filhos recursivamente
            };
        }

        // Função para capturar o pai do elemento e construir a estrutura hierárquica
        function getElementParent(element) {
            if (element.parentElement) {
                const parent = buildElementObject(element.parentElement);
                parent.parent = getElementParent(element.parentElement);  // Recursivamente pega o pai
                return parent;  // Retorna o pai com a estrutura hierárquica
            }
            return null;  // Se não houver pai (caso do <html>), retorna null
        }

        // Função para enviar eventos
        function sendEvent(type, element, event) {
            const eventData = {
                type: type,
                route: window.location.pathname,
                element: buildElementObject(element),  // Usa a função buildElementObject
                event_data: {
                    clientX: event.clientX,
                    clientY: event.clientY,
                    timestamp: Date.now()
                }
            };

            // Adiciona o pai com a estrutura hierárquica ao elemento
            if (type === 'click') {
                console.log(eventData)
            }
            socket.send(JSON.stringify(eventData));  // Envia os dados
        }

        // Captura eventos de clique
        document.addEventListener('click', (event) => {
            sendEvent('click', event.target, event);
        });

        // Captura eventos de hover
        document.addEventListener('mouseover', (event) => {
            sendEvent('hover', event.target, event);
        });

        // Captura eventos de teclas pressionadas
        document.addEventListener('keypress', (event) => {
            sendEvent('keypress', event.target, event);
        });

        // Captura eventos de movimento do mouse
        document.addEventListener('mousemove', (event) => {
            sendEvent('mousemove', event.target, event);
        });

        //replace here

"""

PAGE_NOT_FOUND = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 Not Found</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f4f4f4;
            color: #333;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            font-size: 48px;
            color: #ff4757;
            margin: 0;
        }
        p {
            font-size: 18px;
            margin: 10px 0 20px;
        }
        a {
            text-decoration: none;
            color: white;
            background-color: #ff4757;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
            transition: 0.3s;
        }
        a:hover {
            background-color: #e84118;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <p>Ops! Page not Found.</p>
        <a href="/">Back to home page</a>
    </div>
</body>
</html>
"""

BASE_MAIN = '''import pyweber as pw

def main(app: pw.Router):
    app.add_route(route='/', template=pw.Template(template='index.html'))

if __name__ == '__main__':
    pw.run(target=main, reload=True)
'''

BASE_HTML = '''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wellcome to PyWeber!</title>
    <link rel="stylesheet" href="/src/style/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎉 Wellcome to your PyWeber Project!</h1>
        </header>
        <section class="content">
            <p>Now, your finished to create a pyweber project. Let's go to this development journey with style.🚀</p>
        </section>
    </div>
</body>
</html>
'''

BASE_CSS = '''/* Basic style for pyweber home page */
body {
    font-family: Arial, sans-serif;
    background-color: #f4f7f6;
    color: #333;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background-color: #4CAF50;
    color: white;
    padding: 10px 0;
    text-align: center;
}

h1 {
    margin: 0;
    font-size: 36px;
}

.content {
    background-color: white;
    padding: 20px;
    margin-top: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.content p {
    font-size: 18px;
    line-height: 1.6;
    text-align: center;
}
'''