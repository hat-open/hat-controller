from hat.controller.common import *  # NOQA

from collections.abc import Callable, Collection

import abc

from hat import json

from hat.controller.common import ActionName, UnitName, FunctionName


CallCb = Callable[[UnitName, FunctionName, Collection[json.Data]],
                  json.Data]


class Evaluator(abc.ABC):
    """Code/action evaluator"""

    @abc.abstractmethod
    def eval_code(self, code: str):
        """Evaluate code"""

    @abc.abstractmethod
    def eval_action(self, action: ActionName):
        """Evaluate action"""
