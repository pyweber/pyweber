import socket
import sys
import pytest

from pyweber.connection.selector import (
    IOSelector,
    EpollSelector,
    KqueueSelector,
    PollSelector,
    SelectSelector,
)


@pytest.fixture
def listen_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', 0))
    sock.listen(5)
    yield sock
    sock.close()


class TestIOSelectorFactory:
    def test_factory_returns_platform_selector(self):
        selector = IOSelector()
        if sys.platform == 'linux':
            assert isinstance(selector, EpollSelector)
        elif sys.platform == 'win32':
            assert isinstance(selector, SelectSelector)
        elif sys.platform in ('darwin', 'freebsd', 'openbsd', 'netbsd'):
            assert isinstance(selector, KqueueSelector)


class TestSelectorRegisterSelect:
    @pytest.mark.parametrize(
        'selector_cls',
        [EpollSelector, SelectSelector],
    )
    def test_register_and_select(self, selector_cls, listen_socket):
        if selector_cls is EpollSelector and sys.platform != 'linux':
            pytest.skip('EpollSelector only on Linux')

        selector = selector_cls()
        selector.register(listen_socket)
        ready = selector.select(timeout=0.01)
        assert isinstance(ready, list)
        selector.unregister(listen_socket)
        selector.close()

    @pytest.mark.skipif(not hasattr(__import__('select'), 'poll'), reason='poll unavailable')
    def test_poll_selector(self, listen_socket):
        selector = PollSelector()
        selector.register(listen_socket)
        ready = selector.select(timeout=0.01)
        assert isinstance(ready, list)
        selector.unregister(listen_socket)
        selector.close()

    def test_kqueue_on_supported_platform(self, listen_socket):
        if sys.platform not in ('darwin', 'freebsd', 'openbsd', 'netbsd'):
            pytest.skip('kqueue not on this platform')

        selector = KqueueSelector()
        selector.register(listen_socket)
        ready = selector.select(timeout=0.01)
        assert isinstance(ready, list)
        selector.close()
