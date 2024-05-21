import collections
import pytest

from hat import aio

from hat.controller import common
from hat.controller import evaluators
from hat.controller import interpreters


class MockUnit(common.Unit):

    def __init__(self, conf, raise_trigger_cb=None):
        self._async_group = aio.Group()

    @property
    def async_group(self):
        return self._async_group

    def call(self, function, args, trigger):
        pass


@pytest.mark.parametrize('interpreter_type, evaluator_type', [
    (interpreters.InterpreterType.DUKTAPE, evaluators.JsEvaluator),
    (interpreters.InterpreterType.QUICKJS, evaluators.JsEvaluator),
    (interpreters.InterpreterType.CPYTHON, evaluators.PyEvaluator),
    (interpreters.InterpreterType.LUA, evaluators.LuaEvaluator)])
def test_evaluators(interpreter_type, evaluator_type):
    unit_name = 'u1'
    fn_name = 'f1'

    action_codes = {
        'a1': f'units.{unit_name}.{fn_name}("a1");',
        'a2': f'units.{unit_name}.{fn_name}("a2");'}

    infos = [
        common.UnitInfo(
            name=unit_name,
            functions={fn_name},
            create=MockUnit,
            json_schema_id=None,
            json_schema_repo=None)]

    unit_call_args_queue = collections.deque()

    def on_unit_call(unit_name, fn_name, args):
        unit_call_args_queue.append((unit_name, fn_name, args))

    evaluator = evaluators.create_evaluator(
        interpreter_type=interpreter_type,
        action_codes=action_codes,
        infos=infos,
        call_cb=on_unit_call)

    assert isinstance(evaluator, evaluator_type)

    code = f"units.{unit_name}.{fn_name}(123, 'abc');"
    evaluator.eval_code(code)
    called_unit_name, called_fn, called_args = unit_call_args_queue.popleft()
    assert called_unit_name == unit_name
    assert called_fn == fn_name
    assert list(called_args) == [123, 'abc']

    evaluator.eval_action('a1')
    called_unit_name, called_fn, called_args = unit_call_args_queue.popleft()
    assert called_unit_name == unit_name
    assert called_fn == fn_name
    assert list(called_args) == ['a1']

    evaluator.eval_action('a2')
    called_unit_name, called_fn, called_args = unit_call_args_queue.popleft()
    assert called_unit_name == unit_name
    assert called_fn == fn_name
    assert list(called_args) == ['a2']
