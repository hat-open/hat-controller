import subprocess

import pytest

from hat import aio
from hat import json

from hat.controller.units.os import info


def test_info():
    assert info.name == 'os'
    assert info.functions == {
        'readFile',
        'writeFile',
        'appendFile',
        'deleteFile',
        'execute'}
    assert isinstance(info.create, aio.AsyncCallable)
    assert isinstance(info.json_schema_repo, dict)
    assert isinstance(info.json_schema_id, str)


def test_conf():
    conf = {'thread_pool_size': 5}
    validator = json.DefaultSchemaValidator(info.json_schema_repo)
    validator.validate(info.json_schema_id, conf)


async def test_create():
    unit = await aio.call(info.create, {}, None)

    assert unit.is_open

    unit.close()
    await unit.wait_closing()
    assert unit.is_closing
    await unit.wait_closed()
    assert unit.is_closed


async def test_read_file(tmp_path):
    unit = await aio.call(info.create, {}, None)

    file_content = """
    This is some
    file content.
    """

    file_path = tmp_path / 'file_to_read.txt'
    with open(file_path, 'w') as f:
        f.write(file_content)

    result = await aio.call(unit.call, 'readFile', [file_path], None)
    assert result == file_content

    await unit.async_close()


async def test_write_file(tmp_path):
    unit = await aio.call(info.create, {}, None)

    write_content = """
    This is some
    file content.
    """

    file_path = tmp_path / 'file_to_write.txt'

    result = await aio.call(
        unit.call, 'writeFile', [file_path, write_content], None)
    assert result is None

    assert file_path.exists()
    with open(file_path, 'r') as f:
        result_content = f.readlines()

    assert ''.join(result_content) == write_content

    await unit.async_close()


async def test_append_file(tmp_path):
    unit = await aio.call(info.create, {}, None)

    init_content = """
    This is some
    file content.
    """
    file_path = tmp_path / 'file_to_append.txt'
    with open(file_path, 'w') as f:
        f.write(init_content)

    append_content = """
    There is some more,
    and more...
    """
    result = await aio.call(
        unit.call, 'appendFile', [file_path, append_content], None)
    assert result is None

    assert file_path.exists()
    with open(file_path, 'r') as f:
        result_content = f.readlines()

    assert ''.join(result_content) == ''.join((init_content, append_content))

    await unit.async_close()


async def test_delete_file(tmp_path):
    unit = await aio.call(info.create, {}, None)

    file_path = tmp_path / 'file_to_read.txt'
    with open(file_path, 'w') as f:
        f.write("content...")

    assert file_path.exists()

    result = await aio.call(unit.call, 'deleteFile', [file_path], None)
    assert result is None

    assert not file_path.exists()

    await unit.async_close()


@pytest.mark.parametrize('command', [
    ["echo", "\"xyz\""],
    ["ls", "./", "-al"],
    ["any", "command", "line", "goes", "here"]])
async def test_execute(monkeypatch, command):
    unit = await aio.call(info.create, {}, None)
    command_queue = aio.Queue()

    class MockPopen(subprocess.Popen):

        def __init__(self, *args, **kwargs):
            command_queue.put_nowait(args[0])
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(subprocess, 'Popen', MockPopen)

    result = await aio.call(unit.call, 'execute', [command], None)
    assert result is None

    result_command = await command_queue.get()
    assert result_command == command

    await unit.async_close()


async def test_read_file_not_exists(tmp_path):
    unit = await aio.call(info.create, {}, None)

    file_path = tmp_path / 'file_to_read.txt'

    with pytest.raises(Exception):
        await aio.call(unit.call, 'readFile', [file_path], None)

    await unit.async_close()


@pytest.mark.parametrize('function', [
    'readFile',
    'writeFile',
    'appendFile',
    'deleteFile'])
@pytest.mark.parametrize('path', [
    123,
    {},
    []])
async def test_invalid_path(tmp_path, function, path):
    unit = await aio.call(info.create, {}, None)

    text = "..."

    args = [path]
    if function in ['writeFile', 'appendFile']:
        args.append(text)
    with pytest.raises(Exception):
        await aio.call(
            unit.call, function, args, None)

    await unit.async_close()


@pytest.mark.parametrize('function', [
    'writeFile',
    'appendFile'])
@pytest.mark.parametrize("text", [123, None, {'abc': 123}])
async def test_invalid_text(tmp_path, function, text):
    unit = await aio.call(info.create, {}, None)

    file_path = tmp_path / 'file_to_write.txt'

    with pytest.raises(Exception):
        await aio.call(
            unit.call, function, [file_path, text], None)

    await unit.async_close()


async def test_execute_invalid_commands():
    unit = await aio.call(info.create, {}, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'execute', [[1, 23, None]], None)

    await unit.async_close()


async def test_invalid_function(monkeypatch):
    unit = await aio.call(info.create, {}, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'invalid', ['abc123'], None)

    await unit.async_close()
