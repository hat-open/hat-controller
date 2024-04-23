from .duktape import *  # NOQA
from .quickjs import *  # NOQA

from . import duktape
from . import quickjs


__all__ = ['task_pymodules',
           *duktape.__all__,
           *quickjs.__all__]


def task_pymodules():
    """Build pymodules"""
    return {'actions': None,
            'task_dep': ['pymodules_quickjs',
                         'pymodules_duktape']}
