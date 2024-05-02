import pytest

import hat.controller.interpreters


interpreter_types = [hat.controller.interpreters.InterpreterType.DUKTAPE,
                     hat.controller.interpreters.InterpreterType.QUICKJS]


@pytest.mark.parametrize('interpreter_type', interpreter_types)
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
def test_eval(interpreter_type, code, result):
    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    val = interpreter.eval(code)
    assert val == result


@pytest.mark.parametrize('interpreter_type', interpreter_types)
@pytest.mark.parametrize('code, args, result', [
    ('(function () { return null; })', [], None),
    ('(function () { return 123; })', [], 123),
    ('(function (x) { return x; })', [None], None),
    ('(function (x) { return x; })', [True], True),
    ('(function (x) { return x; })', [[1, 2, 3]], [1, 2, 3]),
    ('(function (x) { return x; })', [{}], {}),
    ('(function (x) { return x; })', [{'a': [{}]}], {'a': [{}]}),
    ('(function (x, y) { return x + y; })', [1, 2], 3),
    ('(function () { return Array.prototype.slice.call(arguments); })',
     [1, True, {'a': {}}, ['abc']],
     [1, True, {'a': {}}, ['abc']])
])
def test_eval_function(interpreter_type, code, args, result):
    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    fn = interpreter.eval(code)
    val = fn(*args)
    assert val == result


@pytest.mark.parametrize('interpreter_type', interpreter_types)
def test_eval_raise_exception(interpreter_type):
    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    with pytest.raises(Exception, match="abc"):
        interpreter.eval('throw "abc"')


@pytest.mark.parametrize('interpreter_type', interpreter_types)
@pytest.mark.parametrize('args', [
    [],
    [None],
    [1, None, {}, []]
])
def test_eval_function_arguments(interpreter_type, args):
    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    fn = interpreter.eval(
        '(function (f, args) { return f.apply(null, args); })')
    val = fn((lambda *xs: list(xs)), args)
    assert val == args


@pytest.mark.parametrize('interpreter_type', interpreter_types)
def test_eval_catch_py_exception(interpreter_type):

    def cb():
        raise Exception('abc')

    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    fn = interpreter.eval('(function (f) { try { f(); return 123; } '
                          'catch(e) { return String(e); }})')
    val = fn(cb)
    assert val.endswith('abc')


@pytest.mark.parametrize('interpreter_type', interpreter_types)
def test_t1(interpreter_type):
    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    fn = interpreter.eval('(function (arg) { return {fn: arg.fn}; })')
    arg = {'fn': lambda a, b: a + b}
    result = fn(arg)
    del fn
    del arg
    del interpreter
    assert result['fn'](1, 2) == 3


@pytest.mark.parametrize('interpreter_type', interpreter_types)
def test_t2(interpreter_type):
    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    fn = interpreter.eval('(function () { return 123; })')
    del interpreter
    assert fn() == 123


@pytest.mark.parametrize('interpreter_type', interpreter_types)
def test_t3(interpreter_type):
    interpreter = hat.controller.interpreters.create_interpreter(
        interpreter_type)
    fn = interpreter.eval("(function (x) { return 'abc' + x.value; })")
    result = fn({'value': 123.45})
    assert result == 'abc123.45'
