from pathlib import Path
import subprocess

from hat import aio

from hat.controller import common


class OsUnit(common.Unit):

    def __init__(self, conf, raise_trigger_cb):
        self._executor = aio.Executor(conf.get('thread_pool_size', 5),
                                      log_exceptions=False)

    @property
    def async_group(self):
        return self._executor.async_group

    async def call(self, function, args, trigger):
        if function == 'readFile':
            path = Path(args[0])

            return await self._executor.spawn(_ext_read_file, path)

        if function == 'writeFile':
            path = Path(args[0])
            text = args[1]

            if not isinstance(text, str):
                raise Exception('invalid text type')

            return await self._executor.spawn(_ext_write_file, path, text)

        if function == 'appendFile':
            path = Path(args[0])
            text = args[1]

            if not isinstance(text, str):
                raise Exception('invalid text type')

            return await self._executor.spawn(_ext_append_file, path, text)

        if function == 'deleteFile':
            path = Path(args[0])

            return await self._executor.spawn(_ext_delete_file, path)

        if function == 'execute':
            if not isinstance(args[0], list):
                raise Exception('invalid args type')

            for arg in args[0]:
                if not isinstance(arg, str):
                    raise Exception('invalid args type')

            self._executor.spawn(_ext_execute, args[0])
            return

        raise Exception('unsupported function')


info = common.UnitInfo(name='os',
                       functions={'readFile', 'writeFile', 'appendFile',
                                  'deleteFile', 'execute'},
                       create=OsUnit,
                       json_schema_id='hat-controller://units/os.yaml',
                       json_schema_repo=common.json_schema_repo)


def _ext_read_file(path):
    return path.read_text(encoding='utf-8', errors='ignore')


def _ext_write_file(path, text):
    path.write_text(text, encoding='utf-8', errors='ignore')


def _ext_append_file(path, text):
    with open(path, 'a', encoding='utf-8', errors='ignore') as f:
        f.write(text)


def _ext_delete_file(path):
    path.unlink(missing_ok=True)


def _ext_execute(args):
    with subprocess.Popen(args,
                          stdin=subprocess.DEVNULL,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL) as p:
        p.wait()
