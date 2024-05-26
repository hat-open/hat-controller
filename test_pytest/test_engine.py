import contextlib
import importlib
import itertools
import sys
import types
import typing

import pytest

from hat import aio

from hat.controller import common
import hat.controller.engine


@pytest.fixture
def create_unit_module():
    unit_names = []

    def create_unit_module(unit_queue):

        class TestUnit(common.Unit):

            def __init__(self, conf, raise_trigger_cb):
                self._async_group = aio.Group()
                self._conf = conf
                self._raise_trigger_cb = raise_trigger_cb

                unit_queue.put_nowait(self)

            @property
            def async_group(self):
                return self._async_group

            def call(self, function, args, trigger):
                pass

            @property
            def conf(self):
                return self._conf

            @property
            def raise_trigger_cb(self):
                return self._raise_trigger_cb

        for i in itertools.count(1):
            unit_name = f'test_unit_{i}'
            if unit_name not in sys.modules:
                break

        info = common.UnitInfo(name=unit_name,
                               functions={'test_fn'},
                               create=TestUnit,
                               json_schema_id=None,
                               json_schema_repo=None)

        unit_module = types.ModuleType(unit_name)
        unit_module.info = info
        sys.modules[unit_name] = unit_module

        unit_names.append(unit_name)
        return unit_name

    try:
        yield create_unit_module
    finally:
        for unit_name in unit_names:
            del sys.modules[unit_name]


@pytest.fixture
def mock_environment(monkeypatch):

    env_queue = None

    class MockEnvironment(aio.Resource):

        def __init__(self, environment_conf, proxies, trigger_queue_size=4096):
            self._async_group = aio.Group()
            self._conf = environment_conf
            self._trigger_queue = aio.Queue()
            self._unit_proxies = proxies

            if env_queue is not None:
                env_queue.put_nowait(self)

        @property
        def async_group(self):
            return self._async_group

        async def enqueue_trigger(self, trigger):
            self._trigger_queue.put_nowait(trigger)

        @property
        def conf(self):
            return self._conf

        @property
        def trigger_queue(self):
            return self._trigger_queue

        @property
        def unit_proxies(self):
            return self._unit_proxies

    @contextlib.contextmanager
    def mock_environment(environment_queue=None):
        nonlocal env_queue
        env_queue = environment_queue

        with monkeypatch.context() as ctx:
            ctx.setattr(
                hat.controller.environment, 'Environment', MockEnvironment)
            yield

    yield mock_environment


async def test_create():
    conf = {'units': [],
            'environments': []}

    engine = await hat.controller.engine.create_engine(conf)

    assert isinstance(engine, hat.controller.engine.Engine)
    assert engine.is_open

    engine.close()
    await engine.wait_closing()
    assert engine.is_closing
    await engine.wait_closed()
    assert engine.is_closed
    await engine.async_close()


async def test_units(create_unit_module):
    unit_queue = aio.Queue()

    units_conf = []
    for i in range(3):
        unit_module = create_unit_module(unit_queue)
        units_conf.append({'module': unit_module})

    conf = {'units': units_conf,
            'environments': []}

    engine = await hat.controller.engine.create_engine(conf)

    units = []
    for unit_conf in units_conf:
        unit = await unit_queue.get()
        unit_module = unit_conf['module']

        assert isinstance(unit, common.Unit)
        assert unit.is_open
        assert hasattr(unit, 'call')

        unit.conf == unit_conf

        module = importlib.import_module(unit_module)
        unit_info = module.info
        assert isinstance(unit_info, common.UnitInfo)
        assert unit_info.name == unit_module
        assert unit_info.functions == {'test_fn'}
        assert isinstance(unit_info.create, typing.Callable)
        assert unit_info.json_schema_id is None
        assert unit_info.json_schema_repo is None

        units.append(unit)

    assert all(unit.is_open for unit in units)
    assert engine.is_open
    assert unit_queue.empty()

    # closing one unit closes engine and all other units
    units[0].close()
    for unit in units:
        await unit.wait_closed()
    await engine.wait_closed()


async def test_environments(create_unit_module, mock_environment):
    environments_conf = [{
            'name': f'env{i}',
            'init_code': "",
            'actions': []} for i in range(3)]

    unit_queue = aio.Queue()
    units_conf = []
    for i in range(3):
        unit_module = create_unit_module(unit_queue)
        units_conf.append({'module': unit_module})

    conf = {'units': units_conf,
            'environments': environments_conf}

    units = []
    environments = []
    environment_queue = aio.Queue()
    with mock_environment(environment_queue):

        engine = await hat.controller.engine.create_engine(conf)

        for _ in units_conf:
            unit = await unit_queue.get()
            units.append(unit)

        for env_conf in environments_conf:
            env = await environment_queue.get()

            assert env
            assert env.is_open
            assert env.conf == env_conf
            for unit_proxy, unit, unit_conf in zip(env.unit_proxies,
                                                   units,
                                                   units_conf):
                assert isinstance(
                    unit_proxy, hat.controller.environment.UnitProxy)
                assert unit_proxy.unit == unit
                unit_module = importlib.import_module(unit_conf['module'])
                assert unit_proxy.info == unit_module.info

            environments.append(env)

        assert all(env.is_open for env in environments)
        assert environment_queue.empty()

        # closing one enviroment closes engine and all other envs and units
        environments[0].close()
        for env in environments:
            await env.wait_closed()
        for unit in units:
            await unit.wait_closed()
        await engine.wait_closed()


async def test_trigger(create_unit_module, mock_environment):
    unit_queue = aio.Queue()
    unit_module = create_unit_module(unit_queue)
    unit_conf = {'module': unit_module}
    environments_conf = [{'name': f'env{i}',
                          'init_code': "",
                          'actions': []} for i in range(3)]

    conf = {'units': [unit_conf],
            'environments': environments_conf}

    environment_queue = aio.Queue()
    with mock_environment(environment_queue):
        engine = await hat.controller.engine.create_engine(conf)

        unit = await unit_queue.get()

        trigger = common.Trigger(type='test/type',
                                 name='test/name',
                                 data={'test': 123})
        await aio.call(unit.raise_trigger_cb, trigger)

        for _ in environments_conf:
            environment = await environment_queue.get()
            trigger_received = await environment.trigger_queue.get()

            assert trigger_received == trigger

    # unit and environment closed after engine is closed
    await engine.async_close()
    await unit.wait_closed()
    await environment.wait_closed()
