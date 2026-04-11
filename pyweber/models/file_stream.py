import asyncio
from typing import Union
from dataclasses import dataclass

from pyweber.models.request import Request

FILE_CHUNK_FUTURES: dict[str, asyncio.Future] = {} # pragma: no cover

@dataclass
class FileResult: # pragma: no cover
    file_id: str
    status: str
    data: Union[bytes, str]
    code: int = 200

class FileChunkManager:
    def __init__(self):
        self._futures: dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    def register(self, file_id: str):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        self._futures[file_id] = loop.create_future()

    async def get(self, file_id: str, timeout: float) -> FileResult:
        future = self._futures.get(file_id)

        if future is None:
            return FileResult(file_id=file_id, status='error', data='File not found', code=404)

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return FileResult(file_id=file_id, status='error', data='Timeout', code=408)
        finally:
            async with self._lock:
                self._futures.pop(file_id, None)

    async def resolve(self, request: Request) -> FileResult:
        query_params = request.query_params

        file_id = query_params.get('file_id')
        status = query_params.get('status')
        data = request.body.get('body')

        if not file_id or not status:
            return FileResult(file_id='unknown', status='error', data='Missing file_id or status', code=400)

        async with self._lock:
            future = self._futures.get(file_id)

            if future is None:
                return FileResult(file_id=file_id, status='error', data='No pending request', code=404)

            if future.done():
                return FileResult(file_id=file_id, status='error', data='Already resolved', code=409)

            result = FileResult(file_id=file_id, status=status, data=data or b'')
            future.set_result(result)

        return result

file_chunk_manager = FileChunkManager()
