from collections.abc import Callable, Collection, Iterable

from hat import json

from hat.controller import common
import hat.controller.interpreters


CallCb = Callable[
    [common.UnitName, common.FunctionName, Collection[json.Data]],
    json.Data]


class Evaluator:
    """Code/action evaluator"""

    def __init__(self,
                 interpreter_type: hat.controller.interpreters.InterpreterType,
                 action_codes: dict[common.ActionName, str],
                 infos: Iterable[common.UnitInfo],
                 call_cb: CallCb):
        self._interpreter = hat.controller.interpreters.create_interpreter(
            interpreter_type)
        self._actions = {}

        _init_interpreter(interpreter_type, self._interpreter, infos, call_cb)
        for action, code in action_codes.items():
            self._actions[action] = self._interpreter.eval(
                _create_action_code(interpreter_type, code))

    def eval_code(self, code: str):
        """Evaluate code"""
        self._interpreter.eval(code)

    def eval_action(self, action: common.ActionName):
        """Evaluate action"""
        self._actions[action]()


def _init_interpreter(interpreter_type, interpreter, infos, call_cb):
    if interpreter_type == hat.controller.interpreters.InterpreterType.DUKTAPE:
        _init_js_interpreter(interpreter, infos, call_cb)
        return interpreter

    if interpreter_type == hat.controller.interpreters.InterpreterType.QUICKJS:
        _init_js_interpreter(interpreter, infos, call_cb)
        return interpreter

    raise ValueError('unsupported interpreter type')


def _create_action_code(interpreter_type, code):
    if interpreter_type == hat.controller.interpreters.InterpreterType.DUKTAPE:
        return _create_js_action_code(code)

    if interpreter_type == hat.controller.interpreters.InterpreterType.QUICKJS:
        return _create_js_action_code(code)

    raise ValueError('unsupported interpreter type')


def _init_js_interpreter(interpreter, infos, call_cb):
    api_code = _create_js_api_code(infos)
    api_fn = interpreter.eval(api_code)
    api_fn(call_cb)


def _create_js_api_code(infos):
    api_dict = _create_js_api(infos)
    units = _encode_js_api(api_dict)

    return f"var units; (function(f) {{ units = {units}; }})"


def _create_js_action_code(code):
    return f"new Function({json.encode(code)})"


def _create_js_api(infos):
    api_dict = {}
    for info in infos:
        unit_api_dict = {}

        for function in info.functions:
            segments = function.split('.')
            parent = unit_api_dict

            for segment in segments[:-1]:
                if segment not in parent:
                    parent[segment] = {}

                parent = parent[segment]

            parent[segments[-1]] = (f"function() {{ return f("
                                    f"'{info.name}', "
                                    f"'{function}', "
                                    f"Array.prototype.slice.call(arguments)"
                                    f"); }}")

        api_dict[info.name] = unit_api_dict

    return api_dict


def _encode_js_api(x):
    if isinstance(x, str):
        return x

    elements = (f"'{k}': {_encode_js_api(v)}" for k, v in x.items())
    return f"{{{', '.join(elements)}}}"
