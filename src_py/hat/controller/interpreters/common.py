from hat.controller.common import *  # NOQA

import abc
import enum
import typing


Data: typing.TypeAlias = (None | bool | int | float | str |
                          typing.List['Data'] |
                          typing.Dict[str, 'Data'] |
                          typing.Callable)
"""Supported data types"""


class InterpreterType(enum.Enum):
    DUKTAPE = 'DUKTAPE'
    QUICKJS = 'QUICKJS'


class Interpreter(abc.ABC):
    """Interpreter"""

    def eval(self, code: str) -> Data:
        """Evaluate code"""
