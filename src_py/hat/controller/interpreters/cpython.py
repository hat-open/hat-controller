import typing

from hat.controller.interpreters import common


class CPython(common.PyInterpreter):

    def __init__(self):
        self._globals = {}

    @property
    def globals(self) -> dict[str, typing.Any]:
        return self._globals

    def eval(self, code: str, locals: dict[str, typing.Any] | None):
        exec(code,
             self._globals,
             (locals if locals is not None else self._globals))
