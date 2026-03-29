import sys
import select
import socket

class IOSelector: # pragma: no cover
    """
    Selecciona automaticamente o melhor mecanismo de I/O para o OS actual.
    Interface uniforme independente do OS.
    """

    def __new__(cls, *args, **kwargs):
        if sys.platform == 'linux':
            return EpollSelector()
        elif sys.platform in ('darwin', 'freebsd', 'openbsd', 'netbsd'):
            return KqueueSelector()
        elif sys.platform == 'win32':
            return SelectSelector()   # Windows não tem epoll/kqueue
        else:
            return PollSelector()     # fallback genérico


class EpollSelector: # pragma: no cover
    """Linux — epoll. O(1), ilimitado."""

    def __init__(self):
        self._epoll = select.epoll()
        self._sockets: dict[int, socket.socket] = {}

    def register(self, sock: socket.socket):
        self._sockets[sock.fileno()] = sock
        self._epoll.register(sock.fileno(), select.EPOLLIN | select.EPOLLET)

    def unregister(self, sock: socket.socket):
        try:
            self._epoll.unregister(sock.fileno())
            del self._sockets[sock.fileno()]
        except Exception:
            pass

    def select(self, timeout: float = 1.0) -> list[socket.socket]:
        events = self._epoll.poll(timeout)
        return [self._sockets[fd] for fd, _ in events if fd in self._sockets]

    def close(self):
        self._epoll.close()


class KqueueSelector: # pragma: no cover
    """macOS / BSD — kqueue. O(1), ilimitado."""

    def __init__(self):
        self._kqueue = select.kqueue()
        self._sockets: dict[int, socket.socket] = {}

    def register(self, sock: socket.socket):
        self._sockets[sock.fileno()] = sock
        event = select.kevent(
            sock.fileno(),
            filter=select.KQ_FILTER_READ,
            flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE
        )
        self._kqueue.control([event], 0)

    def unregister(self, sock: socket.socket):
        try:
            event = select.kevent(
                sock.fileno(),
                filter=select.KQ_FILTER_READ,
                flags=select.KQ_EV_DELETE
            )
            self._kqueue.control([event], 0)
            del self._sockets[sock.fileno()]
        except Exception:
            pass

    def select(self, timeout: float = 1.0) -> list[socket.socket]:
        events = self._kqueue.control(None, 100, timeout)
        return [
            self._sockets[e.ident]
            for e in events
            if e.ident in self._sockets and e.filter == select.KQ_FILTER_READ
        ]

    def close(self):
        self._kqueue.close()


class PollSelector: # pragma: no cover
    """Linux/macOS/BSD — poll. Sem limite de fds, mais portável que epoll."""

    def __init__(self):
        self._poll = select.poll()
        self._sockets: dict[int, socket.socket] = {}

    def register(self, sock: socket.socket):
        self._sockets[sock.fileno()] = sock
        self._poll.register(sock.fileno(), select.POLLIN)

    def unregister(self, sock: socket.socket):
        try:
            self._poll.unregister(sock.fileno())
            del self._sockets[sock.fileno()]
        except Exception:
            pass

    def select(self, timeout: float = 1.0) -> list[socket.socket]:
        # poll timeout em milissegundos
        events = self._poll.poll(int(timeout * 1000))
        return [self._sockets[fd] for fd, _ in events if fd in self._sockets]

    def close(self):
        pass


class SelectSelector: # pragma: no cover
    """Windows + fallback universal — select. Limite ~1024 fds."""

    def __init__(self):
        self._sockets: dict[int, socket.socket] = {}

    def register(self, sock: socket.socket):
        fd = sock.fileno()
        if fd > 0: self._sockets[fd] = sock

    def unregister(self, sock: socket.socket):
        fd = sock.fileno()
        self._sockets.pop(fd, None)
        self._sockets.pop(-1, None)

    def select(self, timeout: float = 1.0) -> list[socket.socket]:
        valid = {fd: s for fd, s in self._sockets.items() if fd >= 0 and s.fileno() >= 0}

        if not valid:
            return []
        
        readable, _, _ = select.select(list(valid.values()), [], [], timeout)
        return readable

    def close(self):
        pass