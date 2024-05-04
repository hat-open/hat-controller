from hat.controller.common import *  # NOQA

import abc
import enum
import typing


JsData: typing.TypeAlias = (None | bool | int | float | str |
                            typing.List['JsData'] |
                            typing.Dict[str, 'JsData'] |
                            typing.Callable)
"""Supported JavaScript data types"""


class InterpreterType(enum.Enum):
    DUKTAPE = 'DUKTAPE'
    QUICKJS = 'QUICKJS'
    CPYTHON = 'CPYTHON'


class JsInterpreter(abc.ABC):
    """JavaScript interpreter"""

    @abc.abstractmethod
    def eval(self, code: str) -> JsData:
        """Evaluate code"""


class PyInterpreter(abc.ABC):
    """Python interpreter"""

    @property
    @abc.abstractmethod
    def globals(self) -> dict[str, typing.Any]:
        """Global variables"""

    @abc.abstractmethod
    def eval(self, code: str, locals: dict[str, typing.Any] | None):
        """Evaluate code"""


Interpreter: typing.TypeAlias = JsInterpreter | PyInterpreter
