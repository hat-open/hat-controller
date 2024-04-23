from hat.controller.interpreters.common import (Data,
                                                InterpreterType,
                                                Interpreter)
from hat.controller.interpreters.duktape import Duktape
from hat.controller.interpreters.quickjs import QuickJS


__all__ = ['Data',
           'InterpreterType',
           'Interpreter',
           'Duktape',
           'QuickJS',
           'create_interpreter']


def create_interpreter(interpreter_type: InterpreterType) -> Interpreter:
    if interpreter_type == InterpreterType.DUKTAPE:
        return Duktape()

    if interpreter_type == InterpreterType.QUICKJS:
        return QuickJS()

    raise ValueError('unsupported interpreter type')
