from hat.controller.interpreters.common import (JsData,
                                                InterpreterType,
                                                JsInterpreter,
                                                PyInterpreter,
                                                Interpreter)
from hat.controller.interpreters.cpython import CPython
from hat.controller.interpreters.duktape import Duktape
from hat.controller.interpreters.quickjs import QuickJS


__all__ = ['JsData',
           'InterpreterType',
           'JsInterpreter',
           'PyInterpreter',
           'Interpreter',
           'CPython',
           'Duktape',
           'QuickJS',
           'create_interpreter']


def create_interpreter(interpreter_type: InterpreterType) -> Interpreter:
    if interpreter_type == InterpreterType.CPYTHON:
        return CPython()

    if interpreter_type == InterpreterType.DUKTAPE:
        return Duktape()

    if interpreter_type == InterpreterType.QUICKJS:
        return QuickJS()

    raise ValueError('unsupported interpreter type')
