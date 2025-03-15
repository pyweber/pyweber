import os
import json
import shutil
import argparse
import subprocess
from time import sleep
from pathlib import Path
from datetime import datetime
from pyweber import __version__
from pyweber.utils.load import StaticTemplates
from pyweber.utils.defaults import APP, SERVER, SESSION

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
            
            else:
                self.parser.print_help()
                exit(code=1)
        
        except KeyboardInterrupt:
            pass

class CommandFunctions:
    def __init__(self):
        self.project_name: Path = None

    def create(self, project_name: str):
        self.project_name = Path(project_name)

        if self.project_name.exists():
            self.log_message(
                message=f'❌ O diretório {project_name} já existe!',
                level='error'
            )
            return

        try:
            project_paths = [
                self.project_name, # Main project
                self.project_name / 'src' / 'style', # for style sheet
                self.project_name / 'templates', # for templates
                self.project_name / 'src' / 'assets', # for assets
                self.project_name / '.pyweber' # for config file
            ]

            file_contents = [
                ['main.py', StaticTemplates.BASE_MAIN()],
                ['style.css', StaticTemplates.BASE_CSS()],
                ['index.html', StaticTemplates.BASE_HTML()],
                ['favicon.ico', StaticTemplates.FAVICON()],
                ['config.json', '']
            ]

            for i, path in enumerate(project_paths):
                self.create_path(path=path)
                
                if i == len(project_paths) - 1:
                    self.create_config_file(str(path / file_contents[i][0]))
                
                else:
                    self.create_static_file(str(path / file_contents[i][0]), file_contents[i][1])

            self.log_message(
                message=f'✅ Projeto {project_name} criado com sucesso!',
                level='success'
            )

        except FileNotFoundError as e:
            self.log_message(
                message=f'❌ Erro ao criar o projeto: {e}',
                level='error'
            )
            shutil.rmtree(path=self.project_name, ignore_errors=True)

    def run_app(self, file: str = 'main.py', reload: bool = False):

        try:
            self.log_message(
                message=f'✨ Tentando iniciar o projecto',
                level='warning'
            )
            self.update_reload_mode(file_path=os.path.join('.pyweber', 'config.json'), value=reload)
            subprocess.run(['python', file], shell=True, check=True)
        
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
    
    def inserting_config_info(self, file_path: str):
        config = self.read_config_file(file_path=file_path)
        config['app'] = {
            'name': self.project_name.name,
            'version': APP.VERSION.value,
            'description': f'A powerful {self.project_name.name} made with pyweber',
            'icon': ''
        }
        config['server'] = {
            'host': SERVER.HOST.value,
            'port': SERVER.PORT.value,
            "route": SERVER.ROUTE.value
        }
        config['database'] = {
            'type': 'sqlite',
            'name': 'database',
            'username': '',
            'password': '',
            'host': '',
            'port': ''
        }
        config['session'] = {
            'secret_key': SESSION.SECRET_KEY.value,
            'timeout': SESSION.TIME_OUT.value,
            'reload_mode': SESSION.RELOAD_MODE.value,
            'enviroment': SESSION.ENVIROMENT.value
        }

        with open(file_path, 'w') as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
    
    def update_reload_mode(self, file_path: str, value: bool):
        config = self.read_config_file(file_path=file_path)
        if config:
            config['session']['reload_mode'] = value
            with open(file_path, 'w') as file:
                json.dump(config, fp=file, indent=4, ensure_ascii=False)
    
    def read_config_file(self, file_path: str) -> dict[str, str]:
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        
        except:
            return {}
    
    def create_config_file(self, file_path: str):
        with open(file_path, 'w') as file:
            json.dump({}, fp=file, indent=4, ensure_ascii=False)
        
        self.inserting_config_info(file_path=file_path)
    
    def create_path(self, path: str):
        os.makedirs(path, exist_ok=True)
    
    def create_static_file(self, file_path: str, content: str | bytes):
        encoding='utf-8'
        mode = 'w'

        if isinstance(content, bytes):
            mode = 'wb'
            encoding = None

        with open(file_path, mode=mode, encoding=encoding) as file:
            file.write(content)
    
    def log_message(self, message: str, level: str = 'info'):
        time = datetime.now().strftime('%H:%M:%S')

        colors = {
            'info': '\033[94m',
            'success': '\033[92m',
            'warning': '\033[93m',
            'error': '\033[91m'
        }
        reset = '\033[0m'
        print(f'{colors.get(level, "")}[{time}] {message}{reset}')
        sleep(0.25)

def app():
    cli = CLI()
    cli.run()