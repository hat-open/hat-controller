import collections
import logging

from hat import aio
from hat import json

from hat.controller import common
import hat.controller.environment


mlog = logging.getLogger(__name__)


async def create_engine(conf: json.Data,
                        trigger_queue_size: int = 4096):
    engine = Engine()
    engine._async_group = aio.Group()
    engine._trigger_queue = aio.Queue(trigger_queue_size)
    engine._envs = collections.deque()
    engine._infos = collections.deque()

    proxies = collections.deque()

    try:
        for unit_conf in conf['units']:
            info = common.import_unit_info(unit_conf['module'])
            if info.name in engine._infos:
                raise Exception('duplicate unit name')

            unit = await aio.call(info.create, unit_conf,
                                  engine._trigger_queue.put)
            await _bind_resource(engine.async_group, unit)

            proxy = hat.controller.environment.UnitProxy(unit, info)
            proxies.append(proxy)
            engine._infos.append(info)

        for env_conf in conf['environments']:
            env = hat.controller.environment.Environment(env_conf, proxies)
            await _bind_resource(engine.async_group, env)
            engine._envs.append(env)

        engine.async_group.spawn(engine._trigger_loop)

    except BaseException:
        await aio.uncancellable(engine.async_close())
        raise

    return engine


class Engine(aio.Resource):

    @property
    def async_group(self):
        return self._async_group

    async def _trigger_loop(self):
        try:
            while True:
                trigger = await self._trigger_queue.get()

                for env in self._envs:
                    await env.process_trigger(trigger)

        except Exception as e:
            mlog.error('trigger loop error: %s', e, exc_info=e)

        finally:
            self.close()
            self._trigger_queue.close()


async def _bind_resource(async_group, resource):
    try:
        async_group.spawn(aio.call_on_cancel, resource.async_close)
        async_group.spawn(aio.call_on_done, resource.wait_closing(),
                          async_group.close)

    except Exception:
        await aio.uncancellable(resource.async_close())
        raise
