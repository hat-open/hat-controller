from hat.controller.interpreters.common import (Data,
                                                InterpreterType,
                                                JsInterpreter,
                                                LuaInterpreter,
                                                PyInterpreter,
                                                Interpreter)
from hat.controller.interpreters.cpython import CPython
from hat.controller.interpreters.duktape import Duktape
from hat.controller.interpreters.lua import Lua
from hat.controller.interpreters.quickjs import QuickJS


__all__ = ['Data',
           'InterpreterType',
           'JsInterpreter',
           'LuaInterpreter',
           'PyInterpreter',
           'Interpreter',
           'CPython',
           'Duktape',
           'Lua',
           'QuickJS',
           'create_interpreter']


def create_interpreter(interpreter_type: InterpreterType) -> Interpreter:
    if interpreter_type == InterpreterType.CPYTHON:
        return CPython()

    if interpreter_type == InterpreterType.DUKTAPE:
        return Duktape()

    if interpreter_type == InterpreterType.LUA:
        return Lua()

    if interpreter_type == InterpreterType.QUICKJS:
        return QuickJS()

    raise ValueError('unsupported interpreter type')
