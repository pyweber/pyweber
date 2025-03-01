import typer
import os
import subprocess
from datetime import datetime
from time import sleep
from pathlib import Path
from pyweber.template_codes.template_codes import BASE_CSS, BASE_HTML, BASE_MAIN

app = typer.Typer()

@app.command(name='create-new', help='Create a new pyweb project')
def create(project_name: str):
    # Caminho onde o novo projeto será criado
    base_path = Path(project_name)

    # Verificar se o diretório já existe
    if base_path.exists():
        log_message(
            message=f'❌ O diretório {project_name} já existe!',
            level='error'
        )
        return

    try:
        # Criar as pastas do projeto
        os.makedirs(base_path / 'src' / 'style')  # pasta para CSS
        os.makedirs(base_path / 'templates')  # pasta para HTML
        
        # Criar o arquivo main.py com a estrutura básica
        main_py_content = BASE_MAIN

        with open(base_path / 'main.py', 'w', encoding='utf-8') as f:
            f.write(main_py_content)
        
        # Criar o arquivo template index.html
        index_html_content = BASE_HTML

        with open(base_path / 'templates' / 'index.html', 'w', encoding='utf-8') as f:
            f.write(index_html_content)
        
        # Criar o arquivo CSS style.css
        style_css_content = BASE_CSS

        with open(base_path / 'src' / 'style' / 'style.css', 'w', encoding='utf-8') as f:
            f.write(style_css_content)

        log_message(
            message=f'✅ Projeto {project_name} criado com sucesso!',
            level='success'
        )

    except Exception as e:
        log_message(
            message=f'❌ Erro ao criar o projeto: {e}',
            level='error'
        )

@app.command(name='run', help='Init your pyweb project')
def run_app(file: str = 'main.py'):
    command = f'python {file}'

    try:
        log_message(
            message=f'✨ Tentando iniciar o projecto',
            level='warning'
        )
        subprocess.run(command, shell=True, check=True)
    
    except subprocess.CalledProcessError as e:
        log_message(
            message=f'❌ Error: {e}',
            level='error'
        )

@app.command(name='update', help='Update your pyweber version')
def update():
    try:
        subprocess.run(['pip', 'install', 'pyweber', '--upgrade'], shell=True, stderr=subprocess.PIPE)

        log_message(
            message=f'✅ biblioteca actualizada com sucesso!',
            level='warning'
        )

    except subprocess.CalledProcessError as e:
        log_message(
            message=f'❌ Error: {e}',
            level='error'
        )

def log_message(message: str, level: str = 'info'):
    # Exibir as messagens durante a execução do CLI
    time = datetime.now().strftime('%H:%M:%S')

    colors = {
        'info': typer.colors.BRIGHT_BLUE,
        'sucess': typer.colors.GREEN,
        'warning': typer.colors.YELLOW,
        'error': typer.colors.RED
    }

    typer.echo(
        typer.style(
            text=f'[{time}] {message}',
            fg=colors.get(level, typer.colors.WHITE)
        )
    )

    sleep(0.25)

if __name__ == '__main__':
    app()