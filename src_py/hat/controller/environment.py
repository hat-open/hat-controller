from collections.abc import Collection
import asyncio
import logging
import typing

from hat import aio
from hat import json
from hat import duktape

from hat.controller import common


mlog = logging.getLogger(__name__)


class UnitProxy(typing.NamedTuple):
    unit: common.Unit
    info: common.UnitInfo


class Environment(aio.Resource):

    def __init__(self,
                 environment_conf: json.Data,
                 proxies: Collection[UnitProxy],
                 trigger_queue_size: int = 4096):
        self._loop = asyncio.get_running_loop()
        self._executor = aio.Executor(log_exceptions=False)
        self._trigger_queue = aio.Queue(trigger_queue_size)
        self._proxies = {proxy.info.name: proxy for proxy in proxies}
        self._last_trigger = None
        self._init_code = environment_conf['init']
        self._action_confs = {action_conf['name']: action_conf
                              for action_conf in environment_conf['actions']}

        self.async_group.spawn(self._run_loop)

    @property
    def async_group(self) -> aio.Group:
        return self._executor.async_group

    async def process_trigger(self, trigger: common.Trigger):
        await self._trigger_queue.put(trigger)

    async def _run_loop(self):
        try:
            interpreter = await self._executor.spawn(duktape.Interpreter)

            infos = (proxy.info for proxy in self._proxies.values())
            await self._executor.spawn(_ext_init_api, interpreter, infos,
                                       self._ext_call)

            actions = {}
            for action_name, action_conf in self._action_confs.items():
                actions[action_name] = await self._executor.spawn(
                    _ext_create_action, interpreter, action_conf['code'])

            await self._executor.spawn(interpreter.eval, self._init_code)

            while True:
                self._last_trigger = await self._trigger_queue.get()

                for action_name in self._get_matching_action_names():
                    action = actions[action_name]
                    await self._executor.spawn(action)

        except Exception as e:
            mlog.error('run loop error: %s', e, exc_info=e)

        finally:
            self.close()
            self._trigger_queue.close()

    async def _call(self, unit_name, function, args):
        proxy = self._proxies[unit_name]
        return await aio.call(proxy.unit.call, function, args,
                              self._last_trigger)

    def _ext_call(self, unit_name, function, args):
        coro = self._call(unit_name, function, args)
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def _get_matching_action_names(self):
        for action_name, action_conf in self._action_confs.items():
            for trigger_conf in action_conf['triggers']:
                if _match_trigger(self._last_trigger, trigger_conf['type'],
                                  trigger_conf['name']):
                    yield action_name
                    break


def _ext_init_api(interpreter, infos, call_cb):

    def encode(x):
        if isinstance(x, str):
            return x

        elements = (f"'k': {encode(v)}" for k, v in x.items())
        return f"{{{', '.join(elements)}}}"

    api_dict = {}
    for info in infos:
        unit_api_dict = {}

        for function in info.functions:
            segments = function.split('.')
            parent = unit_api_dict

            for segment in segments[:-1]:
                if segment not in parent:
                    parent[segment] = {}

                parent = parent[segment]

            parent[segments[-1]] = (
                f"function () {{ "
                f"return f('{info.name}', '{function}', arguments); "
                f"}}")

        api_dict[info.name] = unit_api_dict

    units = encode(api_dict)
    init_fn = interpreter.eval(f"var units; "
                               f"function (f) {{ units = {units}; }}")
    init_fn(call_cb)


def _ext_create_action(interpreter, code):
    return interpreter.eval(f"new Function({json.encode(code)})")


def _match_trigger(trigger, type_query, name_query):
    return (_match_query(trigger.type, type_query) and
            _match_query(trigger.name, name_query))


def _match_query(value, query):
    if query == '*':
        return True

    if query.endswith('/*'):
        return value.startswith(query[:-1]) or value == query[:-2]

    return value == query
