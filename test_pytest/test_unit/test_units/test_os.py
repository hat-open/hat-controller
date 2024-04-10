import pytest
import subprocess

from hat import aio

from hat.controller.units.os import info


def test_conf():
    conf = {'thread_pool_size': 5}
    info.json_schema_repo.validate(info.json_schema_id, conf)


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


async def test_invalid_function(monkeypatch):
    unit = await aio.call(info.create, {}, None)

    with pytest.raises(Exception):
        await aio.call(unit.call, 'invalid', ['abc123'], None)

    await unit.async_close()
