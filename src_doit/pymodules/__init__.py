from .duktape import *  # NOQA
from .lua import *  # NOQA
from .quickjs import *  # NOQA

from . import duktape
from . import lua
from . import quickjs


__all__ = ['task_pymodules',
           *duktape.__all__,
           *lua.__all__,
           *quickjs.__all__]


def task_pymodules():
    """Build pymodules"""
    return {'actions': None,
            'task_dep': ['pymodules_duktape',
                         'pymodules_lua',
                         'pymodules_quickjs']}
