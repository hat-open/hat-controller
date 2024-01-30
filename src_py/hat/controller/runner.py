import asyncio
import logging

from hat import aio
from hat import json

import hat.controller.engine


mlog: logging.Logger = logging.getLogger(__name__)
"""Module logger"""


class MainRunner(aio.Resource):

    def __init__(self, conf: json.Data):
        self._conf = conf
        self._loop = asyncio.get_running_loop()
        self._async_group = aio.Group()
        self._engine = None

        self.async_group.spawn(self._run)

    @property
    def async_group(self) -> aio.Group:
        return self._async_group

    async def _run(self):
        try:
            await self._start()
            await self._loop.create_future()

        except Exception as e:
            mlog.error("main runner loop error: %s", e, exc_info=e)

        finally:
            self.close()
            await aio.uncancellable(self._stop())

    async def _start(self):
        self._engine = await hat.controller.engine.create_engine(self._conf)

    async def _stop(self):
        if self._engine:
            await self._engine.async_close()
