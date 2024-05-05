import pytest

import hat.controller.interpreters


@pytest.mark.parametrize('data, result', [
    ('nil', None),
    ('true', True),
    ('false', False),
    ('123', 123),
    ('1.5', 1.5),
    ('"abc"', 'abc'),
    ('{}', []),
    ('{1, 2, 3}', [1, 2, 3]),
    ('{a=123}', {'a': 123})
])
def test_lua_to_py_data(data, result):
    interpreter = hat.controller.interpreters.create_interpreter(
        hat.controller.interpreters.InterpreterType.LUA)
    fn = interpreter.load(f'return {data}')
    val = fn()
    assert val == result


@pytest.mark.parametrize('data', [
    None, True, False, 123, 1.5, 'abc', {'xyz': {'abc': 42, '': [{'a': 'b'}]}}
])
def test_lua_to_py_fn(data):
    interpreter = hat.controller.interpreters.create_interpreter(
        hat.controller.interpreters.InterpreterType.LUA)
    fn1 = interpreter.load('return (function(x) return x end)')
    fn2 = fn1()
    val = fn2(data)
    assert val == data


def test_lua_error():
    interpreter = hat.controller.interpreters.create_interpreter(
        hat.controller.interpreters.InterpreterType.LUA)
    fn = interpreter.load('x = nil + 123')

    with pytest.raises(Exception):
        fn()


def test_py_error():
    interpreter = hat.controller.interpreters.create_interpreter(
        hat.controller.interpreters.InterpreterType.LUA)
    fn = interpreter.load('return (function(f) f() end)')

    def cb():
        raise Exception('abc')

    try:
        fn()(cb)
        assert False

    except Exception as e:
        assert str(e).endswith('abc')
