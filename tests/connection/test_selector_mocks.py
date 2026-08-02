"""Mock-based coverage for non-Windows selectors and factory fallback."""

from unittest.mock import MagicMock, patch

from pyweber.connection.selector import (
    EpollSelector,
    KqueueSelector,
    PollSelector,
    SelectSelector,
    IOSelector,
)


class TestSelectorMocks:
    def test_epoll_selector_lifecycle(self):
        fake_epoll = MagicMock()
        fake_epoll.poll.return_value = [(7, 1)]
        sock = MagicMock()
        sock.fileno.return_value = 7

        with patch('pyweber.connection.selector.select.EPOLLIN', create=True, new=1):
            sel = EpollSelector.__new__(EpollSelector)
            sel._epoll = fake_epoll
            sel._sockets = {}
            sel.register(sock)
            ready = sel.select(timeout=0.01)
            assert sock in ready
            sel.unregister(sock)
            fake_epoll.unregister.side_effect = OSError('gone')
            sel.unregister(sock)
            sel.close()
            fake_epoll.close.assert_called()

    def test_kqueue_selector_lifecycle(self):
        fake_kq = MagicMock()
        event = MagicMock()
        event.ident = 9
        event.filter = 1
        fake_kq.control.return_value = [event]
        sock = MagicMock()
        sock.fileno.return_value = 9

        with patch('pyweber.connection.selector.select.kevent', create=True, return_value=MagicMock()):
            with patch('pyweber.connection.selector.select.KQ_FILTER_READ', create=True, new=1):
                with patch('pyweber.connection.selector.select.KQ_EV_ADD', create=True, new=1):
                    with patch('pyweber.connection.selector.select.KQ_EV_ENABLE', create=True, new=2):
                        with patch('pyweber.connection.selector.select.KQ_EV_DELETE', create=True, new=4):
                            sel = KqueueSelector.__new__(KqueueSelector)
                            sel._kqueue = fake_kq
                            sel._sockets = {}
                            sel.register(sock)
                            ready = sel.select(0.01)
                            assert sock in ready
                            sel.unregister(sock)
                            fake_kq.control.side_effect = OSError('x')
                            sel.unregister(sock)
                            sel.close()

    def test_poll_selector_lifecycle(self):
        fake_poll = MagicMock()
        fake_poll.poll.return_value = [(3, 1)]
        sock = MagicMock()
        sock.fileno.return_value = 3

        with patch('pyweber.connection.selector.select.POLLIN', create=True, new=1):
            sel = PollSelector.__new__(PollSelector)
            sel._poll = fake_poll
            sel._sockets = {}
            sel.register(sock)
            ready = sel.select(0.01)
            assert sock in ready
            sel.unregister(sock)
            fake_poll.unregister.side_effect = OSError('x')
            sel.unregister(sock)
            sel.close()

    def test_select_selector_empty_and_invalid_fd(self):
        sel = SelectSelector()
        assert sel.select(0.01) == []
        sock = MagicMock()
        sock.fileno.return_value = -1
        sel.register(sock)
        assert sel.select(0.01) == []
        sel.unregister(sock)
        sel.close()

    def test_io_selector_else_fallback(self):
        with patch('pyweber.connection.selector.sys.platform', 'sunos5'):
            with patch('pyweber.connection.selector.PollSelector') as poll_cls:
                poll_cls.return_value = MagicMock(spec=PollSelector)
                sel = IOSelector()
                poll_cls.assert_called_once()
                assert sel is poll_cls.return_value
