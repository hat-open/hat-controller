from collections.abc import Iterable

from hat import json

from hat.controller import interpreters
from hat.controller.evaluators import common


class JsEvaluator(common.Evaluator):

    def __init__(self,
                 interpreter: interpreters.JsInterpreter,
                 action_codes: dict[common.ActionName, str],
                 infos: Iterable[common.UnitInfo],
                 call_cb: common.CallCb):
        self._interpreter = interpreter
        self._actions = {}

        _init_interpreter(interpreter, infos, call_cb)

        for action, code in action_codes.items():
            try:
                self._actions[action] = interpreter.eval(
                    _create_action_code(code))

            except Exception as e:
                raise Exception(f'action {action} error: {e}') from e

    def eval_code(self, code: str):
        self._interpreter.eval(code)

    def eval_action(self, action: common.ActionName):
        self._actions[action]()


def _init_interpreter(interpreter, infos, call_cb):
    api_code = _create_api_code(infos)
    api_fn = interpreter.eval(api_code)
    api_fn(call_cb)


def _create_api_code(infos):
    api_dict = _create_api(infos)
    units = _encode_api(api_dict)

    return f"var units; (function(f) {{ units = {units}; }})"


def _create_action_code(code):
    return f"new Function({json.encode(code)})"


def _create_api(infos):
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


def _encode_api(x):
    if isinstance(x, str):
        return x

    elements = (f"'{k}': {_encode_api(v)}" for k, v in x.items())
    return f"{{{', '.join(elements)}}}"
