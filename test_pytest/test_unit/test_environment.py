import asyncio

from hat import aio

from hat.controller import common
import hat.controller.environment


class MockUnit(common.Unit):

    def __init__(self, call_cb=None):
        self._async_group = aio.Group()
        self._call_cb = call_cb

    @property
    def async_group(self):
        return self._async_group

    def call(self, function, args, trigger):
        if self._call_cb:
            self._call_cb(function, args, trigger)


async def test_create():
    env_conf = {
        'name': 'env1',
        'init_code': "",
        'actions': []}

    env = hat.controller.environment.Environment(
        environment_conf=env_conf,
        proxies=[],
        trigger_queue_size=100)

    # let init_code to be executed
    await asyncio.sleep(0.01)

    assert env.is_open

    env.close()
    await env.wait_closing()
    assert env.is_closing
    await env.wait_closed()
    assert env.is_closed
    await env.async_close()


async def test_init_code():
    unit_call_queue = aio.Queue()

    def on_unit_call(function, args, trigger):
        unit_call_queue.put_nowait((function, args, trigger))

    unit = MockUnit(call_cb=on_unit_call)
    unit_name = 'u1'
    unit_fn = 'f1'
    unit_proxy = hat.controller.environment.UnitProxy(
        unit=unit,
        info=common.UnitInfo(
            name=unit_name,
            functions={unit_fn},
            create=MockUnit,
            json_schema_id=None,
            json_schema_repo=None))

    env_conf = {
        'name': 'env1',
        'init_code': f"units.{unit_name}.{unit_fn}('x', 'y', 123)",
        'actions': []}

    env = hat.controller.environment.Environment(
        environment_conf=env_conf,
        proxies=[unit_proxy],
        trigger_queue_size=100)

    function, args, trigger = await unit_call_queue.get()

    assert function == unit_fn
    assert args == ['x', 'y', 123]
    assert trigger is None

    await env.async_close()


async def test_action():
    unit_call_queue = aio.Queue()

    def on_unit_call(function, args, trigger):
        unit_call_queue.put_nowait((function, args, trigger))

    unit = MockUnit(call_cb=on_unit_call)
    unit_name = 'u1'
    unit_fn = 'f1'
    unit_proxy = hat.controller.environment.UnitProxy(
        unit=unit,
        info=common.UnitInfo(
            name=unit_name,
            functions={unit_fn},
            create=MockUnit,
            json_schema_id=None,
            json_schema_repo=None))

    env_conf = {
        'name': 'env1',
        'init_code': "",
        'actions': [
            {'name': 'a1',
             'triggers': [{'type': 'test/a',
                           'name': 'a1'}],
             'code': f"units.{unit_name}.{unit_fn}('x', 'y', 123)"}]}

    env = hat.controller.environment.Environment(
        environment_conf=env_conf,
        proxies=[unit_proxy],
        trigger_queue_size=100)

    await asyncio.sleep(0.01)
    assert unit_call_queue.empty()

    trigger = common.Trigger(type='test/a',
                             name='a1',
                             data={'test_data': 123})
    await env.process_trigger(trigger)

    function, args, trigger_res = await unit_call_queue.get()

    assert function == unit_fn
    assert args == ['x', 'y', 123]
    assert trigger_res == trigger

    await env.async_close()
