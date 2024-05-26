from zoneinfo import ZoneInfo
import asyncio
import datetime
import time

import pytest

from hat import aio
from hat import json

from hat.controller.units.timers import info


async def assert_trigger_raised(trigger_name, period, trigger_queue, ts=None):
    dt_tol = period * 0.1
    await asyncio.sleep(period - dt_tol)
    ts_before_ms = time.time() * 1000
    assert trigger_queue.empty()

    trigger = await asyncio.wait_for(trigger_queue.get(), 2 * dt_tol)
    ts_after_ms = time.time() * 1000
    assert trigger.type == ('timers', 'timer')
    assert trigger.name == (trigger_name, )

    if ts:
        assert trigger.data == ts * 1000
    else:
        assert ts_before_ms < trigger.data < ts_after_ms


async def assert_no_trigger(period, trigger_queue):
    await asyncio.sleep(period * 1.1)
    assert trigger_queue.empty()


def test_info():
    assert info.name == 'timers'
    assert info.functions == {'start', 'stop'}
    assert isinstance(info.create, aio.AsyncCallable)
    assert isinstance(info.json_schema_repo, json.SchemaRepository)
    assert isinstance(info.json_schema_id, str)


def test_conf():
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': [
            {'name': 't1',
             'time': 3,
             'auto_start': True,
             'repeat': True}]}
    info.json_schema_repo.validate(info.json_schema_id, conf)


async def test_create():
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': []}
    unit = await aio.call(info.create, conf, None)

    assert unit.is_open

    unit.close()
    await unit.wait_closing()
    assert unit.is_closing
    await unit.wait_closed()
    assert unit.is_closed


async def test_auto_start_repeat():
    period = 0.05
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': [
            {'name': 't1',
             'time': period,
             'auto_start': True,
             'repeat': True}]}

    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, conf, trigger_queue.put_nowait)

    for i in range(3):
        await assert_trigger_raised('t1', period, trigger_queue)

    await unit.async_close()


async def test_auto_start_no_repeat():
    period = 0.05
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': [
            {'name': 't1',
             'time': period,
             'auto_start': True,
             'repeat': False}]}

    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, conf, trigger_queue.put_nowait)

    await assert_trigger_raised('t1', period, trigger_queue)

    await assert_no_trigger(period, trigger_queue)

    await unit.async_close()


@pytest.mark.parametrize('repeat', [True, False])
async def test_start_stop(repeat):
    period = 0.05
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': [
            {'name': 't1',
             'time': period,
             'auto_start': False,
             'repeat': repeat}]}

    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, conf, trigger_queue.put_nowait)

    await assert_no_trigger(period, trigger_queue)

    result = await aio.call(unit.call, 'start', ['t1'], None)
    assert result is None

    triggers_count = 3 if repeat else 1
    for i in range(triggers_count):
        await assert_trigger_raised('t1', period, trigger_queue)

    result = await aio.call(unit.call, 'stop', ['t1'], None)
    assert result is None

    await assert_no_trigger(period, trigger_queue)

    await unit.async_close()


@pytest.mark.parametrize('repeat', [True, False])
async def test_stop_auto_start(repeat):
    period = 0.05
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': [
            {'name': 't1',
             'time': period,
             'auto_start': True,
             'repeat': repeat}]}

    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, conf, trigger_queue.put_nowait)

    await aio.call(unit.call, 'stop', ['t1'], None)

    await assert_no_trigger(period, trigger_queue)

    await unit.async_close()


@pytest.mark.parametrize('cron, trigger_timestamps, timezone', [
    ('* * * * *', [datetime.datetime(2024, 4, 11, 10, 1),
                   datetime.datetime(2024, 4, 11, 10, 2),
                   datetime.datetime(2024, 4, 11, 10, 3)], 'Europe/Zagreb'),
    ('0 * * * *', [datetime.datetime(2024, 4, 11, 10, 0),
                   datetime.datetime(2024, 4, 11, 11, 0)], 'Africa/Maputo'),
    ('13 * * * *', [datetime.datetime(2024, 4, 11, 10, 13),
                    datetime.datetime(2024, 4, 11, 11, 13)], 'Europe/Zagreb'),
    ('2 17 * * *', [datetime.datetime(2024, 4, 11, 17, 2),
                    datetime.datetime(2024, 4, 12, 17, 2)], 'Africa/Maputo'),
    ('2 17 11 4 *', [datetime.datetime(2024, 4, 11, 17, 2),
                     datetime.datetime(2025, 4, 11, 17, 2)], 'Europe/Zagreb'),
    ('15 12 * * 5', [datetime.datetime(2024, 4, 12, 12, 15),
                     datetime.datetime(2024, 4, 19, 12, 15)], 'Africa/Maputo'),
    ])
@pytest.mark.parametrize('repeat', [True, False])
@pytest.mark.parametrize('auto_start, stop', [(True, False),
                                              (True, True),
                                              (False, False)])
async def test_absolute(monkeypatch, timezone, cron, trigger_timestamps,
                        repeat, auto_start, stop):
    dt_step = 0.05
    started = True if auto_start else False
    trigger_timestamps = [t.replace(tzinfo=ZoneInfo(timezone))
                          for t in trigger_timestamps]

    def now_timestamps():
        for ts in trigger_timestamps:
            yield ts - datetime.timedelta(seconds=dt_step)
            yield ts

    now_timestamps = now_timestamps()

    conf = {
        'timezone': timezone,
        'timers': [
            {'name': 't1',
             'time': cron,
             'auto_start': auto_start,
             'repeat': repeat}]}

    trigger_queue = aio.Queue()

    class mock_datetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return next(now_timestamps).astimezone(tz)

    monkeypatch.setattr(datetime, 'datetime', mock_datetime)

    unit = await aio.call(info.create, conf, trigger_queue.put_nowait)

    if stop:
        await aio.call(unit.call, 'stop', ['t1'], None)
        started = False

    trigger_count = 0
    for trigger_timestamp in trigger_timestamps:

        if (trigger_count > 0 and not repeat) or not started:
            await assert_no_trigger(dt_step, trigger_queue)
            continue

        if trigger_count > 0 and not started:
            await aio.call(unit.call, 'start', ['t1'], None)
            started = True

        await assert_trigger_raised(
            't1', dt_step, trigger_queue, trigger_timestamp.timestamp())
        trigger_count += 1

    await unit.async_close()


@pytest.mark.parametrize('function', ['start', 'stop'])
@pytest.mark.parametrize('name', [
    'xyz',
    123,
    {'abc': 123},
    []])
async def test_invalid_timer_name(function, name):
    period = 0.05
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': [
            {'name': 't1',
             'time': period,
             'auto_start': False,
             'repeat': True}]}

    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, conf, trigger_queue.put_nowait)

    with pytest.raises(Exception):
        await aio.call(unit.call, function, [name], None)

    await unit.async_close()


async def test_invalid_function():
    period = 0.05
    conf = {
        'timezone': 'Europe/Zagreb',
        'timers': [
            {'name': 't1',
             'time': period,
             'auto_start': False,
             'repeat': True}]}

    trigger_queue = aio.Queue()

    unit = await aio.call(info.create, conf, trigger_queue.put_nowait)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'invalid', ['t1'], None)

    await unit.async_close()
