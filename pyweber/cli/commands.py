import os
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from pyweber import __version__
from pyweber.utils.load import StaticTemplates
from pyweber.config.config import config
from pyweber.utils.utils import print_line, Colors

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
            
            elif args.command in ['run', '-r']:
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
                message=f'❌ The {project_name} directory already exists!',
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
                    config['app']['name'] = project_name
                    config['app']['description'] = f'A {project_name} builded with pyweber framework'
                    self.create_config_file(str(path / file_contents[i][0]))
                
                else:
                    self.create_static_file(str(path / file_contents[i][0]), file_contents[i][1])

            self.log_message(
                message=f'✅ Project {project_name} sucessfully created!',
                level='success'
            )

        except FileNotFoundError as e:
            self.log_message(
                message=f'❌ Error to create project: {e}',
                level='error'
            )
            shutil.rmtree(path=self.project_name, ignore_errors=True)

    def run_app(self, file: str = 'main.py', reload: bool = False):

        try:
            self.log_message(
                message=f'✨ Trying to start the project',
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
                message=f'✅ Framework updated sucessfully!',
                level='warning'
            )

        except subprocess.CalledProcessError as e:
            self.log_message(
                message=f'❌ Error: {e}',
                level='error'
            )
    
    def inserting_config_info(self, file_path: str):
        with open(file_path, 'w') as file:
            json.dump(config.config, file, indent=4, ensure_ascii=False)
    
    def update_reload_mode(self, file_path: str, value: bool):
        config['session']['reload_mode'] = value
        with open(file_path, 'w') as file:
            json.dump(config.config, fp=file, indent=4, ensure_ascii=False)
    
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
        colors = {
            'info': Colors.BLUE.value,
            'success': Colors.GREEN.value,
            'warning': Colors.YELLOW.value,
            'error': Colors.RED.value,
            'reset': Colors.RESET.value
        }
        print_line(f'{colors.get(level, '')}{message}{colors.get('reset')}')

def app():
    cli = CLI()
    cli.run()