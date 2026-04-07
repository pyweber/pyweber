import asyncio
from threading import Lock
from typing import Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor, Future

from pyweber.utils.utils import PrintLine

class TaskManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.lock = Lock()                          # ✅ para sync
        self.async_lock = asyncio.Lock()            # ✅ para async

        self.active_handlers: dict[str, dict[str, Future]] = {}
        self.active_handlers_async: dict[str, dict[str, asyncio.Task]] = {}

    # ----------------- ASYNC -----------------
    async def create_task_async(self, session_id: str, event_id: str, handler: Awaitable, event_handler):
        async with self.async_lock:
            session = self.active_handlers_async.setdefault(session_id, {})
            existing = session.get(event_id)

            if existing and not existing.done():
                return existing  # já em execução

            task = asyncio.create_task(
                self.__run_async(session_id, event_id, handler, event_handler)
            )
            session[event_id] = task

        return task

    async def __run_async(self, session_id: str, event_id: str, handler: Awaitable, event_handler):
        """Executa handler async e limpa após terminar"""
        try:
            return await handler(event_handler)
        except asyncio.CancelledError:
            PrintLine(f"Async task ({event_id}) cancelled.", level='INFO')
        except Exception as error:
            PrintLine(f"Error on async handler ({event_id}): {error}", level='ERROR')
            raise
        finally:
            # ✅ limpa sempre após terminar
            async with self.async_lock:
                if session_id in self.active_handlers_async:
                    self.active_handlers_async[session_id].pop(event_id, None)
                    if not self.active_handlers_async[session_id]:
                        self.active_handlers_async.pop(session_id, None)

    async def cancel_all_tasks_async(self, session_id: str):
        async with self.async_lock:
            session = self.active_handlers_async.pop(session_id, {})
            tasks = [t for t in session.values() if not t.done()]
            for task in tasks:
                task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return len(tasks)

    # ----------------- SYNC -----------------
    def create_task(self, session_id: str, event_id: str, handler: Callable, event_handler):
        with self.lock:
            session = self.active_handlers.setdefault(session_id, {})
            existing = session.get(event_id)

            if existing and not existing.done():
                return False

            future = self.executor.submit(
                self.__run_executor, session_id, event_id, handler, event_handler
            )
            session[event_id] = future

        return True

    def __run_executor(self, session_id: str, event_id: str, handler: Callable, event_handler):
        try:
            return handler(event_handler)
        except Exception as e:
            PrintLine(f"Error on sync handler ({event_id}): {e}", level='ERROR')
            raise
        finally:
            # ✅ lock protege a limpeza
            with self.lock:
                if session_id in self.active_handlers:
                    self.active_handlers[session_id].pop(event_id, None)
                    if not self.active_handlers[session_id]:
                        self.active_handlers.pop(session_id, None)

    def cancel_session_handlers(self, session_id: str):
        with self.lock:
            session = self.active_handlers.pop(session_id, {})
            for future in session.values():
                if not future.done():
                    future.cancel()

    # ----------------- SHUTDOWN -----------------
    async def cancel_all_async(self):
        sessions = list(self.active_handlers_async.keys())
        for session_id in sessions:
            await self.cancel_all_tasks_async(session_id)

    def shutdown(self):
        for session_id in list(self.active_handlers.keys()):
            self.cancel_session_handlers(session_id)
        self.executor.shutdown(wait=False, cancel_futures=True)
