from collections.abc import Iterable

from hat.controller import interpreters
from hat.controller.evaluators import common
from hat.controller.evaluators.common import CallCb, Evaluator
from hat.controller.evaluators.js import JsEvaluator
from hat.controller.evaluators.py import PyEvaluator


__all__ = ['CallCb',
           'Evaluator',
           'JsEvaluator',
           'PyEvaluator',
           'create_evaluator']


def create_evaluator(interpreter_type: interpreters.InterpreterType,
                     action_codes: dict[common.ActionName, str],
                     infos: Iterable[common.UnitInfo],
                     call_cb: CallCb
                     ) -> Evaluator:
    interpreter = interpreters.create_interpreter(interpreter_type)

    if isinstance(interpreter, interpreters.JsInterpreter):
        return JsEvaluator(interpreter=interpreter,
                           action_codes=action_codes,
                           infos=infos,
                           call_cb=call_cb)

    if isinstance(interpreter, interpreters.PyInterpreter):
        return PyEvaluator(interpreter=interpreter,
                           action_codes=action_codes,
                           infos=infos,
                           call_cb=call_cb)

    raise ValueError('unsupporter interpreter type')
