import asyncio

import pytest

from hat import aio

from hat.controller import common
import hat.controller.environment


interpreter_types = ['DUKTAPE']


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


@pytest.mark.parametrize('interpreter_type', interpreter_types)
async def test_create(interpreter_type):
    env_conf = {
        'name': 'env1',
        'interpreter': interpreter_type,
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


@pytest.mark.parametrize('interpreter_type', interpreter_types)
async def test_init_code(interpreter_type):
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
        'interpreter': interpreter_type,
        'init_code': f"units.{unit_name}.{unit_fn}('x', 'y', 123);",
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


@pytest.mark.parametrize('interpreter_type', interpreter_types)
async def test_action(interpreter_type):
    unit_call_queue = aio.Queue()

    def on_unit_call(function, args, trigger):
        unit_call_queue.put_nowait((function, args, trigger))

    unit = MockUnit(call_cb=on_unit_call)
    unit_name = 'u1'
    unit_fn1 = 'f1.a.b'
    unit_fn2 = 'f1.a.c'
    unit_proxy = hat.controller.environment.UnitProxy(
        unit=unit,
        info=common.UnitInfo(
            name=unit_name,
            functions={unit_fn1, unit_fn2},
            create=MockUnit,
            json_schema_id=None,
            json_schema_repo=None))

    code = f"""
    units.{unit_name}.{unit_fn1}('x', 'y', 123);
    units.{unit_name}.{unit_fn2}('a', null);
    """
    env_conf = {
        'name': 'env1',
        'interpreter': interpreter_type,
        'init_code': "",
        'actions': [
            {'name': 'a1',
             'triggers': [{'type': 'test/a',
                           'name': 'a1'}],
             'code': code}]}

    env = hat.controller.environment.Environment(
        environment_conf=env_conf,
        proxies=[unit_proxy])

    await asyncio.sleep(0.01)
    assert unit_call_queue.empty()

    trigger = common.Trigger(type='test/a',
                             name='a1',
                             data={'test_data': 123})
    await env.process_trigger(trigger)

    function, args, triggered_by = await unit_call_queue.get()

    assert function == unit_fn1
    assert args == ['x', 'y', 123]
    assert triggered_by == trigger

    function, args, triggered_by = await unit_call_queue.get()

    assert function == unit_fn2
    assert args == ['a', None]
    assert triggered_by == trigger

    await env.async_close()


@pytest.mark.parametrize('interpreter_type', interpreter_types)
@pytest.mark.parametrize('trigger_type, trigger_name, triggered_actions', [
    ('test/a', 'x/a', ['a1', 'a3', 'a4', 'a5', 'a7']),
    ('test/a/b', 'x/a', ['a3', 'a5', 'a7']),
    ('test', 'x/a', ['a3', 'a5', 'a7']),
    ('test/a', 'x/a/b/c/d/1', ['a3', 'a4']),
    ('test/a', 'x/bla/123', ['a3', 'a4']),
    ('test/a', 'x', ['a3', 'a4']),
    ('test/b', 'y/b', ['a1', 'a3', 'a4', 'a5']),
    ('test/b', 'y/bla', ['a3', 'a4']),
    ('test/b', 'y', ['a3', 'a4']),
    ('test/b', 'z/bla', ['a3']),
    ('test/c', 'z/c', ['a1', 'a3']),
    ('test/a', 'bla', ['a3']),
    ('bla', 'x/a', ['a3', 'a5']),
    ('bla/123', 'y/b', ['a3', 'a5']),
    ('test/c', 'z/c', ['a1', 'a3']),
    ('bla', 'bla/123', ['a3']),
    ('', '', ['a3']),
    ('test2/a', 'x/d', ['a2', 'a3'])])
async def test_trigger_subscription(interpreter_type, trigger_type,
                                    trigger_name, triggered_actions):
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
        'interpreter': interpreter_type,
        'init_code': "",
        'actions': [
            {'name': 'a1',
             'triggers': [{'type': 'test/a',
                           'name': 'x/a'},
                          {'type': 'test/b',
                           'name': 'y/b'},
                          {'type': 'test/c',
                           'name': 'z/c'}],
             'code': f"units.{unit_name}.{unit_fn}('a1')"},
            {'name': 'a2',
             'triggers': [{'type': 'test2/a',
                           'name': 'x/d'}],
             'code': f"units.{unit_name}.{unit_fn}('a2')"},
            {'name': 'a3',
             'triggers': [{'type': '*',
                           'name': '*'}],
             'code': f"units.{unit_name}.{unit_fn}('a3')"},
            {'name': 'a4',
             'triggers': [{'type': 'test/a',
                           'name': 'x/*'},
                          {'type': 'test/b',
                           'name': 'y/*'}],
             'code': f"units.{unit_name}.{unit_fn}('a4')"},
            {'name': 'a5',
             'triggers': [{'type': '*',
                           'name': 'x/a'},
                          {'type': '*',
                           'name': 'y/b'}],
             'code': f"units.{unit_name}.{unit_fn}('a5')"},
            {'name': 'a6',
             'triggers': [],
             'code': f"units.{unit_name}.{unit_fn}('a6')"},
            {'name': 'a7',
             'triggers': [{'type': 'test/*',
                           'name': 'x/a'}],
             'code': f"units.{unit_name}.{unit_fn}('a7')"}]}

    env = hat.controller.environment.Environment(
        environment_conf=env_conf,
        proxies=[unit_proxy])

    await asyncio.sleep(0.01)
    assert unit_call_queue.empty()

    trigger = common.Trigger(type=trigger_type,
                             name=trigger_name,
                             data={'test_data': 123})
    await env.process_trigger(trigger)

    triggered_actions_res = set()

    for _ in range(len(triggered_actions)):
        _, args, triggered_by = await unit_call_queue.get()
        assert triggered_by == trigger
        triggered_actions_res.add(args[0])

    await asyncio.sleep(0.01)
    assert unit_call_queue.empty()

    assert triggered_actions_res == set(triggered_actions)

    await env.async_close()
