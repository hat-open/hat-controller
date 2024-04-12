import logging

from hat import aio

from hat.controller import common


class LogUnit(common.Unit):

    def __init__(self, conf, raise_trigger_cb):
        self._log = logging.getLogger(conf['logger'])
        self._async_group = aio.Group()

    @property
    def async_group(self):
        return self._async_group

    def call(self, function, args, trigger):
        if function == 'log':
            level = _get_log_level(args[0])
            msg = args[1]

        elif function == 'debug':
            level = logging.DEBUG
            msg = args[0]

        elif function == 'info':
            level = logging.INFO
            msg = args[0]

        elif function == 'warning':
            level = logging.WARNING
            msg = args[0]

        elif function == 'error':
            level = logging.ERROR
            msg = args[0]

        else:
            raise Exception('unsupported function')

        if not isinstance(msg, str):
            raise Exception('invalid message type')

        self._log.log(level, msg)


info = common.UnitInfo(name='log',
                       functions={'log', 'debug', 'info', 'warning', 'error'},
                       create=LogUnit,
                       json_schema_id='hat-controller://units/log.yaml',
                       json_schema_repo=common.json_schema_repo)


def _get_log_level(name):
    if name == 'DEBUG':
        return logging.DEBUG

    if name == 'INFO':
        return logging.INFO

    if name == 'WARNING':
        return logging.WARNING

    if name == 'ERROR':
        return logging.ERROR

    raise ValueError('unsupported name')
