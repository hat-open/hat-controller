from hat.controller.common import *  # NOQA

from collections.abc import Callable

import abc
import enum
import typing


Data: typing.TypeAlias = (None | bool | int | float | str |
                          typing.List['Data'] |
                          typing.Dict[str, 'Data'] |
                          Callable)
"""Supported interpreter data types"""


class InterpreterType(enum.Enum):
    CPYTHON = 'CPYTHON'
    DUKTAPE = 'DUKTAPE'
    LUA = 'LUA'
    QUICKJS = 'QUICKJS'


class JsInterpreter(abc.ABC):
    """JavaScript interpreter"""

    @abc.abstractmethod
    def eval(self, code: str) -> Data:
        """Evaluate code"""


class LuaInterpreter(abc.ABC):
    """Lua interpreter"""

    @abc.abstractmethod
    def load(self, code: str, name: str | None = None) -> Callable[[], Data]:
        """Load code"""


class PyInterpreter(abc.ABC):
    """Python interpreter"""

    @property
    @abc.abstractmethod
    def globals(self) -> dict[str, typing.Any]:
        """Global variables"""

    @abc.abstractmethod
    def eval(self, code: str, locals: dict[str, typing.Any] | None):
        """Evaluate code"""


Interpreter: typing.TypeAlias = JsInterpreter | LuaInterpreter | PyInterpreter
