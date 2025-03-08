import os
import json
import argparse
import subprocess
from time import sleep
from pathlib import Path
from datetime import datetime
from pyweber import __version__
from pyweber.utils.load import StaticTemplates

class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='PyWeber - A Lightweight Python Framework')
        self.parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
        self.parser.add_argument("-u", "--update", action="store_true", help="Update to  last pyweber version")
        self.subparsers = self.parser.add_subparsers(dest="command")
        self._add_create_command()
        self._add_run_command()

        self.commands_funcs = CommandFunctions()
    
    def _add_create_command(self):
        create_parser = self.subparsers.add_parser(
            name='create-new',
            help='Create a new pyweb project'
        )
        create_parser.add_argument(
            'project_name',
            type=str,
            help='Project name with you need to create'
        )

    def _add_run_command(self):
        run_parser = self.subparsers.add_parser(
            name='run',
            help='Run a pyweber project that you created'
        )
        run_parser.add_argument(
            'file',
            type=str,
            nargs='?',
            default='main.py',
            help='Main file of pyweber project. default is main.py'
        )

        run_parser.add_argument(
            '--reload',
            action='store_true',
            help='Add reload mode when running pyweber project'
        )
    
    def run(self):
        try:
            args = self.parser.parse_args()

            if args.update:
                self.commands_funcs.update(framework='pyweber')

            elif args.command == 'create-new':
                self.commands_funcs.create(args.project_name)
            
            elif args.command == 'run':
                self.commands_funcs.run_app(file=args.file, reload=args.reload)
        
        except KeyboardInterrupt:
            pass

class CommandFunctions:
    def __init__(self):
        self.project_name = None

    def create(self, project_name: str):
        # Caminho onde o novo projeto será criado
        base_path = Path(project_name)
        self.project_name = base_path

        # Verificar se o diretório já existe
        if base_path.exists():
            self.log_message(
                message=f'❌ O diretório {project_name} já existe!',
                level='error'
            )
            return

        try:
            # Criar as pastas do projeto
            os.makedirs(base_path / 'src' / 'style')  # pasta para CSS
            os.makedirs(base_path / 'templates')  # pasta para HTML
            
            # Criar o arquivo main.py com a estrutura básica
            main_py_content = StaticTemplates.BASE_MAIN()

            with open(base_path / 'main.py', 'w', encoding='utf-8') as f:
                f.write(main_py_content)
            
            # Criar o arquivo template index.html
            index_html_content = StaticTemplates.BASE_HTML()

            with open(base_path / 'templates' / 'index.html', 'w', encoding='utf-8') as f:
                f.write(index_html_content)
            
            # Criar o arquivo CSS style.css
            style_css_content = StaticTemplates.BASE_CSS()

            with open(base_path / 'src' / 'style' / 'style.css', 'w', encoding='utf-8') as f:
                f.write(style_css_content)

            self.log_message(
                message=f'✅ Projeto {project_name} criado com sucesso!',
                level='success'
            )

        except Exception as e:
            self.log_message(
                message=f'❌ Erro ao criar o projeto: {e}',
                level='error'
            )

    def run_app(self, file: str = 'main.py', reload: bool = None):
        command = f'python {file}'
        self.create_json_config(value=reload)

        try:
            self.log_message(
                message=f'✨ Tentando iniciar o projecto',
                level='warning'
            )
            subprocess.run(command, shell=True, check=True)
        
        except subprocess.CalledProcessError as e:
            self.log_message(
                message=f'❌ Error: {e}',
                level='error'
            )

    def update(self, framework: str):
        try:
            subprocess.run(['pip', 'install', f'{framework}', '--upgrade'], shell=True, stderr=subprocess.PIPE)

            self.log_message(
                message=f'✅ biblioteca actualizada com sucesso!',
                level='warning'
            )

        except subprocess.CalledProcessError as e:
            self.log_message(
                message=f'❌ Error: {e}',
                level='error'
            )
    
    def create_json_config(self, value: bool = False):
        project_name = Path('.pyweber')
        if Path.exists(Path.joinpath(project_name, 'config.json')):
            with open(Path.joinpath(project_name, 'config.json'), 'r+') as f:
                d = json.load(f)
                d['reload_mode'] = value
                f.seek(0)
                json.dump(d, f, indent=4)
                f.truncate()
        else:
            os.makedirs(Path(project_name), exist_ok=True)
            with open(Path.joinpath(project_name, 'config.json'), 'w', encoding='utf-8') as f:
                json.dump({'reload_mode': value}, f, indent=4)

    def log_message(self, message: str, level: str = 'info'):
        # Exibir as messagens durante a execução do CLI
        time = datetime.now().strftime('%H:%M:%S')

        colors = {
            'info': '\033[94m',
            'success': '\033[92m',
            'warning': '\033[93m',
            'error': '\033[91m'
        }

        reset = '\033[0m'  # Reset da cor no terminal
        print(f'{colors.get(level, "")}[{time}] {message}{reset}')
        sleep(0.25)

def app():
    cli = CLI()
    cli.run()