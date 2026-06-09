import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def async_timeout(seconds: float | None):
    """asyncio.timeout compatible with Python 3.10+."""
    if seconds is None:
        yield
        return

    if hasattr(asyncio, 'timeout'):
        async with asyncio.timeout(seconds):
            yield
        return

    loop = asyncio.get_running_loop()
    task = asyncio.current_task()
    if task is None:
        yield
        return

    timed_out = False

    def _on_timeout():
        nonlocal timed_out
        timed_out = True
        task.cancel()

    handle = loop.call_later(seconds, _on_timeout)
    try:
        yield
    except asyncio.CancelledError as exc:
        if timed_out:
            raise asyncio.TimeoutError from exc
        raise
    finally:
        handle.cancel()
