import os
import sys
import toml
import shutil
import argparse
import subprocess
import questionary
from pathlib import Path
from pyweber.config.config import config
from pyweber.utils.loads import StaticTemplates
from pyweber.utils.utils import PrintLine, Colors
from importlib.metadata import version, PackageNotFoundError

class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='PyWeber - A Lightweight Python Framework')
        self.parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.get_version}")
        self.parser.add_argument("-u", "--update", action="store_true", help="Update to last pyweber version")
        self.parser.add_argument("-e", "--edit", action='store_true', help="Edit project file configuration")
        self.parser.add_argument('-r', "--reload-mode", action='store_true', help='Run the project on reload mode. Only if python file named main')
        self.subparsers = self.parser.add_subparsers(dest="command")
        self._add_create_command()
        self._add_create_config_file_command()
        self._add_config_file_new_section()
        self.add_install_requirements()
        self._add_run_command()

        self.commands_funcs = CommandFunctions()
        self.edit_cli_parameters = ConfigManagerCLI()
    
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
        create_parser.add_argument(
            "--with-config",
            action="store_true",
            help="Create a default config file for this project"
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
    
    def _add_create_config_file_command(self):
        create_config_parser = self.subparsers.add_parser(
            name='create-config-file',
            help='Create a config file if not exists'
        )

        create_config_parser.add_argument(
            '--config-path',
            type=str,
            default='.pyweber',
            help='Path to the directory where the config file will be created'
        )

        create_config_parser.add_argument(
            '--config-name',
            type=str,
            default='config.toml',
            help='Name of the config file (default: config.toml)'
        )
    
    def _add_config_file_new_section(self):
        manage_config_parser = self.subparsers.add_parser(
            name='add-section',
            help='Add new fields or sections on project config file'
        )

        manage_config_parser.add_argument(
            '--section-name',
            type=str,
            help='Name for the new section with you need to add'
        )
    
    def add_install_requirements(self):
        install_requirementes_parser = self.subparsers.add_parser(
            name='install',
            help='Install project requirements'
        )
        install_requirementes_parser.add_argument(
            '--config-file-path',
            nargs='?',
            default=Path('.pyweber', 'config.toml'),
            help='Path to project config file'
        )

    
    def run(self):
        try:
            args = sys.argv[1:]

            args = self.parser.parse_args(args)

            if args.update:
                self.commands_funcs.update(framework='pyweber')
            
            elif args.edit:
                self.edit_cli_parameters.init_config()
            
            elif args.reload_mode:
                self.commands_funcs.run_app(file='main.py', reload=True)
            
            elif args.command == 'install':
                self.commands_funcs.install_requirements(path=args.config_file_path)

            elif args.command == 'create-new':
                self.commands_funcs.create(project_name=args.project_name, with_config=args.with_config)
            
            elif args.command == 'run':
                self.commands_funcs.run_app(file=args.file, reload=args.reload)
            
            elif args.command == 'create-config-file':
                self.commands_funcs.create_config_file(path=args.config_path, name=args.config_name)
            
            elif args.command == 'add-section':
                self.edit_cli_parameters.new_section(section_name=args.section_name, value=None)
            
            else:
                self.parser.print_help()
                exit(code=1)
        
        except KeyboardInterrupt:
            pass
    
    @property
    def get_version(self):
        try:
            return version('pyweber')
        except PackageNotFoundError:
            return "0.0.0"

class CommandFunctions:
    def __init__(self):
        self.project_name: Path = None

    def create(self, project_name: str, with_config: bool):
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
            ]

            file_contents = [
                ['main.py', StaticTemplates.BASE_MAIN()],
                ['style.css', StaticTemplates.BASE_CSS()],
                ['index.html', StaticTemplates.BASE_HTML()],
                ['favicon.ico', StaticTemplates.FAVICON()],
            ]

            for i, path in enumerate(project_paths):
                self.create_path(path=path)
                self.create_static_file(str(path / file_contents[i][0]), file_contents[i][1])
            
            if with_config:
                config['app']['name'] = project_name
                config['app']['description'] = f'A {project_name} builded with pyweber framework'
                config.set_parameters(path=Path(project_name, '.pyweber'))
                self.log_message(
                    message=f'🟢 Config file sucessfully created. See in {config.path}!',
                    level='sucess'
                )

            self.log_message(
                message=f'🟢 Project {project_name} sucessfully created!',
                level='success'
            )

        except FileNotFoundError as e:
            self.log_message(
                message=f'❌ Error to create project: {e}',
                level='error'
            )
            shutil.rmtree(path=self.project_name, ignore_errors=True)

    def run_app(self, file: str, reload: bool):

        try:
            self.log_message(
                message=f'✨ Trying to start the project',
                level='warning'
            )
            self.update_reload_mode(file_path=config.path, value=reload)
            subprocess.run(['python', file], check=True, shell=True)
        
        except subprocess.CalledProcessError as e:
            self.log_message(
                message=f'❌ Error: {e}',
                level='error'
            )

    def update(self, framework: str):
        try:
            subprocess.run(['pip', 'install', f'{framework}', '--upgrade'], check=True, shell=True, stderr=subprocess.PIPE)

            self.log_message(
                message=f'✅ Framework updated sucessfully!',
                level='warning'
            )

        except subprocess.CalledProcessError as e:
            self.log_message(
                message=f'❌ Error: {e}',
                level='error'
            )
    
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
    
    def create_config_file(self, path: str, name: str, keep_defaults=True):
        config.set_parameters(path=path, name=name, keep_defaults=keep_defaults)
    
    def update_reload_mode(self, file_path: str, value: bool):
        config['session']['reload_mode'] = value
        with open(file_path, 'w') as file:
            toml.dump(config.config, file)
    
    def install_requirements(self, path: str):
        if not Path.exists(path):
            raise FileNotFoundError('This project does not have a config file')
        
        requires: list[str] = config.get('requirements', 'packages')
        try:
            for require in requires:
                print(f'Installing {Colors.GREEN}{require}{Colors.RESET}, please waiting...')
                subprocess.run(['pip', 'install', require], check=True, capture_output=True, shell=True)
            
            print(f'All done...')

        except Exception as e:
            print(f'Error: {e}')
    
    def log_message(self, message: str, level: str = 'info'):
        colors = {
            'info': Colors.BLUE,
            'success': Colors.GREEN,
            'warning': Colors.YELLOW,
            'error': Colors.RED,
            'reset': Colors.RESET
        }
        PrintLine(f'{colors.get(level, '')}{message}{colors.get('reset')}')

class ConfigManagerCLI:
    def __init__(self):
        self.config_file = config
    
    def init_config(self):
        action = questionary.select(
            "What do you do?",
            choices=[
                'edit field',
                'remove field',
                'remove section',
                'add new field',
                'add new section',
                'exit'
            ]
        ).ask()

        if action.lower() == 'edit field':
            self.edit_parameters()
        
        elif action.lower() == 'add new':
            self.new_field()
        
        elif action.lower() == 'remove field':
            self.remove_field()
        
        elif action.lower() == 'remove section':
            self.remove_section()
        elif action.lower() == 'add new section':
            self.new_section()
    
    def remove_field(self):
        sections = self.get_all_sections()
        path: list[str] = []

        section: str = questionary.select(
            f"Wich section are you need to remove field?:",
            choices=sections
        ).ask()

        if section:
            path.extend(section.split('.'))

            field = questionary.select(
                f"Wich field are you need to remove?:",
                choices=config.get(*path)
            ).ask()

            if field:
                path.append(field)
                config.delete(*path)
    
    def remove_section(self):
        sections = self.get_all_sections()
        path: list[str] = []

        section: str = questionary.select(
            f"Wich section are you need to remove?:",
            choices=sections
        ).ask()

        if section:
            path.extend(section.split('.'))
            config.delete(*path)
    
    def new_section(self, section_name: str = None, value = None):
        if not section_name:
            sections = self.get_all_sections()
            new_section: str = questionary.text(
                f"Write a new parent section:"
            ).ask()

            if new_section:
                if new_section.strip() not in sections:
                    config.set(*new_section.replace('.', ' ').strip().split(), value=value)
        
        else:
            config.set(*section_name.replace('.', ' ').strip().split(), value=value)
    
    def new_field(self):
        sections = self.get_all_sections()
        path: list[str] = []
        section = questionary.select(
            "Choose a section that you need do add a field:",
            choices=sections
        ).ask()

        if section:
            path.extend(section.split('.'))
            while True:
                try:
                    field: str = questionary.text(
                        f"Write a new field and type e.g (password [str, list, dict, ...]) name for {section}:",
                    ).ask()

                    if field.strip():
                        key_value = field.split(' ')
                        if key_value[0] not in config.get(*path):
                            path.append(key_value[0])
                            questionary.print(text=guide_config(), style="bold fg:#00FFFF")

                            value: str = questionary.text(
                                f"Write a value for {key_value[0]}:",
                            ).ask()

                            if key_value[-1].lower() in ['set', 'list', 'tuple']:
                                value = value.strip().split()
                            elif key_value[-1].lower() in ['int', 'integer', 'number']:
                                value = int(value.strip())
                            elif key_value[-1].lower() in ['double', 'float']:
                                value = float(value.strip())
                            elif key_value[-1].lower() in ['dict', 'dictionary']:
                                keys = value.split(';')

                                if ':' not in value and '=' not in value:
                                    raise ValueError('None separator key and value identified')
                                else:
                                    value = {}

                                    for key in keys:
                                        k, v = key.replace(':','=').strip().split('=')
                                        type = k.split()

                                        if type[-1] in DefaultTypes.floats:
                                            v = float(v)
                                        elif type[-1] in DefaultTypes.integer:
                                            v = int(v)
                                        elif type[-1] in DefaultTypes.lists:
                                            v = v.split()
                                        
                                        value[type[0]] = v
                            else:
                                value = value.strip()
                            
                            config.set(*path, value=value)
                        else:
                            questionary.print(
                                text='The field with you need to add alterady exist'
                            )
                        
                        break

                except AttributeError:
                    break
                except TypeError:
                    break
    
    def edit_parameters(self):
        sections = self.get_all_sections()
        path: list[str] = []

        section: str = questionary.select(
            f"Wich section are you need to edit?:",
            choices=sections
        ).ask()

        if section:
            path.extend(section.split('.'))

            field = questionary.select(
                f"Wich field are you need to edit?:",
                choices=config.get(*path)
            ).ask()

            if field:
                path.append(field)
                self.check_content_type(path=path)
    
    def check_content_type(self, path: str):
        current_value = config.get(*path)

        while True:
            if isinstance(current_value, bool):
                confirm: str = questionary.text(
                    f"Confirm to change value for {path[-1]}? (Y/N): "
                ).ask()

                if confirm.lower() == 'y':
                    new_value = not current_value
                else:
                    break

            else:
                new_value: str = questionary.text(
                    f"What's a new value for {path[-1]}?: "
                ).ask()

            try:
                if isinstance(current_value, list):
                    new_value = new_value.split()
                elif isinstance(current_value, int):
                    new_value = int(new_value)
                elif isinstance(current_value, float):
                    new_value = float(new_value)
                
                config.set(*path, value=new_value)
                break
            except ValueError:
                questionary.print(
                    text=f'Invalid value for {path[-1]}, expected {type(current_value).__name__}.'
                )
            
            except TypeError:
                break

    def get_all_sections(self) -> list[str]:
        def walk(obj, prefix=""):
            sections = []
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    sections.append(full_key)
                    sections.extend(walk(value, prefix=full_key))
            return sections

        return walk(config.config)

def app():
    cli = CLI()
    cli.run()

def guide_config():
    text= """
📘 Config Guide (Type hints optional — default is str):

╭──────────────┬──────────────────────────────────-──────╮
│ Type         │ Format Example                          │
├──────────────┼────────────────────────────────────-────┤
│ String       │ name str Alex                           │
│ Integer      │ age int 18                              │
│ Float        │ price float 19.99                       │
│ List         │ tags list python flask api              │
│ Tuple        │ colors tuple red green blue             │
│ Dictionary   │ db dict user:str=admin; port:int=5432   │
╰──────────────┴─────────────────────────────────────-───╯

• Use `=` or `:` to separate key and value  
• Use space or comma to separate pairs  
• Missing type = treated as string
"""
    return text

class DefaultTypes:
    integer = ['integer', 'int', 'number']
    string = ['text', 'string', 'str']
    floats = ['double', 'float']
    lists = ['list', 'set']
    dicts = ['dict', 'dictionary']