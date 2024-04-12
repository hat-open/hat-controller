import logging

import pytest

from hat import aio
from hat import json

from hat.controller.units.log import info


def test_info():
    assert info.name == 'log'
    assert info.functions == {
        'log',
        'debug',
        'info',
        'warning',
        'error'}
    assert isinstance(info.create, aio.AsyncCallable)
    assert isinstance(info.json_schema_repo, json.SchemaRepository)
    assert isinstance(info.json_schema_id, str)


def test_conf():
    conf = {'logger': 'xyz'}
    info.json_schema_repo.validate(info.json_schema_id, conf)


async def test_create():
    conf = {'logger': 'xyz'}

    unit = await aio.call(info.create, conf, None)

    assert unit.is_open

    unit.close()
    await unit.wait_closing()
    assert unit.is_closing
    await unit.wait_closed()
    assert unit.is_closed


@pytest.mark.parametrize('level, message', [
    ('INFO', 'this is info message'),
    ('DEBUG', 'this is debug message'),
    ('WARNING', 'this is warning message'),
    ('ERROR', 'this is error message')])
async def test_log(caplog, level, message):
    logger = 'xyz'
    conf = {'logger': logger}

    caplog.set_level(logging.getLevelName(level), logger)

    unit = await aio.call(info.create, conf, None)

    result = await aio.call(unit.call, 'log', [level, message], None)
    assert result is None

    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.name == logger
        assert record.msg == message
        assert logging.getLevelName(record.levelno) == level

    await unit.async_close()


async def test_log_multi_messages(caplog):
    logger = 'xyz'
    conf = {'logger': logger}
    msg_count = 10
    level = 'INFO'

    caplog.set_level(logging.getLevelName(level), logger)

    unit = await aio.call(info.create, conf, None)

    messages = [f"msg {i}" for i in range(msg_count)]

    for message in messages:
        result = await aio.call(unit.call, 'log', [level, message], None)
        assert result is None

    assert len(caplog.records) == msg_count
    for message, record in zip(messages, caplog.records):
        assert record.name == logger
        assert record.msg == message
        assert logging.getLevelName(record.levelno) == level

    await unit.async_close()


@pytest.mark.parametrize('level, message', [
    ('INFO', 'this is info message'),
    ('DEBUG', 'this is debug message'),
    ('WARNING', 'this is warning message'),
    ('ERROR', 'this is error message')])
async def test_level_functions(caplog, level, message):
    logger = 'xyz'
    conf = {'logger': logger}

    caplog.set_level(logging.getLevelName(level), logger)

    unit = await aio.call(info.create, conf, None)

    result = await aio.call(unit.call, level.lower(), [message], None)
    assert result is None

    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.name == logger
        assert record.msg == message
        assert logging.getLevelName(record.levelno) == level

    await unit.async_close()


async def test_log_invalid_level():
    conf = {'logger': 'xyz'}

    unit = await aio.call(info.create, conf, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'log', ['INVALID', 'abc'], None)

    assert unit.is_open

    await unit.async_close()


@pytest.mark.parametrize('msg', [
    123,
    None,
    {'123': 123},
    ['a']])
async def test_log_invalid_message(msg):
    conf = {'logger': 'xyz'}

    unit = await aio.call(info.create, conf, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'log', ['INFO', msg], None)

    assert unit.is_open

    await unit.async_close()


@pytest.mark.parametrize('level', [
    'debug',
    'info',
    'warning',
    'error'])
@pytest.mark.parametrize('msg', [
    123,
    None,
    {'123': 123},
    ['a']])
async def test_level_invalid_message(level, msg):
    conf = {'logger': 'xyz'}

    unit = await aio.call(info.create, conf, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, level, [msg], None)

    assert unit.is_open

    await unit.async_close()


async def test_invalid_function():
    conf = {'logger': 'xyz'}

    unit = await aio.call(info.create, conf, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'invalid', ['abc'], None)

    assert unit.is_open

    await unit.async_close()
