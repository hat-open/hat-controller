from collections.abc import Iterable
import functools

from hat.controller import interpreters
from hat.controller.evaluators import common


class PyEvaluator(common.Evaluator):

    def __init__(self,
                 interpreter: interpreters.PyInterpreter,
                 action_codes: dict[common.ActionName, str],
                 infos: Iterable[common.UnitInfo],
                 call_cb: common.CallCb):
        self._interpreter = interpreter
        self._actions = {}

        interpreter.globals['units'] = _create_units(infos, call_cb)

    def eval_code(self, code: str):
        self._interpreter.eval(code, None)

    def eval_action(self, action: common.ActionName):
        self._interpreter.eval(self._actions[action], {})


def _create_units(infos, call_cb):
    units = type('units', (), {})
    for info in infos:
        unit = type(info.name, (), {})

        for function in info.functions:
            segments = function.split('.')
            parent = unit

            for segment in segments[:-1]:
                if not hasattr(parent, segment):
                    setattr(parent, segment, type(segment, (), {}))

                parent = getattr(parent, segment)

            fn = functools.partial(_unit_fn, call_cb, info.name, function)
            setattr(parent, segments[-1], fn)

        setattr(units, info.name, unit)

    return units


def _unit_fn(call_cb, unit_name, function_name, *args):
    if not all(_is_valid_arg(arg) for arg in args):
        raise ValueError('unsupported argument type')

    return call_cb(unit_name, function_name, args)


def _is_valid_arg(arg):
    if isinstance(arg, dict):
        return all(isinstance(k, str) and _is_valid_arg(v)
                   for k, v in arg.items())

    if isinstance(arg, list):
        return all(_is_valid_arg(i) for i in arg)

    return arg is None or isinstance(arg, (bool, int, float, str))
