import asyncio

import pytest

from pyweber.models.file_stream import FileChunkManager, FileResult
from pyweber.models.request import Request, ClientInfo


@pytest.fixture
def manager():
    return FileChunkManager()


@pytest.mark.asyncio
async def test_register_and_resolve(manager):
    manager.register('fid-1')
    req = Request(
        headers='POST / HTTP/1.1\r\nHost: localhost\r\n\r\n',
        body=b'chunk-data',
        client_info=ClientInfo(host='127.0.0.1', port=1),
    )
    req.query_params = {'file_id': 'fid-1', 'status': 'ok'}

    async def waiter():
        return await manager.get('fid-1', timeout=1)

    task = asyncio.create_task(waiter())
    await asyncio.sleep(0)
    result = await manager.resolve(req)
    assert result.status == 'ok'
    got = await task
    assert got.data == b'chunk-data'


@pytest.mark.asyncio
async def test_get_missing_file(manager):
    result = await manager.get('missing', timeout=0.01)
    assert result.code == 404


@pytest.mark.asyncio
async def test_resolve_errors(manager):
    req = Request(
        headers='POST / HTTP/1.1\r\nHost: localhost\r\n\r\n',
        body=b'',
        client_info=ClientInfo(host='127.0.0.1', port=1),
    )
    req.query_params = {}
    bad = await manager.resolve(req)
    assert bad.code == 400

    manager.register('done')
    req.query_params = {'file_id': 'done', 'status': 'ok'}
    await manager.resolve(req)
    dup = await manager.resolve(req)
    assert dup.code in (404, 409)
