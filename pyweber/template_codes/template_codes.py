WS_CODE = """<!-- Reload server code. Automatically injected -->
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

        socket.onmessage = function(event) {
            console.log('Mensagem recebida do servidor:', event.data);
            if (event.data === 'reload') {
                console.log('Realizando o reload da página...');
                location.reload();  // Recarrega a página no navegador
            }
        };
    }

    // Inicia a conexão WebSocket
    connectWebSocket();
</script>
</body>
"""

PAGE_NOT_FOUND = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Página não encontrada</title>
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
        <p>Ops! Página não encontrada.</p>
        <a href="/">Voltar para a página inicial</a>
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
    <title>Bem-vindo ao PyWeber!</title>
    <link rel="stylesheet" href="/src/style/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎉 Bem-vindo ao seu Projeto PyWeber!</h1>
        </header>
        <section class="content">
            <p>Você acabou de criar um projeto com o framework PyWeber. Vamos começar a sua jornada de desenvolvimento web com estilo!</p>
        </section>
    </div>
</body>
</html>
'''

BASE_CSS = '''/* Estilos básicos para o PyWeb */
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
}
'''