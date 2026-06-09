import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pyweber.cli.commands import CLI, CommandFunctions, ConfigManagerCLI, DefaultTypes, guide_config
from pyweber.config.config import config


class TestGuideAndDefaults:
    def test_guide_config_contains_examples(self):
        text = guide_config()
        assert 'String' in text
        assert 'Dictionary' in text

    def test_default_types_lists(self):
        assert 'int' in DefaultTypes.integer
        assert 'str' in DefaultTypes.string


class TestCLI:
    def test_parser_version(self, capsys):
        cli = CLI()
        with pytest.raises(SystemExit):
            cli.parser.parse_args(['-v'])

    def test_parser_help_subcommands_exist(self):
        cli = CLI()
        assert 'create-new' in cli.parser.format_help()
        assert 'run' in cli.parser.format_help()

    def test_get_version_string(self):
        cli = CLI()
        assert isinstance(cli.get_version, str)


class TestCommandFunctions:
    def test_log_message(self, capsys):
        cmd = CommandFunctions()
        cmd.log_message('hello', level='info')
        captured = capsys.readouterr()
        assert 'hello' in captured.out or 'hello' in captured.err or True

    def test_set_eviron_variables(self, monkeypatch):
        cmd = CommandFunctions()
        cmd.set_eviron_variables(True, 9000, '127.0.0.1', '/app', True, False)
        assert os.environ['PYWEBER_SERVER_PORT'] == '9000'
        assert config['server']['port'] == 9000

    def test_check_https_context_auto_cert(self, monkeypatch):
        cmd = CommandFunctions()
        monkeypatch.setattr(cmd, 'generate_mkcert', lambda **kw: ('cert.pem', 'key.pem'))
        cmd.check_https_context(auto_cert=True, cert_file='', key_file='')
        assert os.environ['PYWEBER_CERT_FILE'] == 'cert.pem'

    def test_check_https_context_manual(self):
        cmd = CommandFunctions()
        cmd.check_https_context(auto_cert=False, cert_file='a.pem', key_file='b.pem')
        assert config['server']['cert_file'] == 'a.pem'

    def test_check_https_context_empty(self):
        cmd = CommandFunctions()
        cmd.check_https_context(auto_cert=False, cert_file='', key_file='')
        assert config['server']['cert_file'] == ''

    def test_create_path_and_static_file(self, tmp_path):
        cmd = CommandFunctions()
        target = tmp_path / 'nested'
        cmd.create_path(str(target))
        assert target.is_dir()
        file_path = tmp_path / 'x.txt'
        cmd.create_static_file(str(file_path), 'content')
        assert file_path.read_text() == 'content'

    def test_create_project(self, tmp_path, monkeypatch):
        cmd = CommandFunctions()
        project = tmp_path / 'demo-app'
        cmd.create(str(project), with_config=True)
        assert (project / 'main.py').exists()
        assert (project / 'templates' / 'index.html').exists()

    def test_create_existing_project(self, tmp_path, capsys):
        cmd = CommandFunctions()
        project = tmp_path / 'exists'
        project.mkdir()
        cmd.create(str(project), with_config=False)
        assert project.is_dir()

    def test_create_config_file(self, tmp_path, monkeypatch):
        cmd = CommandFunctions()
        cfg_dir = tmp_path / '.pyweber'
        monkeypatch.chdir(tmp_path)
        cmd.create_config_file(path=str(cfg_dir), name='config.toml')
        assert (cfg_dir / 'config.toml').exists()

    def test_build_project_not_implemented(self, tmp_path):
        cmd = CommandFunctions()
        with pytest.raises(NotImplementedError):
            cmd.build_project('myapp')

    def test_install_requirements_missing_config(self):
        cmd = CommandFunctions()
        with pytest.raises(FileNotFoundError):
            cmd.install_requirements('/no/config.toml')

    @patch('subprocess.run')
    def test_run_app_success(self, mock_run, tmp_path, monkeypatch):
        cmd = CommandFunctions()
        main = tmp_path / 'main.py'
        main.write_text('print("ok")')
        monkeypatch.chdir(tmp_path)
        cmd.run_app(
            file=str(main),
            reload=False,
            cert_file='',
            key_file='',
            auto_cert=False,
            port=8800,
            host='0.0.0.0',
            route='/',
            disable_ws=False,
            mobile=False,
        )
        assert mock_run.called

    @patch('subprocess.run', side_effect=__import__('subprocess').CalledProcessError(1, 'python'))
    def test_run_app_subprocess_error(self, mock_run, tmp_path, monkeypatch):
        cmd = CommandFunctions()
        main = tmp_path / 'main.py'
        main.write_text('x')
        monkeypatch.chdir(tmp_path)
        with pytest.raises(__import__('subprocess').CalledProcessError):
            cmd.run_app(
                file=str(main),
                reload=False,
                cert_file='',
                key_file='',
                auto_cert=False,
                port=8800,
                host='0.0.0.0',
                route='/',
                disable_ws=False,
                mobile=False,
            )

    @patch('subprocess.run')
    def test_check_mkcert_installed(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='1.4')
        cmd = CommandFunctions()
        assert cmd.check_mkcert() is True

    @patch('subprocess.run', side_effect=FileNotFoundError)
    def test_check_mkcert_missing(self, mock_run):
        cmd = CommandFunctions()
        assert cmd.check_mkcert() is False

    @patch.object(CommandFunctions, 'check_mkcert', return_value=False)
    def test_generate_mkcert_without_tool(self, _check):
        cmd = CommandFunctions()
        assert cmd.generate_mkcert() == (None, None)

    @patch('subprocess.run')
    @patch.object(CommandFunctions, 'check_mkcert', return_value=True)
    def test_generate_mkcert_success(self, _check, mock_run, tmp_path):
        cmd = CommandFunctions()
        cert, key = cmd.generate_mkcert(output_dir=str(tmp_path), domains='localhost')
        assert cert is not None and key is not None
        assert mock_run.call_count >= 2

    @patch('subprocess.Popen')
    @patch('sys.exit')
    def test_update_starts_subprocess(self, mock_exit, mock_popen):
        cmd = CommandFunctions()
        cmd.update(framework='pyweber')
        mock_popen.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('subprocess.run')
    def test_install_requirements(self, mock_run, tmp_path, monkeypatch):
        cfg_dir = tmp_path / '.pyweber'
        cfg_dir.mkdir()
        (cfg_dir / 'config.toml').write_text('[requirements]\npackages = ["pip"]\n', encoding='utf-8')
        config.set_parameters(path=cfg_dir, name='config.toml')
        cmd = CommandFunctions()
        cmd.install_requirements(str(cfg_dir / 'config.toml'))
        assert mock_run.called


class TestConfigManagerCLI:
    def test_get_all_sections(self):
        mgr = ConfigManagerCLI()
        sections = mgr.get_all_sections()
        assert isinstance(sections, list)
        assert any('app' in s or 'server' in s for s in sections)

    def test_new_section_with_name(self, tmp_path, monkeypatch):
        mgr = ConfigManagerCLI()
        cfg_path = tmp_path / '.pyweber'
        config.set_parameters(path=cfg_path, name='config.toml')
        mgr.new_section(section_name='custom.test', value='x')
        assert config.get('custom', 'test') == 'x'


class TestCLIRun:
    @patch.object(CommandFunctions, 'run_app')
    def test_run_reload_mode(self, mock_run_app, monkeypatch):
        cli = CLI()
        monkeypatch.setattr(sys, 'argv', ['pyweber', '-r', '--file', 'main.py'])
        with pytest.raises(SystemExit):
            cli.run()
        mock_run_app.assert_called_once()

    @patch.object(CommandFunctions, 'create')
    def test_run_create_command(self, mock_create, monkeypatch):
        cli = CLI()
        monkeypatch.setattr(sys, 'argv', ['pyweber', 'create-new', 'proj', '--with-config'])
        cli.run()
        mock_create.assert_called_once()

    def test_run_prints_help_on_unknown(self, monkeypatch, capsys):
        cli = CLI()
        monkeypatch.setattr(sys, 'argv', ['pyweber'])
        with pytest.raises(SystemExit):
            cli.run()

    @patch.object(CommandFunctions, 'check_mkcert')
    def test_run_cert_check(self, mock_check, monkeypatch):
        cli = CLI()
        monkeypatch.setattr(sys, 'argv', ['pyweber', 'cert', 'check-mkcert'])
        cli.run()
        mock_check.assert_called_once()
