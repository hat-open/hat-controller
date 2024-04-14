import pytest

import hat.controller.interpreters._quickjs


@pytest.mark.parametrize('code, result', [
    ('null', None),
    ('true', True),
    ('false', False),
    ('0', 0),
    ('123', 123),
    ('-42', -42),
    ('0.0', 0.0),
    ('1.5', 1.5),
    ('"abc"', 'abc'),
    ('[]', []),
    ('[1, true, "42"]', [1, True, '42']),
    ('({})', {}),
    ('({"abc": 123})', {'abc': 123})
])
def test_eval(code, result):
    interpreter = hat.controller.interpreters._quickjs.Interpreter()
    val = interpreter.eval(code)
    assert val == result


@pytest.mark.parametrize('code, args, result', [
    ('(function () { return null; })', [], None),
    ('(function () { return 123; })', [], 123),
    ('(function (x) { return x; })', [None], None),
    ('(function (x) { return x; })', [True], True),
    ('(function (x) { return x; })', [[1, 2, 3]], [1, 2, 3]),
    ('(function (x) { return x; })', [{}], {}),
    ('(function (x) { return x; })', [{'a': [{}]}], {'a': [{}]}),
    ('(function (x, y) { return x + y; })', [1, 2], 3),
    ('(function () { return Array.from(arguments); })',
     [1, True, {'a': {}}, ['abc']],
     [1, True, {'a': {}}, ['abc']])
])
def test_eval_function(code, args, result):
    interpreter = hat.controller.interpreters._quickjs.Interpreter()
    fn = interpreter.eval(code)
    val = fn(*args)
    assert val == result


def test_eval_raise_exception():
    interpreter = hat.controller.interpreters._quickjs.Interpreter()
    with pytest.raises(Exception, match="abc"):
        interpreter.eval('throw "abc"')


@pytest.mark.parametrize('args', [
    [],
    [None],
    [1, None, {}, []]
])
def test_eval_function_arguments(args):
    interpreter = hat.controller.interpreters._quickjs.Interpreter()
    fn = interpreter.eval('(function (f, args) { return f(...args);  })')
    val = fn((lambda *args: list(args)), args)
    assert val == args


def test_eval_catch_py_exception():

    def cb():
        raise Exception('abc')

    interpreter = hat.controller.interpreters._quickjs.Interpreter()
    fn = interpreter.eval(
        '(function (f) { try { f(); return 123; } catch(e) { return e; }})')
    val = fn(cb)
    assert val == 'abc'


def test_t1():
    interpreter = hat.controller.interpreters._quickjs.Interpreter()
    fn = interpreter.eval('(function (arg) { return {fn: arg.fn}; })')
    arg = {'fn': lambda a, b: a + b}
    result = fn(arg)
    del fn
    del arg
    del interpreter
    assert result['fn'](1, 2) == 3


def test_t2():
    interpreter = hat.controller.interpreters._quickjs.Interpreter()
    fn = interpreter.eval('(function () { return 123; })')
    del interpreter
    assert fn() == 123
