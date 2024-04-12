import asyncio
import pytest

from hat import aio

from hat.controller import common
from hat.controller.units.triggers import info


def test_info():
    assert info.name == 'triggers'
    assert info.functions == {'getCurrent', 'raise'}
    assert isinstance(info.create, aio.AsyncCallable)
    assert info.json_schema_repo is None
    assert info.json_schema_id is None


async def test_create():
    unit = await aio.call(info.create, None, None)

    assert unit.is_open

    unit.close()

    await unit.wait_closing()
    assert unit.is_closing

    await unit.wait_closed()
    assert unit.is_closed


@pytest.mark.parametrize('name, data', [
    ('abc', {'xyz': 123}),
    ('bc/de/ef', None),
    ('123', 123),
    ])
async def test_raise(name, data):
    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, None, trigger_queue.put_nowait)

    args = [name]
    if data:
        args.append(data)
    result = await aio.call(unit.call, 'raise', args, None)
    assert result is None

    assert not trigger_queue.empty()
    trigger = trigger_queue.get_nowait()
    assert trigger.type == 'triggers/custom'
    assert trigger.name == name
    if data is None:
        assert trigger.data is data
    else:
        assert trigger.data == data

    assert trigger_queue.empty()

    await unit.async_close()


async def test_raise_with_delay():
    delay = 50
    name = 'abc'
    data = {'123': 12345}
    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, None, trigger_queue.put_nowait)

    result = await aio.call(unit.call, 'raise', [name, data, delay], None)
    assert result is None

    assert trigger_queue.empty()

    await asyncio.sleep((delay / 1000) * 0.95)
    assert trigger_queue.empty()

    await asyncio.sleep((delay / 1000) * 0.05)
    assert not trigger_queue.empty()

    trigger = trigger_queue.get_nowait()
    assert trigger.type == 'triggers/custom'
    assert trigger.name == name
    assert trigger.data == data

    assert trigger_queue.empty()

    await unit.async_close()


@pytest.mark.parametrize('trigger', [
    None,
    common.Trigger(type='test/type',
                   name='abc',
                   data={'123': 12345}),
    common.Trigger(type='test/type/none',
                   name='none',
                   data=None)])
async def test_get_current(trigger):
    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, None, trigger_queue.put_nowait)

    result_trigger = await aio.call(unit.call, 'getCurrent', [], trigger)

    assert trigger_queue.empty()

    if trigger is None:
        assert result_trigger is trigger
    else:
        assert result_trigger == trigger._asdict()

    assert trigger_queue.empty()

    await unit.async_close()


@pytest.mark.parametrize('name', [123,
                                  None,
                                  {'a', 'b'},
                                  ['name']])
async def test_raise_invalid_name(name):
    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, None, trigger_queue.put_nowait)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'raise', [name], None)

    assert trigger_queue.empty()

    await unit.async_close()


@pytest.mark.parametrize('delay', [
    '50',
    {'abc': 123},
    []])
async def test_invalid_delay(delay):
    name = 'abc'
    data = {'123': 12345}
    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, None, trigger_queue.put_nowait)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'raise', [name, data, delay], None)

    await unit.async_close()


async def test_invalid_function():
    unit = await aio.call(info.create, None, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'bla', ['b', 'l', 'a'], None)

    await unit.async_close()
