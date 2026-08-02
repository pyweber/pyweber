import asyncio
from unittest.mock import patch

import pytest

from pyweber.utils.async_utils import async_timeout


class TestAsyncTimeout:
    @pytest.mark.asyncio
    async def test_none_timeout_yields_without_limit(self):
        async with async_timeout(None):
            await asyncio.sleep(0)
        assert True

    @pytest.mark.asyncio
    async def test_with_timeout_uses_asyncio_timeout(self):
        async with async_timeout(1.0):
            await asyncio.sleep(0)
        assert True

    @pytest.mark.asyncio
    async def test_fallback_path_without_asyncio_timeout(self):
        """Cover legacy call_later path when asyncio.timeout is missing."""
        saved = getattr(asyncio, 'timeout', None)
        try:
            if hasattr(asyncio, 'timeout'):
                delattr(asyncio, 'timeout')
            async with async_timeout(1.0):
                await asyncio.sleep(0)
        finally:
            if saved is not None:
                asyncio.timeout = saved

    @pytest.mark.asyncio
    async def test_fallback_raises_timeout_error(self):
        saved = getattr(asyncio, 'timeout', None)
        try:
            if hasattr(asyncio, 'timeout'):
                delattr(asyncio, 'timeout')
            with pytest.raises(asyncio.TimeoutError):
                async with async_timeout(0.05):
                    await asyncio.sleep(2.0)
        finally:
            if saved is not None:
                asyncio.timeout = saved

    @pytest.mark.asyncio
    async def test_fallback_no_current_task(self):
        saved = getattr(asyncio, 'timeout', None)
        try:
            if hasattr(asyncio, 'timeout'):
                delattr(asyncio, 'timeout')
            with patch('pyweber.utils.async_utils.asyncio.current_task', return_value=None):
                async with async_timeout(1.0):
                    pass
        finally:
            if saved is not None:
                asyncio.timeout = saved

    @pytest.mark.asyncio
    async def test_fallback_propagate_external_cancel(self):
        saved = getattr(asyncio, 'timeout', None)
        try:
            if hasattr(asyncio, 'timeout'):
                delattr(asyncio, 'timeout')

            async def cancelled_body():
                async with async_timeout(10.0):
                    task = asyncio.current_task()
                    task.cancel()
                    await asyncio.sleep(1.0)

            with pytest.raises(asyncio.CancelledError):
                await cancelled_body()
        finally:
            if saved is not None:
                asyncio.timeout = saved
