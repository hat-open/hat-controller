import asyncio

from hat import aio

from hat.controller import common


class TriggersUnit(common.Unit):

    def __init__(self, conf, raise_trigger_cb):
        self._raise_trigger_cb = raise_trigger_cb
        self._async_group = aio.Group()

    @property
    def async_group(self):
        return self._async_group

    async def call(self, function, args, trigger):
        if function == 'getCurrent':
            if not trigger:
                return

            return {'type': trigger.type,
                    'name': trigger.name,
                    'data': trigger.data}

        if function == 'raise':
            name = args[0]
            data = args[1] if len(args) > 1 else None
            delay = args[2] if len(args) > 2 else 0

            if not isinstance(name, str):
                raise Exception('invalid name type')

            if not isinstance(delay, (int, float)):
                raise Exception('invalid delay type')

            t = common.Trigger(type='triggers/custom',
                               name=name,
                               data=data)

            if delay > 0:
                self.async_group.spawn(self._raise_trigger_with_delay,
                                       t, delay)

            else:
                await self._raise_trigger(t)

            return

        raise Exception('unsupported function')

    async def _raise_trigger(self, trigger):
        if not self._raise_trigger_cb:
            return

        await aio.call(self._raise_trigger_cb, trigger)

    async def _raise_trigger_with_delay(self, trigger, delay):
        await asyncio.sleep(delay / 1000)
        await self._raise_trigger(trigger)


info = common.UnitInfo(name='triggers',
                       functions={'getCurrent', 'raise'},
                       create=TriggersUnit,
                       json_schema_id=None,
                       json_schema_repo=None)
