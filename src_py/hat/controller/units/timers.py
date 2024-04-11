import asyncio
import datetime
import logging
import time
import zoneinfo

from hat import aio
from hat import util

from hat.controller import common


mlog = logging.getLogger(__name__)


class TimersUnit(common.Unit):

    def __init__(self, conf, raise_trigger_cb):
        self._raise_trigger_cb = raise_trigger_cb
        self._async_group = aio.Group()
        self._tzinfo = zoneinfo.ZoneInfo(conf['timezone'])
        self._timer_confs = {}
        self._absolute_timer_exprs = {}
        self._timer_subgroups = {}

        for timer_conf in conf['timers']:
            name = timer_conf['name']
            self._timer_confs[name] = timer_conf

            if isinstance(timer_conf['time'], str):
                self._absolute_timer_exprs[name] = \
                    util.cron.parse(timer_conf['time'])

            if timer_conf['auto_start']:
                self._call_start(name)

    @property
    def async_group(self):
        return self._async_group

    def call(self, function, args, trigger):
        name = args[0]
        if name not in self._timer_confs:
            raise Exception('invalid timer name')

        if function == 'start':
            return self._call_start(name)

        if function == 'stop':
            return self._call_stop(name)

        raise Exception('unsupported function')

    async def _absolute_timer_loop(self, name):
        try:
            timer_conf = self._timer_confs[name]
            expr = self._absolute_timer_exprs[name]
            repeat = timer_conf['repeat']

            t_prev_local = None
            t_next_local = None

            while True:
                t_utc = datetime.datetime.now(datetime.timezone.utc)
                t_local = t_utc.astimezone(self._tzinfo)

                if t_prev_local is None:
                    t_prev_local = t_local

                if t_next_local is None:
                    t_next_local = util.cron.next(expr, t_prev_local)
                    t_next_utc = t_next_local.astimezone(datetime.timezone.utc)

                if t_utc < t_next_utc:
                    duration = min((t_next_utc - t_utc).total_seconds(), 3600)
                    await asyncio.sleep(duration)
                    continue

                trigger = common.Trigger(type='timers/timer',
                                         name=name,
                                         data=t_next_utc.timestamp() * 1000)
                await self._raise_trigger(trigger)

                if not repeat:
                    break

                t_prev_local = t_next_local
                t_next_local = None

        except Exception as e:
            mlog.error('relative timer loop error: %s', e, exc_info=e)

        finally:
            self._call_stop(name)

    async def _relative_timer_loop(self, name):
        try:
            timer_conf = self._timer_confs[name]
            duration = timer_conf['time']
            repeat = timer_conf['repeat']

            while True:
                await asyncio.sleep(duration)

                trigger = common.Trigger(type='timers/timer',
                                         name=name,
                                         data=time.time() * 1000)
                await self._raise_trigger(trigger)

                if not repeat:
                    break

        except Exception as e:
            mlog.error('relative timer loop error: %s', e, exc_info=e)

        finally:
            self._call_stop(name)

    async def _raise_trigger(self, trigger):
        if not self._raise_trigger_cb:
            return

        await aio.call(self._raise_trigger_cb, trigger)

    def _call_start(self, name):
        self._call_stop(name)

        subgroup = self.async_group.create_subgroup()
        self._timer_subgroups[name] = subgroup

        if name in self._absolute_timer_exprs:
            subgroup.spawn(self._absolute_timer_loop, name)

        else:
            subgroup.spawn(self._relative_timer_loop, name)

    def _call_stop(self, name):
        subgroup = self._timer_subgroups.pop(name, None)
        if not subgroup:
            return

        subgroup.close()


info = common.UnitInfo(name='timers',
                       functions={'start', 'stop'},
                       create=TimersUnit,
                       json_schema_id='hat-controller://units/timers.yaml',
                       json_schema_repo=common.json_schema_repo)
