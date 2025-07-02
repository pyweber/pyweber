import asyncio
from threading import Lock
from typing import Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor, Future

from pyweber.utils.utils import PrintLine

class TaskManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.lock = Lock()
        self.active_handlers: dict[str, dict[str, Future]] = {}
        self.active_handlers_async: dict[str, dict[str, Future]] = {}
    
    async def create_task_async(self, session_id: str, event_id: str, handler: Awaitable, event_handler):
        
        if session_id not in self.active_handlers_async:
            self.active_handlers_async[session_id] = {}

        if event_id in self.active_handlers_async[session_id]:
            existing_task = self.active_handlers_async[session_id][event_id]
            if existing_task.done():
                del self.active_handlers_async[session_id][event_id]
            else:
                # Tarefa já em execução, não criar uma nova
                return event_id
        
        task = asyncio.create_task(self.__run_task_async(session_id, event_id, handler, event_handler))
        self.active_handlers_async[session_id][event_id] = task
        
        return event_id

    async def __run_task_async(self, session_id: str, event_id: str, handler, event_handler):
        try:
            return await handler(event_handler)
        except asyncio.CancelledError:
            # Tarefa foi cancelada normalmente
            raise
        except Exception as e:
            # Capturar qualquer outra exceção
            PrintLine(f"Error on async handler ({event_id}): {e}", level='ERROR')
            raise e

        finally:
            if session_id in self.active_handlers_async and event_id in self.active_handlers_async[session_id]:
                del self.active_handlers_async[session_id][event_id]

                if not self.active_handlers_async[session_id]:
                    del self.active_handlers_async[session_id]
    
    async def cancel_all_tasks_async(self, session_id: str) -> int:
        count = 0
        if session_id in self.active_handlers_async:
            tasks = list(self.active_handlers_async[session_id].items())
            
            for event_id, task in tasks:
                if not task.done():
                    task.cancel()
                    count += 1
            
            del self.active_handlers_async[session_id]
        
        return count

    
    def create_task(self, session_id: str, event_id: str, handler: Callable, event_handler):
        session_handlers = self.active_handlers.get(session_id, {})

        if session_handlers and session_handlers.get(event_handler, None):
            return False
        
        future = self.executor.submit(
            self.__run_executor,
            session_id,
            event_id,
            handler,
            event_handler
        )

        if session_id not in self.active_handlers:
            self.active_handlers[session_id] = {}
        
        self.active_handlers[session_id][event_id] = future

        return True
    
    def __run_executor(self, session_id: str, event_id: str, handler: Callable, event_handler):
        
        try:
            result = handler(event_handler)
            return result
        except Exception as e:
            PrintLine(text=f'Error on sync handler ({event_id}): {e}', level='ERROR')
            raise e

        finally:
            if session_id in self.active_handlers:
                if event_id in self.active_handlers[session_id]:
                    del self.active_handlers[session_id][event_id]
            
            if not self.active_handlers[session_id]:
                del self.active_handlers[session_id]
    
    async def cancel_session_handlers(self, session_id: str):
        if session_id:
            if session_id in self.active_handlers:
                for event_id, future in self.active_handlers[session_id].items():
                    if future and not future.done():
                        future.cancel()
                
                del self.active_handlers[session_id]
        else:
            for session_id in self.active_handlers:
                for event_id, future in self.active_handlers[session_id].items():
                    if future and not future.done():
                        future.cancel()
                
                if not self.active_handlers[session_id]:
                    del self.active_handlers[session_id]
    
    def shutdown(self):
        self.executor.shutdown(wait=False, cancel_futures=True)