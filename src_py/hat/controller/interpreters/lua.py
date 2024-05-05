from collections.abc import Callable

from hat.controller.interpreters import _lua
from hat.controller.interpreters import common


class Lua(common.LuaInterpreter):

    def __init__(self):
        self._interpreter = _lua.Interpreter()

    def load(self,
             code: str,
             name: str | None = None
             ) -> Callable[[], common.Data]:
        return self._interpreter.load(code, name)
