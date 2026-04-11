import asyncio
from threading import Lock
from typing import Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor, Future

from pyweber.utils.utils import PrintLine

class TaskManager: # pragma: no cover
    """Gerencia tasks async e sync por sessão, evitando tasks antigas após reload."""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.lock = Lock()

        # Tasks sync: {session_id: {event_id: Future}}
        self.active_handlers: dict[str, dict[str, Future]] = {}

        # Tasks async: {session_id: {event_id: asyncio.Task}}
        self.active_handlers_async: dict[str, dict[str, asyncio.Task]] = {}

    # ----------------- ASYNC TASKS -----------------
    async def create_task_async(self, session_id: str, event_id: str, handler: Awaitable, event_handler):
        """Cria uma task async se não houver duplicata ativa."""
        if session_id not in self.active_handlers_async:
            self.active_handlers_async[session_id] = {}

        existing_task = self.active_handlers_async[session_id].get(event_id)
        if existing_task and not existing_task.done():
            # Task já em execução, não cria duplicata
            return event_id

        task = asyncio.create_task(handler(event_handler))
        self.active_handlers_async[session_id][event_id] = task

        try:
            result = await task
            return result
        except asyncio.CancelledError:
            PrintLine(f"Async task ({event_id}) cancelled.", level='INFO')
        except Exception as error:
            PrintLine(f"Error on async handler ({event_id}): {error}", level='ERROR')
            raise error
        finally:
            # Limpa task finalizada
            self.active_handlers_async[session_id].pop(event_id, None)
            if not self.active_handlers_async[session_id]:
                self.active_handlers_async.pop(session_id, None)

    async def cancel_all_tasks_async(self, session_id: str):
        """Cancela todas as tasks async de uma sessão."""
        count = 0
        if session_id in self.active_handlers_async:
            tasks = list(self.active_handlers_async[session_id].values())
            for task in tasks:
                if not task.done():
                    task.cancel()
                    count += 1
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            self.active_handlers_async.pop(session_id, None)
        return count

    # ----------------- SYNC TASKS -----------------
    def create_task(self, session_id: str, event_id: str, handler: Callable, event_handler):
        """Cria task sync via ThreadPoolExecutor."""
        if session_id not in self.active_handlers:
            self.active_handlers[session_id] = {}

        existing = self.active_handlers[session_id].get(event_id)
        if existing and not existing.done():
            # Task já em execução
            return False

        future = self.executor.submit(self.__run_executor, session_id, event_id, handler, event_handler)
        self.active_handlers[session_id][event_id] = future
        return True

    def __run_executor(self, session_id: str, event_id: str, handler: Callable, event_handler):
        """Executa handler sync em thread, limpa após terminar."""
        try:
            result = handler(event_handler)
            return result
        except Exception as e:
            PrintLine(f"Error on sync handler ({event_id}): {e}", level='ERROR')
            raise e
        finally:
            # Limpa handler finalizado
            if session_id in self.active_handlers:
                self.active_handlers[session_id].pop(event_id, None)
                if not self.active_handlers[session_id]:
                    self.active_handlers.pop(session_id, None)

    def cancel_session_handlers(self, session_id: str):
        """Cancela todas as tasks sync de uma sessão."""
        if session_id in self.active_handlers:
            for event_id, future in self.active_handlers[session_id].items():
                if future and not future.done():
                    future.cancel()
            self.active_handlers.pop(session_id, None)

    # ----------------- SHUTDOWN -----------------
    async def cancel_all_async(self):
        """Cancela todas tasks async de todas sessões."""
        all_sessions = list(self.active_handlers_async.keys())
        for session_id in all_sessions:
            await self.cancel_all_tasks_async(session_id)

    def shutdown(self):
        """Finaliza executor e cancela todas tasks sync."""
        for session_id in list(self.active_handlers.keys()):
            self.cancel_session_handlers(session_id)
        self.executor.shutdown(wait=False, cancel_futures=True)
