"""Env interpolation and .env loading for config.toml."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pyweber.config.config import PyweberConfig
from pyweber.config.env import (
    EnvConfigView,
    apply_dotenv,
    coerce_env_value,
    dotenv_candidates,
    interpolate_string,
    load_dotenv,
    parse_dotenv,
    resolve_config_value,
)


def test_parse_dotenv_syntax():
    parsed = parse_dotenv(
        '\n'.join([
            '# comment',
            'export QUOTED="hello world"',
            "SINGLE='x'",
            'BARE=abc',
            'not a line',
            '1INVALID=no',
            '',
            'EMPTY=',
        ])
    )
    assert parsed['QUOTED'] == 'hello world'
    assert parsed['SINGLE'] == 'x'
    assert parsed['BARE'] == 'abc'
    assert parsed['EMPTY'] == ''
    assert '1INVALID' not in parsed


def test_interpolate_string_variants(monkeypatch):
    env = {'NAME': 'Ada', 'PORT': '8800'}
    assert interpolate_string('plain', env) == 'plain'
    assert interpolate_string('${NAME}', env) == 'Ada'
    assert interpolate_string('hi-${NAME}!', env) == 'hi-Ada!'
    assert interpolate_string('${MISSING}', env) == ''
    assert interpolate_string('${MISSING:-fallback}', env) == 'fallback'
    assert interpolate_string('${NAME:-x}', env) == 'Ada'
    assert interpolate_string('$$${NAME}', env) == '$Ada'
    monkeypatch.setenv('LIVE', 'yes')
    assert interpolate_string('${LIVE}') == 'yes'


def test_empty_env_uses_default():
    assert interpolate_string('${BLANK:-x}', {'BLANK': ''}) == 'x'


def test_coerce_env_value():
    assert coerce_env_value('true') is True
    assert coerce_env_value('OFF') is False
    assert coerce_env_value('8800') == 8800
    assert coerce_env_value('-3') == -3
    assert coerce_env_value('hello') == 'hello'


def test_resolve_full_ref_coerces_and_partial_does_not():
    env = {'PORT': '8800', 'NAME': 'app'}
    assert resolve_config_value('${PORT}', env) == 8800
    assert resolve_config_value('p-${PORT}', env) == 'p-8800'
    assert resolve_config_value(['${NAME}', 'x'], env) == ['app', 'x']


def test_env_config_view_read_write_save_shape():
    raw = {'secret': '${TOKEN}', 'nested': {'n': 1}}
    view = EnvConfigView(raw, {'TOKEN': 's3cret'})
    assert view['secret'] == 's3cret'
    assert view.get('missing', 'd') == 'd'
    assert 'secret' in view
    assert list(view) == ['secret', 'nested']
    assert len(view) == 2
    assert ('secret', 's3cret') in view.items()
    assert 's3cret' in view.values()
    view['secret'] = '${TOKEN}'
    assert raw['secret'] == '${TOKEN}'
    view.setdefault('extra', {'k': '${TOKEN}'})
    assert raw['extra']['k'] == '${TOKEN}'
    view.setdefault('created')
    assert raw['created'] == {}
    view.update({'a': 1}, b=2)
    assert raw['a'] == 1
    assert raw['b'] == 2
    del view['b']
    assert 'b' not in raw
    popped = view.pop('a')
    assert popped == 1
    assert view.pop('nope', 'x') == 'x'
    view.clear()
    assert raw == {}
    assert 'z' in repr(EnvConfigView({'x': '${Y}'}, {'Y': 'z'}))


def test_load_dotenv_does_not_override_process_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('KEEP', 'process')
    (tmp_path / '.env').write_text('KEEP=file\nNEW=fromfile\n', encoding='utf-8')
    load_dotenv()
    try:
        assert os.environ['KEEP'] == 'process'
        assert os.environ['NEW'] == 'fromfile'
    finally:
        os.environ.pop('NEW', None)


def test_dotenv_candidates_include_explicit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    extra = tmp_path / 'prod.env'
    extra.write_text('X=1\n', encoding='utf-8')
    monkeypatch.setenv('PYWEBER_ENV_FILE', str(extra))
    cfg = tmp_path / '.pyweber' / 'config.toml'
    paths = dotenv_candidates(cfg)
    assert extra in paths or extra.resolve() in {p.resolve() for p in paths}


def test_apply_dotenv_missing_file(tmp_path):
    apply_dotenv(tmp_path / 'nope.env')


def test_pyweber_config_interpolates_and_save_keeps_refs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('APP_SECRET', 'not-in-git')
    monkeypatch.setenv('APP_PORT', '9900')
    cfg_dir = tmp_path / '.pyweber'
    cfg_dir.mkdir()
    (cfg_dir / 'config.toml').write_text(
        '\n'.join([
            '[app]',
            "name = '${APP_NAME:-Pyweber App}'",
            '[server]',
            "port = '${APP_PORT}'",
            '[session]',
            "secret_key = '${APP_SECRET}'",
        ]) + '\n',
        encoding='utf-8',
    )
    cfg = PyweberConfig()
    assert cfg.get('session', 'secret_key') == 'not-in-git'
    assert cfg['session']['secret_key'] == 'not-in-git'
    assert cfg.get('server', 'port') == 9900
    assert cfg.get('app', 'name') == 'Pyweber App'
    cfg.set('server', 'route', value='/home')
    saved = (cfg_dir / 'config.toml').read_text(encoding='utf-8')
    assert '${APP_SECRET}' in saved
    assert 'not-in-git' not in saved
    assert '/home' in saved


def test_pyweber_config_reads_dotenv_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('DOTENV_SECRET', raising=False)
    (tmp_path / '.env').write_text('DOTENV_SECRET=from-dotenv\n', encoding='utf-8')
    cfg_dir = tmp_path / '.pyweber'
    cfg_dir.mkdir()
    (cfg_dir / 'config.toml').write_text(
        '[session]\nsecret_key = "${DOTENV_SECRET}"\n',
        encoding='utf-8',
    )
    cfg = PyweberConfig()
    try:
        assert cfg.get('session', 'secret_key') == 'from-dotenv'
    finally:
        os.environ.pop('DOTENV_SECRET', None)


def test_decode_config_bytes_encodings():
    from pyweber.config.config import decode_config_bytes

    assert decode_config_bytes('ação'.encode('utf-8')) == 'ação'
    assert decode_config_bytes('ação'.encode('cp1252')) == 'ação'
    assert decode_config_bytes(b'\xef\xbb\xbfname = "ok"') == 'name = "ok"'
    mixed = decode_config_bytes(b'name = "x\xffy"')
    assert mixed.startswith('name') and 'x' in mixed and 'y' in mixed


def test_pyweber_config_reads_cp1252(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_dir = tmp_path / '.pyweber'
    cfg_dir.mkdir()
    (cfg_dir / 'config.toml').write_bytes(
        '[app]\nname = "Aplica\xe7\xe3o"\n'.encode('latin-1')
    )
    cfg = PyweberConfig()
    assert cfg.get('app', 'name') == 'Aplicação'
