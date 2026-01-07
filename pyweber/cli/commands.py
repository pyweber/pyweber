import os
import sys
import shutil
import argparse
import subprocess
import questionary
from pathlib import Path
from pyweber.config.config import config
from pyweber.utils.loads import StaticTemplates
from pyweber.utils.utils import PrintLine, Colors
from importlib.metadata import version, PackageNotFoundError

class CLI: # pragma: no cover
    def __init__(self):
        self.default_file = 'main.py'
        self.default_path_config_file = '.pyweber'
        self.parser = argparse.ArgumentParser(description='PyWeber - A Lightweight Python Framework')
        self.parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.get_version}")
        self.parser.add_argument("-u", "--update", action="store_true", help="Update to last pyweber version")
        self.parser.add_argument("-e", "--edit", action='store_true', help="Edit project file configuration")
        
        reload_group = self.parser.add_argument_group('reload mode options')
        self._add_run_arguments(reload_group)
        reload_group.add_argument(
            '-r',
            "--reload-mode",
            action='store_true',
            help=f'Run the project on reload mode with {self.default_file}'
        )
        
        self.subparsers = self.parser.add_subparsers(dest="command")
        self._add_create_command()
        self._add_create_config_file_command()
        self._add_config_file_new_section()
        self.add_install_requirements()
        self.add_cert_command()
        self._add_run_command()
        self.add_build_command()

        self.commands_funcs = CommandFunctions()
        self.edit_cli_parameters = ConfigManagerCLI()

    def _add_run_arguments(self, parser: argparse.ArgumentParser):
        """Adiciona argumentos comuns para execução do servidor"""
        parser.add_argument(
            '--file',
            type=str,
            default=self.default_file,
            help=f'Main file of pyweber project. default is {self.default_file}'
        )

        parser.add_argument(
            '--cert-file',
            type=str,
            help='Path to SSL certificate file (required for HTTPS unless --auto-cert is used)'
        )

        parser.add_argument(
            '--key-file',
            type=str,
            help='Path to SSL key file (required for HTTPS unless --auto-cert is used)'
        )

        parser.add_argument(
            '--auto-cert',
            action='store_true',
            help='Automatically generate a self-signed certificate for development'
        )

        parser.add_argument(
            '--port',
            type=int,
            default=8800,
            help='Port to server run'
        )

        parser.add_argument(
            '--host',
            type=str,
            default='0.0.0.0',
            help='Hostname to server run'
        )

        parser.add_argument(
            '--route',
            type=str,
            default='/',
            help='Initial route when open website in first time'
        )

        # por concluir modificar o run_app, templates e create-app
        parser.add_argument(
            '--disable-ws',
            action='store_true',
            help='Enable websockets server'
        )

        parser.add_argument(
            '--ws-port',
            type=int,
            default=8800,
            help='Port to websocket run'
        )
    
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

        # Adicionar argumentos comuns
        self._add_run_arguments(run_parser)

        # Adicionar argumento específico para run
        run_parser.add_argument(
            '--reload',
            action='store_true',
            help='Add reload mode when running pyweber project'
        )

        # Sobrescrever o argumento 'file' para torná-lo posicional
        run_parser.add_argument(
            'file',
            type=str,
            nargs='?',
            default=self.default_file,
            help=f'Main file of pyweber project. default is {self.default_file}'
        )
    
    def add_cert_command(self):
        cert_parser = self.subparsers.add_parser(
            name='cert',
            help='Manage SSL certificates for HTTPS'
        )

        cert_subparsers = cert_parser.add_subparsers(dest="cert_command")

        check_parser = cert_subparsers.add_parser(
            name='check-mkcert',
            help='Check if mkcert is installed and install it if not'
        )

        mkcert_parser = cert_subparsers.add_parser(
            name='mkcert',
            help='Generate a locally-trusted certificate using mkcert (recommended for development)'
        )

        mkcert_parser.add_argument(
            '--output-dir',
            type=str,
            default=f'{self.default_path_config_file}/certs',
            help='Directory to save the generated certificate files'
        )

        mkcert_parser.add_argument(
            '--domains',
            type=str,
            default='localhost,127.0.0.1',
            help='Comma-separated list of domains/IPs to include in the certificate'
        )
    
    def _add_create_config_file_command(self):
        create_config_parser = self.subparsers.add_parser(
            name='create-config-file',
            help='Create a config file if not exists'
        )

        create_config_parser.add_argument(
            '--config-path',
            type=str,
            default=self.default_path_config_file,
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
            default=Path(self.default_path_config_file, 'config.toml'),
            help='Path to project config file'
        )
    
    def add_build_command(self):
        build_parser = self.subparsers.add_parser(
            'build',
            help='Build the pyweber project'
        )

        build_parser.add_argument(
            '--project-name',
            type=str,
            default=os.path.basename(os.getcwd()),
            help='Name to your final project'
        )

    
    def run(self):
        try:
            args = sys.argv[1:]

            args = self.parser.parse_args(args)

            if args.reload_mode:
                run_kwargs = {
                    'file': getattr(args, 'file', self.default_file),
                    'reload': True,
                    'cert_file': getattr(args, 'cert_file', None),
                    'key_file': getattr(args, 'key_file', None),
                    'auto_cert': getattr(args, 'auto_cert', False),
                    'port': getattr(args, 'port', 8800),
                    'host': getattr(args, 'host', '0.0.0.0'),
                    'route': getattr(args, 'route', '/'),
                    'disable_ws': getattr(args, 'disable_ws', False),
                    'ws_port': getattr(args, 'ws_port', 8800)
                }
                self.commands_funcs.run_app(**run_kwargs)

            if args.update:
                self.commands_funcs.update(framework='pyweber')
            
            elif args.edit:
                self.edit_cli_parameters.init_config()
            
            elif args.command == 'install':
                self.commands_funcs.install_requirements(path=args.config_file_path)

            elif args.command == 'create-new':
                self.commands_funcs.create(project_name=args.project_name, with_config=args.with_config)
            
            elif args.command == 'run':
                file = getattr(args, 'file', None)
                reload = getattr(args, 'reload', None)
                cert_file = getattr(args, 'cert_file', None)
                key_file = getattr(args, 'key_file', None)
                auto_cert = getattr(args, 'auto_cert', False)
                port = getattr(args, 'port')
                host = getattr(args, 'host')
                route = getattr(args, 'route')
                ws_port = getattr(args, 'ws_port')
                disable_ws = getattr(args, 'disable_ws', False)

                self.commands_funcs.run_app(
                    file=file,
                    reload=reload,
                    cert_file=cert_file,
                    key_file=key_file,
                    auto_cert=auto_cert,
                    port = port,
                    host = host,
                    route = route,
                    ws_port = ws_port,
                    disable_ws=disable_ws
                )
            
            elif args.command == 'create-config-file':
                self.commands_funcs.create_config_file(path=args.config_path, name=args.config_name)
            
            elif args.command == 'add-section':
                self.edit_cli_parameters.new_section(section_name=args.section_name, value=None)
            
            elif args.command == 'cert':
                self.run_cert_commands(args=args)
            
            elif args.command == 'build':
                project_name = getattr(args, 'project_name')
                self.commands_funcs.build_project(project_name=project_name)
            else:
                self.parser.print_help()
                exit(code=1)
        
        except KeyboardInterrupt:
            pass
    
    def run_cert_commands(self, args):
        if args.cert_command == 'check-mkcert':
            self.commands_funcs.check_mkcert()
        
        elif args.cert_command == 'mkcert':
            output_dir = getattr(args, 'output_dir', f'{self.default_path_config_file}/certs')
            domains = getattr(args, 'domains', 'localhost,127.0.0.1')

            self.commands_funcs.generate_mkcert(
                output_dir=output_dir,
                domains=domains
            )

        else:
            self.parser.parse_args(['cert', '--help'])

    @property
    def get_version(self):
        try:
            return version('pyweber')
        except PackageNotFoundError:
            return "0.0.0"

class CommandFunctions: # pragma: no cover
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
                config.set_parameters(path=Path(project_name, '.pyweber'))
                config['app']['name'] = project_name
                config['app']['description'] = f'A {project_name} builded with pyweber framework'
                config.save()

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
    
    def set_eviron_variables(self, reload: bool, port: int, host: str, route: str, ws_port: int, disable_ws: bool):
        os.environ['PYWEBER_RELOAD_MODE'] = str(reload)
        os.environ['PYWEBER_SERVER_PORT'] = str(port)
        os.environ['PYWEBER_SERVER_HOST'] = str(host)
        os.environ['PYWEBER_SERVER_ROUTE'] = str(route)
        os.environ['PYWEBER_WS_PORT'] = str(ws_port)
        os.environ['PYWEBER_DISABLE_WS'] = str(disable_ws)

        config['session']['reload_mode'] = reload
        config['server']['host'] = host
        config['server']['port'] = port
        config['server']['route'] = route
        config['websocket']['port'] = ws_port
        config['websocket']['disable_ws'] = disable_ws
    
    def check_https_context(self, auto_cert: bool, cert_file: str, key_file: str):
        if auto_cert:
            cert_file, key_file = self.generate_mkcert()

            self.log_message(
                message=f'🔒 Using auto-generated self-signed certificate',
                level='info'
            )
        
        elif cert_file and key_file:
            self.log_message(
                message=f'🔒 Using provided certificate: {cert_file}',
                level='info'
            )
            
        else:
            cert_file, key_file = '', ''
        
        os.environ['PYWEBER_CERT_FILE'] = cert_file
        os.environ['PYWEBER_KEY_FILE'] = key_file

        config['server']['cert_file'] = cert_file
        config['server']['key_file'] = key_file

    def run_app(self, **kwargs):

        try:
            reload = kwargs.get('reload')
            cert_file = kwargs.get('cert_file')
            key_file = kwargs.get('key_file')
            file = kwargs.get('file')
            auto_cert = kwargs.get('auto_cert')
            port = kwargs.get('port')
            host = kwargs.get('host')
            route = kwargs.get('route')
            ws_port = kwargs.get('ws_port')
            disable_ws = kwargs.get('disable_ws')

            self.log_message(
                message=f'✨ Trying to start the project',
                level='warning'
            )

            self.set_eviron_variables(reload, port, host, route, ws_port, disable_ws)
            self.check_https_context(auto_cert, cert_file, key_file)

            try:
                config.save() if config.path else None
            except FileNotFoundError:
                pass
            
            if sys.platform == 'win32':
                subprocess.run(['python', file], check=True, shell=True)
            else:
                subprocess.run(['python3', file], check=True)
        
        except subprocess.CalledProcessError as e:
            self.log_message(
                message=f'❌ Error: {e}',
                level='error'
            )

    def update(self, framework: str):
        try:
            update_script = StaticTemplates.UPDATE_FILE().replace('{framework}', framework)

            # Salvar o script em um arquivo temporário
            import tempfile
            with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
                f.write(update_script)
                temp_script = f.name

            self.log_message(
                message=f'Starting {framework} update...',
                level='warning'
            )

            # Executar o script em uma nova janela
            if sys.platform == 'win32':
                # No Windows, abrir em uma nova janela
                subprocess.Popen(['start', 'python', temp_script], shell=True)
            else:
                # No Linux/Mac, executar em segundo plano
                subprocess.Popen(
                    ['python3', temp_script],
                    start_new_session=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            self.log_message(
                message=f'Update process started in second plan',
                level='success'
            )

            # Sair do programa atual
            sys.exit(0)

        except Exception as e:
            self.log_message(
                message=f'❌ Error to start the update: {e}',
                level='error'
            )
    
    def create_path(self, path: str):
        os.makedirs(path, exist_ok=True)
    
    def create_static_file(self, file_path: str, content: str | bytes):
        encoding, mode=('utf-8', 'w') if not isinstance(content, bytes) else (None, 'wb')
        with open(file_path, mode=mode, encoding=encoding) as file:
            file.write(content)
    
    def create_config_file(self, path: str, name: str, keep_defaults=True):
        config.set_parameters(path=path, name=name, keep_defaults=keep_defaults)
        config['app']['name'] = os.path.basename(os.getcwd())
        config['app']['description'] = f"A {config['app']['name']} builded with pyweber framework"
        config.save()
    
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
    
    def build_project(self, project_name: str):
        os.makedirs(os.path.join('build', project_name), exist_ok=True)
        raise NotImplementedError(f'Build method for {project_name} not implemented yet')
    
    def generate_mkcert(self, **kwargs):
        """Generate a locally-trusted certificate using mkcert"""
        if not self.check_mkcert():
            return None, None

        try:
            # Criar diretório para certificados
            cert_dir = Path(kwargs.get('output_dir', '.pyweber/cert'))
            cert_dir.mkdir(parents=True, exist_ok=True)

            # Instalar CA local
            subprocess.run(['mkcert', '-install'], check=True, capture_output=True)

            # Gerar certificado
            domain_list = [str(domain).strip() for domain in kwargs.get('domains', 'localhost, 127.0.0.1').strip().split(',')]
            output_name = f"pyweber-{'-'.join(domain_list)}"
            output_path = cert_dir / output_name

            cmd = ['mkcert', '-key-file', f"{output_path}-key.pem", '-cert-file', f"{output_path}.pem"]
            cmd.extend(domain_list)

            subprocess.run(cmd, check=True, capture_output=True)

            cert_file = f"{output_path}.pem"
            key_file = f"{output_path}-key.pem"

            self.log_message(
                message=f"🔒 Certificate generated with mkcert at: {cert_file}",
                level='success'
            )

            return str(cert_file), str(key_file)

        except subprocess.SubprocessError as e:
            self.log_message(
                message=f"❌ Error generating certificate with mkcert: {e}",
                level='error'
            )
            return None, None
    
    def check_mkcert(self):
        """Check if mkcert is installed and provide installation instructions if not"""
        try:
            result = subprocess.run(['mkcert', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_message(
                    message=f"✅ mkcert is installed: {result.stdout.strip()}",
                    level='success'
                )
                return True
            else:
                raise FileNotFoundError
        except (FileNotFoundError, subprocess.SubprocessError):
            self.log_message(
                message="❌ mkcert is not installed",
                level='error'
            )

            # Instruções de instalação
            self.log_message(
                message="📋 Installation instructions:",
                level='info'
            )

            if sys.platform == 'win32':
                self.log_message(
                    message="Windows: Install with Chocolatey: choco install mkcert",
                    level='info'
                )
                self.log_message(
                    message="Or download from: https://github.com/FiloSottile/mkcert/releases",
                    level='info'
                )
            elif sys.platform == 'darwin':
                self.log_message(
                    message="macOS: Install with Homebrew: brew install mkcert",
                    level='info'
                )
            else:
                self.log_message(
                    message="Linux: Install with your package manager or download from: https://github.com/FiloSottile/mkcert/releases",
                    level='info'
                )

            return False
    
    def log_message(self, message: str, level: str = 'info'):
        colors = {
            'info': Colors.BLUE,
            'success': Colors.GREEN,
            'warning': Colors.YELLOW,
            'error': Colors.RED,
            'reset': Colors.RESET
        }
        PrintLine(f"{colors.get(level, '')}{message}{colors.get('reset')}")

class ConfigManagerCLI: # pragma: no cover
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

                            value = self.__get_new_field_value(key_value=key_value)
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
    
    def __get_new_field_value(self, key_value: list[str]):
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
            value = self.__get_dict_values(keys=value.split(';'))
        else:
            value = value.strip()
    
    def __get_dict_values(self, keys: list[str], default_value: dict = {}):
        if any(':' not in v and '=' not in v for v in keys):
            raise ValueError('None separator key and value identified')
        else:
            default_value = default_value

            for key in keys:
                k, v = key.replace(':','=').strip().split('=')
                type = k.split()

                if type[-1] in DefaultTypes.floats:
                    v = float(v)
                elif type[-1] in DefaultTypes.integer:
                    v = int(v)
                elif type[-1] in DefaultTypes.lists:
                    v = v.split()
                
                default_value[type[0]] = v
        return default_value
    
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
                self.__set_new_value(list_path=path)
    
    def __get_new_value(self, list_path: list[str], current_value: bool | str):
        if isinstance(current_value, bool):
            confirm: str = questionary.text(
                f"Confirm to change value for {list_path[-1]}? (Y/N): "
            ).ask()

            if confirm.lower() == 'y':
                return not current_value
            
            return current_value

        new_value: str = questionary.text(
            f"What's a new value for {list_path[-1]}?: "
        ).ask()
        
        return new_value
    
    def __set_new_value(self, list_path: list[str]):
        current_value = config.get(*list_path)

        while True:
            new_value = self.__get_new_value(list_path, current_value)

            try:
                if isinstance(current_value, list):
                    new_value = new_value.split()
                elif isinstance(current_value, int):
                    new_value = int(new_value)
                elif isinstance(current_value, float):
                    new_value = float(new_value)
                
                config.set(*list_path, value=new_value)
                break
            except ValueError:
                questionary.print(
                    text=f'Invalid value for {list_path[-1]}, expected {type(current_value).__name__}.'
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
│ List         │ tags list python pyweber api            │
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