import asyncio
import functools
import pytest

from hat import aio

from hat.controller import common
import hat.controller.environment
import hat.controller.evaluators
import hat.controller.interpreters


class MockEvaluator(hat.controller.evaluators.Evaluator):

    def __init__(self,
                 interpreter_type,
                 action_codes,
                 infos,
                 call_cb,
                 eval_code_cb=None,
                 eval_action_cb=None):
        self._interpreter_type = interpreter_type
        self._action_codes = action_codes
        self._infos = infos
        self._call_cb = call_cb
        self._eval_code_cb = eval_code_cb
        self._eval_action_cb = eval_action_cb

    def eval_code(self, code: str):
        if self._eval_code_cb:
            self._eval_code_cb(code)

    def eval_action(self, action):
        if self._eval_action_cb:
            self._eval_action_cb(action)


class MockUnit(common.Unit):

    def __init__(self, conf, raise_trigger_cb=None, call_cb=None):
        self._async_group = aio.Group()
        self._call_cb = call_cb

    @property
    def async_group(self):
        return self._async_group

    def call(self, function, args, trigger):
        if self._call_cb:
            return self._call_cb(function, args, trigger)


async def test_create(monkeypatch):
    env_conf = {
        'name': 'env1',
        'interpreter': 'DUKTAPE',
        'init_code': "",
        'actions': []}

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    MockEvaluator)

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[],
            trigger_queue_size=100)

        await asyncio.sleep(0.01)

        assert env.is_open

        env.close()
        await env.wait_closing()
        assert env.is_closing
        await env.wait_closed()
        assert env.is_closed
        await env.async_close()


@pytest.mark.parametrize('interpreter_type',
                         hat.controller.interpreters.InterpreterType)
async def test_create_evaluator(monkeypatch, interpreter_type):
    a1_code = 'some code of action 1'
    a2_code = 'some code of action 2'
    env_conf = {
        'name': 'env1',
        'interpreter': interpreter_type.value,
        'init_code': "",
        'actions': [
            {'name': 'a1',
             'triggers': [{'type': 'test',
                           'name': 'a1'}],
             'code': a1_code},
            {'name': 'a2',
             'triggers': [{'type': 'test',
                           'name': 'a2'}],
             'code': a2_code}]}

    unit = MockUnit(None)
    unit_info = common.UnitInfo(
            name='u1',
            functions={'f1'},
            create=MockUnit,
            json_schema_id=None,
            json_schema_repo=None)
    unit_proxy = hat.controller.environment.UnitProxy(
        unit=unit,
        info=unit_info)

    loop = asyncio.get_running_loop()
    evaluator_args_queue = aio.Queue()

    def ext_create_mock_evaluator(*args):
        loop.call_soon_threadsafe(evaluator_args_queue.put_nowait, args)
        return MockEvaluator(*args)

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    ext_create_mock_evaluator)

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[unit_proxy])

        (interpreter_type_arg,
         action_codes,
         infos,
         call_cb) = await evaluator_args_queue.get()

        assert interpreter_type_arg == interpreter_type
        assert action_codes == {'a1': a1_code,
                                'a2': a2_code}
        assert list(infos) == [unit_info]
        assert callable(call_cb)

        await env.async_close()


async def test_init_code(monkeypatch):
    init_code = "some init code ..."
    env_conf = {
        'name': 'env1',
        'interpreter': 'QUICKJS',
        'init_code': init_code,
        'actions': []}

    loop = asyncio.get_running_loop()
    init_code_queue = aio.Queue()

    def ext_on_init_code(code):
        loop.call_soon_threadsafe(init_code_queue.put_nowait, code)

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    functools.partial(MockEvaluator,
                                      eval_code_cb=ext_on_init_code))

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[])

        evaluated_init_code = await init_code_queue.get()
        assert evaluated_init_code == init_code

        await env.async_close()


async def test_action(monkeypatch):
    code = 'some random code goes here...'
    env_conf = {
        'name': 'env1',
        'interpreter': 'CPYTHON',
        'init_code': "",
        'actions': [
            {'name': 'a1',
             'triggers': [{'type': 'test',
                           'name': 'a1'}],
             'code': code}]}

    loop = asyncio.get_running_loop()
    action_queue = aio.Queue()

    def ext_on_eval_action(action):
        loop.call_soon_threadsafe(action_queue.put_nowait, action)

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    functools.partial(
                        MockEvaluator,
                        eval_action_cb=ext_on_eval_action))

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[])

        await asyncio.sleep(0.01)
        assert action_queue.empty()

        process_trigger_res = await env.process_trigger(common.Trigger(
            type='test',
            name='a1',
            data=None))
        assert process_trigger_res is None

        action = await action_queue.get()
        assert action == 'a1'

        await env.async_close()


async def test_unit_call_cb_init(monkeypatch):
    unit_call_args_queue = aio.Queue()
    unit_call_result = {'unit': 'result',
                        'abc': 123}

    def on_unit_call(function, args, trigger):
        unit_call_args_queue.put_nowait((function, args, trigger))
        return unit_call_result

    create_unit = functools.partial(MockUnit, call_cb=on_unit_call)
    unit = create_unit(None)
    unit_name = 'u1'
    unit_fn = 'f1.x.y'
    unit_proxy = hat.controller.environment.UnitProxy(
        unit=unit,
        info=common.UnitInfo(
            name=unit_name,
            functions={unit_fn},
            create=create_unit,
            json_schema_id=None,
            json_schema_repo=None))

    env_conf = {
        'name': 'env1',
        'interpreter': 'LUA',
        'init_code': "",
        'actions': []}

    loop = asyncio.get_running_loop()
    call_result_queue = aio.Queue()

    def ext_on_init_code(call_cb, code):
        result = call_cb(unit_name, unit_fn, ('x', 'y', 123, None))
        loop.call_soon_threadsafe(call_result_queue.put_nowait, result)

    def mock_create_evaluator(*args):
        _, _, _, call_cb = args
        return MockEvaluator(
            *args,
            eval_code_cb=functools.partial(ext_on_init_code, call_cb))

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    mock_create_evaluator)

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[unit_proxy])

        function, args, unit_trigger = await unit_call_args_queue.get()
        assert function == unit_fn
        assert args == ('x', 'y', 123, None)
        assert unit_trigger is None

        call_cb_result = await call_result_queue.get()
        assert call_cb_result == unit_call_result

        await env.async_close()


async def test_unit_call_cb_action(monkeypatch):
    unit_call_args_queue = aio.Queue()
    unit_call_result = {'unit': 'result',
                        'abc': 123}

    def on_unit_call(function, args, trigger):
        unit_call_args_queue.put_nowait((function, args, trigger))
        return unit_call_result

    create_unit = functools.partial(MockUnit, call_cb=on_unit_call)
    unit = create_unit(None)
    unit_name = 'u1'
    unit_fn = 'f1.x.y'
    unit_proxy = hat.controller.environment.UnitProxy(
        unit=unit,
        info=common.UnitInfo(
            name=unit_name,
            functions={unit_fn},
            create=create_unit,
            json_schema_id=None,
            json_schema_repo=None))

    env_conf = {
        'name': 'env1',
        'interpreter': 'LUA',
        'init_code': "",
        'actions': [
            {'name': 'a1',
             'triggers': [{'type': 'test',
                           'name': 'a1'}],
             'code': 'a1 code'}]}

    loop = asyncio.get_running_loop()
    call_result_queue = aio.Queue()

    def ext_on_eval_action(call_cb, action):
        result = call_cb(unit_name, unit_fn, (['a'], 123.4, {'1': 1, '2': 2}))
        loop.call_soon_threadsafe(call_result_queue.put_nowait, result)

    def mock_create_evaluator(*args):
        _, _, _, call_cb = args
        return MockEvaluator(
            *args,
            eval_action_cb=functools.partial(ext_on_eval_action, call_cb))

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    mock_create_evaluator)

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[unit_proxy])

        trigger = common.Trigger(type='test',
                                 name='a1',
                                 data={'test_trigger_data': 123})
        await env.process_trigger(trigger)
        await asyncio.sleep(0.01)

        function, args, unit_trigger = await unit_call_args_queue.get()
        assert function == unit_fn
        assert args == (['a'], 123.4, {'1': 1, '2': 2})
        assert unit_trigger == trigger

        call_cb_result = await call_result_queue.get()
        assert call_cb_result == unit_call_result

        await env.async_close()


async def test_action_exception(monkeypatch, caplog):
    env_conf = {
        'name': 'env1',
        'interpreter': 'DUKTAPE',
        'init_code': "",
        'actions': [
            {'name': 'action_w_exc',
             'triggers': [{'type': 'test',
                           'name': 'action_w_exc'}],
             'code': 'action_w_exc code...'},
            {'name': 'action_wo_exc',
             'triggers': [{'type': 'test',
                           'name': 'action_wo_exc'}],
             'code': 'action_wo_exc code...'}]}

    eval_action_queue = aio.Queue()
    loop = asyncio.get_running_loop()

    def ext_on_eval_action(action):
        loop.call_soon_threadsafe(eval_action_queue.put_nowait, action)
        if action == 'action_w_exc':
            raise Exception("test action exception")

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    functools.partial(
                        MockEvaluator,
                        eval_action_cb=ext_on_eval_action))

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[])

        trigger_action_w_exc = common.Trigger(
            type='test',
            name='action_w_exc',
            data=None)
        await env.process_trigger(trigger_action_w_exc)
        action = await eval_action_queue.get()
        assert action == 'action_w_exc'

        await asyncio.sleep(0.01)
        assert len(caplog.records) == 1
        assert env.is_open

        # action is run again after exception
        await env.process_trigger(trigger_action_w_exc)
        action = await eval_action_queue.get()
        assert action == 'action_w_exc'

        await asyncio.sleep(0.01)
        assert len(caplog.records) == 2
        assert env.is_open

        # another action is called after previous action raised exception
        trigger_action_wo_exc = common.Trigger(type='test',
                                               name='action_wo_exc',
                                               data=None)
        await env.process_trigger(trigger_action_wo_exc)
        action = await eval_action_queue.get()
        assert action == 'action_wo_exc'

        await asyncio.sleep(0.01)
        assert len(caplog.records) == 2
        assert env.is_open

        await env.async_close()


@pytest.mark.parametrize('trigger_type, trigger_name, triggered_actions', [
    ('test/a', 'x/a', {'a1', 'a3', 'a4', 'a5', 'a7'}),
    ('test/a/b', 'x/a', {'a3', 'a5', 'a7'}),
    ('test', 'x/a', {'a3', 'a5', 'a7'}),
    ('test/a', 'x/a/b/c/d/1', {'a3', 'a4'}),
    ('test/a', 'x/bla/123', {'a3', 'a4'}),
    ('test/a', 'x', {'a3', 'a4'}),
    ('test/b', 'y/b', {'a1', 'a3', 'a4', 'a5'}),
    ('test/b', 'y/bla', {'a3', 'a4'}),
    ('test/b', 'y', {'a3', 'a4'}),
    ('test/b', 'z/bla', {'a3'}),
    ('test/c', 'z/c', {'a1', 'a3'}),
    ('test/a', 'bla', {'a3'}),
    ('bla', 'x/a', {'a3', 'a5'}),
    ('bla/123', 'y/b', {'a3', 'a5'}),
    ('test/c', 'z/c', {'a1', 'a3'}),
    ('bla', 'bla/123', {'a3'}),
    ('', '', {'a3'}),
    ('test2/a', 'x/d', {'a2', 'a3'})])
async def test_trigger_subscription(trigger_type, trigger_name,
                                    triggered_actions, monkeypatch):
    env_conf = {
        'name': 'env1',
        'interpreter': 'LUA',
        'init_code': "",
        'actions': [
            {'name': 'a1',
             'triggers': [{'type': 'test/a',
                           'name': 'x/a'},
                          {'type': 'test/b',
                           'name': 'y/b'},
                          {'type': 'test/c',
                           'name': 'z/c'}],
             'code': "some random code of a1"},
            {'name': 'a2',
             'triggers': [{'type': 'test2/a',
                           'name': 'x/d'}],
             'code': "some random code of a2"},
            {'name': 'a3',
             'triggers': [{'type': '*',
                           'name': '*'}],
             'code': "some random code of a3"},
            {'name': 'a4',
             'triggers': [{'type': 'test/a',
                           'name': 'x/*'},
                          {'type': 'test/b',
                           'name': 'y/*'}],
             'code': "some random code of a4"},
            {'name': 'a5',
             'triggers': [{'type': '*',
                           'name': 'x/a'},
                          {'type': '*',
                           'name': 'y/b'}],
             'code': "some random code of a5"},
            {'name': 'a6',
             'triggers': [],
             'code': "some random code of a6"},
            {'name': 'a7',
             'triggers': [{'type': 'test/*',
                           'name': 'x/a'}],
             'code': "some random code of a7"}]}

    loop = asyncio.get_running_loop()
    action_queue = aio.Queue()

    def ext_on_eval_action(action):
        loop.call_soon_threadsafe(action_queue.put_nowait, action)

    with monkeypatch.context() as ctx:
        ctx.setattr(hat.controller.evaluators, 'create_evaluator',
                    functools.partial(
                        MockEvaluator,
                        eval_action_cb=ext_on_eval_action))

        env = hat.controller.environment.Environment(
            environment_conf=env_conf,
            proxies=[])
        await asyncio.sleep(0.01)

        trigger = common.Trigger(type=trigger_type,
                                 name=trigger_name,
                                 data={'test_data': 123})
        await env.process_trigger(trigger)

        triggered_actions_res = set()
        for _ in range(len(triggered_actions)):
            action = await action_queue.get()
            triggered_actions_res.add(action)
        assert triggered_actions_res == triggered_actions

        await asyncio.sleep(0.01)
        assert action_queue.empty()

        await env.async_close()
